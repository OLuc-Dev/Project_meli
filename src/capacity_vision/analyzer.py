from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import csv
import io
import math
import re
from typing import Iterable, Sequence


@dataclass(frozen=True)
class DataPoint:
    """Single period of operational capacity data."""

    period: str
    packages: float
    people: float
    forecast: float | None = None
    capacity: float | None = None

    @property
    def productivity(self) -> float | None:
        if self.people <= 0:
            return None
        return self.packages / self.people

    @property
    def capacity_utilization(self) -> float | None:
        if not self.capacity or self.capacity <= 0:
            return None
        return self.packages / self.capacity

    @property
    def forecast_error(self) -> float | None:
        if not self.forecast or self.forecast <= 0:
            return None
        return (self.packages - self.forecast) / self.forecast


@dataclass(frozen=True)
class MetricChange:
    start_period: str
    end_period: str
    start_value: float
    end_value: float
    absolute: float
    percent: float | None
    direction: str


@dataclass(frozen=True)
class CapacityReport:
    status: str
    risk_score: int
    executive_summary: str
    package_change: MetricChange
    people_change: MetricChange
    productivity_change: MetricChange | None
    trend_direction: str
    trend_strength: float
    turning_points: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    highlights: dict[str, str] = field(default_factory=dict)

    def to_markdown(self) -> str:
        sections = [
            "# Capacity Vision ML — análise operacional",
            f"**Status:** {self.status} | **Risco:** {self.risk_score}/100",
            "",
            "## Resumo executivo",
            self.executive_summary,
            "",
            "## Tendência",
            f"Pacotes: {self.trend_direction} com força {self.trend_strength:.2f}.",
            _format_change("Pacotes", self.package_change),
            _format_change("Pessoas", self.people_change),
        ]
        if self.productivity_change:
            sections.append(_format_change("Produtividade", self.productivity_change))
        if self.turning_points:
            sections += ["", "## Viradas detectadas", *_bulletize(self.turning_points)]
        if self.alerts:
            sections += ["", "## Alertas", *_bulletize(self.alerts)]
        if self.recommendations:
            sections += ["", "## Recomendações", *_bulletize(self.recommendations)]
        return "\n".join(sections)


_COLUMN_ALIASES = {
    "period": {"period", "periodo", "período", "data", "date", "mes", "mês", "dia", "semana"},
    "packages": {"packages", "pacotes", "volume", "pkg", "shipments", "processados", "processed"},
    "people": {"people", "pessoas", "headcount", "hc", "colaboradores", "fte", "equipe"},
    "forecast": {"forecast", "previsto", "previsao", "previsão", "demand_forecast", "planejado"},
    "capacity": {"capacity", "capacidade", "cap", "capacidade_planejada"},
}


