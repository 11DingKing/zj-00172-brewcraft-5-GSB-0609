from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from app.models.models import User, Process, Master, Course, Schedule, Booking, Certificate, course_process_association, CourseType, ScheduleType, UserRole, MemberLevel, CourseDifficulty, ExperienceRecord
from app.schemas.schemas import UserCreate, ProcessCreate, MasterCreate, CourseCreate, ScheduleCreate, BookingCreate, CertificateCreate, BookingReview
from app.core.security import get_password_hash, verify_password


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


def create_booking(db: Session, booking: BookingCreate):
    course = get_course(db, booking.course_id)
    if not course:
        raise ValueError("Course not found")
    
    if booking.user_id:
        if not check_booking_permission(db, booking.user_id, booking.course_id):
            raise ValueError(f"Insufficient member level. Required: {course.required_level}")
    
    if course.course_type == CourseType.HANDS_ON:
        if course.max_participants and booking.participant_count > course.max_participants:
            raise ValueError(f"Maximum {course.max_participants} participants allowed")
    
    end_time = booking.start_time + timedelta(minutes=course.duration_minutes)
    
    if check_schedule_conflict(db, booking.workshop_code, booking.start_time, end_time):
        raise ValueError("Schedule conflict: workshop is occupied")
    
    total_price = course.price * booking.participant_count
    
    booking_data = booking.dict(exclude={"workshop_code", "start_time"})
    booking_data["total_price"] = total_price
    db_booking = Booking(**booking_data)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    db_schedule = Schedule(
        workshop_code=booking.workshop_code,
        schedule_type=ScheduleType.EXPERIENCE,
        start_time=booking.start_time,
        end_time=end_time,
        description=f"Experience: {course.name}",
        booking_id=db_booking.id
    )
    db.add(db_schedule)
    db.commit()
    
    if booking.user_id:
        add_experience_for_booking(db, db_booking.id)
    
    return db_booking


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
