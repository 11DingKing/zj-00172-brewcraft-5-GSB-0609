from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.core.response import success, success_page
from app.crud.crud import (
    get_material, get_materials, create_material, update_material,
    get_low_stock_materials, create_process_bom, get_process_boms,
    get_stock_batch_by_number, get_stock_batches_by_booking
)
from app.schemas.schemas import (
    Material, MaterialCreate, MaterialUpdate, MaterialAlert,
    ProcessBOMCreate, ProcessBOMDetail, StockBatchDetail,
    ApiResponse, PageResponse
)

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("/", response_model=ApiResponse[Material])
def create_new_material(material: MaterialCreate, db: Session = Depends(get_db)):
    try:
        result = create_material(db=db, material=material)
        return success(data=result, message="创建原料成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=ApiResponse[PageResponse[Material]])
def read_materials(page: int = 1, pageSize: int = 100, db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = get_materials(db, skip=skip, limit=pageSize)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取原料列表成功")


@router.get("/alerts", response_model=ApiResponse[List[MaterialAlert]])
def read_low_stock_alerts(db: Session = Depends(get_db)):
    items = get_low_stock_materials(db)
    return success(data=items, message="获取库存告警清单成功")


@router.get("/{material_id}", response_model=ApiResponse[Material])
def read_material(material_id: int, db: Session = Depends(get_db)):
    db_material = get_material(db, material_id=material_id)
    if db_material is None:
        raise HTTPException(status_code=404, detail="原料不存在")
    return success(data=db_material, message="获取原料详情成功")


@router.put("/{material_id}", response_model=ApiResponse[Material])
def update_existing_material(material_id: int, material: MaterialUpdate, db: Session = Depends(get_db)):
    try:
        result = update_material(db=db, material_id=material_id, material=material)
        return success(data=result, message="更新原料成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/boms", response_model=ApiResponse[ProcessBOMDetail])
def create_new_process_bom(bom: ProcessBOMCreate, db: Session = Depends(get_db)):
    try:
        result = create_process_bom(db=db, bom=bom)
        details = get_process_boms(db, process_id=bom.process_id)
        match = next((d for d in details if d["id"] == result.id), None)
        return success(data=match, message="创建工序 BOM 成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/boms/list", response_model=ApiResponse[List[ProcessBOMDetail]])
def read_process_boms(process_id: Optional[int] = None, db: Session = Depends(get_db)):
    items = get_process_boms(db, process_id=process_id)
    return success(data=items, message="获取工序 BOM 列表成功")


@router.get("/batches/{batch_number}", response_model=ApiResponse[StockBatchDetail])
def read_stock_batch(batch_number: str, db: Session = Depends(get_db)):
    batch = get_stock_batch_by_number(db, batch_number)
    if batch is None:
        raise HTTPException(status_code=404, detail="批次不存在")
    return success(data=batch, message="获取批次明细成功")


@router.get("/batches/by-booking/{booking_id}", response_model=ApiResponse[List[StockBatchDetail]])
def read_stock_batches_by_booking(booking_id: int, db: Session = Depends(get_db)):
    batches = get_stock_batches_by_booking(db, booking_id)
    return success(data=batches, message="获取预约对应的批次明细成功")
