from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class BusinessException(Exception):
    def __init__(self, code: int, message: str, data: dict = None):
        self.code = code
        self.message = message
        self.data = data


async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=200,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": exc.data
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=200,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join([str(x) for x in error["loc"]]),
            "message": error["msg"]
        })
    return JSONResponse(
        status_code=200,
        content={
            "code": 400,
            "message": "参数验证失败",
            "data": {"errors": errors}
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None
        }
    )
