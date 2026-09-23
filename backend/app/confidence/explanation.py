from app.ai.schemas import QueryPlan


def explain_plan(plan: QueryPlan) -> str:
    parts = []

    if plan.metrics:
        metrics = ", ".join(
            f"{metric.aggregation}({metric.name})"
            for metric in plan.metrics
        )
        parts.append(f"Metrics: {metrics}")

    if plan.group_by:
        parts.append(
            f"Grouped by: {', '.join(plan.group_by)}"
        )

    if plan.filters:
        parts.append(
            f"Filters: {len(plan.filters)} condition(s)"
        )

    if plan.ranking:
        parts.append(
            f"Ranked {plan.ranking.direction} "
            f"by {plan.ranking.metric}"
        )

    if plan.derived_metric:
        parts.append(
            f"Derived metric: {plan.derived_metric.name}"
        )

    if plan.comparison:
        parts.append(
            f"Comparison: {plan.comparison.type}"
        )

    return ". ".join(parts) + "."