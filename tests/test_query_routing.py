from src.task9_retrieval_pipeline import (
    _aggregation_numbers,
    _event_subquery,
    _needs_cross_kb,
    expand_query,
)
from src.task10_generation import _has_unresolved_reference, _is_domain_query


def test_named_person_plus_legal_question_routes_to_news_and_law():
    question = (
        "Có thể kết luận Miu Lê phạm Bộ luật Hình sự "
        "chỉ từ kết quả test nhanh dương tính không?"
    )
    assert _needs_cross_kb(question)


def test_plain_person_question_does_not_force_legal_retrieval():
    assert not _needs_cross_kb("Tên thật của Miu Lê là gì?")


def test_unaccented_typo_query_expands_to_canonical_terms():
    expanded = expand_query("Miu Le choi mai thuy o dau?")
    assert "Lê Ánh Nhật" in expanded
    assert "chất ma túy" in expanded


def test_out_of_domain_and_unresolved_pronoun_are_gated():
    assert not _is_domain_query("Ngày mai Hà Nội có mưa không?")
    assert _has_unresolved_reference("Còn cô ấy có bị khởi tố theo Điều 255 không?")


def test_multi_clause_named_event_removes_legal_tail():
    query = "Miu Lê được phát hiện ở đâu, hành vi sử dụng bị xử lý theo điều nào?"
    event_query = _event_subquery(query)
    assert "Miu Lê được phát hiện ở đâu" in event_query
    assert "hành vi" not in event_query


def test_numbered_case_comparison_is_domain_aggregation():
    query = "So sánh vụ 48 đối tượng, 53 đối tượng và 65 đối tượng"
    assert _is_domain_query(query)
    assert _aggregation_numbers(query) == ["48", "53", "65"]