class CapacityAnalyzer:
    """Analytical engine for package, people and capacity planning signals."""

    def __init__(self, points: Sequence[DataPoint]):
        if len(points) < 2:
            raise ValueError("Informe pelo menos dois períodos para analisar tendência e variação.")
        self.points = sorted(points, key=lambda point: _period_sort_key(point.period))

    def analyze(self) -> CapacityReport:
        first = self.points[0]
        last = self.points[-1]
        package_change = _metric_change(first.period, last.period, first.packages, last.packages)
        people_change = _metric_change(first.period, last.period, first.people, last.people)
        productivity_change = self._productivity_change(first, last)
        trend_direction, trend_strength = self._package_trend()
        turning_points = self._turning_points()
        alerts: list[str] = []
        recommendations: list[str] = []
        risk_score = 10

        growth_gap = _safe_percent(package_change.percent) - _safe_percent(people_change.percent)
        if growth_gap >= 15:
            risk_score += 25
            alerts.append(
                f"Pacotes cresceram {package_change.percent:.1f}% enquanto pessoas cresceram "
                f"{people_change.percent:.1f}%, abrindo gap de {growth_gap:.1f} p.p."
            )
            recommendations.append("Validar se o ganho de produtividade é sustentável por turno e site.")
        elif growth_gap <= -15:
            risk_score += 15
            alerts.append("Headcount cresceu bem acima do volume, com possível capacidade ociosa.")
            recommendations.append("Revisar escala e redistribuição de pessoas antes de novas contratações.")

        worst_capacity = self._worst_capacity_utilization()
        if worst_capacity:
            period, utilization = worst_capacity
            if utilization > 1.05:
                risk_score += 30
                alerts.append(f"Capacidade excedida em {period}: utilização de {utilization * 100:.1f}%.")
                recommendations.append("Criar plano de contingência para reforço, overtime ou redistribuição de demanda.")
            elif utilization > 0.9:
                risk_score += 15
                alerts.append(f"Capacidade próxima do limite em {period}: utilização de {utilization * 100:.1f}%.")

        worst_forecast = self._worst_forecast_error()
        if worst_forecast:
            period, error = worst_forecast
            if abs(error) > 0.15:
                risk_score += 15
                alerts.append(f"Forecast com desvio relevante em {period}: {error * 100:+.1f}% vs. previsto.")
                recommendations.append("Recalibrar forecast usando histórico recente e sazonalidade operacional.")

        if productivity_change and productivity_change.percent is not None:
            if productivity_change.percent < -10:
                risk_score += 20
                alerts.append(f"Produtividade caiu {abs(productivity_change.percent):.1f}% no período analisado.")
                recommendations.append("Investigar absenteísmo, mix de pacotes, treinamento e layout operacional.")
            elif productivity_change.percent > 15 and package_change.percent and package_change.percent > people_change.percent:
                recommendations.append("Monitorar fadiga e qualidade, pois a produtividade subiu junto com pressão de volume.")

        if trend_direction == "queda" and package_change.percent is not None and package_change.percent < -8:
            risk_score += 10
            alerts.append("Volume em queda relevante; validar se é efeito esperado do forecast ou perda de demanda.")

        status = _status_from_score(risk_score)
        executive_summary = self._executive_summary(status, package_change, people_change, productivity_change, alerts)
        highlights = self._highlights()
        return CapacityReport(
            status=status,
            risk_score=min(risk_score, 100),
            executive_summary=executive_summary,
            package_change=package_change,
            people_change=people_change,
            productivity_change=productivity_change,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            turning_points=turning_points,
            alerts=alerts or ["Nenhum alerta crítico detectado com os dados informados."],
            recommendations=recommendations or ["Manter acompanhamento semanal de volume, pessoas e produtividade."],
            highlights=highlights,
        )

    def answer(self, question: str) -> str:
        report = self.analyze()
        normalized = _normalize(question)
        if any(word in normalized for word in ["subindo", "caindo", "tendencia", "tendência"]):
            return (
                f"O volume de pacotes está em {report.trend_direction}. "
                f"De {report.package_change.start_period} até {report.package_change.end_period}, "
                f"a variação foi de {_format_percent(report.package_change.percent)}."
            )
        if any(word in normalized for word in ["pessoas", "headcount", "equipe"]):
            return (
                f"Pessoas variaram {_format_percent(report.people_change.percent)} no período. "
                f"Comparando com pacotes ({_format_percent(report.package_change.percent)}), "
                f"o status é {report.status}."
            )
        if any(word in normalized for word in ["risco", "capacidade", "bem", "qualidade"]):
            return f"Status {report.status}, risco {report.risk_score}/100. {report.executive_summary}"
        return report.executive_summary

    def _productivity_change(self, first: DataPoint, last: DataPoint) -> MetricChange | None:
        if first.productivity is None or last.productivity is None:
            return None
        return _metric_change(first.period, last.period, first.productivity, last.productivity)

    def _package_trend(self) -> tuple[str, float]:
        values = [point.packages for point in self.points]
        slope = _linear_regression_slope(values)
        avg = sum(values) / len(values)
        strength = abs(slope) / avg if avg else 0
        if strength < 0.01:
            return "estável", strength
        return ("alta" if slope > 0 else "queda"), strength

    def _turning_points(self) -> list[str]:
        messages: list[str] = []
        previous_direction: str | None = None
        for previous, current in zip(self.points, self.points[1:]):
            delta = current.packages - previous.packages
            if abs(delta) < max(previous.packages * 0.03, 1):
                direction = "estável"
            else:
                direction = "alta" if delta > 0 else "queda"
            if previous_direction and direction != "estável" and previous_direction != "estável" and direction != previous_direction:
                messages.append(f"Mudança para {direction} em {current.period} após período de {previous_direction}.")
            previous_direction = direction
        return messages

    def _worst_capacity_utilization(self) -> tuple[str, float] | None:
        utilizations = [
            (point.period, point.capacity_utilization)
            for point in self.points
            if point.capacity_utilization is not None
        ]
        if not utilizations:
            return None
        period, utilization = max(utilizations, key=lambda item: item[1] or 0)
        return period, float(utilization)

    def _worst_forecast_error(self) -> tuple[str, float] | None:
        errors = [(point.period, point.forecast_error) for point in self.points if point.forecast_error is not None]
        if not errors:
            return None
        period, error = max(errors, key=lambda item: abs(item[1] or 0))
        return period, float(error)

    def _executive_summary(
        self,
        status: str,
        package_change: MetricChange,
        people_change: MetricChange,
        productivity_change: MetricChange | None,
        alerts: Sequence[str],
    ) -> str:
        productivity_text = ""
        if productivity_change and productivity_change.percent is not None:
            productivity_text = f" Produtividade variou {_format_percent(productivity_change.percent)}."
        alert_text = f" Principal ponto de atenção: {alerts[0]}" if alerts else " Sem alertas críticos no período."
        return (
            f"Cenário {status.lower()}: pacotes variaram {_format_percent(package_change.percent)} "
            f"entre {package_change.start_period} e {package_change.end_period}, enquanto pessoas variaram "
            f"{_format_percent(people_change.percent)}.{productivity_text}{alert_text}"
        )

    def _highlights(self) -> dict[str, str]:
        max_package = max(self.points, key=lambda point: point.packages)
        min_package = min(self.points, key=lambda point: point.packages)
        max_productivity = max(
            (point for point in self.points if point.productivity is not None),
            key=lambda point: point.productivity or 0,
            default=None,
        )
        highlights = {
            "maior_volume": f"{max_package.period}: {max_package.packages:,.0f} pacotes",
            "menor_volume": f"{min_package.period}: {min_package.packages:,.0f} pacotes",
        }
        if max_productivity:
            highlights["maior_produtividade"] = (
                f"{max_productivity.period}: {max_productivity.productivity:,.1f} pacotes/pessoa"
            )
        return highlights


