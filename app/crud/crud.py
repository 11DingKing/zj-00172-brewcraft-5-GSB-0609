from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta
import uuid
from app.models.models import (
    User, Process, Master, Course, Schedule, Booking, Certificate,
    course_process_association, CourseType, ScheduleType, UserRole,
    MemberLevel, CourseDifficulty, ExperienceRecord, Material, ProcessBOM,
    StockTransaction, StockTransactionType
)
from app.schemas.schemas import (
    UserCreate, ProcessCreate, MasterCreate, CourseCreate, ScheduleCreate,
    BookingCreate, CertificateCreate, BookingReview, MaterialCreate,
    MaterialUpdate, ProcessBOMCreate, BookingCancel, BatchDetail, StockShortageInfo
)
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import BusinessException


def generate_batch_number() -> str:
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    unique_id = uuid.uuid4().hex[:6].upper()
    return f"BATCH-{timestamp}-{unique_id}"


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_process(db: Session, process_id: int):
    return db.query(Process).filter(Process.id == process_id).first()


def get_process_by_code(db: Session, code: str):
    return db.query(Process).filter(Process.code == code).first()


def get_processes(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[Process], int]:
    query = db.query(Process)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def create_process(db: Session, process: ProcessCreate):
    db_process = Process(**process.dict())
    db.add(db_process)
    db.commit()
    db.refresh(db_process)
    return db_process


def get_master(db: Session, master_id: int):
    return db.query(Master).filter(Master.id == master_id).first()


def get_masters(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[Master], int]:
    query = db.query(Master)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def create_master(db: Session, master: MasterCreate):
    db_master = Master(**master.dict())
    db.add(db_master)
    db.commit()
    db.refresh(db_master)
    return db_master


def get_course(db: Session, course_id: int):
    return db.query(Course).filter(Course.id == course_id).first()


def get_courses(db: Session, skip: int = 0, limit: int = 100, course_type: Optional[CourseType] = None) -> Tuple[List[Course], int]:
    query = db.query(Course)
    if course_type:
        query = query.filter(Course.course_type == course_type)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def create_course(db: Session, course: CourseCreate):
    process_ids = course.process_ids
    course_data = course.dict(exclude={"process_ids"})
    db_course = Course(**course_data)
    
    if process_ids:
        processes = db.query(Process).filter(Process.id.in_(process_ids)).all()
        db_course.processes = processes
    
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


def check_schedule_conflict(db: Session, workshop_code: str, start_time: datetime, end_time: datetime, exclude_booking_id: Optional[int] = None):
    query = db.query(Schedule).filter(
        Schedule.workshop_code == workshop_code,
        or_(
            and_(Schedule.start_time <= start_time, Schedule.end_time > start_time),
            and_(Schedule.start_time < end_time, Schedule.end_time >= end_time),
            and_(Schedule.start_time >= start_time, Schedule.end_time <= end_time)
        )
    )
    if exclude_booking_id:
        query = query.filter(Schedule.booking_id != exclude_booking_id)
    return query.first() is not None


def get_schedule(db: Session, schedule_id: int):
    return db.query(Schedule).filter(Schedule.id == schedule_id).first()


