import pandas as pd

from app.ai.schemas import Metric
from app.data.registry import SemanticRegistry


def prepare_dataframe(
    df: pd.DataFrame,
    metric_names: list[str],
    registry: SemanticRegistry,
) -> pd.DataFrame:
    """
    Materialize semantic metrics that are represented by
    row-level expressions.
    """
    result = df.copy()

    for metric_name in metric_names:
        if metric_name == "revenue":
            required = [
                "quantity",
                "unit_price",
                "discount",
            ]

            missing = [
                column
                for column in required
                if column not in result.columns
            ]

            if missing:
                raise ValueError(
                    f"Cannot calculate revenue. "
                    f"Missing columns: {missing}"
                )

            result["revenue"] = (
                result["quantity"]
                * result["unit_price"]
                * (1 - result["discount"])
            )

    return result


def resolve_metric(
    metric: Metric,
    registry: SemanticRegistry,
) -> tuple[str, str]:
    """
    Resolve a semantic metric into a physical column and aggregation.
    """

    if metric.name == "orders":
        return "order_id", "count"

    if metric.name == "avg_order_value":
        raise ValueError(
            "avg_order_value must be represented as a derived metric."
        )

    expression = registry.metrics.get(metric.name)

    if expression is None:
        # Allow physical dataset columns such as profit and quantity.
        return metric.name, metric.aggregation

    if expression == metric.name:
        return metric.name, metric.aggregation

    if expression.startswith("count(") and expression.endswith(")"):
        column = expression[len("count("):-1].strip()
        return column, "count"

    if metric.name == "revenue":
        return "revenue", metric.aggregation

    raise ValueError(
        f"Unsupported semantic metric: '{metric.name}'"
    )


def resolve_result_column(
    result: pd.DataFrame,
    metric_name: str,
) -> str:
    """
    Resolve a semantic metric reference to an aggregated result column.
    """

    if metric_name in result.columns:
        return metric_name

    candidates = [
        column
        for column in result.columns
        if column.endswith(f"_{metric_name}")
    ]

    if len(candidates) == 1:
        return candidates[0]

    raise ValueError(
        f"Could not resolve metric '{metric_name}' "
        f"in the aggregated result."
    )