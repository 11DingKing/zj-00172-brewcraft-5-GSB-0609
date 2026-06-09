from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.response import success, success_page
from app.core.exceptions import BusinessException
from app.crud import crud
from app.schemas.schemas import (
    Material, MaterialCreate, MaterialUpdate, ProcessBOM, ProcessBOMCreate,
    StockTransaction, StockShortageInfo, BatchDetail, ApiResponse, PageResponse
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/materials", response_model=ApiResponse[PageResponse[Material]])
def read_materials(page: int = 1, pageSize: int = 100, db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = crud.get_materials(db, skip=skip, limit=pageSize)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取原料列表成功")


@router.post("/materials", response_model=ApiResponse[Material])
def create_new_material(material: MaterialCreate, db: Session = Depends(get_db)):
    try:
        result = crud.create_material(db=db, material=material)
        return success(data=result, message="创建原料成功")
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/materials/{material_id}", response_model=ApiResponse[Material])
def read_material(material_id: int, db: Session = Depends(get_db)):
    db_material = crud.get_material(db, material_id=material_id)
    if db_material is None:
        raise HTTPException(status_code=404, detail="原料不存在")
    return success(data=db_material, message="获取原料详情成功")


@router.put("/materials/{material_id}", response_model=ApiResponse[Material])
def update_existing_material(material_id: int, material_update: MaterialUpdate, db: Session = Depends(get_db)):
    try:
        result = crud.update_material(db=db, material_id=material_id, material_update=material_update)
        return success(data=result, message="更新原料成功")
    except BusinessException as e:
        raise HTTPException(status_code=400 if e.code == 400 else 404, detail=e.message)


@router.get("/alerts/low-stock", response_model=ApiResponse[list[StockShortageInfo]])
def read_low_stock_alerts(db: Session = Depends(get_db)):
    items = crud.get_low_stock_materials(db)
    return success(data=items, message=f"查询到 {len(items)} 个库存告警原料")


@router.get("/boms", response_model=ApiResponse[PageResponse[ProcessBOM]])
def read_boms(process_id: Optional[int] = None, page: int = 1, pageSize: int = 100, db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = crud.get_process_boms(db, process_id=process_id, skip=skip, limit=pageSize)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取 BOM 列表成功")


@router.post("/boms", response_model=ApiResponse[ProcessBOM])
def create_new_bom(bom: ProcessBOMCreate, db: Session = Depends(get_db)):
    try:
        result = crud.create_process_bom(db=db, bom=bom)
        return success(data=result, message="创建 BOM 成功")
    except BusinessException as e:
        raise HTTPException(status_code=400 if e.code == 400 else 404, detail=e.message)


@router.delete("/boms/{bom_id}", response_model=ApiResponse[ProcessBOM])
def delete_existing_bom(bom_id: int, db: Session = Depends(get_db)):
    try:
        result = crud.delete_process_bom(db=db, bom_id=bom_id)
        return success(data=result, message="删除 BOM 成功")
    except BusinessException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/transactions", response_model=ApiResponse[PageResponse[StockTransaction]])
def read_stock_transactions(
    booking_id: Optional[int] = None,
    material_id: Optional[int] = None,
    page: int = 1,
    pageSize: int = 100,
    db: Session = Depends(get_db)
):
    skip = (page - 1) * pageSize
    items, total = crud.get_stock_transactions(
        db, booking_id=booking_id, material_id=material_id, skip=skip, limit=pageSize
    )
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取库存流水成功")


@router.get("/batches/{batch_number}", response_model=ApiResponse[list[BatchDetail]])
def read_batch_details(batch_number: str, db: Session = Depends(get_db)):
    items = crud.get_stock_transactions_by_batch(db, batch_number=batch_number)
    if not items:
        raise HTTPException(status_code=404, detail="批次号不存在")
    return success(data=items, message=f"查询到批次 {batch_number} 的 {len(items)} 条消耗记录")
