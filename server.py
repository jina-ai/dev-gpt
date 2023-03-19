from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from main import main

app = FastAPI()

# Define the request model
class CreateRequest(BaseModel):
    executor_name: str
    executor_description: str
    input_modality: str
    input_doc_field: str
    output_modality: str
    output_doc_field: str
    test_in: str
    test_out: str

# Define the response model
class CreateResponse(BaseModel):
    result: Dict[str, str]
    success: bool
    message: Optional[str]

@app.post("/create", response_model=CreateResponse)
async def create_endpoint(request: CreateRequest):

    result = await main(
        executor_name=request.executor_name,
        executor_description=request.executor_description,
        input_modality=request.input_modality,
        input_doc_field=request.input_doc_field,
        output_modality=request.output_modality,
        output_doc_field=request.output_doc_field,
        test_in=request.test_in,
        test_out=request.test_out,
        do_validation=False
    )
    return CreateResponse(result=result, success=True, message=None)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add a custom exception handler for RequestValidationError
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, log_level="info")
