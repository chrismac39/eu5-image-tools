import tempfile
import unittest
from pathlib import Path

from PIL import Image

from import_vanilla_icons import (
    icon_paths,
    import_icons,
    parse_mapping,
    resolved_source,
)


class ImportVanillaIconsTests(unittest.TestCase):
    def test_imports_selected_dds_as_transparent_png(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "vanilla" / "modifier_types"
            source_dir.mkdir(parents=True)
            source = source_dir / "blocked_from_cabinet.dds"
            icon = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            icon.putpixel((32, 32), (220, 30, 20, 200))
            icon.save(source, format="PNG")
            output = root / "imported"

            self.assertEqual(
                import_icons(
                    root / "vanilla",
                    output,
                    mappings=[
                        (
                            "blocked_badge",
                            Path("modifier_types/blocked_from_cabinet.dds"),
                        )
                    ],
                ),
                (1, 0, 0),
            )
            with Image.open(output / "blocked_badge.png") as imported:
                self.assertEqual(imported.size, (64, 64))
                self.assertEqual(imported.mode, "RGBA")
                self.assertEqual(imported.getpixel((32, 32)), (220, 30, 20, 200))
                self.assertEqual(imported.getpixel((0, 0))[3], 0)

    def test_import_all_uses_relative_folder_names_for_unique_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vanilla = root / "vanilla"
            folder = vanilla / "modifier_types"
            folder.mkdir(parents=True)
            Image.new("RGBA", (8, 8), (10, 20, 30, 255)).save(
                folder / "sample.dds", format="PNG"
            )
            output = root / "imported"

            self.assertEqual(
                import_icons(vanilla, output, import_all=True),
                (1, 0, 0),
            )
            self.assertTrue((output / "modifier_types__sample.png").is_file())

    def test_import_all_reports_bad_files_and_keeps_importing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vanilla = root / "vanilla"
            folder = vanilla / "modifier_types"
            folder.mkdir(parents=True)
            Image.new("RGBA", (8, 8), (10, 20, 30, 255)).save(
                folder / "valid.dds", format="PNG"
            )
            (folder / "empty.dds").touch()
            output = root / "imported"

            self.assertEqual(
                import_icons(vanilla, output, import_all=True),
                (1, 0, 1),
            )
            self.assertTrue((output / "modifier_types__valid.png").is_file())
            self.assertFalse((output / "modifier_types__empty.png").exists())

    def test_list_search_filters_relative_vanilla_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "trade_goods").mkdir()
            (root / "modifier_types").mkdir()
            (root / "trade_goods" / "icon_goods_alum.dds").touch()
            (root / "modifier_types" / "blocked_from_cabinet.dds").touch()

            self.assertEqual(
                [
                    path.relative_to(root).as_posix()
                    for path in icon_paths(root, "blocked")
                ],
                ["modifier_types/blocked_from_cabinet.dds"],
            )

    def test_parse_mapping_preserves_equals_in_relative_path(self) -> None:
        self.assertEqual(
            parse_mapping("custom_badge=modifier_types/icon=variant.dds"),
            ("custom_badge", Path("modifier_types/icon=variant.dds")),
        )

    def test_rejects_source_paths_outside_vanilla_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vanilla = root / "vanilla"
            vanilla.mkdir()
            outside = root / "outside.dds"
            outside.touch()

            with self.assertRaisesRegex(ValueError, "escapes vanilla root"):
                resolved_source(vanilla, Path("../outside.dds"))

    def test_rejects_output_directory_inside_vanilla_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vanilla = root / "vanilla"
            vanilla.mkdir()

            with self.assertRaisesRegex(ValueError, "cannot be inside"):
                import_icons(
                    vanilla,
                    vanilla / "output",
                    mappings=[("sample", Path("missing.dds"))],
                )


if __name__ == "__main__":
    unittest.main()
