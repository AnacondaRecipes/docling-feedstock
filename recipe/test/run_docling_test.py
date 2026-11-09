# Integration smoke test for the docling metapackage (docling-slim[standard]
# equivalent). Exercises the docling-parse PDF backend and a full docling
# pipeline conversion WITHOUT model downloads or network access:
# - the PDF is a ~700-byte document built in memory (no large PDF fixtures),
#   parsed through the same docling_parse API docling's backend uses
# - the pipeline test converts a markdown file; markdown uses the model-free
#   SimplePipeline, so no layout/OCR model is downloaded (the PDF pipeline
#   itself requires local layout-model artifacts and stays out of CI scope)

import io
import os
import sys
import tempfile

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# 1. docling-core transforms import
from docling_core.types.doc import DoclingDocument

doc = DoclingDocument(name="test")
doc.add_text(label="text", text="hello docling")
assert len(doc.texts) == 1

# 2. docling_parse python API (same entry point docling's PDF backend uses)
from docling_parse.pdf_parser import (
    DecodeConfig,
    DoclingThreadedPdfParser,
    ThreadedPdfParserConfig,
)

MINIMAL_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 46>>stream
BT /F1 24 Tf 72 720 Td (Hello docling) Tj ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
trailer<</Root 1 0 R/Size 6>>
"""

parser = DoclingThreadedPdfParser(
    parser_config=ThreadedPdfParserConfig(loglevel="fatal"),
    decode_config=DecodeConfig(),
)
doc_key = parser.load(io.BytesIO(MINIMAL_PDF), password=None, page_range=(1, sys.maxsize))
assert parser.page_count(doc_key) >= 1, "docling-parse could not load the minimal PDF"
cells = []
for result in parser.iterate_results():
    cells.extend(cell.text for cell in result.get_page().textline_cells)
    parser.unload(doc_key)
assert any("Hello docling" in c for c in cells), f"text extraction failed: {cells}"
print(f"docling_parse: parsed minimal PDF ({len(MINIMAL_PDF)} bytes), cells: {cells}")

# 3. full docling pipeline, models-free (SimplePipeline -- no HF downloads)
from docling.document_converter import DocumentConverter

with tempfile.TemporaryDirectory() as tmp:
    md_path = os.path.join(tmp, "test.md")
    with open(md_path, "w") as fh:
        fh.write("# Title\n\nHello **docling** world.\n\n- item one\n- item two\n")
    converted = DocumentConverter().convert(md_path).document
    assert len(converted.texts) > 0, "pipeline conversion produced no text"
    md_out = converted.export_to_markdown()
    assert "docling" in md_out, "markdown round-trip lost content"
    print(f"pipeline: converted md -> {len(converted.texts)} text items")

print("docling integration tests PASSED")
