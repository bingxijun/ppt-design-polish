#!/usr/bin/env python3
"""Read-only PPTX inventory. Standard library; not a renderer or OOXML validator."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import posixpath
import sys
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
}
EMU = 914400


def read_xml(archive, name):
    raw = archive.read(name)
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("DTD/entity declarations are unsupported: " + name)
    return ET.fromstring(raw)


def relationships(archive, part):
    folder, base = posixpath.split(part)
    rel_part = posixpath.join(folder, "_rels", base + ".rels")
    if rel_part not in archive.namelist():
        return {}
    result = {}
    for rel in read_xml(archive, rel_part):
        external = rel.get("TargetMode") == "External"
        target = rel.get("Target", "")
        if not external:
            target = posixpath.normpath(posixpath.join(folder, target)).lstrip("/")
        result[rel.get("Id")] = {
            "type": rel.get("Type", "").rsplit("/", 1)[-1],
            "target": target,
            "external": external,
        }
    return result


def paragraphs(root):
    return [
        "".join((node.text or "") if node.tag == "{" + NS["a"] + "}t" else "\n"
                for node in p.iter() if node.tag in ["{" + NS["a"] + "}t", "{" + NS["a"] + "}br"])
        for p in root.findall(".//a:p", NS)
        if p.find(".//a:t", NS) is not None
    ]


def color_key(properties):
    if properties is None:
        return None
    fill = properties.find("a:solidFill", NS)
    if fill is None or not len(fill):
        return None
    color = fill[0]
    kind = color.tag.split("}")[-1]
    # Preserve scheme tokens and modifiers; do not pretend to resolve theme color.
    attrs = dict(color.attrib)
    mods = [(c.tag.split("}")[-1], dict(c.attrib)) for c in color]
    return json.dumps([kind, attrs, mods], sort_keys=True, ensure_ascii=False)


def object_box(obj):
    # Descendants of groups use group coordinates: only call on top-level objects.
    xf = obj.find("a:xfrm", NS)
    if xf is None:
        xf = obj.find("p:xfrm", NS)
    if xf is None:
        xf = obj.find("p:spPr/a:xfrm", NS)
    if xf is None:
        xf = obj.find("p:grpSpPr/a:xfrm", NS)
    if xf is None or int(xf.get("rot", "0")) % 21600000:
        return None
    off, ext = xf.find("a:off", NS), xf.find("a:ext", NS)
    if off is None or ext is None:
        return None
    return tuple(int(node.get(key, "0")) for node, key in
                 [(off, "x"), (off, "y"), (ext, "cx"), (ext, "cy")])


def object_name(obj):
    prop = obj.find(".//p:cNvPr", NS)
    return prop.get("name", "") if prop is not None else ""


def inspect_slide(archive, part, number, width, height):
    root = read_xml(archive, part)
    rels = relationships(archive, part)
    text = paragraphs(root)
    colors, sizes, fonts = Counter(), Counter(), Counter()
    unresolved = {"color": 0, "size": 0, "font": 0}
    runs = root.findall(".//a:r", NS) + root.findall(".//a:fld", NS)
    for run in runs:
        value = "".join(t.text or "" for t in run.findall("a:t", NS))
        if not value:
            continue
        prop = run.find("a:rPr", NS)
        key = color_key(prop)
        if key:
            colors[key] += len(value)
        else:
            unresolved["color"] += 1
        if prop is not None and prop.get("sz"):
            sizes[str(int(prop.get("sz")) / 100)] += len(value)
        else:
            unresolved["size"] += 1
        found_font = False
        if prop is not None:
            for role in ["latin", "ea", "cs"]:
                face = prop.find("a:" + role, NS)
                if face is not None and face.get("typeface"):
                    fonts[role + ":" + face.get("typeface")] += len(value)
                    found_font = True
        if not found_font:
            unresolved["font"] += 1

    title = ""
    for shape in root.findall(".//p:sp", NS):
        ph = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
        if ph is not None and ph.get("type") in ["title", "ctrTitle"]:
            title = " ".join(paragraphs(shape))
            break

    tree = root.find("p:cSld/p:spTree", NS)
    outside, large_pics = [], []
    unchecked_geometry = 0
    if tree is not None:
        for obj in tree:
            kind = obj.tag.split("}")[-1]
            if kind not in ["sp", "pic", "graphicFrame", "grpSp", "cxnSp"]:
                continue
            box = object_box(obj)
            if box is None:
                unchecked_geometry += 1
                continue
            x, y, w, h = box
            tolerance = EMU * 0.02
            if x < -tolerance or y < -tolerance or x+w > width+tolerance or y+h > height+tolerance:
                outside.append({"name": object_name(obj), "kind": kind,
                                "box_inches": [round(v / EMU, 3) for v in box]})
            if kind == "pic":
                visible_w = max(0, min(x+w, width) - max(x, 0))
                visible_h = max(0, min(y+h, height) - max(y, 0))
                ratio = visible_w * visible_h / (width * height)
                if ratio >= 0.85:
                    large_pics.append({"name": object_name(obj), "visible_area_ratio": round(ratio, 3)})

    notes = []
    for rel in rels.values():
        if rel["type"] == "notesSlide" and not rel["external"]:
            # Placeholder slide-number/header/footer text is excluded from note content.
            for shape in read_xml(archive, rel["target"]).findall(".//p:sp", NS):
                ph = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
                if ph is None or ph.get("type") in [None, "body"]:
                    notes.extend(paragraphs(shape))

    flags = []
    if len(colors) >= 4:
        flags.append("many_explicit_text_colors")
    if large_pics:
        flags.append("full_frame_image_review")
    if outside:
        flags.append("out_of_bounds_review")
    if any(float(size) < 14 for size in sizes):
        flags.append("small_explicit_text_review")
    count = lambda path: len(root.findall(path, NS))
    return {
        "slide": number, "part": part, "hidden": root.get("show") == "0",
        "title_placeholder_text": title,
        "paragraphs": text, "text_characters": sum(map(len, text)),
        "speaker_notes": notes,
        "objects": {"text_shapes": count(".//p:sp[p:txBody]"),
                    "pictures": count(".//p:pic"), "groups": count(".//p:grpSp"),
                    "native_charts": count(".//c:chart"), "native_tables": count(".//a:tbl"),
                    "smartart_links": count(".//dgm:relIds")},
        "explicit_text_colors_by_characters": dict(colors),
        "explicit_font_sizes_pt_by_characters": dict(sizes),
        "explicit_font_faces_by_characters": dict(fonts),
        "unresolved_text_style_runs": unresolved,
        "top_level_geometry_unchecked": unchecked_geometry,
        "out_of_bounds_top_level": outside, "large_top_level_pictures": large_pics,
        "related_parts": list(rels.values()), "review_flags": flags,
    }


def inspect_pptx(path):
    with ZipFile(path) as archive:
        presentation = read_xml(archive, "ppt/presentation.xml")
        if not presentation.tag.startswith("{" + NS["p"] + "}"):
            raise ValueError("Unsupported namespace; convert Strict OOXML to ordinary PPTX first")
        size = presentation.find("p:sldSz", NS)
        if size is None:
            raise ValueError("Missing slide dimensions")
        width, height = int(size.get("cx")), int(size.get("cy"))
        if min(width, height) <= 0:
            raise ValueError("Invalid slide dimensions")
        rels = relationships(archive, "ppt/presentation.xml")
        slides = []
        for n, item in enumerate(presentation.findall("p:sldIdLst/p:sldId", NS), 1):
            rel = rels[item.get("{" + NS["r"] + "}id")]
            if rel["external"] or rel["type"] != "slide":
                raise ValueError("Invalid slide relationship")
            slides.append(inspect_slide(archive, rel["target"], n, width, height))
        media = [{"part": name, "bytes": archive.getinfo(name).file_size,
                  "sha256": hashlib.sha256(archive.read(name)).hexdigest()}
                 for name in archive.namelist() if name.startswith("ppt/media/") and not name.endswith("/")]
    return {
        "schema_version": 1, "input": str(Path(path).resolve()),
        "input_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "slide_count": len(slides),
        "slide_size_inches": [round(width / EMU, 4), round(height / EMU, 4)],
        "limitations": ["Not a renderer, visual score, AI detector, or OOXML validator",
                        "Styles are direct run properties; layout/master/theme inheritance is unresolved",
                        "Geometry covers unrotated top-level objects only; groups are not flattened",
                        "No OCR, clipping, overlap, contrast or complete chart/SmartArt data validation"],
        "slides": slides, "media": media,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--output", type=Path, help="Write JSON here; defaults to stdout")
    args = parser.parse_args()
    if args.output and args.output.resolve() == args.pptx.resolve():
        parser.error("Output must not overwrite the input PPTX")
    try:
        result = inspect_pptx(args.pptx)
        payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
            print(str(args.output.resolve()))
        else:
            print(payload, end="")
    except (OSError, BadZipFile, ET.ParseError, KeyError, TypeError, ValueError) as exc:
        print("Cannot inventory PPTX: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
