import pytest

from pypeal.parsers import parse_single_method
from pypeal.entities.method import Classification, Stage

methods = [
    (
        '640 changes of Cambridge Surprise Major',
        Stage.MAJOR,
        Classification.SURPRISE,
        'Cambridge',
        640
    ),
    (
        '640 changes Cambridge Surprise Major',
        Stage.MAJOR,
        Classification.SURPRISE,
        'Cambridge',
        640
    ),
    (
        '640 each of Cambridge Surprise Major',
        Stage.MAJOR,
        Classification.SURPRISE,
        'Cambridge',
        640
    ),
    (
        '120 Cambridge Surprise Major',
        Stage.MAJOR,
        Classification.SURPRISE,
        'Cambridge',
        120
    ),
    (
        '1260 Cambridge',
        None,
        None,
        'Cambridge',
        1260
    ),
]


@pytest.mark.parametrize('title,expected_stage,expected_classification,expected_method,expected_changes', methods)
def test_parse_method_title(title: str,
                            expected_stage: Stage,
                            expected_classification: Classification,
                            expected_method: str,
                            expected_changes: int):
    stage, classification, method, changes = parse_single_method(title)
    assert stage == expected_stage
    assert classification == expected_classification
    assert method == expected_method
    assert changes == expected_changes
