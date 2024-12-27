from dataclasses import dataclass, asdict, fields
from typing import Dict, List


@dataclass
class Node:
    url: str
    freshness: float = 0
    last_visited: float = None
    cache: object = None
    label: str = None
    data: object = None
    pattern: str = None
    fan_in: List[object] = None
    fan_out: List[object] = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def get_fields(cls, begin=1):
        return {f.name: i + begin for i, f in enumerate(fields(cls))}
        
    @classmethod
    def from_dict(cls, data: dict):
        field_names = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)