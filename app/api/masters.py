from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import success, success_page
from app.crud.crud import get_master, get_masters, create_master
from app.schemas.schemas import Master, MasterCreate, ApiResponse, PageResponse

router = APIRouter(prefix="/masters", tags=["masters"])


@router.post("/", response_model=ApiResponse[Master])
def create_new_master(master: MasterCreate, db: Session = Depends(get_db)):
    result = create_master(db=db, master=master)
    return success(data=result, message="创建师傅成功")


@router.get("/", response_model=ApiResponse[PageResponse[Master]])
def read_masters(page: int = 1, pageSize: int = 100, db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = get_masters(db, skip=skip, limit=pageSize)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取师傅列表成功")


@router.get("/{master_id}", response_model=ApiResponse[Master])
def read_master(master_id: int, db: Session = Depends(get_db)):
    db_master = get_master(db, master_id=master_id)
    if db_master is None:
        raise HTTPException(status_code=404, detail="师傅不存在")
    return success(data=db_master, message="获取师傅详情成功")
