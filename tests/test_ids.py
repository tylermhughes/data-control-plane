import time

from app.ids import new_id


def test_ids_have_prefix_and_fixed_length() -> None:
    value = new_id("prj")
    assert value.startswith("prj_")
    assert len(value) == len("prj_") + 26


def test_ids_sort_by_creation_time() -> None:
    first = new_id("prj")
    time.sleep(0.002)
    second = new_id("prj")
    assert first < second


def test_ids_are_unique() -> None:
    assert len({new_id("x") for _ in range(1000)}) == 1000
