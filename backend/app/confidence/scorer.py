from app.ai.schemas import QueryPlan
from app.data.registry import SemanticRegistry


class ConfidenceScorer:
    """
    Estimate confidence in a generated QueryPlan.

    This score is deterministic and based on structural validity,
    semantic coverage, and ambiguity.
    """

    def score(
        self,
        plan: QueryPlan,
        registry: SemanticRegistry,
    ) -> float:

        score = 1.0

        if not plan.metrics:
            return 0.0

        # Penalize unknown semantic metrics.
        for metric in plan.metrics:
            if (
                metric.name not in registry.metrics
                and metric.name not in registry.dimensions
            ):
                score -= 0.20

        # Missing grouping information for a grouped-looking plan
        # is difficult to detect reliably, so don't penalize here.

        if plan.derived_metric:
            derived = plan.derived_metric

            if derived.operation in {
                "ratio",
                "percentage",
                "growth",
                "difference",
            }:
                score += 0.0

        if plan.comparison:
            if plan.comparison.type not in {
                "target",
                "previous_period",
                "previous_year",
            }:
                score -= 0.15

        # Keep score within [0, 1].
        return round(
            max(0.0, min(1.0, score)),
            2,
        )