import re
from app.ai.schemas import (
    QueryPlan,
    Metric,
    Ranking,
    Filter
)
from app.data.registry import SemanticRegistry
from app.ai.prompts import build_planner_prompt

class QueryPlanner:
    """Convert a natural language query into a validated structured QueryPlan.
    The planner is intentionally deterministic for the first version.
    SemanticRegistry is responsible for resolving business terminology. 
    """

    AGGREGATION_KEYWORDS={
        "sum":"sum",
        "total":"sum",
        "overall":"sum",
        "average":"mean",
        "avg":"mean",
        "mean":"mean",
        "count":"count",
        "minimum":"min",
        "min":"min",
        "maximum":"max",
        "max":"max"
    }

    def __init__(self,registry: SemanticRegistry):
        self.registry=registry

    def plan(self, query:str)->QueryPlan:
        #ask LLM to convert the query into our structured schema
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.") 
        normalized=query.strip().lower()
        metric_name,aggregation=self._extract_metric(normalized)
        group_by=self._extract_group_by(normalized)
        filters=self._extract_filters(normalized)
        ranking=self._extract_ranking(normalized,metric_name)

        metrics=[
            Metric(
                name=metric_name,
                aggregation=aggregation
            )
        ]
        
        # Convert LLM response into our validated Pydantic schema.
        return QueryPlan(
            metrics=metrics,
            group_by=group_by,
            filters=filters,
            ranking=ranking
        )
    def _extract_metric(self, query:str)->tuple[str,str]:
        """Find a metric mentioned in the query and determine its aggregation."""
        metric_candidates=sorted(self.registry.metrics.keys(),key=len,reverse=True)
        for term in metric_candidates:
            if self._contains_term(query,term):
                aggregation=self._infer_aggregation(query,term)
                if term=="orders":
                    return "order_id","count"
                expression=self.registry.metrics[term]
                if expression==term:
                    return term,aggregation
                count_match=re.fullmatch(
                    r"count\(([^)]+)\)",
                    expression.strip()
                )  
                if count_match:
                    return count_match.group(1),"count"
                raise ValueError(
                    f"Metric '{term}' is  a derived expression"
                    f"and is not yet supported by the current executor."
                )
        synonym_candidates=sorted(self.registry.synonyms.keys(),key=len,reverse=True)
        for synonym in synonym_candidates:
            if self._contains_term(query,synonym):
                canonical=self.registry.resolve_term(synonym)
                if canonical=="orders":
                    return "order_id","count"
                if canonical not in self.registry.metrics:
                    raise ValueError(
                        f"Unknown canonical metric: '{canonical}'"

                    )  
                expression=self.registry.metrics[canonical]
                if expression==canonical:
                    aggregation=self._infer_aggregation(query,canonical)
                    return canonical,aggregation
                count_match=re.fullmatch(
                    r"count\(([^)]+\)",
                    expression.strip()
                ) 
                if count_match:
                    return count_match.group(1),"count"
                raise ValueError(
                    f"Metric '{canonical}' is a derived expression"
                    f"and is not yet supported by the current executor."
                ) 
        raise ValueError(
            "Could not identify a metric in the query. "
        )    

    def _infer_aggregation(self,query:str,metric:str)->str:
        """Infer aggreagtion from words such as total,average,count,minimum, maximum"""

        for keyword,aggregation in self.AGGREGATION_KEYWORDS.items():
            if self._contains_term(query,keyword):
                return aggregation
        
        return "sum"

    def _extract_group_by(self, query: str) -> list[str]:
        """
        Extract dimensions from phrases such as:

        by city
        by region
        grouped by country
        per product category
        top 5 cities by profit
        """

        dimensions = sorted(
            self.registry.dimensions,
            key=len,
            reverse=True
        )

        found = []

        for dimension in dimensions:

            # Normal grouping phrases.
            patterns = [
                rf"\bby\s+{re.escape(dimension)}\b",
                rf"\bper\s+{re.escape(dimension)}\b",
                rf"\bgrouped\s+by\s+{re.escape(dimension)}\b",

                # Ranking phrases such as "top 5 cities".
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
        """
        Extract simple filters such as:

        quantity > 1
        profit >= 100
        country = India
        quantity != 0
        """

        filters = []

        # Numeric comparisons
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

        # String equality
        string_pattern = re.compile(
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*"
            r"(?:==|=)\s*"
            r"([a-zA-Z][a-zA-Z0-9 _-]*)"
        )

        for match in string_pattern.finditer(query):
            column = match.group(1)
            value = match.group(2).strip()

            # Avoid duplicating numeric filters.
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
        """
        Extract queries such as:

        top 5 cities by profit
        bottom 3 countries by profit
        top 10 products
        """

        top_match = re.search(
            r"\btop\s+(\d+)\b",
            query,
        )

        bottom_match = re.search(
            r"\bbottom\s+(\d+)\b",
            query,
        )

        if top_match:
            limit = int(top_match.group(1))

            ranking_metric = self._ranking_metric(metric)

            return Ranking(
                metric=ranking_metric,
                direction="desc",
                limit=limit,
            )

        if bottom_match:
            limit = int(bottom_match.group(1))

            ranking_metric = self._ranking_metric(metric)

            return Ranking(
                metric=ranking_metric,
                direction="asc",
                limit=limit,
            )

        return None

    def _ranking_metric(self, metric: str) -> str:
        """
        Convert semantic metric names into the physical metric name
        currently produced by the executor.
        """

        if metric == "order_id":
            return "order_id"

        return metric



    @staticmethod
    def _contains_term(query: str, term: str) -> bool:
        """
        Match a semantic term as a complete word/phrase rather than
        accidentally matching a substring.
        """

        pattern = rf"(?<!\w){re.escape(term.lower())}(?!\w)"

        return re.search(
            pattern,
            query.lower(),
        ) is not None 

              
class LLMQueryPlanner:
    """Convert natural language into a validated QueryPlan using an LLM"""
    def __init__(self,provider,registry:SemanticRegistry,dataset_columns:list[str]):
        self.provider=provider
        self.registry=registry
        self.dataset_columns=dataset_columns

    def plan(self,query:str)->QueryPlan:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
        prompt=build_planner_prompt(
            query=query,
            registry=self.registry,
            dataset_columns=self.dataset_columns
        )    

        response=self.provider.generate(prompt)
        response=response.strip()
        if response.startswith("```"):
            response=response.replace("```json","",1)
            response=response.replace("```","",1)
            response=response.strip()
        return  QueryPlan.model_validate_json(response)
        