from capacity_vision import CapacityAnalyzer, parse_csv


SAMPLE = """periodo,pacotes,pessoas,forecast,capacidade
2026-01,100000,100,98000,115000
2026-02,112000,103,110000,118000
2026-03,130000,108,123000,128000
2026-04,126000,109,132000,130000
2026-05,148000,112,140000,142000
2026-06,162000,114,150000,150000
"""


def test_parse_csv_accepts_portuguese_headers():
    points = parse_csv(SAMPLE)

    assert len(points) == 6
    assert points[0].period == "2026-01"
    assert points[-1].packages == 162000
    assert points[-1].people == 114


def test_analyze_detects_capacity_risk_and_growth_gap():
    report = CapacityAnalyzer(parse_csv(SAMPLE)).analyze()

    assert report.status == "Vermelho"
    assert report.package_change.percent == 62
    assert round(report.people_change.percent or 0, 1) == 14
    assert any("gap" in alert for alert in report.alerts)
    assert any("Capacidade excedida" in alert for alert in report.alerts)


def test_answer_handles_natural_language_questions():
    analyzer = CapacityAnalyzer(parse_csv(SAMPLE))

    answer = analyzer.answer("O volume está subindo ou caindo?")

    assert "alta" in answer
    assert "+62.0%" in answer
