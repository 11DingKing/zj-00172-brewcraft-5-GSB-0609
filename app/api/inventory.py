from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.core.response import success, success_page
from app.crud.crud import (
    get_material, get_materials, create_material, update_material,
    get_material_alerts, get_process_bom, get_process_boms, create_process_bom,
    delete_process_bom, get_process_bom_by_process,
    get_batch_by_batch_no, get_batches_by_booking, get_all_batches
)
from app.schemas.schemas import (
    Material, MaterialCreate, ProcessBOM, ProcessBOMCreate, ProcessBOMDetail,
    InventoryBatch, MaterialAlert, ApiResponse, PageResponse
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/materials", response_model=ApiResponse[Material])
def create_new_material(material: MaterialCreate, db: Session = Depends(get_db)):
    from app.crud.crud import get_material_by_name
    existing = get_material_by_name(db, material.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"原料 {material.name} 已存在")
    result = create_material(db, name=material.name, unit=material.unit,
                            current_stock=material.current_stock, safety_stock=material.safety_stock)
    return success(data=result, message="创建原料成功")


@router.get("/materials", response_model=ApiResponse[PageResponse[Material]])
def read_materials(page: int = 1, pageSize: int = 100, db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = get_materials(db, skip=skip, limit=pageSize)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取原料列表成功")


@router.get("/materials/{material_id}", response_model=ApiResponse[Material])
def read_material(material_id: int, db: Session = Depends(get_db)):
    db_material = get_material(db, material_id)
    if db_material is None:
        raise HTTPException(status_code=404, detail="原料不存在")
    return success(data=db_material, message="获取原料详情成功")


@router.put("/materials/{material_id}", response_model=ApiResponse[Material])
def update_existing_material(material_id: int, current_stock: Optional[float] = None,
                            safety_stock: Optional[float] = None, db: Session = Depends(get_db)):
    try:
        result = update_material(db, material_id, current_stock, safety_stock)
        return success(data=result, message="更新原料成功")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/alerts", response_model=ApiResponse[List[MaterialAlert]])
def read_material_alerts(db: Session = Depends(get_db)):
    alerts = get_material_alerts(db)
    return success(data=alerts, message="获取库存告警成功")


@router.post("/bom", response_model=ApiResponse[ProcessBOMDetail])
def create_new_bom(bom: ProcessBOMCreate, db: Session = Depends(get_db)):
    try:
        result = create_process_bom(db, process_id=bom.process_id,
                                    material_id=bom.material_id,
                                    quantity_per_session=bom.quantity_per_session)
        return success(data=result, message="创建BOM成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bom", response_model=ApiResponse[PageResponse[ProcessBOMDetail]])
def read_boms(page: int = 1, pageSize: int = 100, db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = get_process_boms(db, skip=skip, limit=pageSize)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取BOM列表成功")


@router.get("/bom/process/{process_id}", response_model=ApiResponse[List[ProcessBOMDetail]])
def read_bom_by_process(process_id: int, db: Session = Depends(get_db)):
    items = get_process_bom_by_process(db, process_id)
    return success(data=items, message="获取工序BOM成功")


@router.delete("/bom/{bom_id}", response_model=ApiResponse[ProcessBOMDetail])
def delete_existing_bom(bom_id: int, db: Session = Depends(get_db)):
    try:
        result = delete_process_bom(db, bom_id)
        return success(data=result, message="删除BOM成功")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/batches", response_model=ApiResponse[PageResponse[InventoryBatch]])
def read_batches(page: int = 1, pageSize: int = 100, db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = get_all_batches(db, skip=skip, limit=pageSize)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取批次列表成功")


@router.get("/batches/batch-no/{batch_no}", response_model=ApiResponse[List[InventoryBatch]])
def read_batch_by_batch_no(batch_no: str, db: Session = Depends(get_db)):
    items = get_batch_by_batch_no(db, batch_no)
    if not items:
        raise HTTPException(status_code=404, detail="批次号不存在")
    return success(data=items, message="获取批次明细成功")


@router.get("/batches/booking/{booking_id}", response_model=ApiResponse[List[InventoryBatch]])
def read_batches_by_booking(booking_id: int, db: Session = Depends(get_db)):
    items = get_batches_by_booking(db, booking_id)
    return success(data=items, message="获取预约批次明细成功")
