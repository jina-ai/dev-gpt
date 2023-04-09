# from fastapi import FastAPI
# from fastapi.exceptions import RequestValidationError
# from pydantic import BaseModel
# from typing import Optional, Dict
#
# from starlette.middleware.cors import CORSMiddleware
# from starlette.requests import Request
# from starlette.responses import JSONResponse
# from main import main
#
# app = FastAPI()
#
# # Define the request model
# class CreateRequest(BaseModel):
#     test_scenario: str
#     executor_description: str
#
# # Define the response model
# class CreateResponse(BaseModel):
#     result: Dict[str, str]
#     success: bool
#     message: Optional[str]
#
# @app.post("/create", response_model=CreateResponse)
# def create_endpoint(request: CreateRequest):
#
#     result = main(
#         executor_description=request.executor_description,
#         test_scenario=request.test_scenario,
#     )
#     return CreateResponse(result=result, success=True, message=None)
#
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# # Add a custom exception handler for RequestValidationError
# @app.exception_handler(RequestValidationError)
# def validation_exception_handler(request: Request, exc: RequestValidationError):
#     return JSONResponse(
#         status_code=422,
#         content={"detail": exc.errors()},
#     )
#
#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("server:app", host="0.0.0.0", port=8000, log_level="info")
