from typing import Any, Literal
from pydantic import BaseModel, Field

class Filter(BaseModel):
    column:str
    operator: Literal["==","!=",">",">=","<","<=","in","contains"]
    value: Any

class QueryPlan(BaseModel):
    """Structured representation of an analytical query."""

    metric:str
    aggregation:Literal["sum","mean","count","count_distinct","min","max"]
    group_by: list[str]=Field(default_factory=list)
    filters:list[Filter]=Field(default_factory=list)
    order_by: str | None = None
    order_direction: Literal["asc","desc"]="desc"
    limit: int | None = None
    time_column: str | None = None
    explanation: str | None = None   
    