from src import task8_pageindex_vectorless as pageindex


def test_pageindex_search_is_safe_without_api_key(monkeypatch):
    monkeypatch.setattr(pageindex, "PAGEINDEX_API_KEY", "")

    assert pageindex.pageindex_search("quy định về ma túy", top_k=3) == []


def test_parse_retrieval_builds_pageindex_search_results():
    payload = {
        "status": "completed",
        "retrieved_nodes": [
            {
                "node_id": "node-7",
                "title": "Điều 23",
                "score": 0.91,
                "relevant_contents": [
                    {
                        "page_index": 12,
                        "relevant_content": "Quy định xử phạt hành vi sử dụng trái phép chất ma túy.",
                    }
                ],
            }
        ],
    }

    results = pageindex._parse_retrieval(
        payload,
        doc_id="pi-doc-1",
        source="nghi-dinh-144-2021.pdf",
    )

    assert results == [
        {
            "id": "pageindex::pi-doc-1::node-7::0",
            "content": "Quy định xử phạt hành vi sử dụng trái phép chất ma túy.",
            "score": 0.91,
            "metadata": {
                "source": "nghi-dinh-144-2021.pdf",
                "title": "Điều 23",
                "doc_type": "legal",
                "url": None,
                "chunk_index": 12,
            },
            "retrieval_method": "pageindex",
        }
    ]


def test_pageindex_search_uses_cache_and_survives_one_provider_error(monkeypatch):
    monkeypatch.setattr(pageindex, "PAGEINDEX_API_KEY", "test-key")
    monkeypatch.setattr(
        pageindex,
        "_load_cache",
        lambda: {
            "documents": {
                "first.pdf": {"doc_id": "pi-1", "source": "first.pdf"},
                "second.pdf": {"doc_id": "pi-2", "source": "second.pdf"},
            }
        },
        raising=False,
    )

    def fake_query(doc_id, query):
        if doc_id == "pi-1":
            raise RuntimeError("provider temporarily unavailable")
        return {
            "status": "completed",
            "retrieved_nodes": [
                {
                    "node_id": "n2",
                    "title": "Nguồn thứ hai",
                    "relevant_contents": [{"relevant_content": "Nội dung có bằng chứng."}],
                }
            ],
        }

    monkeypatch.setattr(pageindex, "_query_document", fake_query, raising=False)

    results = pageindex.pageindex_search("câu hỏi", top_k=2)

    assert len(results) == 1
    assert results[0]["retrieval_method"] == "pageindex"
    assert results[0]["metadata"]["source"] == "second.pdf"
