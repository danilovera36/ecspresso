from pydantic import BaseModel, validator
import json

class VariableCreate(BaseModel):
    app_name: str
    environment: str
    key: str
    value: str

class SecretCreate(BaseModel):
    app_name: str
    environment: str
    key: str
    value: str # Este valor viaja a AWS SSM, nunca se guarda en la DB

class TemplateCreate(BaseModel):
    environment: str
    target_container: str
    base_json: str

    @validator('base_json')
    def validate_json(cls, v):
        try:
            json.loads(v)
        except json.JSONDecodeError:
            raise ValueError('El JSON proporcionado no es válido')
        return v