def get_schedules(db: Session, workshop_code: Optional[str] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    query = db.query(Schedule)
    if workshop_code:
        query = query.filter(Schedule.workshop_code == workshop_code)
    if start_date:
        query = query.filter(Schedule.start_time >= start_date)
    if end_date:
        query = query.filter(Schedule.end_time <= end_date)
    return query.order_by(Schedule.start_time).all()


def create_schedule(db: Session, schedule: ScheduleCreate):
    if check_schedule_conflict(db, schedule.workshop_code, schedule.start_time, schedule.end_time):
        raise ValueError("Schedule conflict")
    db_schedule = Schedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


def get_booking(db: Session, booking_id: int):
    return db.query(Booking).filter(Booking.id == booking_id).first()


def get_bookings(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> Tuple[List[Booking], int]:
    query = db.query(Booking)
    if status:
        query = query.filter(Booking.status == status)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def calculate_course_material_requirements(db: Session, course_id: int, participant_count: int) -> List[Dict]:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise BusinessException(code=404, message="课程不存在")
    
    requirements = []
    seen_materials = set()
    
    for process in course.processes:
        bom_items = db.query(ProcessBOM).filter(ProcessBOM.process_id == process.id).all()
        for bom in bom_items:
            material = db.query(Material).filter(Material.id == bom.material_id).first()
            if not material:
                continue
            total_qty = bom.quantity_per_batch * participant_count
            key = (bom.material_id, process.id)
            if key not in seen_materials:
                seen_materials.add(key)
                requirements.append({
                    "material_id": material.id,
                    "material_name": material.name,
                    "material_code": material.code,
                    "unit": material.unit,
                    "process_id": process.id,
                    "process_name": process.name,
                    "required_quantity": total_qty,
                    "current_stock": material.stock_quantity
                })
    
    return requirements


def check_and_deduct_stock_for_booking(db: Session, booking_id: int, requirements: List[Dict]) -> List[StockTransaction]:
    transactions = []
    batch_number = generate_batch_number()
    
    try:
        material_ids = list(set([r["material_id"] for r in requirements]))
        materials = db.query(Material).filter(Material.id.in_(material_ids)).with_for_update().all()
        material_map = {m.id: m for m in materials}
        
        shortages = []
        for req in requirements:
            mat = material_map.get(req["material_id"])
            if not mat:
                shortages.append({
                    "material_name": req["material_name"],
                    "shortage": req["required_quantity"]
                })
                continue
            if mat.stock_quantity < req["required_quantity"]:
                shortages.append({
                    "material_name": req["material_name"],
                    "current_stock": mat.stock_quantity,
                    "required": req["required_quantity"],
                    "shortage": req["required_quantity"] - mat.stock_quantity,
                    "unit": req["unit"]
                })
        
        if shortages:
            shortage_msgs = []
            for s in shortages:
                shortage_msgs.append(
                    f"原料「{s['material_name']}」库存不足：当前库存 {s['current_stock']}{s['unit']}，"
                    f"需要 {s['required']}{s['unit']}，缺 {s['shortage']}{s['unit']}"
                )
            raise BusinessException(code=400, message="；".join(shortage_msgs), data={"shortages": shortages})
        
        for req in requirements:
            mat = material_map[req["material_id"]]
            mat.stock_quantity -= req["required_quantity"]
            
            transaction = StockTransaction(
                batch_number=batch_number,
                booking_id=booking_id,
                process_id=req["process_id"],
                material_id=req["material_id"],
                quantity=req["required_quantity"],
                transaction_type=StockTransactionType.DEDUCT,
                remark=f"预约扣减 - {req['process_name']} - {req['material_name']}"
            )
            db.add(transaction)
            transactions.append(transaction)
        
        db.flush()
        return transactions
        
    except BusinessException:
        raise
    except Exception as e:
        db.rollback()
        raise BusinessException(code=500, message=f"库存扣减失败: {str(e)}")


def rollback_stock_for_booking(db: Session, booking_id: int, reason: Optional[str] = None):
    deduct_transactions = db.query(StockTransaction).filter(
        StockTransaction.booking_id == booking_id,
        StockTransaction.transaction_type == StockTransactionType.DEDUCT
    ).all()
    
    if not deduct_transactions:
        return []
    
    material_ids = list(set([t.material_id for t in deduct_transactions]))
    materials = db.query(Material).filter(Material.id.in_(material_ids)).with_for_update().all()
    material_map = {m.id: m for m in materials}
    
    rollback_transactions = []
    
    for deduct_tx in deduct_transactions:
        mat = material_map.get(deduct_tx.material_id)
        if mat:
            mat.stock_quantity += deduct_tx.quantity
        
        existing_rollback = db.query(StockTransaction).filter(
            StockTransaction.related_transaction_id == deduct_tx.id,
            StockTransaction.transaction_type == StockTransactionType.ROLLBACK
        ).first()
        
        if existing_rollback:
            continue
        
        rollback_batch = generate_batch_number()
        rollback_tx = StockTransaction(
            batch_number=rollback_batch,
            booking_id=booking_id,
            process_id=deduct_tx.process_id,
            material_id=deduct_tx.material_id,
            quantity=deduct_tx.quantity,
            transaction_type=StockTransactionType.ROLLBACK,
            related_transaction_id=deduct_tx.id,
            remark=f"预约取消回滚 - {reason or '无原因'}"
        )
        db.add(rollback_tx)
        rollback_transactions.append(rollback_tx)
    
    db.flush()
    return rollback_transactions


def create_booking(db: Session, booking: BookingCreate):
    course = get_course(db, booking.course_id)
    if not course:
        raise BusinessException(code=404, message="课程不存在")
    
    if booking.user_id:
        if not check_booking_permission(db, booking.user_id, booking.course_id):
            raise BusinessException(code=403, message=f"会员等级不足。需要等级: {course.required_level}")
    
    if course.course_type == CourseType.HANDS_ON:
        if course.max_participants and booking.participant_count > course.max_participants:
            raise BusinessException(code=400, message=f"最多允许 {course.max_participants} 人参与")
    
    end_time = booking.start_time + timedelta(minutes=course.duration_minutes)
    
    if check_schedule_conflict(db, booking.workshop_code, booking.start_time, end_time):
        raise BusinessException(code=400, message="排期冲突：该车间此时段已被占用")
    
    total_price = course.price * booking.participant_count
    
    try:
        requirements = calculate_course_material_requirements(db, booking.course_id, booking.participant_count)
        
        booking_data = booking.dict(exclude={"workshop_code", "start_time"})
        booking_data["total_price"] = total_price
        db_booking = Booking(**booking_data)
        db.add(db_booking)
        db.flush()
        
        check_and_deduct_stock_for_booking(db, db_booking.id, requirements)
        
        db_schedule = Schedule(
            workshop_code=booking.workshop_code,
            schedule_type=ScheduleType.EXPERIENCE,
            start_time=booking.start_time,
            end_time=end_time,
            description=f"体验课程: {course.name}",
            booking_id=db_booking.id
        )
        db.add(db_schedule)
        
        if booking.user_id:
            add_experience_for_booking(db, db_booking.id)
        
        db.commit()
        db.refresh(db_booking)
        return db_booking
        
    except BusinessException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise BusinessException(code=500, message=f"创建预约失败: {str(e)}")


def cancel_booking(db: Session, booking_id: int, cancel_data: Optional[BookingCancel] = None):
    db_booking = get_booking(db, booking_id)
    if not db_booking:
        raise BusinessException(code=404, message="预约不存在")
    
    if db_booking.status in ["cancelled", "completed"]:
        raise BusinessException(code=400, message=f"预约状态为 {db_booking.status}，无法取消")
    
    reason = cancel_data.reason if cancel_data else None
    
    try:
        rollback_stock_for_booking(db, booking_id, reason)
        
        db_booking.status = "cancelled"
        
        db_schedule = db.query(Schedule).filter(Schedule.booking_id == booking_id).first()
        if db_schedule:
            db.delete(db_schedule)
        
        db.commit()
        db.refresh(db_booking)
        return db_booking
        
    except BusinessException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise BusinessException(code=500, message=f"取消预约失败: {str(e)}")


def add_booking_review(db: Session, booking_id: int, review: BookingReview):
    db_booking = get_booking(db, booking_id)
    if not db_booking:
        raise ValueError("Booking not found")
    
    db_booking.rating = review.rating
    db_booking.review = review.review
    
    course = db_booking.course
    if course and course.master_id:
        master = get_master(db, course.master_id)
        if master:
            total_rating = master.rating * master.total_reviews
            total_rating += review.rating
            master.total_reviews += 1
            master.rating = round(total_rating / master.total_reviews, 2)
    
    db.commit()
    db.refresh(db_booking)
    return db_booking


def get_certificate(db: Session, certificate_id: int):
    return db.query(Certificate).filter(Certificate.id == certificate_id).first()


def get_certificate_by_number(db: Session, certificate_number: str):
    return db.query(Certificate).filter(Certificate.certificate_number == certificate_number).first()


def create_certificate(db: Session, certificate: CertificateCreate):
    booking = get_booking(db, certificate.booking_id)
    if not booking:
        raise ValueError("Booking not found")
    
    if booking.certificate:
        raise ValueError("Certificate already exists")
    
    certificate_number = f"CERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{booking.id}"
    
    course = booking.course
    experience_content = f"完成 {course.name} 体验课程，包含以下工序：" + "、".join([p.name for p in course.processes])
    
    master_name = None
    if course.master and course.master.user:
        master_name = course.master.user.full_name
    
    db_certificate = Certificate(
        booking_id=certificate.booking_id,
        certificate_number=certificate_number,
        issue_date=datetime.now(),
        participant_names=booking.participant_names or booking.customer_name,
        experience_content=experience_content,
        tasting_notes=certificate.tasting_notes,
        master_name=master_name
    )
    db.add(db_certificate)
    db.commit()
    db.refresh(db_certificate)
    return db_certificate


def get_material(db: Session, material_id: int):
    return db.query(Material).filter(Material.id == material_id).first()


def get_material_by_code(db: Session, code: str):
    return db.query(Material).filter(Material.code == code).first()


def get_materials(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[Material], int]:
    query = db.query(Material)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def create_material(db: Session, material: MaterialCreate):
    existing = get_material_by_code(db, material.code)
    if existing:
        raise BusinessException(code=400, message=f"原料编码 {material.code} 已存在")
    db_material = Material(**material.dict())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material


def update_material(db: Session, material_id: int, material_update: MaterialUpdate):
    db_material = get_material(db, material_id)
    if not db_material:
        raise BusinessException(code=404, message="原料不存在")
    update_data = material_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_material, key, value)
    db.commit()
    db.refresh(db_material)
    return db_material


def get_low_stock_materials(db: Session) -> List[StockShortageInfo]:
    materials = db.query(Material).filter(Material.stock_quantity <= Material.safety_threshold).all()
    result = []
    for mat in materials:
        shortage = mat.safety_threshold - mat.stock_quantity
        result.append(StockShortageInfo(
            material_id=mat.id,
            material_name=mat.name,
            material_code=mat.code,
            unit=mat.unit,
            current_stock=mat.stock_quantity,
            safety_threshold=mat.safety_threshold,
            shortage=shortage if shortage > 0 else 0
        ))
    return result


def get_process_bom(db: Session, bom_id: int):
    return db.query(ProcessBOM).filter(ProcessBOM.id == bom_id).first()


def get_process_boms(db: Session, process_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> Tuple[List[ProcessBOM], int]:
    query = db.query(ProcessBOM)
    if process_id:
        query = query.filter(ProcessBOM.process_id == process_id)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def create_process_bom(db: Session, bom: ProcessBOMCreate):
    process = get_process(db, bom.process_id)
    if not process:
        raise BusinessException(code=404, message="工序不存在")
    material = get_material(db, bom.material_id)
    if not material:
        raise BusinessException(code=404, message="原料不存在")
    existing = db.query(ProcessBOM).filter(
        ProcessBOM.process_id == bom.process_id,
        ProcessBOM.material_id == bom.material_id
    ).first()
    if existing:
        raise BusinessException(code=400, message="该工序已配置此原料的 BOM")
    db_bom = ProcessBOM(**bom.dict())
    db.add(db_bom)
    db.commit()
    db.refresh(db_bom)
    return db_bom


def delete_process_bom(db: Session, bom_id: int):
    db_bom = get_process_bom(db, bom_id)
    if not db_bom:
        raise BusinessException(code=404, message="BOM 不存在")
    db.delete(db_bom)
    db.commit()
    return db_bom


def get_stock_transactions_by_batch(db: Session, batch_number: str) -> List[BatchDetail]:
    transactions = db.query(StockTransaction).filter(
        StockTransaction.batch_number == batch_number
    ).all()
    
    if not transactions:
        return []
    
    booking_ids = list(set([t.booking_id for t in transactions if t.booking_id]))
    bookings = {}
    if booking_ids:
        for b in db.query(Booking).filter(Booking.id.in_(booking_ids)).all():
            bookings[b.id] = b
    
    process_ids = list(set([t.process_id for t in transactions if t.process_id]))
    processes = {}
    if process_ids:
        for p in db.query(Process).filter(Process.id.in_(process_ids)).all():
            processes[p.id] = p
    
    material_ids = list(set([t.material_id for t in transactions]))
    materials = {}
    for m in db.query(Material).filter(Material.id.in_(material_ids)).all():
        materials[m.id] = m
    
    result = []
    for tx in transactions:
        booking = bookings.get(tx.booking_id) if tx.booking_id else None
        process = processes.get(tx.process_id) if tx.process_id else None
        material = materials.get(tx.material_id)
        
        result.append(BatchDetail(
            batch_number=tx.batch_number,
            booking_id=tx.booking_id,
            customer_name=booking.customer_name if booking else None,
            course_name=booking.course.name if booking and booking.course else None,
            process_name=process.name if process else None,
            material_name=material.name if material else "",
            material_code=material.code if material else "",
            unit=material.unit if material else "",
            quantity=tx.quantity,
            transaction_type=tx.transaction_type,
            created_at=tx.created_at
        ))
    
    return result


def get_stock_transactions(
    db: Session,
    booking_id: Optional[int] = None,
    material_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[StockTransaction], int]:
    query = db.query(StockTransaction)
    if booking_id:
        query = query.filter(StockTransaction.booking_id == booking_id)
    if material_id:
        query = query.filter(StockTransaction.material_id == material_id)
    total = query.count()
    items = query.order_by(StockTransaction.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_process_statistics(db: Session):
    results = db.query(
        Process.id,
        Process.name,
        func.count(Booking.id).label('booking_count'),
        func.sum(Booking.participant_count).label('participant_count')
    ).join(
        course_process_association,
        course_process_association.c.process_id == Process.id
    ).join(
        Course,
        Course.id == course_process_association.c.course_id
    ).join(
        Booking,
        Booking.course_id == Course.id
    ).group_by(Process.id, Process.name).all()
    
    return [
        {
            "process_id": r.id,
            "process_name": r.name,
            "booking_count": r.booking_count or 0,
            "participant_count": r.participant_count or 0
        }
        for r in results
    ]


def get_master_statistics(db: Session):
    results = db.query(
        Master.id.label('master_id'),
        User.full_name.label('master_name'),
        Master.rating,
        Master.total_reviews,
        func.count(Course.id).label('course_count')
    ).join(
        User, User.id == Master.user_id
    ).outerjoin(
        Course, Course.master_id == Master.id
    ).group_by(
        Master.id, User.full_name, Master.rating, Master.total_reviews
    ).all()
    
    return [
        {
            "master_id": r.master_id,
            "master_name": r.master_name,
            "rating": r.rating,
            "total_reviews": r.total_reviews,
            "course_count": r.course_count
        }
        for r in results
    ]


def get_monthly_revenue(db: Session, months: int = 12):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    
    results = db.query(
        func.strftime('%Y', Booking.created_at).label('year'),
        func.strftime('%m', Booking.created_at).label('month'),
        func.sum(Booking.total_price).label('total_revenue'),
        func.count(Booking.id).label('booking_count')
    ).filter(
        Booking.created_at >= start_date
    ).group_by(
        func.strftime('%Y', Booking.created_at),
        func.strftime('%m', Booking.created_at)
    ).order_by(
        'year', 'month'
    ).all()
    
    return [
        {
            "year": int(r.year),
            "month": int(r.month),
            "total_revenue": r.total_revenue or 0.0,
            "booking_count": r.booking_count
        }
        for r in results
    ]


LEVEL_THRESHOLDS = {
    MemberLevel.APPRENTICE: 0,
    MemberLevel.CRAFTSMAN: 1000,
    MemberLevel.MASTER_BREWER: 5000
}


def calculate_level(points: int) -> MemberLevel:
    if points >= LEVEL_THRESHOLDS[MemberLevel.MASTER_BREWER]:
        return MemberLevel.MASTER_BREWER
    elif points >= LEVEL_THRESHOLDS[MemberLevel.CRAFTSMAN]:
        return MemberLevel.CRAFTSMAN
    else:
        return MemberLevel.APPRENTICE


def get_next_level_points(current_level: MemberLevel, current_points: int) -> int:
    if current_level == MemberLevel.MASTER_BREWER:
        return 0
    elif current_level == MemberLevel.CRAFTSMAN:
        return LEVEL_THRESHOLDS[MemberLevel.MASTER_BREWER] - current_points
    else:
        return LEVEL_THRESHOLDS[MemberLevel.CRAFTSMAN] - current_points


def calculate_experience_points(course: Course, participant_count: int = 1) -> int:
    base_points_per_hour = 10
    duration_hours = course.duration_minutes / 60
    
    difficulty_multiplier = {
        CourseDifficulty.BEGINNER: 1,
        CourseDifficulty.INTERMEDIATE: 1.5,
        CourseDifficulty.ADVANCED: 2
    }
    
    type_multiplier = {
        CourseType.OBSERVATION: 1,
        CourseType.HANDS_ON: 2
    }
    
    points = int(base_points_per_hour * duration_hours * 
                 difficulty_multiplier[course.difficulty] * 
                 type_multiplier[course.course_type])
    
    return points


def add_experience_for_booking(db: Session, booking_id: int) -> Optional[ExperienceRecord]:
    booking = get_booking(db, booking_id)
    if not booking:
        return None
    
    if not booking.user_id:
        return None
    
    user = get_user(db, booking.user_id)
    if not user:
        return None
    
    course = booking.course
    points = calculate_experience_points(course, booking.participant_count)
    
    existing_record = db.query(ExperienceRecord).filter(
        ExperienceRecord.booking_id == booking_id
    ).first()
    
    if existing_record:
        return existing_record
    
    experience_record = ExperienceRecord(
        user_id=user.id,
        course_id=course.id,
        booking_id=booking.id,
        points_earned=points,
        course_name=course.name,
        course_type=course.course_type,
        duration_minutes=course.duration_minutes,
        difficulty=course.difficulty
    )
    
    db.add(experience_record)
    
    user.experience_points += points
    user.member_level = calculate_level(user.experience_points)
    
    db.commit()
    db.refresh(experience_record)
    db.refresh(user)
    
    return experience_record


def get_member_experience_records(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[ExperienceRecord], int]:
    query = db.query(ExperienceRecord).filter(
        ExperienceRecord.user_id == user_id
    ).order_by(
        ExperienceRecord.created_at.desc()
    )
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def get_member_certificates(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[Certificate], int]:
    query = db.query(Certificate).join(
        Booking, Certificate.booking_id == Booking.id
    ).filter(
        Booking.user_id == user_id
    ).order_by(
        Certificate.issue_date.desc()
    )
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def get_leaderboard(db: Session, limit: int = 20) -> List[tuple]:
    results = db.query(
        User.id,
        User.username,
        User.full_name,
        User.experience_points,
        User.member_level
    ).filter(
        User.role == UserRole.MEMBER,
        User.is_active == True
    ).order_by(
        User.experience_points.desc()
    ).limit(limit).all()
    
    return results


def check_booking_permission(db: Session, user_id: int, course_id: int) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    
    course = get_course(db, course_id)
    if not course:
        return True
    
    user_level_value = list(LEVEL_THRESHOLDS.keys()).index(user.member_level)
    required_level_value = list(LEVEL_THRESHOLDS.keys()).index(course.required_level)
    
    return user_level_value >= required_level_value
