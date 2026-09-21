import pandas as pd

from app.ai.schemas import QueryPlan

class AnalyticsExecutor:
    """Execute validated QueryPlans against a pandas DataFrame."""
    def execute(self,df:pd.DataFrame,plan: QueryPlan)-> pd.DataFrame:
        working_df=df.copy()

        #Applying filters
        for filter_condition in plan.filters:
            working_df=self._apply_filter(
                working_df,
                filter_condition.column,
                filter_condition.operator,
                filter_condition.value
            )

        if working_df.empty:
            return pd.DataFrame()

        #Aggregate
        result=self._aggregate(working_df,plan)

        #Sort
        if plan.order_by:
            if plan.order_by not in result.columns:
                raise ValueError(
                    f"Cannot order by '{plan.order_by}'."
                    f"Available columns: {list(result.columns)}" 
                )     
            result=result.sort_values(
                by=plan.order_by,
                ascending=plan.order_ascending=="asc"
            )
        #Limit
        if plan.limit is not None:
            result=result.head(plan.limit)
        return result.reset_index(drop=True)

    @staticmethod
    def _aggregate(df:pd.DataFrame,plan:QueryPlan)->pd.DataFrame:
        if plan.metric not in df.columns:
            raise ValueError(
                f"Unknown metric '{plan.metric}'."
                f"Available columns: {list(df.columns)}"
            )

        if plan.group_by:
            missing=[column for column in plan.group_by if column not in df.columns]

            if missing:
                raise ValueError(
                    f"Unknown grouping columns: {missing} "

                )             

            grouped=df.groupby(plan.group_by, dropna=False)[plan.metric]

            if plan.aggregation=="sum":
                result=grouped.sum()
            elif plan.aggregation=="mean":
                result=grouped.mean()
            elif plan.aggregation=="count":
                result=grouped.count()
            elif plan.aggregation=="count_distinct":
                result=grouped.nunique()
            elif plan.aggregation=="min":
                result=grouped.min()
            elif plan.aggregation=="max":
                result=grouped.max()
            else:
                raise ValueError(
                    f"Unsupported aggregation: '{plan.aggregation}'"                
                )
            return result.reset_index(
                name=f"{plan.aggregation}_{plan.metric}"
            ) 

        if plan.aggregation=="sum":
            value=df[plan.metric].sum()
        elif plan.aggregation=="mean":
            value=df[plan.metric].mean()
        elif plan.aggregation=="count":
            value=df[plan.metric].count()
        elif plan.aggregation=="count_distinct":
            value=df[plan.metric].nunique()
        elif plan.aggregation=="min":
            value=df[plan.metric].min()   
        elif plan.aggregation=="max":
            value=df[plan.metric].max()
        else:
            raise ValueError(
                f"Unsupported aggregation: '{plan.aggregation}'"
            )
        return pd.DataFrame(
            {
                f"{plan.aggregation}_{plan.metric}":[value]
            }
        )                                       