from pydantic import BaseModel, Field
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from app.models.models import UserRole, CourseType, ScheduleType, MemberLevel, CourseDifficulty, StockTransactionType

T = TypeVar('T')


class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    pageSize: int


class ApiResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict] = None


class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.MEMBER


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    experience_points: int
    member_level: MemberLevel

    class Config:
        from_attributes = True


class MemberProfile(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    experience_points: int
    member_level: MemberLevel
    next_level_points: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExperienceRecordSchema(BaseModel):
    id: int
    course_name: str
    course_type: CourseType
    difficulty: CourseDifficulty
    duration_minutes: int
    points_earned: int
    created_at: datetime

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    full_name: Optional[str]
    experience_points: int
    member_level: MemberLevel

    class Config:
        from_attributes = True


class ProcessBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    min_temperature: float
    max_temperature: float
    min_humidity: float
    max_humidity: float
    duration_minutes: int
    operation_points: Optional[str] = None
    safety_notes: Optional[str] = None


class ProcessCreate(ProcessBase):
    pass


class Process(ProcessBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MasterBase(BaseModel):
    skill_tags: Optional[str] = None
    max_daily_tours: int = 2
    bio: Optional[str] = None


class MasterCreate(MasterBase):
    user_id: int


class Master(MasterBase):
    id: int
    rating: float
    total_reviews: int
    user: User

    class Config:
        from_attributes = True


class MasterSimple(BaseModel):
    id: int
    skill_tags: Optional[str] = None
    rating: float
    total_reviews: int

    class Config:
        from_attributes = True


class CourseBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    course_type: CourseType
    difficulty: CourseDifficulty = CourseDifficulty.BEGINNER
    required_level: MemberLevel = MemberLevel.APPRENTICE
    max_participants: Optional[int] = None
    min_age: Optional[int] = None
    price: float
    duration_minutes: int


class CourseCreate(CourseBase):
    master_id: Optional[int] = None
    process_ids: List[int] = []


class Course(CourseBase):
    id: int
    master: Optional[MasterSimple] = None
    processes: List[Process] = []

    class Config:
        from_attributes = True


class ScheduleBase(BaseModel):
    workshop_code: str
    schedule_type: ScheduleType
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    booking_id: Optional[int] = None


class ScheduleCreate(ScheduleBase):
    pass


class Schedule(ScheduleBase):
    id: int

    class Config:
        from_attributes = True


class BookingBase(BaseModel):
    course_id: int
    user_id: Optional[int] = None
    customer_name: str
    customer_phone: str
    participant_count: int
    participant_names: Optional[str] = None


class BookingCreate(BookingBase):
    workshop_code: str
    start_time: datetime


class Booking(BookingBase):
    id: int
    status: str
    total_price: float
    rating: Optional[int] = None
    review: Optional[str] = None
    created_at: datetime
    course: Course
    user: Optional[User] = None
    schedule: Optional[Schedule] = None

    class Config:
        from_attributes = True


class BookingReview(BaseModel):
    rating: int = Field(ge=1, le=5)
    review: Optional[str] = None


class CertificateBase(BaseModel):
    booking_id: int
    tasting_notes: Optional[str] = None


class CertificateCreate(CertificateBase):
    pass


class Certificate(BaseModel):
    id: int
    certificate_number: str
    issue_date: datetime
    participant_names: str
    experience_content: str
    tasting_notes: Optional[str] = None
    master_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProcessStatistics(BaseModel):
    process_id: int
    process_name: str
    booking_count: int
    participant_count: int


class MasterStatistics(BaseModel):
    master_id: int
    master_name: str
    rating: float
    total_reviews: int
    course_count: int


class MonthlyRevenue(BaseModel):
    year: int
    month: int
    total_revenue: float
    booking_count: int


class MaterialBase(BaseModel):
    name: str
    code: str
    unit: str
    safety_threshold: float = 0.0
    description: Optional[str] = None


class MaterialCreate(MaterialBase):
    stock_quantity: float = 0.0


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    safety_threshold: Optional[float] = None
    description: Optional[str] = None
    stock_quantity: Optional[float] = None


class Material(MaterialBase):
    id: int
    stock_quantity: float
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessBOMBase(BaseModel):
    process_id: int
    material_id: int
    quantity_per_batch: float


class ProcessBOMCreate(ProcessBOMBase):
    pass


class ProcessBOM(ProcessBOMBase):
    id: int
    created_at: datetime
    material: Material

    class Config:
        from_attributes = True


class StockTransactionBase(BaseModel):
    batch_number: str
    booking_id: Optional[int] = None
    process_id: Optional[int] = None
    material_id: int
    quantity: float
    transaction_type: StockTransactionType
    remark: Optional[str] = None


class StockTransaction(StockTransactionBase):
    id: int
    created_at: datetime
    material: Material
    related_transaction_id: Optional[int] = None

    class Config:
        from_attributes = True


class StockShortageInfo(BaseModel):
    material_id: int
    material_name: str
    material_code: str
    unit: str
    current_stock: float
    safety_threshold: float
    shortage: float


class BatchDetail(BaseModel):
    batch_number: str
    booking_id: Optional[int]
    customer_name: Optional[str]
    course_name: Optional[str]
    process_name: Optional[str]
    material_name: str
    material_code: str
    unit: str
    quantity: float
    transaction_type: StockTransactionType
    created_at: datetime


class BookingCancel(BaseModel):
    reason: Optional[str] = None
