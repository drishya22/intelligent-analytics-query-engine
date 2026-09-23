from app.ai.planner import LLMQueryPlanner
from app.ai.providers import GeminiProvider
from app.data.registry import SemanticRegistry


registry = SemanticRegistry.from_json(
    "../dataset/data_dictionary.json"
)

provider = GeminiProvider()

planner = LLMQueryPlanner(
    provider=provider,
    registry=registry,
    dataset_columns=[
        "order_id",
        "order_date",
        "customer_id",
        "customer_segment",
        "country",
        "city",
        "region",
        "product_category",
        "product_subcategory",
        "product_name",
        "quantity",
        "unit_price",
        "discount",
        "revenue",
        "profit",
    ],
)

query = "What are the top 2 cities by profit?"

plan = planner.plan(query)

print(plan.model_dump_json(indent=2))