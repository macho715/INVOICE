import pandas as pd

from core.header_detector import HeaderDetector


def test_header_detector_uses_resolver_signal():
    df = pd.DataFrame(
        [
            ["HITACHI Energy - Report", None, None],
            [None, None, None],
            ["Case#", "Item Desc", "Q'ty"],
            ["A001", "Bolt", 10],
            ["A002", "Nut", 20],
        ]
    )
    detector = HeaderDetector()
    row, confidence = detector.detect_with_column_names(
        df, expected_columns=["CASE NO", "MATERIAL", "QTY"]
    )
    assert row == 2
    assert confidence >= 0.70
