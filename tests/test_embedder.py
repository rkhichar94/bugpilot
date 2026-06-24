import pytest
from rag.embedder import embed


def test_embed_returns_list_of_floats():
    result = embed("NullPointerException in UserService.java at line 42")
    assert isinstance(result, list)
    assert len(result) == 384
    assert all(isinstance(v, float) for v in result)


def test_embed_normalised():
    import math
    result = embed("test sentence")
    magnitude = math.sqrt(sum(v * v for v in result))
    assert abs(magnitude - 1.0) < 1e-4


def test_embed_different_texts_differ():
    a = embed("NullPointerException in UserService")
    b = embed("Database connection timeout in RepositoryImpl")
    assert a != b
