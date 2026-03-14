# Hero Portraits Viewer

A local desktop app for browsing hero portrait images in a scrollable, scalable grid and building a selectable “bans” row in a separate window—styled for stream overlays and capture.

## Features

- **Main window**: Alphabetically sorted grid of hero portraits (from `HeroPortraits/`), with zoom and scroll
- **Selection**: Click a portrait to move it to the **BANS** popout; click again in the popout to unselect and return it to the grid
- **BANS window**: Separate window titled “BANS” showing selected portraits in a row with red glow styling; appears in the taskbar for use as a window/source in OBS or other capture tools
- **Styling**: Black/grey theme with semi-transparent rounded red glow on selected portraits

## Requirements

- **Python** 3.10+
- **Pillow** (PIL) 10.0.0+

## Installation

1. Clone or download this repository.
2. Create and use a virtual environment (recommended):

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Place your hero portrait PNGs in the `HeroPortraits/` folder. Files should be named by ID (e.g. `id1.png`, `id10.png`). The app uses `hero_viewer.py`’s `HERO_ID_MAPPINGS` for display order and naming.

## Usage

Run the viewer:

```bash
python hero_viewer.py
```

- **Main window**: Use the zoom slider to scale thumbnails; scroll with the mouse wheel or scrollbars. Click a portrait to add it to the BANS window.
- **BANS window**: Shows selected portraits in a row. Click a portrait to remove it from the selection (it returns to the main grid). Drag the window by the title bar or the grey area to reposition. The window appears in the taskbar as “BANS” so you can select it as a window/source in OBS or similar tools.

## Project structure

```
DL-Twitch-BanBar-Fearless-Draft/
├── README.md
├── requirements.txt
├── hero_viewer.py      # Main application
└── HeroPortraits/      # PNG files (e.g. id1.png, id2.png, …)
```

## Customization

- **Hero order/names**: Edit the `HERO_ID_MAPPINGS` dictionary in `hero_viewer.py` to change sort order and display names.
- **Glow style**: Adjust `make_rounded_glow()` parameters (e.g. `glow_padding`, `corner_radius`, `glow_color`) and the call in `update_popout()` to change the red glow look.

## License

Use and modify as needed for your project.
