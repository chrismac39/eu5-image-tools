# EU5 Image Tools

Free, MIT-licensed utilities for Europa Universalis V mod image workflows:

- Convert PNG graphics to transparent B8G8R8A8 DDS files with mipmaps.
- Composite existing transparent trade-good artwork with reusable modifier
  overlays. This tool performs image processing only; it does not generate,
  redraw, or alter source artwork.

No game files, mod artwork, or modifier overlays are included. Keep your own
assets in the ignored `input/` directory.

## Requirements

- Python 3.10+
- Pillow 12.x

From the repository root, create an environment and install Pillow:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r scripts\assets\requirements.txt
```

## Build modifier icon variants

Put transparent base icons in `input/trade_goods/` using the name
`icon_goods_<trade_good>.png`. Trade-good IDs may include underscores. Put the
four transparent overlays in `input/modifiers/`:

- `positive.png`
- `negative.png`
- `inflation.png`
- `pop_demand.png`

Edit `scripts/assets/modifier_icon_config.json` to adjust paths, output size,
base scaling and placement, per-modifier scaling and offsets, alpha-bound
thresholds, and resampling. Relative paths in the config are resolved from
the repository root. The default master output follows an EU5 graphics tree
at `output/main_menu/gfx/interface/icons/modifier_types/`; previews and
contact sheets are under `output/`.

Build one good or every good:

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

Transparent padding is trimmed for layout calculations. Resizing uses
premultiplied-alpha filtering, preserves aspect ratios, and leaves original
inputs unchanged. Existing master files are skipped unless `--overwrite` is
provided. Use `--modifier positive` to build only one modifier and
`--no-previews` to omit individual 128 × 128 previews.

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
