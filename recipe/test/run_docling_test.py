# Integration smoke test for the docling metapackage (docling-slim[standard]
# equivalent). Exercises the formats that define the `standard` extra WITHOUT
# model downloads or network access: markdown (SimplePipeline) and the office
# backends (fixtures generated in memory). The compiled docling-parse backend is
# tested in its own feedstock; PDF *pipeline* conversion requires layout-model
# artifacts and is out of scope here.
import os
import tempfile

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# full docling pipeline, models-free (SimplePipeline -- no HF downloads)
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

# office extras: build DOCX/XLSX in memory (no fixtures) and convert
from docx import Document
from openpyxl import Workbook

with tempfile.TemporaryDirectory() as tmp:
    docx_path = os.path.join(tmp, "test.docx")
    document = Document()
    document.add_heading("Title", 0)
    document.add_paragraph("Hello docling")
    document.save(docx_path)
    docx_out = DocumentConverter().convert(docx_path).document.export_to_markdown()
    assert "Hello docling" in docx_out, "docx conversion lost content"
    print("office: converted in-memory docx")

    xlsx_path = os.path.join(tmp, "test.xlsx")
    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "docling"
    sheet["B1"] = 42
    workbook.save(xlsx_path)
    xlsx_out = DocumentConverter().convert(xlsx_path).document.export_to_markdown()
    assert "docling" in xlsx_out, "xlsx conversion lost content"
    print("office: converted in-memory xlsx")

print("docling integration tests PASSED")
