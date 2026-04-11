import pytest
from src.preprocessor import Preprocessor

@pytest.fixture
def preprocessor():
    return Preprocessor(max_tokens=10, overlap_tokens=2)

def test_clean_html_tags(preprocessor):
    text = "<p>Hello <b>World</b>!</p>"
    assert preprocessor.clean(text) == "Hello World !"

def test_clean_html_entities(preprocessor):
    text = "R&amp;D is Great &lt;3"
    assert preprocessor.clean(text) == "R&D is Great <3"

def test_clean_empty(preprocessor):
    assert preprocessor.clean("") == ""
    assert preprocessor.clean("   ") == ""

def test_chunk_single(preprocessor):
    text = "Short text"
    chunks = preprocessor.chunk(text)
    assert len(chunks) == 1
    assert chunks[0] == "Short text"

def test_chunk_multiple(preprocessor):
    text = "This is a much longer text that will definitely exceed the ten token limit we set in the fixture."
    chunks = preprocessor.chunk(text)
    assert len(chunks) > 1

def test_process_empty(preprocessor):
    assert preprocessor.process("") == []
    assert preprocessor.process("   ") == []
