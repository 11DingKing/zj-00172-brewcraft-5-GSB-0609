from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.response import success, success_page
from app.crud.crud import get_course, get_courses, create_course
from app.schemas.schemas import Course, CourseCreate, ApiResponse, PageResponse
from app.models.models import CourseType

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("/", response_model=ApiResponse[Course])
def create_new_course(course: CourseCreate, db: Session = Depends(get_db)):
    result = create_course(db=db, course=course)
    return success(data=result, message="创建课程成功")


@router.get("/", response_model=ApiResponse[PageResponse[Course]])
def read_courses(page: int = 1, pageSize: int = 100, course_type: Optional[CourseType] = None, db: Session = Depends(get_db)):
    skip = (page - 1) * pageSize
    items, total = get_courses(db, skip=skip, limit=pageSize, course_type=course_type)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取课程列表成功")


@router.get("/{course_id}", response_model=ApiResponse[Course])
def read_course(course_id: int, db: Session = Depends(get_db)):
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    return success(data=db_course, message="获取课程详情成功")
