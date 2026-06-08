from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import success, success_page
from app.crud.crud import get_process, get_processes, create_process
from app.schemas.schemas import Process, ProcessCreate, ApiResponse, PageResponse

router = APIRouter(prefix="/processes", tags=["processes"])


@router.post("/", response_model=ApiResponse[Process])
def create_new_process(process: ProcessCreate, db: Session = Depends(get_db)):
    result = create_process(db=db, process=process)
    return success(data=result, message="创建工序成功")


@router.get("/", response_model=ApiResponse[PageResponse[Process]])
def read_processes(page: int = 1, pageSize: int = 100, db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = get_processes(db, skip=skip, limit=pageSize)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取工序列表成功")


@router.get("/{process_id}", response_model=ApiResponse[Process])
def read_process(process_id: int, db: Session = Depends(get_db)):
    db_process = get_process(db, process_id=process_id)
    if db_process is None:
        raise HTTPException(status_code=404, detail="工序不存在")
    return success(data=db_process, message="获取工序详情成功")
