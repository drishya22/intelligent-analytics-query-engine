import pandas as pd

from app.ai.schemas import QueryPlan

class AnalyticsExecutor:
    """Execute validated QueryPlans against a pandas DataFrame."""
    def execute(self,df:pd.DataFrame,plan: QueryPlan)-> pd.DataFrame:
        working_df=df.copy()

        #Applying filters
        
        working_df=self._apply_filters(working_df,plan)
        working_df=self._apply_time_range(working_df,plan)

        if working_df.empty:
            return pd.DataFrame()

        #Aggregate
        result=self._aggregate(working_df,plan)

        #Derived metric
        if plan.derived_metric:
            result=self._apply_derived_metric(result,plan)          
            
        #Ranking
        if plan.ranking:
            result=result._apply_ranking(result,plan)
        return result.reset_index(drop=True)

    @staticmethod
    def _aggregate(df:pd.DataFrame,plan:QueryPlan)->pd.DataFrame:
        if plan.metric not in df.columns:
            raise ValueError(
                f"Unknown metric '{plan.metric}'."
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
    @staticmethod
    def _apply_filters(df:pd.DataFrame,plan:QueryPlan)->pf.DataFrame:
        for condition in plan.filters:
            if condition.column not in df.columns:
                raise ValueError(
                    f"Unknown filter column:"
                    f"'{condition.column}'"
                )
            series=df[condition.column]
            operator=condition.operator
            value=condition.value

            if operator=="==":
                df=df[series==value]
            elif operator=="!=":
                df=df[series!=value]
            elif operator==">":
                df=df[series>value]
            elif operator==">=":
                df=df[series>=value]
            elif operator=="<":
                df=df[series<value]
            elif operator=="<=":
                df=df[series<=value]
            elif operator=="in":
                df=df[series.isin(value)]
            elif operator=="contains":
                df=df[series.astype(str).contains(str(value),case=False,na=False)]          
            else:
                raise ValueError(
                    f"Unsupported filter operator: "
                    f"{operator}"
                )
        return df
    @staticmethod
    def _apply_time_range(df:pd.DataFrame,plan:QueryPlan)->pd.DataFrame:
        if not plan.time_range:
            return df 
        time_column=plan.time_range.column
        if time_column not in df.columns:
            raise ValueError(
                f"Unknown time column: '{time_column}'"
            ) 
        df=df.copy()
        df[time_column]=pd.to_datetime(
            df[time_column],
            errors="coerce"
        )                  
        if plan.time_range.start:
            df=df[df[time_column]>=pd.to_datetime(plan.time_range.start)]
        if plan.time_range.end:
            df=df[df[time_column]<=pd.to_datetime(plan.time_range.end)]
        return df 
    @staticmethod
    def _apply_derived_metric(result: pd.DataFrame, plan:QueryPlan)->pd.DataFrame:
        return result
    @staticmethod
    def _apply_ranking(result:pd.DataFrame,plan:QueryPlan)->pd.DataFrame:
        return result

