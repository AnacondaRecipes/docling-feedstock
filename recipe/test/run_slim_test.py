# Integration smoke test for the docling-slim output.
# Proves the docling-core chunker -> tree_sitter -> grammar chain resolves and
# runs against the packages this build actually resolves (tree-sitter chain comes
# from staging channels; see abs.yaml). No network, no model downloads, no PDF
# fixtures -- everything is generated in memory.

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# 1. docling-slim imports (the package __init__ only resolves a version, so
# import the module that holds the real API)
import docling  # noqa: F401
import docling.document_converter  # noqa: F401

# 2. docling-core transforms + hierarchical chunking on a small in-memory document
from docling_core.transforms.chunker import HierarchicalChunker
from docling_core.types.doc import DoclingDocument

chunk_doc = DoclingDocument(name="test")
chunk_doc.add_text(label="text", text="def hello(): return 42")
chunks = list(HierarchicalChunker().chunk(dl_doc=chunk_doc))
assert any(c.text for c in chunks), "HierarchicalChunker produced no text chunks"
print(f"chunking: {len(chunks)} hierarchical chunk(s)")

# 3. tree-sitter + grammar chain: parse a snippet in each grammar's language
import tree_sitter
import tree_sitter_c
import tree_sitter_javascript
import tree_sitter_python
import tree_sitter_typescript
from tree_sitter import Language, Parser

for mod, src, want in [
    (tree_sitter_python, b"def hello():\n    return 42\n", "module"),
    (tree_sitter_c, b"int main(void) { return 0; }\n", "translation_unit"),
    (tree_sitter_javascript, b"const x = 1;\n", "program"),
]:
    root = Parser(Language(mod.language())).parse(src).root_node
    assert root.type == want, f"{mod.__name__}: root node {root.type} != {want}"
ts_mod, tsx_mod = tree_sitter_typescript
for lang in (ts_mod, tsx_mod):
    Parser(Language(lang.language())).parse(b"const x: number = 1;")
print(f"tree-sitter: {tree_sitter.__version__} + python/c/javascript/typescript grammars OK")

print("docling-slim integration tests PASSED")
