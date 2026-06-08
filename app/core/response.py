from typing import Generic, TypeVar, Optional, List
from app.schemas.schemas import ApiResponse, PageResponse

T = TypeVar('T')


def success(data: Optional[T] = None, message: str = "Success") -> ApiResponse[T]:
    return ApiResponse[T](code=200, message=message, data=data)


def success_page(items: List[T], total: int, page: int, page_size: int, message: str = "Success") -> ApiResponse[PageResponse[T]]:
    page_data = PageResponse[T](
        items=items,
        total=total,
        page=page,
        pageSize=page_size
    )
    return ApiResponse[PageResponse[T]](code=200, message=message, data=page_data)


def error(code: int, message: str, data: Optional[dict] = None) -> ApiResponse:
    return ApiResponse(code=code, message=message, data=data)
