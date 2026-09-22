import pandas as pd
from app.ai.schemas import QueryPlan

class QueryValidator:
    """Validate a QueryPlan before sending it to the executor."""

    def validate(self,df:pd.DataFrame,plan:QueryPlan)->None:
        #check that the requested metric exists.
        if not plan.metrics:
            raise ValueError(
                "At least one metric is required."
            )
        for metric in plan.metrics:
            if metric.name not in df.columns:
                raise ValueError(
                    f"Unknown metric: '{metric.name}'"
                )

        #Every grouping column must exist in the dataset
        missing_group_columns=[
            column 
            for column in plan.group_by
            if column not in df.columns
        ]
        if missing_group_columns:
            raise ValueError(
                f"Unknown grouping columns: "
                f"{missing_group_columns}"
            )

        #Every filter must reference a real dataset column
        for condition in plan.filters:
            if condition.column not in df.columns:
                raise ValueError(
                    f"Unknown filter column: "
                    f"'{condition.column}'"
                )

        if plan.ranking:

            #The ranking metric must exist
            if plan.ranking.metric not in df.columns:
                raise ValueError(
                    f"Unknown ranking metric: "
                    f"'{plan.ranking.metric}'"
                )    

            #partition columns must exist too.
            missing_partition_columns=[
                column 
                for column in plan.ranking.partition_by
                if column not in df.columns
            ]

            if missing_partition_columns:
                raise ValueError(
                    f"Unknown partition columns:"
                    f"{missing_partition_columns}"
                )
        if plan.time_range:

            #time column must exist in the dataset
            if plan.time_range.column not in df.columns:
                raise ValueError(
                    f"Unknown time column: "
                    f"'{plan.time_range.column}'"
                )    
            