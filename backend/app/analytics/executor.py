import pandas as pd

from app.ai.schemas import QueryPlan
from app.analytics.validator import QueryValidator

class AnalyticsExecutor:
    """Execute validated QueryPlans against a pandas DataFrame."""
    def execute(self,df:pd.DataFrame,plan: QueryPlan)-> pd.DataFrame:

        validator=QueryValidator()
        validator.validate(df,plan)

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
            result=self._apply_ranking(result,plan)
        return result.reset_index(drop=True)

    @staticmethod
    def _aggregate(df:pd.DataFrame,plan:QueryPlan)->pd.DataFrame:
        results=[]
        if not plan.metrics:
            raise ValueError("At least one metric is required.")
        for metric in plan.metrics:
            if metric.name not in df.columns:
                raise ValueError(
                    f"Unknown metric '{metric.name}'."
                )

            if plan.group_by:
                missing=[column for column in plan.group_by if column not in df.columns]

                if missing:
                    raise ValueError(
                        f"Unknown grouping columns: {missing} "

                    )             

                grouped=df.groupby(plan.group_by, dropna=False)[metric.name]

                if metric.aggregation=="sum":
                    result=grouped.sum()
                elif metric.aggregation=="mean":
                    result=grouped.mean()
                elif metric.aggregation=="count":
                    result=grouped.count()
                elif metric.aggregation=="count_distinct":
                    result=grouped.nunique()
                elif metric.aggregation=="min":
                    result=grouped.min()
                elif metric.aggregation=="max":
                    result=grouped.max()
                else:
                    raise ValueError(
                        f"Unsupported aggregation: '{metric.aggregation}'"                
                    )
                result=result.reset_index(name=f"{metric.aggregation}_{metric.name}")
            else:
                if metric.aggregation=="sum":
                    value=df[metric.name].sum()
                elif metric.aggregation=="mean":
                    value=df[metric.name].mean()
                elif metric.aggregation=="count":
                    value=df[metric.name].count()
                elif metric.aggregation=="count_distinct":
                    value=df[metric.name].nunique()
                elif metric.aggregation=="min":
                    value=df[metric.name].min()
                elif metric.aggregation=="max":
                    value=df[metric.name].max()
                else:
                    raise ValueError(
                        f"Unsupported aggregation: "
                        f"'{metric.aggregation}'"
                    )                        
                result=pd.DataFrame({
                    f"{metric.aggregation}_{metric.name}":[value]
                })
            results.append(result)
        if len(results)==1:
            return results[0]
        final_result=results[0]

        for result in results[1:]:
            final_result=final_result.merge(
                result,
                on=plan.group_by,
                how="outer"
            )    

        return final_result    

    
    @staticmethod
    def _apply_filters(df:pd.DataFrame,plan:QueryPlan)->pd.DataFrame:
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
                df=df[series.astype(str).str.contains(str(value),case=False,na=False)]          
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
        derived=plan.derived_metric
        if derived is None:
            return result
        if derived.operation=="ratio":
            if not derived.numerator or not derived.denominator:
                raise ValueError(
                    "Ratio requires numerator and denominator."
                )
            if derived.denominator not in result.columns:
                raise ValueError(
                    f"Unknown denominator column: '{derived.denominator}'"
                )
            result[derived.name]=(
                result[derived.numerator]/result[derived.denominator]
            )
        elif derived.operation=="percentage":
            if not derived.numerator or not derived.denominator:
                raise ValueError(
                    "Percentage requires numerator and denominator"
                )
            if derived.denominator not in result.columns:
                raise ValueError(
                    f"Unknown denominator column: '{derived.denominator}'"
                )    
            result[derived.name]=(
                result[derived.numerator]/result[derived.denominator]
            )*100

        elif derived.operation=="difference":
            if not derived.current_metric or not derived.previous_metric:
                raise ValueError(
                    "Difference requires current_metric and previous_metric."
                )
            result[derived.name]=(result[derived.current_metric]-result[derived.previous_metric])
        elif derived.operation=="growth":
            if not derived.current_metric or not derived.previous_metric:
                raise ValueError(
                    "Growth requires current_metric and previous_metric."
                )
            result[derived.name]=(
                (result[derived.current_metric]-result[derived.previous_metric])/result[derived.previous_metric]
            )*100
        else:
            raise ValueError(
                f"Unsupported derived operation: '{derived.operation}'"
            )    
        return result

    
    @staticmethod
    def _apply_ranking(result:pd.DataFrame,plan:QueryPlan)->pd.DataFrame:
        ranking=plan.ranking
        if ranking is None:
            return result
        metric_columns=[
            column 
            for column in result.columns
            if ranking.metric.lower() in column.lower()
        ]

        if not metric_columns:
            raise ValueError(
                f"Could not find ranking metric:"
                f"'{ranking.metric}'"
            )

        metric_column=metric_columns[0]

        if not ranking.partition_by:
            result=result.sort_values(
                by=metric_column,
                ascending=ranking.direction=="asc"
            ) 
            if ranking.limit is not None:
                result=result.head(ranking.limit)
            return result

        missing=[
            column 
            for column in ranking.partition_by
            if column not in result.columns
        ]
        if missing:
            raise ValueError(
                f"Unknown partition columns: {missing}"
            )

        result=result.sort_values(
            by=metric_column,
            ascending=ranking.direction=="asc"
        )

        if ranking.limit is not None:
            result=(
                result.groupby(
                    ranking.partition_by,
                    group_keys=False,
                ).head(ranking.limit)
            )
        return result    

