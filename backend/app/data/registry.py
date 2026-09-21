from dataclasses import dataclass,field

@dataclass
class SemanticRegistry:
    """Semantic metadata used by the query planner."""

    metrics: dict[str,str]=field(default_factory=dict)
    dimensions: list[str]=field(default_factory=list)
    synonyms: dict[str,str]=field(default_factory=dict)
    time_mappings: dict[str,str]=field(default_factory=dict)

    def resolve_term(self,term:str)->str:
        normalized=term.strip().lower()
        return self.synonyms.get(normalized,normalized)
         