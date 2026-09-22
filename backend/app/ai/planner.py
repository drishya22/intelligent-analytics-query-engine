from app.ai.schemas import QueryPlan

class QueryPlanner:
    """Convert a natural language query into a structured QueryPlan."""

    def __init__(self,llm):
        self.llm=llm

    def plan(self, query:str, context:str)->QueryPlan:
        #ask LLM to convert the query into our structured schema

        response=self.llm.generate(
            query=query,
            context=context
        ) 
        # Convert LLM response into our validated Pydantic schema.
        return QueryPlan.model_validate(response)
             