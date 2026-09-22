from dataclasses import dataclass,field
import json

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

    @classmethod
    def from_dict(cls,data:dict)->"SemanticRegistry":
        """Create a registry from data dictionary."""

        return cls(
            metrics=data.get("metrics",{}),
            dimensions=data.get("dimensions",[]),
            synonyms=data.get("synonyms",{}),
            time_mappings=data.get("time_mappings",{})
        )     

    @classmethod
    def from_json(cls,path:str)->"SemanticRegistry":
        """Load semantic metadata from a JSON file. """

        with open(path,"r",encoding="utf-8-sig") as file:
            data=json.load(file)

        return cls.from_dict(data)

    def is_metric(self,term:str)->bool:
        """Check whether a term resolves to a known metric."""
        resolved=self.resolve_term(term)
        return resolved in self.metrics

    def is_dimension(self,term:str)->bool:
        """Check whether a term resolves to a known dimension."""
        resolved=self.resolve_term(term)
        return resolved in self.dimensions

    def resolve_time(self,term:str)->bool:
        """Resolve a natural-language time expression."""      
        normalized=term.strip().lower()
        return self.time_mappings.get(normalized)

