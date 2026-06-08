from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.response import success
from app.crud.crud import get_schedule, get_schedules, create_schedule
from app.schemas.schemas import Schedule, ScheduleCreate, ApiResponse

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/", response_model=ApiResponse[Schedule])
def create_new_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    try:
        result = create_schedule(db=db, schedule=schedule)
        return success(data=result, message="创建排期成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=ApiResponse[list[Schedule]])
def read_schedules(workshop_code: Optional[str] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, db: Session = Depends(get_db)):
    schedules = get_schedules(db, workshop_code=workshop_code, start_date=start_date, end_date=end_date)
    return success(data=schedules, message="获取排期列表成功")


@router.get("/{schedule_id}", response_model=ApiResponse[Schedule])
def read_schedule(schedule_id: int, db: Session = Depends(get_db)):
    db_schedule = get_schedule(db, schedule_id=schedule_id)
    if db_schedule is None:
        raise HTTPException(status_code=404, detail="排期不存在")
    return success(data=db_schedule, message="获取排期详情成功")
