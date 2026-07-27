from hypothesis import given, strategies as st

from orchestrator.canonical import canonical_json_bytes


@given(st.dictionaries(st.text(min_size=1, max_size=12), st.integers(), max_size=20))
def test_canonical_mapping_serialization_is_insertion_order_independent(values: dict[str, int]) -> None:
    assert canonical_json_bytes(values) == canonical_json_bytes(dict(reversed(list(values.items()))))
