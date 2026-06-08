from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import success
from app.crud.crud import get_process_statistics, get_master_statistics, get_monthly_revenue
from app.schemas.schemas import ProcessStatistics, MasterStatistics, MonthlyRevenue, ApiResponse

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/processes", response_model=ApiResponse[list[ProcessStatistics]])
def read_process_statistics(db: Session = Depends(get_db)):
    result = get_process_statistics(db)
    return success(data=result, message="获取工序统计成功")


@router.get("/masters", response_model=ApiResponse[list[MasterStatistics]])
def read_master_statistics(db: Session = Depends(get_db)):
    result = get_master_statistics(db)
    return success(data=result, message="获取师傅统计成功")


@router.get("/revenue", response_model=ApiResponse[list[MonthlyRevenue]])
def read_monthly_revenue(months: int = 12, db: Session = Depends(get_db)):
    result = get_monthly_revenue(db, months=months)
    return success(data=result, message="获取营收统计成功")
