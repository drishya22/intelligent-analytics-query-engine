import re

from app.ai.schemas import (
    QueryPlan,
    Metric,
    Ranking,
    Filter,
)
from app.data.registry import SemanticRegistry
from app.ai.prompts import build_planner_prompt


class QueryPlanner:
    """
    Deterministic fallback planner.

    Used when the LLM providers are unavailable.
    """

    AGGREGATION_KEYWORDS = {
        "sum": "sum",
        "total": "sum",
        "overall": "sum",
        "average": "mean",
        "avg": "mean",
        "mean": "mean",
        "count": "count",
        "minimum": "min",
        "min": "min",
        "maximum": "max",
        "max": "max",
    }

    def __init__(self, registry: SemanticRegistry):
        self.registry = registry

    def plan(self, query: str) -> QueryPlan:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        normalized = query.strip().lower()

        metric_name, aggregation = self._extract_metric(normalized)
        group_by = self._extract_group_by(normalized)
        filters = self._extract_filters(normalized)
        ranking = self._extract_ranking(normalized, metric_name)

        return QueryPlan(
            metrics=[
                Metric(
                    name=metric_name,
                    aggregation=aggregation,
                )
            ],
            group_by=group_by,
            filters=filters,
            ranking=ranking,
        )

    def _extract_metric(self, query: str) -> tuple[str, str]:
        """Find a metric mentioned in the query."""

        metric_candidates = sorted(
            self.registry.metrics.keys(),
            key=len,
            reverse=True,
        )

        for term in metric_candidates:
            if self._contains_term(query, term):
                aggregation = self._infer_aggregation(query, term)
                expression = self.registry.metrics[term]

                # Semantic orders metric
                if term == "orders":
                    return "order_id", "count"

                # Physical metric
                if expression == term:
                    return term, aggregation

                # Revenue is materialized by the executor.
                if term == "revenue":
                    return "revenue", aggregation

                # count(column)
                count_match = re.fullmatch(
                    r"count\(([^)]+)\)",
                    expression.strip(),
                )

                if count_match:
                    return count_match.group(1), "count"

                raise ValueError(
                    f"Metric '{term}' is a derived expression "
                    f"and is not supported by the deterministic planner."
                )

        # Try synonyms
        synonym_candidates = sorted(
            self.registry.synonyms.keys(),
            key=len,
            reverse=True,
        )

        for synonym in synonym_candidates:
            if self._contains_term(query, synonym):
                canonical = self.registry.resolve_term(synonym)

                if canonical == "orders":
                    return "order_id", "count"

                if canonical not in self.registry.metrics:
                    raise ValueError(
                        f"Unknown canonical metric: '{canonical}'"
                    )

                expression = self.registry.metrics[canonical]

                if expression == canonical:
                    aggregation = self._infer_aggregation(
                        query,
                        canonical,
                    )
                    return canonical, aggregation

                # Revenue is materialized by the executor.
                if canonical == "revenue":
                    aggregation = self._infer_aggregation(
                        query,
                        canonical,
                    )
                    return "revenue", aggregation

                count_match = re.fullmatch(
                    r"count\(([^)]+)\)",
                    expression.strip(),
                )

                if count_match:
                    return count_match.group(1), "count"

                raise ValueError(
                    f"Metric '{canonical}' is a derived expression "
                    f"and is not supported by the deterministic planner."
                )

        raise ValueError(
            "Could not identify a metric in the query."
        )

    def _infer_aggregation(
        self,
        query: str,
        metric: str,
    ) -> str:
        for keyword, aggregation in self.AGGREGATION_KEYWORDS.items():
            if self._contains_term(query, keyword):
                return aggregation

        return "sum"

    def _extract_group_by(self, query: str) -> list[str]:
        dimensions = sorted(
            self.registry.dimensions,
            key=len,
            reverse=True,
        )

        found = []

        for dimension in dimensions:
            patterns = [
                rf"\bby\s+{re.escape(dimension)}\b",
                rf"\bper\s+{re.escape(dimension)}\b",
                rf"\bgrouped\s+by\s+{re.escape(dimension)}\b",
                rf"\btop\s+\d+\s+{re.escape(dimension)}\b",
                rf"\bbottom\s+\d+\s+{re.escape(dimension)}\b",
            ]

            if any(
                re.search(pattern, query)
                for pattern in patterns
            ):
                found.append(dimension)

        return found

    def _extract_filters(self, query: str) -> list[Filter]:
        filters = []

        numeric_pattern = re.compile(
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*"
            r"(>=|<=|!=|==|>|<)\s*"
            r"(-?\d+(?:\.\d+)?)"
        )

        for match in numeric_pattern.finditer(query):
            column = match.group(1)
            operator = match.group(2)
            value = match.group(3)

            value = (
                float(value)
                if "." in value
                else int(value)
            )

            filters.append(
                Filter(
                    column=column,
                    operator=operator,
                    value=value,
                )
            )

        string_pattern = re.compile(
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*"
            r"(?:==|=)\s*"
            r"([a-zA-Z][a-zA-Z0-9 _-]*)"
        )

        for match in string_pattern.finditer(query):
            column = match.group(1)
            value = match.group(2).strip()

            if any(
                existing.column == column
                for existing in filters
            ):
                continue

            filters.append(
                Filter(
                    column=column,
                    operator="==",
                    value=value,
                )
            )

        return filters

    def _extract_ranking(
        self,
        query: str,
        metric: str,
    ) -> Ranking | None:

        top_match = re.search(
            r"\btop\s+(\d+)\b",
            query,
        )

        bottom_match = re.search(
            r"\bbottom\s+(\d+)\b",
            query,
        )

        if top_match:
            return Ranking(
                metric=self._ranking_metric(metric),
                direction="desc",
                limit=int(top_match.group(1)),
            )

        if bottom_match:
            return Ranking(
                metric=self._ranking_metric(metric),
                direction="asc",
                limit=int(bottom_match.group(1)),
            )

        return None

    def _ranking_metric(self, metric: str) -> str:
        return metric

    @staticmethod
    def _contains_term(query: str, term: str) -> bool:
        pattern = rf"(?<!\w){re.escape(term.lower())}(?!\w)"

        return re.search(
            pattern,
            query.lower(),
        ) is not None


class LLMQueryPlanner:
    """Convert natural language into a validated QueryPlan using an LLM."""

    def __init__(
        self,
        provider,
        registry: SemanticRegistry,
        dataset_columns: list[str],
    ):
        self.provider = provider
        self.registry = registry
        self.dataset_columns = dataset_columns

    def plan(self, query: str) -> QueryPlan:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        prompt = build_planner_prompt(
            query=query,
            registry=self.registry,
            dataset_columns=self.dataset_columns,
        )

        response = self.provider.generate(prompt)

        response = response.strip()

        if response.startswith("```"):
            response = response.replace("```json", "", 1)
            response = response.replace("```", "", 1)
            response = response.strip()

        return QueryPlan.model_validate_json(response)