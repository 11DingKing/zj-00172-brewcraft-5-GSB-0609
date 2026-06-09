from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.response import success, success_page
from app.core.exceptions import BusinessException
from app.crud.crud import get_booking, get_bookings, create_booking, add_booking_review, cancel_booking
from app.schemas.schemas import Booking, BookingCreate, BookingReview, BookingCancel, ApiResponse, PageResponse

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=ApiResponse[Booking])
def create_new_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    try:
        result = create_booking(db=db, booking=booking)
        return success(data=result, message="创建预约成功")
    except BusinessException as e:
        raise HTTPException(status_code=200, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=ApiResponse[PageResponse[Booking]])
def read_bookings(page: int = 1, pageSize: int = 100, status: Optional[str] = None, db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = get_bookings(db, skip=skip, limit=pageSize, status=status)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取预约列表成功")


@router.get("/{booking_id}", response_model=ApiResponse[Booking])
def read_booking(booking_id: int, db: Session = Depends(get_db)):
    db_booking = get_booking(db, booking_id=booking_id)
    if db_booking is None:
        raise HTTPException(status_code=404, detail="预约不存在")
    return success(data=db_booking, message="获取预约详情成功")


@router.post("/{booking_id}/cancel", response_model=ApiResponse[Booking])
def cancel_booking_endpoint(booking_id: int, cancel_data: Optional[BookingCancel] = None, db: Session = Depends(get_db)):
    try:
        result = cancel_booking(db=db, booking_id=booking_id, cancel_data=cancel_data)
        return success(data=result, message="取消预约成功，库存已回滚")
    except BusinessException as e:
        raise HTTPException(status_code=200, detail=e.message)


@router.post("/{booking_id}/review", response_model=ApiResponse[Booking])
def create_booking_review(booking_id: int, review: BookingReview, db: Session = Depends(get_db)):
    try:
        result = add_booking_review(db=db, booking_id=booking_id, review=review)
        return success(data=result, message="评价成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
