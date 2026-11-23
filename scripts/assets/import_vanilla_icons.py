import argparse
import re
import sys
from pathlib import Path

from PIL import Image


DEFAULT_OUTPUT_DIR = Path("input/modifiers")
MODIFIER_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def parse_mapping(value: str) -> tuple[str, Path]:
    modifier_id, separator, source_path = value.partition("=")
    if not separator or not modifier_id or not source_path:
        raise argparse.ArgumentTypeError(
            "expected MODIFIER_ID=RELATIVE_DDS_PATH"
        )
    if not MODIFIER_ID.fullmatch(modifier_id):
        raise argparse.ArgumentTypeError(
            "modifier IDs must use letters, numbers, underscores, or hyphens"
        )
    return modifier_id, Path(source_path)


def icon_paths(vanilla_root: Path, search: str | None = None) -> list[Path]:
    paths = sorted(
        (
            path
            for path in vanilla_root.rglob("*")
            if path.is_file() and path.suffix.lower() == ".dds"
        ),
        key=lambda path: path.relative_to(vanilla_root).as_posix().casefold(),
    )
    if search:
        search_key = search.casefold()
        paths = [
            path
            for path in paths
            if search_key in path.relative_to(vanilla_root).as_posix().casefold()
        ]
    return paths


def resolved_source(vanilla_root: Path, relative_path: Path) -> Path:
    if relative_path.is_absolute():
        raise ValueError(f"Icon path must be relative to vanilla root: {relative_path}")
    path = (vanilla_root / relative_path).resolve()
    if not path.is_relative_to(vanilla_root):
        raise ValueError(f"Icon path escapes vanilla root: {relative_path}")
    if path.suffix.lower() != ".dds":
        raise ValueError(f"Selected source is not a DDS icon: {relative_path}")
    if not path.is_file():
        raise FileNotFoundError(f"Vanilla DDS icon does not exist: {path}")
    return path


def import_icons(
    vanilla_root: Path,
    output_dir: Path,
    mappings: list[tuple[str, Path]] | None = None,
    import_all: bool = False,
    overwrite: bool = False,
) -> tuple[int, int, int]:
    vanilla_root = vanilla_root.resolve()
    output_dir = output_dir.resolve()
    if output_dir == vanilla_root or output_dir.is_relative_to(vanilla_root):
        raise ValueError("Output directory cannot be inside the vanilla icon root")

    if import_all:
        selected = [
            (
                "__".join(path.relative_to(vanilla_root).with_suffix("").parts),
                path.relative_to(vanilla_root),
            )
            for path in icon_paths(vanilla_root)
        ]
    else:
        selected = mappings or []

    if not selected:
        raise ValueError("No DDS icons selected for import")

    ids: set[str] = set()
    destinations: set[Path] = set()
    sources: list[tuple[str, Path, Path]] = []
    for modifier_id, relative_path in selected:
        if not MODIFIER_ID.fullmatch(modifier_id):
            raise ValueError(f"Invalid modifier ID: {modifier_id}")
        if modifier_id.casefold() in ids:
            raise ValueError(f"Duplicate modifier ID: {modifier_id}")
        ids.add(modifier_id.casefold())

        source = resolved_source(vanilla_root, relative_path)
        destination = output_dir / f"{modifier_id}.png"
        if destination.resolve() in destinations:
            raise ValueError(f"Multiple icons map to {destination.name}")
        destinations.add(destination.resolve())
        sources.append((modifier_id, source, destination))

    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    failed = 0
    for modifier_id, source_path, output_path in sources:
        if output_path.exists() and not overwrite:
            print(f"Skipped existing output (use --overwrite): {output_path}")
            skipped += 1
            continue
        try:
            with Image.open(source_path) as source:
                rgba = source.convert("RGBA")
                rgba.save(output_path, format="PNG")
                rgba.close()
        except (OSError, ValueError) as error:
            print(
                f"Failed {source_path.relative_to(vanilla_root)}: {error}",
                file=sys.stderr,
            )
            failed += 1
            continue
        written += 1
        print(
            f"Imported {source_path.relative_to(vanilla_root)} as "
            f"{modifier_id}.png ({source_path})"
        )
    return written, skipped, failed


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert selected vanilla DDS icons to local PNG modifier overlays."
        )
    )
    parser.add_argument(
        "--vanilla-icons-root",
        required=True,
        help="Root directory containing vanilla icon subfolders.",
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--map",
        action="append",
        type=parse_mapping,
        metavar="MODIFIER_ID=RELATIVE_DDS_PATH",
        help="Import one selected icon; repeat to import multiple icons.",
    )
    selection.add_argument(
        "--all",
        action="store_true",
        help="Import every DDS recursively using its folder path as the ID.",
    )
    selection.add_argument(
        "--list",
        action="store_true",
        help="List paths of DDS icons under the vanilla root.",
    )
    parser.add_argument(
        "--search",
        help="Filter --list results by a case-insensitive path substring.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Local PNG output directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    vanilla_root = Path(args.vanilla_icons_root).resolve()
    if not vanilla_root.is_dir():
        parser.error(f"Vanilla icon root does not exist: {vanilla_root}")

    if args.list:
        paths = icon_paths(vanilla_root, args.search)
        for path in paths:
            print(path.relative_to(vanilla_root))
        print(f"Found {len(paths)} DDS icon(s).")
        return 0
    if args.search:
        parser.error("--search can only be used with --list")

    try:
        written, skipped, failed = import_icons(
            vanilla_root,
            Path(args.output_dir),
            mappings=args.map,
            import_all=args.all,
            overwrite=args.overwrite,
        )
        print(
            f"Imported {written} icon(s); {skipped} existing output(s) skipped; "
            f"{failed} source file(s) failed."
        )
        return int(failed > 0)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
