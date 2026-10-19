#!/usr/bin/env python3
"""Exercise inventory behavior with tiny OOXML fixtures, not visual-quality claims."""

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

from inspect_pptx import EMU, NS, inspect_pptx


def shape(text, properties="", x=0, y=0, w=2*EMU, h=EMU):
    return f'''<p:sp><p:nvSpPr><p:cNvPr id="2" name="text"/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm></p:spPr>
      <p:txBody><a:p><a:r>{properties}<a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>'''


def fixture(path, slides, order=None):
    namespaces = " ".join(f'xmlns:{k}="{v}"' for k, v in NS.items())
    order = order or list(range(1, len(slides)+1))
    ids = "".join(f'<p:sldId id="{255+n}" r:id="rId{n}"/>' for n in order)
    rels = "".join(f'<Relationship Id="rId{n}" Type="{NS["r"]}/slide" Target="slides/slide{n}.xml"/>'
                   for n in range(1, len(slides)+1))
    with ZipFile(path, "w") as z:
        z.writestr("ppt/presentation.xml", f'<p:presentation {namespaces}><p:sldIdLst>{ids}</p:sldIdLst><p:sldSz cx="{10*EMU}" cy="{6*EMU}"/></p:presentation>')
        z.writestr("ppt/_rels/presentation.xml.rels", f'<Relationships>{rels}</Relationships>')
        for n, content in enumerate(slides, 1):
            z.writestr(f"ppt/slides/slide{n}.xml", f'<p:sld {namespaces}><p:cSld><p:spTree>{content}</p:spTree></p:cSld></p:sld>')


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "fixture.pptx"

    def test_presentation_order_and_input_unchanged(self):
        fixture(self.path, [shape("甲"), shape("乙")], order=[2, 1])
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        result = inspect_pptx(self.path)
        self.assertEqual([s["paragraphs"] for s in result["slides"]], [["乙"], ["甲"]])
        self.assertEqual(before, hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(result["input_sha256"], before)

    def test_explicit_styles_and_unresolved_inheritance(self):
        prop = '<a:rPr sz="1200"><a:solidFill><a:schemeClr val="accent1"/></a:solidFill><a:ea typeface="TestCJK"/></a:rPr>'
        fixture(self.path, [shape("中文", prop) + shape("继承样式")])
        slide = inspect_pptx(self.path)["slides"][0]
        self.assertEqual(slide["explicit_font_sizes_pt_by_characters"], {"12.0": 2})
        self.assertEqual(slide["unresolved_text_style_runs"], {"color": 1, "size": 1, "font": 1})
        self.assertIn("small_explicit_text_review", slide["review_flags"])
        self.assertTrue(any('accent1' in key for key in slide["explicit_text_colors_by_characters"]))

    def test_color_flags_do_not_claim_bad_design(self):
        content = "".join(shape("字", f'<a:rPr><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:rPr>')
                          for color in ["111111", "FFFFFF", "FF0000", "0000FF"])
        fixture(self.path, [content])
        flags = inspect_pptx(self.path)["slides"][0]["review_flags"]
        self.assertEqual(flags, ["many_explicit_text_colors"])

    def test_group_coordinates_and_rotated_geometry_not_misread(self):
        group = f'''<p:grpSp><p:nvGrpSpPr><p:cNvPr id="1" name="group"/></p:nvGrpSpPr>
          <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{EMU}" cy="{EMU}"/>
          <a:chOff x="0" y="0"/><a:chExt cx="100" cy="100"/></a:xfrm></p:grpSpPr>
          {shape("local coordinates", x=999999999)}</p:grpSp>'''
        rotated = shape("rotated").replace('<a:xfrm>', '<a:xfrm rot="5400000">')
        fixture(self.path, [group + rotated + shape("outside", x=-EMU)])
        slide = inspect_pptx(self.path)["slides"][0]
        self.assertEqual(len(slide["out_of_bounds_top_level"]), 1)
        self.assertEqual(slide["top_level_geometry_unchecked"], 1)

    def test_large_picture_with_native_text_is_only_review_flag(self):
        pic = f'''<p:pic><p:nvPicPr><p:cNvPr id="3" name="background"/></p:nvPicPr>
          <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{10*EMU}" cy="{6*EMU}"/></a:xfrm></p:spPr></p:pic>'''
        fixture(self.path, [pic + shape("Editable title")])
        slide = inspect_pptx(self.path)["slides"][0]
        self.assertEqual(slide["objects"]["text_shapes"], 1)
        self.assertEqual(slide["objects"]["pictures"], 1)
        self.assertIn("full_frame_image_review", slide["review_flags"])
        self.assertNotIn("flattened", slide)

    def test_cli_refuses_input_overwrite(self):
        fixture(self.path, [shape("Keep")])
        before = self.path.read_bytes()
        proc = subprocess.run([sys.executable, str(Path(__file__).with_name("inspect_pptx.py")),
                               str(self.path), "--output", str(self.path)], capture_output=True)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.path.read_bytes(), before)

    def test_notes_links_native_evidence_and_linebreaks(self):
        text = shape("第一行").replace('</a:r></a:p>', '</a:r><a:br/><a:r><a:t>第二行</a:t></a:r></a:p>')
        evidence = '<p:graphicFrame><a:graphic><a:graphicData><a:tbl/><c:chart r:id="chart1"/></a:graphicData></a:graphic></p:graphicFrame>'
        fixture(self.path, [text + evidence])
        with ZipFile(self.path, "a") as z:
            z.writestr("ppt/slides/_rels/slide1.xml.rels", f'''<Relationships>
              <Relationship Id="n1" Type="{NS['r']}/notesSlide" Target="../notesSlides/notesSlide1.xml"/>
              <Relationship Id="link1" Type="{NS['r']}/hyperlink" Target="https://example.com" TargetMode="External"/>
              </Relationships>''')
            ns = " ".join(f'xmlns:{k}="{v}"' for k, v in NS.items())
            z.writestr("ppt/notesSlides/notesSlide1.xml", f'<p:notes {ns}>{shape("来源与备注")}</p:notes>')
        slide = inspect_pptx(self.path)["slides"][0]
        self.assertEqual(slide["paragraphs"], ["第一行\n第二行"])
        self.assertEqual(slide["speaker_notes"], ["来源与备注"])
        self.assertEqual(slide["objects"]["native_charts"], 1)
        self.assertEqual(slide["objects"]["native_tables"], 1)
        self.assertTrue(any(r["external"] and r["target"] == "https://example.com" for r in slide["related_parts"]))

    def test_invalid_zip_cli_is_clear(self):
        self.path.write_text("not a zip")
        proc = subprocess.run([sys.executable, str(Path(__file__).with_name("inspect_pptx.py")),
                               str(self.path)], capture_output=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn(b"Cannot inventory PPTX", proc.stderr)
        self.assertNotIn(b"Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
