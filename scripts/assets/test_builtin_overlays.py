import json
import unittest
from pathlib import Path

from PIL import Image


OVERLAY_DIR = Path(__file__).with_name("builtin_overlays")
OVERLAY_NAMES = (
    "positive",
    "negative",
    "inflation",
    "pop_demand",
    "blocked",
    "allowed",
)


class BuiltinOverlayTests(unittest.TestCase):
    def test_builtin_overlays_are_rgba_and_transparent_around_the_badge(self) -> None:
        for name in OVERLAY_NAMES:
            with self.subTest(name=name):
                path = OVERLAY_DIR / f"{name}.png"
                self.assertTrue(path.is_file())
                with Image.open(path) as image:
                    self.assertEqual(image.mode, "RGBA")
                    self.assertEqual(image.size, (256, 256))
                    self.assertEqual(image.getpixel((0, 0))[3], 0)
                    self.assertIsNotNone(image.getchannel("A").getbbox())

    def test_default_config_uses_every_bundled_overlay(self) -> None:
        config_path = Path(__file__).with_name("modifier_icon_config.json")
        with config_path.open(encoding="utf-8") as file:
            config = json.load(file)

        self.assertEqual(
            Path(config["modifier_dir"]),
            Path("input/modifiers"),
        )
        self.assertEqual(
            Path(config["builtin_modifier_dir"]),
            Path("scripts/assets/builtin_overlays"),
        )
        self.assertEqual(set(config["modifiers"]), set(OVERLAY_NAMES))
        for settings in config["modifiers"].values():
            self.assertTrue((OVERLAY_DIR / settings["file"]).is_file())


if __name__ == "__main__":
    unittest.main()
