from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


SIZE = 256
SCALE = 4
OUTPUT_DIR = Path(__file__).resolve().parent / "builtin_overlays"

PALETTES = {
    "positive": ((37, 166, 92), (19, 105, 61)),
    "negative": ((210, 73, 72), (132, 38, 48)),
    "inflation": ((226, 164, 52), (154, 99, 27)),
    "pop_demand": ((76, 142, 194), (41, 81, 137)),
    "blocked": ((205, 66, 63), (122, 34, 41)),
    "allowed": ((51, 166, 105), (23, 100, 64)),
}


def scaled_box(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return tuple(value * SCALE for value in box)


def create_badge(name: str) -> Image.Image:
    top_color, bottom_color = PALETTES[name]
    canvas_size = SIZE * SCALE
    badge = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))

    shadow = Image.new("RGBA", badge.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse(scaled_box((27, 31, 235, 239)), fill=(10, 17, 26, 150))
    badge.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(5 * SCALE)))

    circle_mask = Image.new("L", badge.size, 0)
    ImageDraw.Draw(circle_mask).ellipse(scaled_box((20, 16, 228, 224)), fill=255)
    gradient = Image.new("RGBA", badge.size, (0, 0, 0, 0))
    gradient_pixels = gradient.load()
    for y in range(16 * SCALE, 225 * SCALE):
        blend = (y / SCALE - 16) / 208
        color = tuple(
            round(top * (1 - blend) + bottom * blend)
            for top, bottom in zip(top_color, bottom_color)
        )
        for x in range(20 * SCALE, 229 * SCALE):
            gradient_pixels[x, y] = (*color, 255)
    gradient.putalpha(circle_mask)
    badge.alpha_composite(gradient)

    draw = ImageDraw.Draw(badge)
    draw.ellipse(
        scaled_box((20, 16, 228, 224)),
        outline=(238, 241, 238, 255),
        width=4 * SCALE,
    )
    draw.arc(
        scaled_box((29, 24, 219, 214)),
        start=198,
        end=342,
        fill=(255, 255, 255, 95),
        width=3 * SCALE,
    )

    if name == "positive":
        draw.rounded_rectangle(
            scaled_box((107, 57, 141, 183)),
            radius=8 * SCALE,
            fill=(18, 67, 45, 210),
        )
        draw.rounded_rectangle(
            scaled_box((57, 103, 191, 137)),
            radius=8 * SCALE,
            fill=(18, 67, 45, 210),
        )
        draw.rounded_rectangle(
            scaled_box((103, 53, 137, 179)),
            radius=8 * SCALE,
            fill=(250, 255, 245, 255),
        )
        draw.rounded_rectangle(
            scaled_box((53, 99, 187, 133)),
            radius=8 * SCALE,
            fill=(250, 255, 245, 255),
        )
    elif name == "negative":
        draw.rounded_rectangle(
            scaled_box((57, 109, 191, 147)),
            radius=10 * SCALE,
            fill=(92, 28, 38, 210),
        )
        draw.rounded_rectangle(
            scaled_box((53, 103, 187, 141)),
            radius=10 * SCALE,
            fill=(255, 246, 239, 255),
        )
    elif name in ("blocked", "allowed"):
        symbol = Image.new("RGBA", badge.size, (0, 0, 0, 0))
        symbol_draw = ImageDraw.Draw(symbol)
        if name == "blocked":
            symbol_draw.line(
                [point * SCALE for point in (76, 76, 172, 172)],
                fill=(86, 27, 34, 220),
                width=26 * SCALE,
            )
            symbol_draw.line(
                [point * SCALE for point in (172, 76, 76, 172)],
                fill=(86, 27, 34, 220),
                width=26 * SCALE,
            )
            symbol_draw.line(
                [point * SCALE for point in (72, 70, 168, 166)],
                fill=(255, 245, 238, 255),
                width=16 * SCALE,
            )
            symbol_draw.line(
                [point * SCALE for point in (168, 70, 72, 166)],
                fill=(255, 245, 238, 255),
                width=16 * SCALE,
            )
        else:
            symbol_draw.line(
                [point * SCALE for point in (61, 127, 103, 168, 190, 83)],
                fill=(17, 75, 51, 220),
                width=28 * SCALE,
                joint="curve",
            )
            symbol_draw.line(
                [point * SCALE for point in (57, 121, 99, 162, 186, 77)],
                fill=(250, 255, 245, 255),
                width=16 * SCALE,
                joint="curve",
            )
        badge.alpha_composite(symbol)
    elif name == "inflation":
        draw = ImageDraw.Draw(badge)
        for x, height in ((58, 46), (90, 67), (122, 88)):
            top = 170 - height
            draw.rectangle(
                scaled_box((x, top, x + 24, 170)),
                fill=(115, 68, 23, 255),
            )
            draw.ellipse(
                scaled_box((x, top - 8, x + 24, top + 8)),
                fill=(255, 220, 121, 255),
                outline=(112, 67, 24, 255),
                width=3 * SCALE,
            )
            draw.arc(
                scaled_box((x, 162, x + 24, 178)),
                start=0,
                end=180,
                fill=(255, 220, 121, 255),
                width=4 * SCALE,
            )
        draw.line(
            [point * SCALE for point in (113, 118, 148, 88, 178, 88)],
            fill=(97, 50, 16, 255),
            width=18 * SCALE,
            joint="curve",
        )
        draw.line(
            [point * SCALE for point in (109, 111, 144, 81, 176, 81)],
            fill=(255, 250, 221, 255),
            width=10 * SCALE,
            joint="curve",
        )
        draw.polygon(
            [
                (169 * SCALE, 70 * SCALE),
                (188 * SCALE, 80 * SCALE),
                (170 * SCALE, 96 * SCALE),
            ],
            fill=(255, 250, 221, 255),
        )
    elif name == "pop_demand":
        draw = ImageDraw.Draw(badge)
        draw.ellipse(
            scaled_box((60, 62, 120, 122)),
            fill=(31, 67, 111, 255),
        )
        draw.ellipse(
            scaled_box((136, 62, 196, 122)),
            fill=(31, 67, 111, 255),
        )
        draw.ellipse(
            scaled_box((64, 56, 120, 112)),
            fill=(255, 238, 206, 255),
        )
        draw.ellipse(
            scaled_box((136, 56, 192, 112)),
            fill=(255, 238, 206, 255),
        )
        draw.rounded_rectangle(
            scaled_box((42, 116, 138, 187)),
            radius=32 * SCALE,
            fill=(255, 238, 206, 255),
        )
        draw.rounded_rectangle(
            scaled_box((118, 116, 214, 187)),
            radius=32 * SCALE,
            fill=(255, 238, 206, 255),
        )
        draw.rectangle(
            scaled_box((68, 146, 190, 190)),
            fill=(255, 238, 206, 255),
        )

    return badge.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in PALETTES:
        image = create_badge(name)
        image.save(OUTPUT_DIR / f"{name}.png", format="PNG", optimize=True)
        image.close()


if __name__ == "__main__":
    main()
