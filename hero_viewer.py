"""
Hero Portraits Viewer — local desktop app for browsing hero portraits and
building a BANS selection in a separate, capture-friendly window.
See README.md for setup and usage.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw

HERO_DIR = Path(__file__).parent / "HeroPortraits"
THUMB_BASE = 120  # base thumbnail size in pixels
ZOOM_MIN, ZOOM_MAX = 0.5, 2.0

HERO_ID_MAPPINGS = {
    1: 'Infernus', 2: 'Seven', 3: 'Vindicta', 4: 'Lady Geist',
    6: 'Abrams', 7: 'Wraith', 8: 'McGinnis', 10: 'Paradox',
    11: 'Dynamo', 12: 'Kelvin', 13: 'Haze', 14: 'Holliday',
    15: 'Bebop', 16: 'Calico', 17: 'Grey Talon', 18: 'Mo & Krill',
    19: 'Shiv', 20: 'Ivy', 21: 'Kali', 25: 'Warden', 27: 'Yamato',
    31: 'Lash', 35: 'Viscous', 38: 'Gunslinger', 39: 'The Boss',
    47: 'Tokamak', 48: 'Wrecker', 49: 'Rutger', 50: 'Pocket',
    51: 'Thumper', 52: 'Mirage', 53: 'Fathom', 54: 'Cadence',
    56: 'Bomber', 57: 'Shield Guy', 58: 'Vyper', 59: 'Vandal',
    60: 'Sinclair', 61: 'Trapper', 62: 'Raven', 63: 'Mina',
    64: 'Drifter', 65: 'Venator', 66: 'Victor', 67: 'Paige',
    68: 'Boho', 69: 'The Doorman', 70: 'Skyrunner', 71: 'Swan',
    72: 'Billy', 73: 'Druid', 74: 'Graf', 75: 'Fortuna',
    76: 'Graves', 77: 'Apollo', 78: 'Airheart', 79: 'Rem',
    80: 'Silver', 81: 'Celeste', 82: 'Opera',
}


def _sort_key(path):
    """Order by hero name (alphabetically); unmapped IDs last by ID."""
    stem = path.stem
    if stem.startswith("id") and stem[2:].isdigit():
        hero_id = int(stem[2:])
        name = HERO_ID_MAPPINGS.get(hero_id)
        if name is not None:
            return (0, name)
        return (1, hero_id)
    return (2, stem)


def make_rounded_glow(img, glow_padding=12, corner_radius=20, glow_color=(200, 40, 40, 70)):
    """Composite image with a semi-transparent rounded red glow behind it."""
    w, h = img.size
    pad = glow_padding
    out_w, out_h = w + 2 * pad, h + 2 * pad
    out = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(out, "RGBA")
    draw.rounded_rectangle(
        [(0, 0), (out_w - 1, out_h - 1)],
        radius=corner_radius,
        fill=glow_color,
        outline=(180, 30, 30, 85),
        width=2,
    )
    out.paste(img, (pad, pad), img if img.mode == "RGBA" else None)
    return out


def load_images():
    path = HERO_DIR
    if not path.is_dir():
        return []
    return sorted(path.glob("*.png"), key=_sort_key)


def main():
    root = tk.Tk()
    root.title("Hero Portraits")
    root.minsize(400, 300)
    root.geometry("800x600")

    images = load_images()
    if not images:
        tk.Label(root, text=f"No PNGs found in {HERO_DIR}").pack(expand=True)
        root.mainloop()
        return

    # Scale factor (1.0 = THUMB_BASE)
    scale_var = tk.DoubleVar(value=1.0)

    # Top bar: zoom
    top = ttk.Frame(root, padding=4)
    top.pack(fill=tk.X)
    ttk.Label(top, text="Zoom:").pack(side=tk.LEFT, padx=(0, 4))
    zoom_slider = ttk.Scale(
        top, from_=ZOOM_MIN, to=ZOOM_MAX, variable=scale_var,
        orient=tk.HORIZONTAL, length=200, command=lambda _: rebuild_thumbs()
    )
    zoom_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
    zoom_label = ttk.Label(top)
    zoom_label.pack(side=tk.LEFT, padx=4)

    def update_zoom_label(*_):
        zoom_label.config(text=f"{scale_var.get():.1f}x")
    scale_var.trace_add("write", update_zoom_label)
    update_zoom_label()

    # Scrollable area
    canvas = tk.Canvas(root, highlightthickness=0)
    vbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
    hbar = ttk.Scrollbar(root, orient=tk.HORIZONTAL, command=canvas.xview)

    canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

    vbar.pack(side=tk.RIGHT, fill=tk.Y)
    hbar.pack(side=tk.BOTTOM, fill=tk.X)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Inner frame to hold thumbnails
    inner = ttk.Frame(canvas)
    canvas_window = canvas.create_window((0, 0), window=inner, anchor=tk.NW)

    # Keep inner frame width in sync with canvas
    def on_canvas_configure(e):
        canvas.itemconfig(canvas_window, width=e.width)

    canvas.bind("<Configure>", on_canvas_configure)

    # Cache: path -> (PhotoImage, tk.Label) for images still in grid
    thumb_cache = {}
    # Paths still shown in main grid (order preserved for layout)
    current_paths = list(images)
    # Paths that have been clicked, in click order (shown in popout row)
    selected_paths = []
    popout_win = None
    popout_frame = None
    POPOUT_SIZE = 100  # height for images in popout row

    COLS = 6

    def get_thumb_size():
        return int(THUMB_BASE * scale_var.get())

    def rebuild_thumbs():
        size = get_thumb_size()
        for path, (photo, label) in list(thumb_cache.items()):
            try:
                img = Image.open(path).convert("RGBA")
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                new_photo = ImageTk.PhotoImage(img)
                label.configure(image=new_photo, width=size, height=size)
                label.image = new_photo
            except Exception:
                pass
        update_scroll_region()

    def update_scroll_region():
        inner.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def update_popout():
        nonlocal popout_win, popout_frame
        if popout_win is not None and not popout_win.winfo_exists():
            popout_win = None
            popout_frame = None
        if not selected_paths:
            if popout_win is not None:
                popout_win.destroy()
                popout_win = None
                popout_frame = None
            return
        if popout_win is None:
            popout_win = tk.Toplevel(root)
            # No overrideredirect so the window appears in the taskbar (selectable as a source)
            popout_win.title("BANS")
            popout_win.configure(bg="#0d0d0d")
            popout_frame = tk.Frame(popout_win, padx=8, pady=8, bg="#1a1a1a")
            popout_frame.pack(fill=tk.BOTH, expand=True)
            popout_win.photos = []

            def _on_drag_start(e):
                popout_win._drag_start = (e.x_root, e.y_root, popout_win.winfo_x(), popout_win.winfo_y())

            def _on_drag_motion(e):
                if hasattr(popout_win, "_drag_start") and popout_win._drag_start is not None:
                    sx, sy, wx, wy = popout_win._drag_start
                    popout_win.geometry(f"+{wx + e.x_root - sx}+{wy + e.y_root - sy}")

            def _on_drag_stop(e):
                if hasattr(popout_win, "_drag_start"):
                    popout_win._drag_start = None

            for w in (popout_win, popout_frame):
                w.bind("<Button-1>", _on_drag_start)
                w.bind("<B1-Motion>", _on_drag_motion)
                w.bind("<ButtonRelease-1>", _on_drag_stop)
        popout_win.lift()
        popout_win.focus_force()
        # Clear and rebuild row
        for w in popout_frame.winfo_children():
            w.destroy()
        popout_win.photos.clear()
        for path in selected_paths:
            try:
                img = Image.open(path).convert("RGBA")
                img.thumbnail((POPOUT_SIZE, POPOUT_SIZE), Image.Resampling.LANCZOS)
                glow_img = make_rounded_glow(img, glow_padding=10, corner_radius=18, glow_color=(200, 50, 50, 55))
                photo = ImageTk.PhotoImage(glow_img)
                popout_win.photos.append(photo)
                lbl = tk.Label(popout_frame, image=photo, cursor="hand2", bg="#1a1a1a")
                lbl.pack(side=tk.LEFT, padx=4, pady=4)
                lbl.bind("<Button-1>", lambda e, p=path: on_popout_click(p))
            except Exception:
                pass

    def on_popout_click(path):
        """Unselect: remove from popout and add back to main grid in sorted order."""
        if path not in selected_paths:
            return
        selected_paths.remove(path)
        current_paths.append(path)
        current_paths.sort(key=_sort_key)
        # Create thumbnail and add to grid
        size = get_thumb_size()
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
        except Exception:
            photo = None
        label = tk.Label(inner, image=photo, width=size, height=size, cursor="hand2")
        if photo:
            label.image = photo
        thumb_cache[path] = (photo, label)
        # Regrid all thumbnails
        for i, p in enumerate(current_paths):
            _, lbl = thumb_cache[p]
            lbl.grid(row=i // COLS, column=i % COLS, padx=2, pady=2, sticky=tk.NW)
        label.bind("<Button-1>", on_click(path))
        update_popout()
        update_scroll_region()

    def on_click(p):
        def handler(event=None):
            if p not in thumb_cache:
                return
            # Remove from main grid
            _, label = thumb_cache.pop(p)
            current_paths.remove(p)
            label.destroy()
            # Regrid remaining thumbnails (no gaps)
            for i, path_item in enumerate(current_paths):
                _, lbl = thumb_cache[path_item]
                lbl.grid(row=i // COLS, column=i % COLS, padx=2, pady=2, sticky=tk.NW)
            # Add to selected and show in popout
            selected_paths.append(p)
            update_popout()
            update_scroll_region()
        return handler

    # Build grid of thumbnails
    size = get_thumb_size()
    for i, path in enumerate(images):
        row, col = i // COLS, i % COLS
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
        except Exception:
            photo = None
        label = tk.Label(inner, image=photo, width=size, height=size, cursor="hand2")
        if photo:
            label.image = photo
        label.grid(row=row, column=col, padx=2, pady=2, sticky=tk.NW)
        label.bind("<Button-1>", lambda e, p=path: on_click(p)(e))
        thumb_cache[path] = (photo, label)

    update_scroll_region()

    # Mouse wheel scroll
    def on_mousewheel(e):
        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    root.bind("<MouseWheel>", on_mousewheel)

    root.mainloop()


if __name__ == "__main__":
    main()
