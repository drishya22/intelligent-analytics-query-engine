import pandas as pd

from app.ai.schemas import QueryPlan, Filter
from app.analytics.validator import QueryValidator


df = pd.DataFrame({
    "city": ["Delhi", "Mumbai", "Delhi"],
    "profit": [100, 200, 150],
    "quantity": [2, 3, 1],
})


# A valid query plan should pass.
valid_plan = QueryPlan(
    metric="profit",
    aggregation="sum",
    group_by=["city"],
    filters=[
        Filter(
            column="quantity",
            operator=">",
            value=1,
        )
    ],
)

validator = QueryValidator()

validator.validate(df, valid_plan)

print("✅ Valid plan passed validation")


# An invalid plan should fail.
invalid_plan = QueryPlan(
    metric="sales",
    aggregation="sum",
)

try:
    validator.validate(df, invalid_plan)
except ValueError as error:
    print("✅ Invalid plan rejected:")
    print(error)