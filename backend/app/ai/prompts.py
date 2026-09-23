import json

from app.ai.schemas import QueryPlan
from app.data.registry import SemanticRegistry


def build_planner_prompt(
    query: str,
    registry: SemanticRegistry,
    dataset_columns: list[str],
) -> str:
    """
    Build the prompt used to convert a natural-language query
    into a structured QueryPlan.
    """

    schema = json.dumps(
        QueryPlan.model_json_schema(),
        separators=(",", ":"),
    )

    registry_data = {
        "metrics": registry.metrics,
        "dimensions": registry.dimensions,
        "synonyms": registry.synonyms,
        "time_mappings": registry.time_mappings,
    }

    return f"""You are an analytics query planner. Convert the user's natural-language question into a QueryPlan that strictly conforms to the schema below.

<schema>
{schema}
</schema>

<semantic_registry>
{json.dumps(registry_data, separators=(",", ":"))}
</semantic_registry>

<available_columns>
{json.dumps(dataset_columns, separators=(",", ":"))}
</available_columns>

<rules>
- Resolve business terms via the semantic registry (metrics, dimensions, synonyms, time_mappings) before mapping to columns.
- Registry metrics are semantic definitions, not necessarily physical columns — e.g. "orders" means count(order_id), not a column named "orders".
- Use only registry-defined metrics/dimensions and only columns present in available_columns; never invent a metric, dimension, column, or value not present above.
- Preserve every meaningful filter, grouping, ranking, and time constraint from the query.
- Choose the aggregation implied by the user's wording (e.g. "total" -> sum, "average" -> mean).
- Prefer derived_metric for calculated values.
- For "contribution %", "contribution percentage", "share of total", or similar requests, use:
  derived_metric.operation = "percentage"
  derived_metric.numerator = the grouped metric
  derived_metric.denominator = the overall total of that metric.
- For revenue contribution by category, use revenue as the numerator metric and revenue_total as the denominator concept.
- Use comparison for target, previous-period, and previous-year comparisons.
- If a comparison requires data outside the primary dataset, set secondary_dataset to the appropriate dataset name.
- Never output executable code (Python, SQL, shell, etc.) in any field.
- If a requested operation cannot be safely represented in the schema, do not invent a representation — return the closest valid plan and preserve all other determinable intent.
- For "top X in each/by each region/category/etc.", use ranking.partition_by for the "each" dimension and include both the partition dimension and ranked dimension in group_by.
- For "top product in each region", group by region and product_category, then rank revenue descending with limit 1 and partition_by ["region"].
</rules>

<output_contract>
Return exactly one JSON object matching the schema. No markdown fences, no comments, no prose, no keys outside the schema.
</output_contract>

<user_query>
{query}
</user_query>

JSON:""".strip()