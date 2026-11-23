# EU5 Image Tools

Free, MIT-licensed utilities for Europa Universalis V mod image workflows:

- Convert PNG graphics to transparent B8G8R8A8 DDS files with mipmaps.
- Composite existing transparent trade-good artwork with reusable modifier
  overlays. This tool performs image processing only; it does not generate,
  redraw, or alter source artwork.
- Import locally selected DDS icons as PNG overlays, or browse all icons under
  a configurable vanilla icon root.

The repository includes six original, high-resolution generic modifier badges:
positive, negative, inflation, pop demand, blocked, and allowed. These are
standalone utility assets, not extracted or recreated vanilla artwork. No game
files or mod artwork are included. Keep your own base icons in the ignored
`input/` directory.

## Requirements

- Python 3.10+
- Pillow 12.x

From the repository root, create an environment and install Pillow:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r scripts\assets\requirements.txt
```

## Import vanilla DDS icons as local overlays

The importer reads DDS files from a local game installation and writes chosen
icons as PNGs under the ignored `input/modifiers/` directory. It does not
modify the game files or package the imported artwork in this repository.
List available paths (optionally filtered) to find a symbol:

```powershell
.venv\Scripts\python.exe scripts\assets\import_vanilla_icons.py `
  --vanilla-icons-root "C:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\main_menu\gfx\interface\icons" `
  --list --search blocked
```

Select one or more DDS files and assign each a modifier ID. The path is
relative to the icon root:

```powershell
.venv\Scripts\python.exe scripts\assets\import_vanilla_icons.py `
  --vanilla-icons-root "C:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\main_menu\gfx\interface\icons" `
  --map blocked_cabinet=modifier_types\blocked_from_cabinet.dds `
  --map estate_tax=modifier_types\global_estate_max_tax.dds
```

Use `--all` instead of `--map` to convert every DDS below the icon root into
the local catalog. Folder names are included in generated IDs, separated by
double underscores, to avoid filename collisions. Choose a separate
`--output-dir` if you want to keep imports outside `input/modifiers/`.
Existing PNGs are skipped unless `--overwrite` is given. If `--all` finds
unreadable DDS files, it reports them and continues importing the remaining
files, then returns a failure status.

The importer keeps each source icon's native dimensions and alpha. When
compositing, the configured modifier layout scales and places it on the master
icon; the DDS converter then fits the finished modifier-type icon to 64 × 64.
Vanilla DDS compression may already contain artifacts, but this avoids
reconstructing symbols from flattened modifier composites. The original source
files remain untouched.

## Build modifier icon variants

Put transparent base icons in `input/trade_goods/` using the name
`icon_goods_<trade_good>.png`. Trade-good IDs may include underscores. The
included badges are in `scripts/assets/builtin_overlays/`. They are used when
no user-imported overlay with the same ID exists.

Build one icon using a bundled badge:

```powershell
.venv\Scripts\python.exe scripts\assets\build_modifier_icons.py `
  --good oldworld_tropical_orchard --modifier positive --contact-sheet
```

The built-in modifier IDs are `positive`, `negative`, `inflation`,
`pop_demand`, `blocked`, and `allowed`. Imported overlays in
`input/modifiers/` are available by their assigned modifier ID. Other user
overlays can be placed in a custom modifier directory and selected by PNG
filename stem. Unconfigured overlays use the `modifier_defaults` layout and
output as `<trade_good>_<modifier_id>.png`.

Edit `scripts/assets/modifier_icon_config.json` to adjust paths, output size,
base scaling and placement, per-modifier sizing and offsets, output filenames,
alpha-bound thresholds, and resampling. Relative paths in the config are
resolved from the repository root. The default master output follows an EU5
graphics tree at `output/main_menu/gfx/interface/icons/modifier_types/`;
previews and contact sheets are under `output/`.

Build every bundled modifier for one good or every good:

```powershell
.venv\Scripts\python.exe scripts\assets\build_modifier_icons.py `
  --good oldworld_tropical_orchard --all-modifiers --contact-sheet

.venv\Scripts\python.exe scripts\assets\build_modifier_icons.py `
  --all-goods --all-modifiers --contact-sheet
```

The output names are deterministic:

- `<trade_good>_positive.png`
- `<trade_good>_negative.png`
- `<trade_good>_impacts_inflation.png`
- `global_<trade_good>_pop_demand.png`
- `<trade_good>_blocked.png`
- `<trade_good>_allowed.png`
- `<trade_good>_<modifier_id>.png` for other overlays

Transparent padding is trimmed for layout calculations. Resizing uses
premultiplied-alpha filtering, preserves aspect ratios, and leaves original
inputs unchanged. Existing master files are skipped unless `--overwrite` is
provided. Use `--modifier <modifier_id>` to build one badge and
`--no-previews` to omit individual 128 × 128 previews. `--all-modifiers`
includes PNGs in `input/modifiers/` and the bundled catalog.

The included source artwork can be regenerated with:

```powershell
.venv\Scripts\python.exe scripts\assets\generate_builtin_overlays.py
```

## Convert PNG to DDS

The converter scans PNG files recursively under `input/main_menu/gfx/` by
default and writes DDS files beside them. To convert the modifier masters
created above, point it at their `main_menu/gfx` root:

```powershell
.venv\Scripts\python.exe scripts\assets\convert_rgo_images.py `
  --source output\main_menu\gfx
```

The converter fits trade-good icons to 128 × 128 and modifier-type icons to
64 × 64, based on their relative directories. It uses uncompressed
B8G8R8A8 DDS by default, with a complete mip chain. PNG previews are written
under `.local/dds-conversion-previews/`. DDS files with matching names are
replaced when converted; use `--dds-output` to write them to a separate root
instead.

Other useful options include `--format bc3`, `--mipmaps none`,
`--decoded-preview-output <directory>`, and `--small-preview-output
<directory>`. Run either script with `--help` for the full CLI.

## Tests

```powershell
.venv\Scripts\python.exe -m unittest discover -s scripts\assets -p "test_*.py"
```
