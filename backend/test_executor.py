import pandas as pd

from app.data.loader import CSVLoader
from app.data.registry import SemanticRegistry
from app.ai.schemas import (
    QueryPlan,
    Filter,
    Ranking,
)
from app.analytics.executor import AnalyticsExecutor


# --------------------------------------------------
# 1. Load the dataset
# --------------------------------------------------

loader = CSVLoader()

df = loader.load("../dataset/sales_data.csv")

print("\n=== DATASET ===")
print(f"Rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
print(df.head())


# --------------------------------------------------
# 2. Profile the dataset
# --------------------------------------------------

profile = loader.profile(df)

print("\n=== PROFILE ===")
print(f"Rows: {profile['row_count']}")
print(f"Columns: {profile['column_count']}")

for column in profile["columns"]:
    print(column)


# --------------------------------------------------
# 3. Create semantic registry
# --------------------------------------------------

registry = SemanticRegistry()

print("\n=== REGISTRY ===")
print(registry)


# --------------------------------------------------
# 4. Create a QueryPlan
# --------------------------------------------------
# We are testing TWO metrics:
# - total profit
# - total quantity
#
# Both are grouped by city.
# --------------------------------------------------

plan = QueryPlan(
    metrics=[
        {
            "name": "profit",
            "aggregation": "sum",
        },
        {
            "name": "quantity",
            "aggregation": "sum",
        },
    ],

    group_by=["city"],

    filters=[
        Filter(
            column="quantity",
            operator=">",
            value=1,
        )
    ],

    ranking=Ranking(
        metric="profit",
        direction="desc",
        limit=2,
    ),
)


print("\n=== QUERY PLAN ===")
print(plan.model_dump())


# --------------------------------------------------
# 5. Execute the QueryPlan
# --------------------------------------------------

executor = AnalyticsExecutor()

result = executor.execute(
    df,
    plan,
)


# --------------------------------------------------
# 6. Display the result
# --------------------------------------------------

print("\n=== RESULT ===")
print(result)


# --------------------------------------------------
# 7. Basic sanity checks
# --------------------------------------------------

assert not result.empty

assert "city" in result.columns

assert "sum_profit" in result.columns

assert "sum_quantity" in result.columns

assert len(result) <= 2

print("\n✅ MULTI-METRIC END-TO-END TEST PASSED")