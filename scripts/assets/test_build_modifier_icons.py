import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from build_modifier_icons import (
    alpha_bbox,
    compose_icon,
    fit_size,
    find_modifier_file,
    load_rgba,
    main,
    process_good,
    resize_rgba,
    source_candidates,
    trim_visible,
    variant_filename,
)


class BuildModifierIconsTests(unittest.TestCase):
    def test_alpha_bbox_uses_alpha_channel(self) -> None:
        image = Image.new("RGBA", (8, 6), (255, 0, 0, 0))
        image.putpixel((2, 1), (255, 0, 0, 255))
        image.putpixel((5, 4), (0, 0, 255, 12))

        self.assertEqual(alpha_bbox(image), (2, 1, 6, 5))

    def test_trim_visible_rejects_fully_transparent_images(self) -> None:
        with self.assertRaisesRegex(ValueError, "no visible"):
            trim_visible(Image.new("RGBA", (5, 5)), "test image")

    def test_fit_size_preserves_aspect_ratio(self) -> None:
        self.assertEqual(fit_size((400, 200), (100, 100)), (100, 50))
        self.assertEqual(fit_size((200, 400), (100, 100)), (50, 100))

    def test_resize_rgba_avoids_transparent_color_fringe(self) -> None:
        source = Image.new("RGBA", (2, 2), (255, 0, 0, 255))
        source.putpixel((1, 0), (0, 0, 255, 0))

        resized = resize_rgba(source, (16, 16))

        for red, green, blue, alpha in resized.get_flattened_data():
            if alpha:
                self.assertEqual((green, blue), (0, 0))

    def test_composite_is_rgba_transparent_and_modifier_is_overlaid(self) -> None:
        base = Image.new("RGBA", (20, 20), (20, 40, 60, 255))
        modifier = Image.new("RGBA", (4, 4), (220, 30, 20, 128))
        settings = {
            "max_fraction": 0.5,
            "center_x": 0.75,
            "center_y": 0.75,
            "offset_x": 0,
            "offset_y": 0,
        }
        modifier_settings = {
            "max_width": 4,
            "max_height": 4,
            "scale": 1,
            "right_margin": 2,
            "bottom_margin": 2,
            "horizontal_offset": 0,
            "vertical_offset": 0,
        }

        result, box = compose_icon(
            base, modifier, (20, 20), settings, modifier_settings
        )

        self.assertEqual(result.mode, "RGBA")
        self.assertEqual(result.size, (20, 20))
        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertEqual(box, (14, 14, 18, 18))
        self.assertEqual(result.getpixel((14, 14)), (120, 35, 40, 255))

    def test_composite_results_are_deterministic(self) -> None:
        base = Image.new("RGBA", (20, 20), (1, 2, 3, 255))
        modifier = Image.new("RGBA", (4, 4), (4, 5, 6, 200))
        base_settings = {
            "max_fraction": 0.5,
            "center_x": 0.4,
            "center_y": 0.4,
        }
        modifier_settings = {
            "max_width": 4,
            "max_height": 4,
            "right_margin": 2,
            "bottom_margin": 2,
        }

        first, _ = compose_icon(
            base, modifier, (20, 20), base_settings, modifier_settings
        )
        second, _ = compose_icon(
            base, modifier, (20, 20), base_settings, modifier_settings
        )

        self.assertEqual(first.tobytes(), second.tobytes())

    def test_missing_image_is_reported(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_rgba(Path("missing-rgo-test-image.png"))

    def test_invalid_image_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.png"
            path.write_bytes(b"not a PNG")
            with self.assertRaises(OSError):
                load_rgba(path)

    def test_source_scan_excludes_variants_and_nested_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "icon_goods_cassava.png").touch()
            (root / "icon_goods_cassava_positive.png").touch()
            nested = root / "generated"
            nested.mkdir()
            (nested / "icon_goods_taro.png").touch()

            self.assertEqual(
                source_candidates(root),
                [root / "icon_goods_cassava.png"],
            )

    def test_variant_names_preserve_trade_good_underscores(self) -> None:
        source = Path("icon_goods_oldworld_tropical_orchard.png")

        self.assertEqual(
            variant_filename(source, "positive"),
            "oldworld_tropical_orchard_positive.png",
        )
        self.assertEqual(
            variant_filename(source, "negative"),
            "oldworld_tropical_orchard_negative.png",
        )
        self.assertEqual(
            variant_filename(source, "inflation"),
            "oldworld_tropical_orchard_impacts_inflation.png",
        )
        self.assertEqual(
            variant_filename(source, "pop_demand"),
            "global_oldworld_tropical_orchard_pop_demand.png",
        )
        self.assertEqual(
            variant_filename(source, "estate_max_tax"),
            "oldworld_tropical_orchard_estate_max_tax.png",
        )

    def test_processes_different_source_resolutions_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_path = root / "icon_goods_test.png"
            Image.new("RGBA", (64, 32), (20, 40, 60, 255)).save(source_path)
            modifier_dir = root / "modifiers"
            modifier_dir.mkdir()
            Image.new("RGBA", (100, 50), (255, 0, 0, 255)).save(
                modifier_dir / "positive.png"
            )
            output_dir = root / "output"
            preview_dir = root / "previews"
            config = {
                "modifier_dir": str(modifier_dir),
                "output_dir": str(output_dir),
                "preview_dir": str(preview_dir),
                "contact_sheet": str(root / "sheet.png"),
                "output_size": [1254, 1254],
                "preview_size": [128, 128],
                "base": {
                    "max_fraction": 0.83,
                    "center_x": 0.45,
                    "center_y": 0.45,
                },
                "modifiers": {
                    "positive": {
                        "file": "positive.png",
                        "max_width": 430,
                        "max_height": 430,
                        "alpha_bbox_threshold": 16,
                        "right_margin": 24,
                        "bottom_margin": 24,
                    }
                },
            }

            written, skipped = process_good(
                source_path, ("positive",), config, False, True, False
            )

            self.assertEqual((written, skipped), (1, 0))
            with Image.open(output_dir / "test_positive.png") as output:
                self.assertEqual(output.size, (1254, 1254))
                self.assertEqual(output.mode, "RGBA")
                self.assertEqual(output.getpixel((0, 0))[3], 0)
            with Image.open(preview_dir / "test_positive.png") as preview:
                self.assertEqual(preview.size, (128, 128))
                self.assertEqual(preview.mode, "RGBA")
            self.assertEqual(
                process_good(
                    source_path, ("positive",), config, False, True, False
                ),
                (0, 1),
            )
            self.assertEqual(
                process_good(
                    source_path, ("positive",), config, True, True, False
                ),
                (1, 0),
            )

    def test_composes_unconfigured_catalog_modifier_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_path = root / "icon_goods_new_rgo.png"
            base = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
            base.paste((20, 40, 60, 255), (4, 4, 28, 28))
            base.save(source_path)
            modifier_dir = root / "modifiers"
            modifier_dir.mkdir()
            symbol = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
            symbol.paste((240, 180, 20, 255), (2, 2, 7, 7))
            symbol.save(modifier_dir / "estate_max_tax.png")
            output_dir = root / "output"
            config = {
                "modifier_dir": str(modifier_dir),
                "output_dir": str(output_dir),
                "preview_dir": str(root / "previews"),
                "contact_sheet": str(root / "sheet.png"),
                "output_size": [64, 64],
                "preview_size": [32, 32],
                "base": {
                    "max_fraction": 0.6,
                    "center_x": 0.45,
                    "center_y": 0.45,
                },
                "modifiers": {},
                "modifier_defaults": {
                    "max_width": 16,
                    "max_height": 16,
                    "right_margin": 2,
                    "bottom_margin": 2,
                },
            }

            self.assertEqual(
                process_good(
                    source_path,
                    ("estate_max_tax",),
                    config,
                    False,
                    False,
                    False,
                ),
                (1, 0),
            )
            output = output_dir / "new_rgo_estate_max_tax.png"
            self.assertTrue(output.is_file())
            with Image.open(output) as image:
                self.assertEqual(image.size, (64, 64))
                self.assertGreater(image.getpixel((60, 60))[3], 0)

    def test_bundled_overlay_is_fallback_for_local_modifier_directory(self) -> None:
        config = {
            "modifier_dir": "input/modifiers",
            "builtin_modifier_dir": "scripts/assets/builtin_overlays",
        }

        self.assertEqual(
            find_modifier_file(config, "positive.png"),
            Path(__file__).with_name("builtin_overlays").resolve() / "positive.png",
        )

    def test_cli_targets_external_mod_image_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "mod" / "trade_goods"
            source_dir.mkdir(parents=True)
            Image.new("RGBA", (32, 32), (20, 40, 60, 255)).save(
                source_dir / "icon_goods_cassava.png"
            )
            modifier_dir = root / "vanilla-overlays"
            modifier_dir.mkdir()
            Image.new("RGBA", (8, 8), (240, 180, 20, 255)).save(
                modifier_dir / "positive.png"
            )
            Image.new("RGBA", (8, 8), (20, 80, 200, 255)).save(
                modifier_dir / "negative.png"
            )
            output_dir = root / "mod" / "modifier_types"
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "source_dir": "unused-source",
                        "modifier_dir": "unused-modifiers",
                        "output_dir": "unused-output",
                        "output_size": [64, 64],
                        "base": {
                            "max_fraction": 0.6,
                            "center_x": 0.45,
                            "center_y": 0.45,
                        },
                        "modifiers": {
                            "positive": {
                                "file": "positive.png",
                                "max_width": 16,
                                "max_height": 16,
                                "right_margin": 2,
                                "bottom_margin": 2,
                            },
                            "negative": {
                                "file": "negative.png",
                                "max_width": 16,
                                "max_height": 16,
                                "right_margin": 2,
                                "bottom_margin": 2,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(
                sys,
                "argv",
                [
                    "build_modifier_icons.py",
                    "--good",
                    "cassava",
                    "--modifier",
                    "positive",
                    "--modifier",
                    "negative",
                    "--config",
                    str(config_path),
                    "--source-dir",
                    str(source_dir),
                    "--modifier-dir",
                    str(modifier_dir),
                    "--output-dir",
                    str(output_dir),
                    "--no-previews",
                ],
            ):
                self.assertEqual(main(), 0)

            for name in ("cassava_positive.png", "cassava_negative.png"):
                output = output_dir / name
                self.assertTrue(output.is_file())
                with Image.open(output) as image:
                    self.assertEqual(image.size, (64, 64))


if __name__ == "__main__":
    unittest.main()
