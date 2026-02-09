"""Evaluation pipeline for signal extraction quality measurement.

Public API:
    evaluate(extracted, ground_truth, transcript) -> EvaluationReport
    evaluate_corpus(cases) -> CorpusReport
"""

from .report import CorpusReport, EvaluationReport
from .runner import evaluate, evaluate_corpus

__all__ = ["evaluate", "evaluate_corpus", "EvaluationReport", "CorpusReport"]
