from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import success
from app.crud.crud import get_certificate, get_certificate_by_number, create_certificate
from app.schemas.schemas import Certificate, CertificateCreate, ApiResponse

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.post("/", response_model=ApiResponse[Certificate])
def create_new_certificate(certificate: CertificateCreate, db: Session = Depends(get_db)):
    try:
        result = create_certificate(db=db, certificate=certificate)
        return success(data=result, message="创建证书成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{certificate_id}", response_model=ApiResponse[Certificate])
def read_certificate(certificate_id: int, db: Session = Depends(get_db)):
    db_certificate = get_certificate(db, certificate_id=certificate_id)
    if db_certificate is None:
        raise HTTPException(status_code=404, detail="证书不存在")
    return success(data=db_certificate, message="获取证书详情成功")


@router.get("/number/{certificate_number}", response_model=ApiResponse[Certificate])
def read_certificate_by_number(certificate_number: str, db: Session = Depends(get_db)):
    db_certificate = get_certificate_by_number(db, certificate_number=certificate_number)
    if db_certificate is None:
        raise HTTPException(status_code=404, detail="证书不存在")
    return success(data=db_certificate, message="获取证书详情成功")
