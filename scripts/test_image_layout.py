"""Check actual PPTX crop and extent geometry, not a mirror of the layout code."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
from zipfile import ZipFile
import zlib
import xml.etree.ElementTree as ET
from deck import node_run


class ImageLayoutTests(unittest.TestCase):
    def test_cover_crops_and_contain_preserves_source_ratio(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def chunk(kind, data):
                return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data))
            png = b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', 4, 2, 8, 2, 0, 0, 0))
            png += chunk(b'IDAT', zlib.compress((b'\0'+b'\xff\xff\xff'*4)*2))+chunk(b'IEND', b'')
            (root/'image.png').write_bytes(png)
            spec = {'slides': [{'elements': [{'type': 'image', 'path': 'image.png', 'fit': fit,
                    'options': {'x': 1, 'y': 1, 'w': 2, 'h': 2}}]} for fit in ('cover', 'contain')]}
            (root/'deck.json').write_text(json.dumps(spec))
            node_run('build_deck.mjs', root/'deck.json', root/'test.pptx')
            ns = {'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
                  'p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
            with ZipFile(root/'test.pptx') as z:
                crop = ET.fromstring(z.read('ppt/slides/slide1.xml')).find('.//a:srcRect', ns)
                self.assertEqual(crop.attrib, {'l':'25000','r':'25000','t':'0','b':'0'})
                page = ET.fromstring(z.read('ppt/slides/slide2.xml'))
                ext = page.find('.//p:pic/p:spPr/a:xfrm/a:ext', ns)
                self.assertEqual(int(ext.get('cx')), 2*914400)
                self.assertEqual(int(ext.get('cy')), 914400)
                offset = page.find('.//p:pic/p:spPr/a:xfrm/a:off', ns)
                self.assertEqual(int(offset.get('y')), int(1.5*914400))


if __name__ == '__main__': unittest.main()
