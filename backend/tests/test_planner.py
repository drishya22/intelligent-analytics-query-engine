from app.data.registry import SemanticRegistry
from app.ai.planner import QueryPlanner


REGISTRY_PATH = "../dataset/data_dictionary.json"


registry = SemanticRegistry.from_json(
    REGISTRY_PATH
)

planner = QueryPlanner(registry)


queries = [
    "show profit by city",
    "total profit by region",
    "average profit by country",
    "top 2 cities by profit",
    "bottom 3 countries by profit",
    "show orders by city",
    "show profit by city where quantity > 1",
]


for query in queries:
    print("\n" + "=" * 70)
    print("QUERY:")
    print(query)

    try:
        plan = planner.plan(query)

        print("\nQUERY PLAN:")
        print(plan.model_dump())

    except Exception as exc:
        print("\n❌ PLANNER ERROR:")
        print(exc)