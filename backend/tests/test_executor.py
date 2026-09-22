import pandas as pd

from app.ai.schemas import QueryPlan, Metric, DerivedMetric
from app.analytics.executor import AnalyticsExecutor


# Load dataset
df = pd.read_csv("../dataset/sales_data.csv")

print("\n=== DATASET ===")
print(df.head())


# Create executor
executor = AnalyticsExecutor()


# Test multi-metric query + derived ratio
plan = QueryPlan(
    metrics=[
        Metric(
            name="profit",
            aggregation="sum"
        ),
        Metric(
            name="quantity",
            aggregation="sum"
        ),
    ],
    group_by=["city"],
    filters=[
        {
            "column": "quantity",
            "operator": ">",
            "value": 1
        }
    ],
    ranking={
        "metric": "profit",
        "direction": "desc",
        "limit": 2,
        "partition_by": []
    },
    derived_metric=DerivedMetric(
        name="profit_per_quantity",
        operation="ratio",
        numerator="sum_profit",
        denominator="sum_quantity"
    )
)


print("\n=== QUERY PLAN ===")
print(plan.model_dump())


# Execute query
result = executor.execute(df, plan)


print("\n=== RESULT ===")
print(result)


print("\n✅ DERIVED METRIC END-TO-END TEST PASSED")