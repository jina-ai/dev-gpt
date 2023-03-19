from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict

from main import main

app = FastAPI()

# Define the request model
class CreateRequest(BaseModel):
    executor_name: str
    input_executor_description: str
    input_modality: str
    input_doc_field: str
    output_modality: str
    output_doc_field: str
    input_test_in: HttpUrl
    input_test_out: str

# Define the response model
class CreateResponse(BaseModel):
    result: Dict[str, str]
    success: bool
    message: Optional[str]

@app.post("/create", response_model=CreateResponse)
async def create_endpoint(request: CreateRequest):
    try:
        result = main(
            executor_name=request.executor_name,
            input_executor_description=request.input_executor_description,
            input_modality=request.input_modality,
            input_doc_field=request.input_doc_field,
            output_modality=request.output_modality,
            output_doc_field=request.output_doc_field,
            input_test_in=request.input_test_in,
            input_test_out=request.input_test_out,
        )
        return CreateResponse(result=result, success=True, message=None)
    except Exception as e:
        return CreateResponse(result=None, success=False, message=str(e))