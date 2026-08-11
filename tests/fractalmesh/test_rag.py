from __future__ import annotations

from fractalmesh.memory.vector_store import SQLiteVectorStore
from fractalmesh.rag.embeddings import HashEmbeddingProvider, get_embedding_provider
from fractalmesh.rag.graph import KnowledgeGraph
from fractalmesh.rag.retriever import GraphRAGRetriever


def test_knowledge_graph_add_entity_and_relation() -> None:
    graph = KnowledgeGraph()
    graph.add_entity("alpha", "service", {"name": "Alpha"})
    graph.add_entity("beta", "service", {"name": "Beta"})
    graph.add_relation("alpha", "beta", "calls")
    assert graph.entities["alpha"]["properties"]["name"] == "Alpha"
    assert graph.adjacency["alpha"][0]["to_id"] == "beta"


def test_extract_entities_and_multi_hop() -> None:
    graph = KnowledgeGraph()
    graph.add_entity("alpha", "service", {"name": "Alpha"})
    graph.add_entity("beta", "service", {"name": "Beta"})
    graph.add_entity("gamma", "service", {"name": "Gamma"})
    graph.add_relation("alpha", "beta", "links")
    graph.add_relation("beta", "gamma", "links")
    entities = graph.extract_entities("Alpha connects to Beta")
    traversed = graph.multi_hop_traverse("alpha", max_hops=2)
    assert {entity["entity_id"] for entity in entities} == {"alpha", "beta"}
    assert traversed[-1]["to_id"] == "gamma"


def test_hash_embedding_provider_is_deterministic() -> None:
    provider = HashEmbeddingProvider()
    first = provider.embed("hello world")
    second = provider.embed("hello world")
    assert len(first) == 128
    assert first == second


def test_embedding_provider_factory_falls_back_to_hash() -> None:
    provider = get_embedding_provider({"embedding_provider": "unknown"})
    assert isinstance(provider, HashEmbeddingProvider)


def test_graph_rag_retriever_combines_vector_and_graph(tmp_path) -> None:
    provider = HashEmbeddingProvider()
    vector_store = SQLiteVectorStore(f"sqlite:///{tmp_path / 'vectors.db'}")
    graph = KnowledgeGraph()
    graph.add_entity("alpha", "service", {"name": "Alpha"})
    graph.add_entity("beta", "service", {"name": "Beta"})
    graph.add_relation("alpha", "beta", "depends_on")
    vector_store.store(
        "doc-1",
        provider.embed("Alpha service depends on Beta"),
        "Alpha service depends on Beta",
        {"entities": ["beta"], "source": "unit-test"},
    )
    retriever = GraphRAGRetriever(vector_store, graph, provider)
    results = retriever.retrieve("Alpha")
    assert results
    assert results[0]["provenance"] == "unit-test"
    assert results[0]["score"] > 0