def parse_csv(content: str) -> list[DataPoint]:
    reader = csv.DictReader(io.StringIO(content.strip()))
    if not reader.fieldnames:
        raise ValueError("CSV sem cabeçalho.")
    mapped = _map_columns(reader.fieldnames)
    required = {"period", "packages", "people"}
    missing = sorted(required - set(mapped.values()))
    if missing:
        raise ValueError(f"CSV precisa conter colunas para: {', '.join(missing)}.")

    points: list[DataPoint] = []
    for row in reader:
        normalized_row = {mapped[key]: value for key, value in row.items() if key in mapped}
        points.append(
            DataPoint(
                period=normalized_row["period"].strip(),
                packages=_parse_number(normalized_row["packages"]),
                people=_parse_number(normalized_row["people"]),
                forecast=_parse_optional_number(normalized_row.get("forecast")),
                capacity=_parse_optional_number(normalized_row.get("capacity")),
            )
        )
    return points


def _map_columns(fieldnames: Iterable[str]) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for fieldname in fieldnames:
        normalized = _normalize(fieldname)
        for canonical, aliases in _COLUMN_ALIASES.items():
            if normalized in {_normalize(alias) for alias in aliases}:
                mapped[fieldname] = canonical
                break
    return mapped


def _metric_change(start_period: str, end_period: str, start: float, end: float) -> MetricChange:
    absolute = end - start
    percent = None if start == 0 else absolute / start * 100
    if math.isclose(absolute, 0, abs_tol=0.0001):
        direction = "estável"
    else:
        direction = "alta" if absolute > 0 else "queda"
    return MetricChange(start_period, end_period, start, end, absolute, percent, direction)


def _linear_regression_slope(values: Sequence[float]) -> float:
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    numerator = sum((index - x_mean) * (value - y_mean) for index, value in enumerate(values))
    denominator = sum((index - x_mean) ** 2 for index in range(n))
    return numerator / denominator if denominator else 0


def _period_sort_key(period: str) -> tuple[int, str]:
    clean = period.strip()
    for pattern in ("%Y-%m-%d", "%Y-%m", "%d/%m/%Y", "%m/%Y"):
        try:
            return int(datetime.strptime(clean, pattern).timestamp()), clean
        except ValueError:
            continue
    return 0, clean


def _parse_number(value: str | None) -> float:
    if value is None or value == "":
        raise ValueError("Valor numérico obrigatório ausente.")
    clean = value.strip().replace(" ", "")
    if "," in clean and "." in clean:
        clean = clean.replace(".", "").replace(",", ".")
    else:
        clean = clean.replace(",", ".")
    return float(clean)


def _parse_optional_number(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return _parse_number(value)


def _normalize(value: str) -> str:
    normalized = value.strip().lower()
    replacements = {"á": "a", "à": "a", "ã": "a", "â": "a", "é": "e", "ê": "e", "í": "i", "ó": "o", "ô": "o", "õ": "o", "ú": "u", "ç": "c"}
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return re.sub(r"[^a-z0-9_]+", "_", normalized).strip("_")


def _safe_percent(value: float | None) -> float:
    return value if value is not None else 0


def _format_percent(value: float | None) -> str:
    if value is None:
        return "indisponível"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


def _format_change(label: str, change: MetricChange) -> str:
    return (
        f"- **{label}:** {change.direction} de {change.start_value:,.1f} para {change.end_value:,.1f} "
        f"({_format_percent(change.percent)}) entre {change.start_period} e {change.end_period}."
    )


def _bulletize(items: Sequence[str]) -> list[str]:
    return [f"- {item}" for item in items]


def _status_from_score(score: int) -> str:
    if score >= 65:
        return "Vermelho"
    if score >= 35:
        return "Amarelo"
    return "Verde"
