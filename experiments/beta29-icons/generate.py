#!/usr/bin/env python3
"""Generate the two experimental icon faces without using upstream outlines."""
import argparse
import hashlib
import json
from pathlib import Path
from shutil import copyfile

import fontTools
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
TABLER_SHA256 = "c63cae0ba30b9b7309a8df66684bee1daf4862b4ce4387dee9a2b22a28ded29c"
WALL = {
    0xEAE7: "eye-off",
    0xF00F0: "calendar-time",
    0xF0141: "chevron-left",
    0xF0142: "chevron-right",
    0xF0156: "x",
    0xF01DA: "download",
    0xF0238: "flame-filled",
    0xF024B: "folder-filled",
    0xF02D1: "heart-filled",
    0xF02D5: "heart",
    0xF02DA: "history",
    0xF0349: "search",
    0xF03D8: "palette-filled",
    0xF040A: "player-play-filled",
    0xF0493: "settings-filled",
    0xF04FB: "tags",
    0xF051F: "hourglass",
    0xF057E: "volume",
    0xF05F9: "spy",
    0xF062E: "adjustments-horizontal",
    0xF072C: "layout-grid-filled",
    0xF075F: "volume-off",
    0xF0764: "square-filled",
    0xF076E: "dice-5-filled",
    0xF0A24: "aspect-ratio",
    0xF0B74: "list-details",
    0xF0CB8: "playlist",
}
ICED = {
    0xE800: "caret-down-filled",
    0xE801: "snowflake",
    0xE802: "chevron-up",
    0xE803: "chevron-down",
    0xE804: "chevron-left",
    0xE805: "chevron-right",
    0xF00C: "check",
}
FACES = (
    ("wall", "Symbols Nerd Font", "SkwdExperimentWallIcons", WALL,
     "71db104aa66567d0efe0b98758f9dfc1895573a453fe85fb53d1c38544a55106"),
    ("iced", "Iced-Icons", "SkwdExperimentWidgetIcons", ICED,
     "2289860dbd2201295bf451deb155561abf4b1fb06899d6f1f81eb294bfebb7ec"),
)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require_hash(path, expected):
    if digest(path) != expected:
        raise ValueError(f"Unexpected input SHA-256 for {path}")


def bounds(glyph_set, name):
    pen = BoundsPen(glyph_set)
    glyph_set[name].draw(pen)
    if pen.bounds is None:
        raise ValueError(f"Missing outlines for {name}")
    return pen.bounds


def build_face(reference, tabler, family, label, mapping, destination):
    source = tabler.getGlyphSet()
    original = reference.getGlyphSet()
    available = set(tabler.getBestCmap().values())
    charmap = {point: f"uni{point:X}" for point in mapping}
    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    metrics = {".notdef": reference["hmtx"].metrics[".notdef"]}
    rows = []
    for point, icon in mapping.items():
        if icon not in available:
            raise ValueError(f"No encoded Tabler icon named {icon}")
        old_name = reference.getBestCmap()[point]
        left, bottom, right, top = bounds(original, old_name)
        x0, y0, x1, y1 = bounds(source, icon)
        # Fit the ink into the previous bounds without changing aspect ratio.
        scale = min((right - left) / (x1 - x0), (top - bottom) / (y1 - y0))
        dx = (left + right - (x0 + x1) * scale) / 2
        dy = (bottom + top - (y0 + y1) * scale) / 2
        pen = TTGlyphPen(source)
        source[icon].draw(TransformPen(pen, (scale, 0, 0, scale, dx, dy)))
        name = charmap[point]
        glyphs[name] = pen.glyph()
        metrics[name] = (reference["hmtx"][old_name][0], 0)
        rows.append({"unicode": f"{point:X}", "original": old_name, "tabler": icon,
                     "reference_bounds": [left, bottom, right, top]})

    builder = FontBuilder(reference["head"].unitsPerEm, isTTF=True)
    builder.setupGlyphOrder(list(glyphs))
    builder.setupCharacterMap(charmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({
        name: (advance, getattr(glyphs[name], "xMin", bearing))
        for name, (advance, bearing) in metrics.items()
    })
    builder.setupHorizontalHeader(**{
        key: getattr(reference["hhea"], key) for key in ("ascent", "descent", "lineGap")
    })
    builder.setupNameTable({
        "familyName": family, "styleName": "Regular",
        "fullName": label, "uniqueFontIdentifier": f"{label}-1",
        "psName": label, "version": "Version 1.0 Experimental",
        "copyright": "Tabler Icons, Copyright (c) 2020-2024 Paweł Kuna",
        "licenseDescription": (HERE / "TABLER-LICENSE.txt").read_text(),
        "licenseInfoURL": "https://github.com/tabler/tabler-icons/blob/v3.31.0/LICENSE",
    })
    builder.setupOS2(**{
        key: getattr(reference["OS/2"], key) for key in (
            "sTypoAscender", "sTypoDescender", "sTypoLineGap",
            "usWinAscent", "usWinDescent", "fsSelection", "version",
        )
    })
    builder.setupPost()
    # 2024-01-01 UTC in the TrueType epoch. Both outline and metadata are repeatable.
    builder.font["head"].created = builder.font["head"].modified = 3786912000
    builder.font.recalcTimestamp = False
    builder.save(destination)

    with TTFont(destination) as generated:
        assert generated.getBestCmap() == charmap
        for point, row in zip(mapping, rows, strict=True):
            name = charmap[point]
            old_name = reference.getBestCmap()[point]
            assert generated.getGlyphID(name) > 0
            glyph_bounds = bounds(generated.getGlyphSet(), name)
            assert generated["hmtx"][name][0] == reference["hmtx"][old_name][0]
            assert all(abs((a + b) - (c + d)) <= 2 for a, b, c, d in (
                (glyph_bounds[0], glyph_bounds[2], row["reference_bounds"][0], row["reference_bounds"][2]),
                (glyph_bounds[1], glyph_bounds[3], row["reference_bounds"][1], row["reference_bounds"][3]),
            )), row
            row.update(bounds=glyph_bounds, advance=generated["hmtx"][name][0])
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tabler", type=Path)
    parser.add_argument("original_wall", type=Path)
    parser.add_argument("original_iced", type=Path)
    parser.add_argument("output", type=Path, help="new directory")
    args = parser.parse_args()
    if fontTools.__version__ != "4.61.1":
        parser.error("fontTools 4.61.1 is required")
    require_hash(args.tabler, TABLER_SHA256)
    for face, path in zip(FACES, (args.original_wall, args.original_iced), strict=True):
        require_hash(path, face[-1])
    args.output.mkdir(mode=0o700)
    with TTFont(args.tabler) as tabler:
        report = {}
        for (key, family, label, mapping, expected), path in zip(
                FACES, (args.original_wall, args.original_iced), strict=True):
            candidate = args.output / f"{key}.ttf"
            with TTFont(path) as reference:
                rows = build_face(reference, tabler, family, label, mapping, candidate)
            copyfile(path, args.output / f"{key}-original.ttf")
            report[key] = {"original_sha256": expected, "experimental_sha256": digest(candidate),
                           "glyphs": rows}
        (args.output / "glyphs.json").write_text(json.dumps(report, indent=2) + "\n")
    copyfile(HERE / "TABLER-LICENSE.txt", args.output / "TABLER-LICENSE.txt")


if __name__ == "__main__":
    main()
