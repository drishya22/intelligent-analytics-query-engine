import pandas as pd

from app.ai.schemas import QueryPlan
from app.data.registry import SemanticRegistry


class QueryValidator:
    """Validate a QueryPlan before execution."""

    def validate(
        self,
        df: pd.DataFrame,
        plan: QueryPlan,
        registry: SemanticRegistry | None = None,
    ) -> None:

        if not plan.metrics:
            raise ValueError("At least one metric is required.")

        for metric in plan.metrics:
            is_physical = metric.name in df.columns
            is_semantic = (
                registry is not None
                and metric.name in registry.metrics
            )

            if not is_physical and not is_semantic:
                raise ValueError(
                    f"Unknown metric: '{metric.name}'"
                )

        missing_group_columns = [
            column
            for column in plan.group_by
            if column not in df.columns
        ]

        if missing_group_columns:
            raise ValueError(
                f"Unknown grouping columns: "
                f"{missing_group_columns}"
            )

        for condition in plan.filters:
            if condition.column not in df.columns:
                raise ValueError(
                    f"Unknown filter column: "
                    f"'{condition.column}'"
                )

        if plan.ranking:
            # Ranking may refer to a semantic metric.
            ranking_metric = plan.ranking.metric

            is_physical = ranking_metric in df.columns
            is_semantic = (
                registry is not None
                and ranking_metric in registry.metrics
            )

            if not is_physical and not is_semantic:
                raise ValueError(
                    f"Unknown ranking metric: "
                    f"'{ranking_metric}'"
                )

            missing_partition_columns = [
                column
                for column in plan.ranking.partition_by
                if column not in df.columns
            ]

            if missing_partition_columns:
                raise ValueError(
                    f"Unknown partition columns: "
                    f"{missing_partition_columns}"
                )

        if plan.time_range:
            if plan.time_range.column not in df.columns:
                raise ValueError(
                    f"Unknown time column: "
                    f"'{plan.time_range.column}'"
                )