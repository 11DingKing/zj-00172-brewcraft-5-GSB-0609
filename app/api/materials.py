from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.response import success, success_page
from app.crud.crud import (
    get_material, get_materials, create_material, update_material, delete_material,
    get_low_stock_materials, get_process_bom, get_process_boms_by_process, 
    get_process_boms_by_course, create_process_bom, delete_process_bom,
    get_material_batch, get_material_batch_by_number, get_material_batches,
    cancel_booking
)
from app.schemas.schemas import (
    Material, MaterialCreate, MaterialUpdate, ApiResponse, PageResponse,
    ProcessBOM, ProcessBOMCreate, ProcessBOMWithProcess,
    MaterialBatch, MaterialBatchDetail, StockAlert
)

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("/", response_model=ApiResponse[PageResponse[Material]])
def read_materials(page: int = 1, pageSize: int = 100, db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = get_materials(db, skip=skip, limit=pageSize)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取原料列表成功")


@router.get("/alert", response_model=ApiResponse[list[StockAlert]])
def read_low_stock_materials(db: Session = Depends(get_db)):
    items = get_low_stock_materials(db)
    return success(data=items, message="获取库存告警清单成功")


@router.get("/{material_id}", response_model=ApiResponse[Material])
def read_material(material_id: int, db: Session = Depends(get_db)):
    db_material = get_material(db, material_id=material_id)
    if db_material is None:
        raise HTTPException(status_code=404, detail="原料不存在")
    return success(data=db_material, message="获取原料详情成功")


@router.post("/", response_model=ApiResponse[Material])
def create_new_material(material: MaterialCreate, db: Session = Depends(get_db)):
    result = create_material(db=db, material=material)
    return success(data=result, message="创建原料成功")


@router.put("/{material_id}", response_model=ApiResponse[Material])
def update_existing_material(material_id: int, material: MaterialUpdate, db: Session = Depends(get_db)):
    result = update_material(db=db, material_id=material_id, material=material)
    if result is None:
        raise HTTPException(status_code=404, detail="原料不存在")
    return success(data=result, message="更新原料成功")


@router.delete("/{material_id}", response_model=ApiResponse[Material])
def delete_existing_material(material_id: int, db: Session = Depends(get_db)):
    result = delete_material(db=db, material_id=material_id)
    if result is None:
        raise HTTPException(status_code=404, detail="原料不存在")
    return success(data=result, message="删除原料成功")


@router.get("/processes/{process_id}/boms", response_model=ApiResponse[list[ProcessBOM]])
def read_process_boms(process_id: int, db: Session = Depends(get_db)):
    items = get_process_boms_by_process(db, process_id=process_id)
    return success(data=items, message="获取工序BOM成功")


@router.get("/courses/{course_id}/boms", response_model=ApiResponse[list[ProcessBOMWithProcess]])
def read_course_boms(course_id: int, db: Session = Depends(get_db)):
    items = get_process_boms_by_course(db, course_id=course_id)
    return success(data=items, message="获取课程BOM成功")


@router.post("/boms", response_model=ApiResponse[ProcessBOM])
def create_new_bom(bom: ProcessBOMCreate, db: Session = Depends(get_db)):
    result = create_process_bom(db=db, bom=bom)
    return success(data=result, message="创建BOM成功")


@router.delete("/boms/{bom_id}", response_model=ApiResponse[ProcessBOM])
def delete_existing_bom(bom_id: int, db: Session = Depends(get_db)):
    result = delete_process_bom(db=db, bom_id=bom_id)
    if result is None:
        raise HTTPException(status_code=404, detail="BOM不存在")
    return success(data=result, message="删除BOM成功")


@router.get("/batches/", response_model=ApiResponse[PageResponse[MaterialBatchDetail]])
def read_material_batches(page: int = 1, pageSize: int = 100, 
                          material_id: Optional[int] = None, 
                          booking_id: Optional[int] = None,
                          db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = get_material_batches(db, material_id=material_id, booking_id=booking_id, skip=skip, limit=pageSize)
    
    detail_items = []
    for batch in items:
        detail_items.append({
            "id": batch.id,
            "batch_number": batch.batch_number,
            "booking_id": batch.booking_id,
            "process_id": batch.process_id,
            "process_name": batch.process.name if batch.process else None,
            "material_id": batch.material_id,
            "material_name": batch.material.name,
            "material_unit": batch.material.unit,
            "quantity": batch.quantity,
            "operation_type": batch.operation_type,
            "remark": batch.remark,
            "created_at": batch.created_at
        })
    
    return success_page(items=detail_items, total=total, page=page, page_size=pageSize, message="获取批次列表成功")


@router.get("/batches/number/{batch_number}", response_model=ApiResponse[list[MaterialBatchDetail]])
def read_batch_by_number(batch_number: str, db: Session = Depends(get_db)):
    items = get_material_batch_by_number(db, batch_number=batch_number)
    if not items:
        raise HTTPException(status_code=404, detail="批次不存在")
    return success(data=items, message="获取批次详情成功")


@router.post("/bookings/{booking_id}/cancel", response_model=ApiResponse)
def cancel_existing_booking(booking_id: int, db: Session = Depends(get_db)):
    try:
        cancel_booking(db=db, booking_id=booking_id)
        return success(message="取消预约成功，库存已回滚")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
