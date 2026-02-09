"""Evaluation report models — Pydantic schemas for evaluation results."""

from __future__ import annotations

import math

from pydantic import BaseModel, Field


class JudgeScore(BaseModel):
    """A single LLM-as-judge rubric score."""

    score: int = Field(ge=1, le=5)
    justification: str


class SignalMetrics(BaseModel):
    """Precision/recall/F1 and optional supplementary metrics for one signal type."""

    signal_name: str
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    count_extracted: int = 0
    count_ground_truth: int = 0

    # Supplementary metrics (signal-type-specific)
    accuracy: float | None = None
    mae: float | None = None
    ordinal_agreement: float | None = None
    baseline_agreement: float | None = None

    # LLM-as-judge scores
    judge_scores: list[JudgeScore] = Field(default_factory=list)
    mean_judge_score: float | None = None

    # Structural issues
    structural_issues: list[str] = Field(default_factory=list)
    score_distribution: dict | None = None

    # Matched pairs for debugging
    matched_pairs: list[tuple[str, str, float]] = Field(default_factory=list)


class LayerReport(BaseModel):
    """Evaluation report for one extraction layer."""

    layer_name: str
    signal_metrics: list[SignalMetrics] = Field(default_factory=list)

    @property
    def mean_f1(self) -> float:
        """Average F1 across signal types that have it."""
        scores = [m.f1 for m in self.signal_metrics if m.f1 is not None]
        return sum(scores) / len(scores) if scores else float("nan")


class EvaluationReport(BaseModel):
    """Complete evaluation report for one extraction result vs ground truth."""

    transcript_id: str
    surface: LayerReport
    behavioral: LayerReport
    psychographic: LayerReport
    multimodal: LayerReport | None = None

    @property
    def all_signal_metrics(self) -> list[SignalMetrics]:
        """Flat list of all signal metrics across layers."""
        metrics = []
        for layer in [self.surface, self.behavioral, self.psychographic]:
            metrics.extend(layer.signal_metrics)
        if self.multimodal:
            metrics.extend(self.multimodal.signal_metrics)
        return metrics

    @property
    def overall_f1(self) -> float:
        """Average F1 across all signal types."""
        scores = [m.f1 for m in self.all_signal_metrics if m.f1 is not None]
        return sum(scores) / len(scores) if scores else float("nan")

    def summary(self) -> str:
        """Human-readable summary of evaluation results."""
        lines = [f"Evaluation Report: {self.transcript_id}", "=" * 60]

        for layer in [self.surface, self.behavioral, self.psychographic, self.multimodal]:
            if layer is None:
                continue
            lines.append(f"\n{layer.layer_name} (avg F1: {layer.mean_f1:.2f})")
            lines.append("-" * 40)
            for m in layer.signal_metrics:
                p_str = f"P={m.precision:.2f}" if m.precision is not None else "P=n/a"
                r_str = f"R={m.recall:.2f}" if m.recall is not None else "R=n/a"
                f_str = f"F1={m.f1:.2f}" if m.f1 is not None else "F1=n/a"
                lines.append(
                    f"  {m.signal_name:30s} {p_str}  {r_str}  {f_str}  "
                    f"({m.count_extracted} extracted, {m.count_ground_truth} gt)"
                )
                if m.accuracy is not None:
                    lines.append(f"    accuracy={m.accuracy:.2f}")
                if m.mae is not None:
                    lines.append(f"    MAE={m.mae:.3f}")
                if m.mean_judge_score is not None:
                    lines.append(f"    judge={m.mean_judge_score:.1f}/5")
                if m.baseline_agreement is not None:
                    lines.append(f"    baseline_agreement={m.baseline_agreement:.2f}")
                if m.structural_issues:
                    for issue in m.structural_issues[:3]:
                        lines.append(f"    ! {issue}")
                    if len(m.structural_issues) > 3:
                        lines.append(f"    ... and {len(m.structural_issues) - 3} more")

        overall = self.overall_f1
        overall_str = f"{overall:.2f}" if not math.isnan(overall) else "n/a"
        lines.append(f"\nOverall F1: {overall_str}")
        return "\n".join(lines)


class CorpusReport(BaseModel):
    """Aggregated evaluation across multiple transcripts."""

    reports: list[EvaluationReport]

    @property
    def n_transcripts(self) -> int:
        return len(self.reports)

    def mean_metrics_by_signal(self) -> dict[str, dict[str, float]]:
        """Aggregate precision/recall/F1 per signal type across transcripts."""
        from collections import defaultdict

        accum: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: {"precision": [], "recall": [], "f1": []}
        )

        for report in self.reports:
            for m in report.all_signal_metrics:
                if m.precision is not None:
                    accum[m.signal_name]["precision"].append(m.precision)
                if m.recall is not None:
                    accum[m.signal_name]["recall"].append(m.recall)
                if m.f1 is not None:
                    accum[m.signal_name]["f1"].append(m.f1)

        result = {}
        for name, vals in accum.items():
            result[name] = {
                k: sum(v) / len(v) if v else float("nan")
                for k, v in vals.items()
            }
        return result

    def summary(self) -> str:
        """Human-readable corpus-level summary."""
        lines = [
            f"Corpus Evaluation ({self.n_transcripts} transcripts)",
            "=" * 60,
        ]

        agg = self.mean_metrics_by_signal()
        for signal_name, vals in sorted(agg.items()):
            p = vals.get("precision", float("nan"))
            r = vals.get("recall", float("nan"))
            f = vals.get("f1", float("nan"))
            p_str = f"P={p:.2f}" if not math.isnan(p) else "P=n/a"
            r_str = f"R={r:.2f}" if not math.isnan(r) else "R=n/a"
            f_str = f"F1={f:.2f}" if not math.isnan(f) else "F1=n/a"
            lines.append(f"  {signal_name:30s} {p_str}  {r_str}  {f_str}")

        overall_f1s = [r.overall_f1 for r in self.reports if not math.isnan(r.overall_f1)]
        mean_overall = sum(overall_f1s) / len(overall_f1s) if overall_f1s else float("nan")
        overall_str = f"{mean_overall:.2f}" if not math.isnan(mean_overall) else "n/a"
        lines.append(f"\nMean Overall F1: {overall_str}")
        return "\n".join(lines)
