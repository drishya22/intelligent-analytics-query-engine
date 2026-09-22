from typing import Any, Literal
from pydantic import BaseModel, Field

class Metric(BaseModel):
    name:str
    aggregation: Literal["sum","mean","count","count_distinct","min","max"]

class Filter(BaseModel):
    column:str
    operator: Literal["==","!=",">",">=","<","<=","in","contains"]
    value: Any

class Ranking(BaseModel):
    metric: str
    direction: Literal["asc","desc"]="desc"
    limit: int | None =None
    partition_by: list[str]=Field(default_factory=list)

class TimeRange(BaseModel):
    column:str
    start: str|None=None
    end:str|None=None
    period:str|None=None

class DerivedMetric(BaseModel):
    name:str
    operation: Literal["ratio","percentage","growth","difference"]
    numerator: str|None=None
    denominator: str|None=None
    previous_metric:str|None=None
    current_metric:str|None=None

class Comparison(BaseModel):
    type:Literal["target","previous_period","previous_year"]
    metric:str
    operation:Literal["==","!=",">=",">","<=","<"] |None=None
    comparison_metric:str|None=None              

class QueryPlan(BaseModel):
    """Structured representation of an analytical query."""

    metrics:list[Metric]=Field(default_factory=list)
    group_by: list[str]=Field(default_factory=list)
    filters:list[Filter]=Field(default_factory=list)
    ranking: Ranking|None=None
    time_range:TimeRange|None=None
    derived_metric:DerivedMetric|None=None
    comparison: Comparison|None=None
    secondary_dataset:str|None=None