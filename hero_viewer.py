"""
Hero Portraits Viewer — local desktop app for browsing hero portraits and
building a BANS selection in a separate, capture-friendly window.
See README.md for setup and usage.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFilter

HERO_DIR = Path(__file__).parent / "HeroPortraits"
THUMB_BASE = 120  # base thumbnail size in pixels
ZOOM_MIN, ZOOM_MAX = 0.5, 2.0

# --- BANS overlay (Option A: chroma-key for OBS) ---
OVERLAY_W, OVERLAY_H = 1920, 1080
CHROMA_KEY = "#0000FF"             # pure blue — keyed out in OBS; chosen via a portrait color
                                   # scan as the color no hero portrait uses (largest margin)
CHROMA_KEY_RGB = tuple(int(CHROMA_KEY.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
OVERLAY_BORDER_COLOR = "#1a1a1a"   # grey frame, matches the BANS bar styling
OVERLAY_BORDER_THICKNESS = 45      # px border, flush to all four edges

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


def make_overlay_border(w, h, thickness,
                        base=(26, 26, 26), highlight=(72, 72, 75), shadow=(6, 6, 6),
                        accent=(200, 45, 45), accent_width=3, glow_radius=7):
    """Beveled grey frame with a soft red inner accent line.

    Returns a w*h RGBA image. Top/left edges catch light (lighter grey) and
    bottom/right fall into shadow, giving a raised 3D bevel; a soft red line
    glows along the inner edge. The interior is filled with the chroma-key
    color so OBS removes it, leaving only the decorative border visible.
    """
    def lerp(a, b, t):
        return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))

    img = Image.new("RGBA", (w, h), CHROMA_KEY_RGB + (255,))  # chroma-key interior
    draw = ImageDraw.Draw(img)
    span = max(thickness - 1, 1)
    for i in range(thickness):
        t = i / span
        light = lerp(highlight, base, t)   # top/left: highlight -> base
        dark = lerp(base, shadow, t)       # bottom/right: base -> shadow
        x0, y0, x1, y1 = i, i, w - 1 - i, h - 1 - i
        draw.line([(x0, y0), (x1, y0)], fill=light)  # top
        draw.line([(x0, y0), (x0, y1)], fill=light)  # left
        draw.line([(x0, y1), (x1, y1)], fill=dark)   # bottom
        draw.line([(x1, y0), (x1, y1)], fill=dark)   # right

    # Soft red inner accent line
    accent_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rect = [thickness, thickness, w - 1 - thickness, h - 1 - thickness]
    ImageDraw.Draw(accent_layer).rectangle(
        rect, outline=accent + (170,), width=accent_width + glow_radius)
    accent_layer = accent_layer.filter(ImageFilter.GaussianBlur(glow_radius))
    ImageDraw.Draw(accent_layer).rectangle(rect, outline=accent + (255,), width=accent_width)
    return Image.alpha_composite(img, accent_layer)


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

    def update_popout(to_back=False):
        nonlocal popout_win, popout_frame
        if popout_win is not None and not popout_win.winfo_exists():
            popout_win = None
            popout_frame = None
        if popout_win is None:
            popout_win = tk.Toplevel(root)
            popout_win.title("BANS")
            # Normal resizable window (keeps its title bar so OBS lists/title-matches it).
            # Maximize or snap it to fill the display like any other window.
            popout_win.geometry(f"{OVERLAY_W}x{OVERLAY_H}")
            popout_win.configure(bg=CHROMA_KEY)
            # Beveled grey frame with a soft red inner accent; chroma-key interior keyed out in
            # OBS. Redrawn to match the current window size so it scales when maximized/snapped.
            bg_label = tk.Label(popout_win, bg=CHROMA_KEY, bd=0, highlightthickness=0)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)

            def render_border(width, height):
                img = make_overlay_border(max(width, 1), max(height, 1), OVERLAY_BORDER_THICKNESS)
                popout_win.border_photo = ImageTk.PhotoImage(img)
                bg_label.configure(image=popout_win.border_photo)

            popout_win._resize_job = None

            def on_overlay_resize(e):
                # Debounce: redraw the border only once the window stops resizing
                if e.widget is not popout_win:
                    return
                if popout_win._resize_job is not None:
                    popout_win.after_cancel(popout_win._resize_job)
                popout_win._resize_job = popout_win.after(
                    120, lambda: render_border(popout_win.winfo_width(), popout_win.winfo_height()))

            popout_win.bind("<Configure>", on_overlay_resize)
            popout_win.after(10, lambda: render_border(popout_win.winfo_width(), popout_win.winfo_height()))
            # Row container: grey panel, centered horizontally and flush against the top border
            popout_frame = tk.Frame(popout_win, bg=OVERLAY_BORDER_COLOR)
            popout_frame.place(relx=0.5, y=OVERLAY_BORDER_THICKNESS, anchor=tk.N)
            popout_frame.lift()
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

            for w in (popout_win, bg_label, popout_frame):
                w.bind("<Button-1>", _on_drag_start)
                w.bind("<B1-Motion>", _on_drag_motion)
                w.bind("<ButtonRelease-1>", _on_drag_stop)
        # On add only, send the overlay to the very back (below all windows, incl. OBS) so it
        # never covers the grid or OBS; OBS Window Capture still grabs it while it's behind.
        if to_back:
            popout_win.lower()
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
                lbl = tk.Label(popout_frame, image=photo, cursor="hand2", bg=OVERLAY_BORDER_COLOR)
                lbl.pack(side=tk.LEFT, padx=4, pady=4)
                lbl.bind("<Button-1>", lambda e, p=path: on_popout_click(p))
            except Exception:
                pass
        # Hide the grey panel entirely when there are no bans (leave only the border)
        if selected_paths:
            popout_frame.place(relx=0.5, y=OVERLAY_BORDER_THICKNESS, anchor=tk.N)
        else:
            popout_frame.place_forget()

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
            update_popout(to_back=True)
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

    # Show the BANS overlay from the start, even before any bans are selected
    update_popout()

    root.mainloop()


if __name__ == "__main__":
    main()
