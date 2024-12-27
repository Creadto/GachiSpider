from dataclasses import dataclass, asdict, fields

@dataclass
class Entity:    
    def to_dict(self):
        return asdict(self)
    
    def update(self, data: dict[str, object]):
        for key, value in data.items():
            if hasattr(self, key):
                if isinstance(value, str):
                    value = value.replace("'", '"')
                setattr(self, key, value)
        
    @classmethod
    def get_fields(cls, begin=1):
        return {f.name: i + begin for i, f in enumerate(fields(cls))}
        
    @classmethod
    def from_dict(cls, data: dict):
        field_names = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)
