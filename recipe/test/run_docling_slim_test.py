import codecs; from io import BytesIO;
from docling.utils.text_decoding import decode_text;
from docling.utils.utils import chunkify, create_file_hash;
import hashlib;
assert list(chunkify(iter(range(5)), 2)) == [[0, 1], [2, 3], [4]];
assert list(chunkify((), 2)) == [];
assert decode_text(BytesIO(codecs.BOM_UTF8 + b'Hello docling'), encoding='utf-8') == 'Hello docling';
assert create_file_hash(BytesIO(b'docling')) == hashlib.sha256(b'docling').hexdigest()