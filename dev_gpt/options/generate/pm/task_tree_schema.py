from typing import Dict, List, Union, Optional
from pydantic import BaseModel, Field

class JSONSchema(BaseModel):
    type: str
    format: Union[str, None] = None
    items: Union['JSONSchema', None] = None
    properties: Dict[str, 'JSONSchema'] = Field(default_factory=dict)
    additionalProperties: Union[bool, 'JSONSchema'] = True
    required: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

class TaskTree(BaseModel):
    description: Optional[str]
    python_fn_signature: str
    sub_fns: List['TaskTree']

JSONSchema.update_forward_refs()
TaskTree.update_forward_refs()
#
