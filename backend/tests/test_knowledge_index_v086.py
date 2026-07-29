from app.knowledge.retriever import INDEX_VERSION, build_index, retrieve


def test_knowledge_index_is_versioned_chunked_and_source_locked() -> None:
    first = build_index()
    second = build_index()

    assert first is second
    assert first
    assert all(chunk.metadata["source_id"].startswith("kb:") for chunk in first)
    assert all(len(chunk.metadata["source_hash"]) == 64 for chunk in first)
    hits = retrieve(["dipirona"])
    assert hits
    assert hits[0].to_dict()["index_version"] == INDEX_VERSION
    assert hits[0].to_dict()["chunk_id"]
