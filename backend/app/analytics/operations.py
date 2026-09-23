import pandas as pd

from app.ai.schemas import Metric
from app.data.registry import SemanticRegistry


def prepare_dataframe(
    df: pd.DataFrame,
    metric_names: list[str],
    registry: SemanticRegistry,
) -> pd.DataFrame:
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

    if metric.name == "orders":
        return "order_id", "count"

    if metric.name == "avg_order_value":
        raise ValueError(
            "avg_order_value should be calculated as a derived metric."
        )

    expression = registry.metrics.get(metric.name)

    if expression is None:
        return metric.name, metric.aggregation

    if expression == metric.name:
        return metric.name, metric.aggregation

    if expression.startswith("count(") and expression.endswith(")"):
        column = expression[
            len("count("):-1
        ].strip()

        return column, "count"

    if metric.name == "revenue":
        return "revenue", metric.aggregation

    raise ValueError(
        f"Unsupported semantic metric: {metric.name}"
    )