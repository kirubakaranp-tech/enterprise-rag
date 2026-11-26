import shutil

import chromadb
import pytest

import ingest
import registry
import vector_store


class FakeEmbedding(chromadb.EmbeddingFunction):
    def __init__(self):
        pass

    def __call__(self, input):
        return [[float(len(text) % 11), float(text.count("leave")), 1.0] for text in input]

    @staticmethod
    def name():
        return "fake"

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config):
        return FakeEmbedding()


@pytest.fixture
def data(tmp_path, monkeypatch):
    shutil.copytree("data", tmp_path / "data")
    monkeypatch.setattr(ingest, "SOURCES", {"PDF": tmp_path / "data" / "pdfs", "CSV": tmp_path / "data" / "csv"})
    monkeypatch.setattr(registry, "REGISTRY_FILE", tmp_path / "index_registry.json")
    monkeypatch.setattr(vector_store, "CHROMA_FOLDER", tmp_path / "chroma_db")
    monkeypatch.setattr(vector_store, "embedding_function", FakeEmbedding())
    return tmp_path / "data"
