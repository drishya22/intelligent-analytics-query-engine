import pandas as pd

from app.ai.schemas import QueryPlan
from app.analytics.validator import QueryValidator
from app.analytics.operations import (
    prepare_dataframe,
    resolve_metric,
)
from app.data.registry import SemanticRegistry


class AnalyticsExecutor:
    """Execute validated QueryPlans against a pandas DataFrame."""

    def __init__(self, registry: SemanticRegistry):
        self.registry = registry

    def execute(
        self,
        df: pd.DataFrame,
        plan: QueryPlan,
    ) -> pd.DataFrame:

        # Materialize semantic metrics such as revenue.
        working_df = prepare_dataframe(
            df=df,
            metric_names=[
                metric.name
                for metric in plan.metrics
            ],
            registry=self.registry,
        )

        # Validate the plan against both physical
        # and semantic metrics.
        validator = QueryValidator()

        validator.validate(
            working_df,
            plan,
            registry=self.registry,
        )

        # Apply filters.
        working_df = self._apply_filters(
            working_df,
            plan,
        )

        # Apply time constraints.
        working_df = self._apply_time_range(
            working_df,
            plan,
        )

        if working_df.empty:
            return pd.DataFrame()

        # Aggregate requested metrics.
        result = self._aggregate(
            working_df,
            plan,
        )

        # Apply derived calculations.
        if plan.derived_metric:
            result = self._apply_derived_metric(
                result,
                plan,
            )

        # Apply ranking / top-N / bottom-N.
        if plan.ranking:
            result = self._apply_ranking(
                result,
                plan,
            )

        return result.reset_index(drop=True)

    def _aggregate(
        self,
        df: pd.DataFrame,
        plan: QueryPlan,
    ) -> pd.DataFrame:

        if not plan.metrics:
            raise ValueError(
                "At least one metric is required."
            )

        results = []

        for metric in plan.metrics:

            # Resolve semantic metric into the actual
            # dataframe column + aggregation.
            physical_column, aggregation = resolve_metric(
                metric,
                self.registry,
            )

            if physical_column not in df.columns:
                raise ValueError(
                    f"Required metric column "
                    f"'{physical_column}' does not exist."
                )

            if plan.group_by:

                missing = [
                    column
                    for column in plan.group_by
                    if column not in df.columns
                ]

                if missing:
                    raise ValueError(
                        f"Unknown grouping columns: {missing}"
                    )

                grouped = df.groupby(
                    plan.group_by,
                    dropna=False,
                )[physical_column]

                if aggregation == "sum":
                    value = grouped.sum()

                elif aggregation == "mean":
                    value = grouped.mean()

                elif aggregation == "count":
                    value = grouped.count()

                elif aggregation == "count_distinct":
                    value = grouped.nunique()

                elif aggregation == "min":
                    value = grouped.min()

                elif aggregation == "max":
                    value = grouped.max()

                else:
                    raise ValueError(
                        f"Unsupported aggregation: "
                        f"'{aggregation}'"
                    )

                result = value.reset_index(
                    name=f"{aggregation}_{metric.name}"
                )

            else:

                series = df[physical_column]

                if aggregation == "sum":
                    value = series.sum()

                elif aggregation == "mean":
                    value = series.mean()

                elif aggregation == "count":
                    value = series.count()

                elif aggregation == "count_distinct":
                    value = series.nunique()

                elif aggregation == "min":
                    value = series.min()

                elif aggregation == "max":
                    value = series.max()

                else:
                    raise ValueError(
                        f"Unsupported aggregation: "
                        f"'{aggregation}'"
                    )

                result = pd.DataFrame(
                    {
                        f"{aggregation}_{metric.name}": [
                            value
                        ]
                    }
                )

            results.append(result)

        # Only one metric.
        if len(results) == 1:
            return results[0]

        # Multiple metrics.
        final_result = results[0]

        for result in results[1:]:
            final_result = final_result.merge(
                result,
                on=plan.group_by,
                how="outer",
            )

        return final_result

    @staticmethod
    def _apply_filters(
        df: pd.DataFrame,
        plan: QueryPlan,
    ) -> pd.DataFrame:

        for condition in plan.filters:

            if condition.column not in df.columns:
                raise ValueError(
                    f"Unknown filter column: "
                    f"'{condition.column}'"
                )

            series = df[condition.column]
            operator = condition.operator
            value = condition.value

            if operator == "==":
                df = df[series == value]

            elif operator == "!=":
                df = df[series != value]

            elif operator == ">":
                df = df[series > value]

            elif operator == ">=":
                df = df[series >= value]

            elif operator == "<":
                df = df[series < value]

            elif operator == "<=":
                df = df[series <= value]

            elif operator == "in":
                df = df[series.isin(value)]

            elif operator == "contains":
                df = df[
                    series.astype(str).str.contains(
                        str(value),
                        case=False,
                        na=False,
                    )
                ]

            else:
                raise ValueError(
                    f"Unsupported filter operator: "
                    f"{operator}"
                )

        return df

    @staticmethod
    def _apply_time_range(df: pd.DataFrame,time_range) -> pd.DataFrame:
        if time_range is None:
            return df

        column = time_range.column

        if column not in df.columns:
            raise ValueError(f"Unknown time column: {column}")

        result = df.copy()
        result[column] = pd.to_datetime(result[column])

        # Handle explicit start/end ranges
        if time_range.start is not None:
            result = result[result[column] >= pd.to_datetime(time_range.start)]

        if time_range.end is not None:
            result = result[result[column] <= pd.to_datetime(time_range.end)]

        # Handle month names such as "March"
        if time_range.period:
            period = time_range.period.strip().lower()

            month_map = {
                "january": 1,
                "february": 2,
                "march": 3,
                "april": 4,
                "may": 5,
                "june": 6,
                "july": 7,
                "august": 8,
                "september": 9,
                "october": 10,
                "november": 11,
                "december": 12,
            }

            if period in month_map:
                result = result[result[column].dt.month == month_map[period]]
            else:
                # Handle values such as "2024-03"
                try:
                    parsed_period = pd.Period(period, freq="M")
                    result = result[
                        result[column].dt.to_period("M") == parsed_period
                    ]
                except Exception:
                    raise ValueError(
                        f"Unsupported time period: {time_range.period}"
                    )

        return result
    
    @staticmethod
    def _apply_derived_metric(
        result: pd.DataFrame,
        plan: QueryPlan,
    ) -> pd.DataFrame:

        derived = plan.derived_metric

        if derived is None:
            return result

        if derived.operation == "ratio":

            if (
                not derived.numerator
                or not derived.denominator
            ):
                raise ValueError(
                    "Ratio requires numerator "
                    "and denominator."
                )

            if derived.numerator not in result.columns:
                raise ValueError(
                    f"Unknown numerator column: "
                    f"'{derived.numerator}'"
                )

            if derived.denominator not in result.columns:
                raise ValueError(
                    f"Unknown denominator column: "
                    f"'{derived.denominator}'"
                )

            denominator = result[
                derived.denominator
            ].replace(0, pd.NA)

            result[derived.name] = (
                result[derived.numerator]
                / denominator
            )

        elif derived.operation == "percentage":

            if (
                not derived.numerator
                or not derived.denominator
            ):
                raise ValueError(
                    "Percentage requires numerator "
                    "and denominator."
                )

            if derived.numerator not in result.columns:
                raise ValueError(
                    f"Unknown numerator column: "
                    f"'{derived.numerator}'"
                )

            if derived.denominator not in result.columns:
                raise ValueError(
                    f"Unknown denominator column: "
                    f"'{derived.denominator}'"
                )

            denominator = result[
                derived.denominator
            ].replace(0, pd.NA)

            result[derived.name] = (
                result[derived.numerator]
                / denominator
            ) * 100

        elif derived.operation == "difference":

            if (
                not derived.current_metric
                or not derived.previous_metric
            ):
                raise ValueError(
                    "Difference requires current_metric "
                    "and previous_metric."
                )

            if derived.current_metric not in result.columns:
                raise ValueError(
                    f"Unknown current metric: "
                    f"'{derived.current_metric}'"
                )

            if derived.previous_metric not in result.columns:
                raise ValueError(
                    f"Unknown previous metric: "
                    f"'{derived.previous_metric}'"
                )

            result[derived.name] = (
                result[derived.current_metric]
                - result[derived.previous_metric]
            )

        elif derived.operation == "growth":

            if (
                not derived.current_metric
                or not derived.previous_metric
            ):
                raise ValueError(
                    "Growth requires current_metric "
                    "and previous_metric."
                )

            if derived.current_metric not in result.columns:
                raise ValueError(
                    f"Unknown current metric: "
                    f"'{derived.current_metric}'"
                )

            if derived.previous_metric not in result.columns:
                raise ValueError(
                    f"Unknown previous metric: "
                    f"'{derived.previous_metric}'"
                )

            previous = result[
                derived.previous_metric
            ].replace(0, pd.NA)

            result[derived.name] = (
                (
                    result[derived.current_metric]
                    - previous
                )
                / previous
            ) * 100

        else:
            raise ValueError(
                f"Unsupported derived operation: "
                f"'{derived.operation}'"
            )

        return result

    @staticmethod
    def _apply_ranking(
        result: pd.DataFrame,
        plan: QueryPlan,
    ) -> pd.DataFrame:

        ranking = plan.ranking

        if ranking is None:
            return result

        metric_columns = [
            column
            for column in result.columns
            if ranking.metric.lower()
            in column.lower()
        ]

        if not metric_columns:
            raise ValueError(
                f"Could not find ranking metric: "
                f"'{ranking.metric}'"
            )

        metric_column = metric_columns[0]

        # Global ranking.
        if not ranking.partition_by:

            result = result.sort_values(
                by=metric_column,
                ascending=(
                    ranking.direction == "asc"
                ),
            )

            if ranking.limit is not None:
                result = result.head(
                    ranking.limit
                )

            return result

        # Partitioned ranking.
        missing = [
            column
            for column in ranking.partition_by
            if column not in result.columns
        ]

        if missing:
            raise ValueError(
                f"Unknown partition columns: "
                f"{missing}"
            )

        result = result.sort_values(
            by=metric_column,
            ascending=(
                ranking.direction == "asc"
            ),
        )

        if ranking.limit is not None:
            result = (
                result.groupby(
                    ranking.partition_by,
                    group_keys=False,
                )
                .head(ranking.limit)
            )

        return result