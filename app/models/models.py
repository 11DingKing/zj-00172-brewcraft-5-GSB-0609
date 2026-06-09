from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MASTER = "master"
    MEMBER = "member"


class MemberLevel(str, enum.Enum):
    APPRENTICE = "apprentice"
    CRAFTSMAN = "craftsman"
    MASTER_BREWER = "master_brewer"


class CourseType(str, enum.Enum):
    OBSERVATION = "observation"
    HANDS_ON = "hands_on"


class CourseDifficulty(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ScheduleType(str, enum.Enum):
    PRODUCTION = "production"
    EXPERIENCE = "experience"


course_process_association = Table(
    'course_process_association',
    Base.metadata,
    Column('course_id', ForeignKey('courses.id'), primary_key=True),
    Column('process_id', ForeignKey('processes.id'), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    experience_points = Column(Integer, default=0)
    member_level = Column(Enum(MemberLevel), default=MemberLevel.APPRENTICE)

    master = relationship("Master", back_populates="user", uselist=False)
    experience_records = relationship("ExperienceRecord", back_populates="user")


class Process(Base):
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    description = Column(Text)
    min_temperature = Column(Float, nullable=False)
    max_temperature = Column(Float, nullable=False)
    min_humidity = Column(Float, nullable=False)
    max_humidity = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    operation_points = Column(Text)
    safety_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    courses = relationship("Course", secondary=course_process_association, back_populates="processes")


class Master(Base):
    __tablename__ = "masters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    skill_tags = Column(String)
    max_daily_tours = Column(Integer, nullable=False, default=2)
    rating = Column(Float, default=5.0)
    total_reviews = Column(Integer, default=0)
    bio = Column(Text)

    user = relationship("User", back_populates="master")
    courses = relationship("Course", back_populates="master")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    description = Column(Text)
    course_type = Column(Enum(CourseType), nullable=False)
    difficulty = Column(Enum(CourseDifficulty), default=CourseDifficulty.BEGINNER)
    required_level = Column(Enum(MemberLevel), default=MemberLevel.APPRENTICE)
    max_participants = Column(Integer)
    min_age = Column(Integer)
    price = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    master_id = Column(Integer, ForeignKey("masters.id"))

    master = relationship("Master", back_populates="courses")
    processes = relationship("Process", secondary=course_process_association, back_populates="courses")
    bookings = relationship("Booking", back_populates="course")
    experience_records = relationship("ExperienceRecord", back_populates="course")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    workshop_code = Column(String, nullable=False)
    schedule_type = Column(Enum(ScheduleType), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    description = Column(String)
    booking_id = Column(Integer, ForeignKey("bookings.id"))

    booking = relationship("Booking", back_populates="schedule")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    participant_count = Column(Integer, nullable=False)
    participant_names = Column(Text)
    status = Column(String, default="confirmed")
    total_price = Column(Float, nullable=False)
    rating = Column(Integer)
    review = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course", back_populates="bookings")
    user = relationship("User")
    schedule = relationship("Schedule", back_populates="booking", uselist=False)
    certificate = relationship("Certificate", back_populates="booking", uselist=False)
    experience_records = relationship("ExperienceRecord", back_populates="booking")


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    certificate_number = Column(String, unique=True, nullable=False)
    issue_date = Column(DateTime, nullable=False)
    participant_names = Column(Text, nullable=False)
    experience_content = Column(Text, nullable=False)
    tasting_notes = Column(Text)
    master_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    booking = relationship("Booking", back_populates="certificate")


class ExperienceRecord(Base):
    __tablename__ = "experience_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    points_earned = Column(Integer, nullable=False)
    course_name = Column(String, nullable=False)
    course_type = Column(Enum(CourseType), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    difficulty = Column(Enum(CourseDifficulty), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="experience_records")
    course = relationship("Course")
    booking = relationship("Booking")


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    unit = Column(String, nullable=False)
    stock_quantity = Column(Float, nullable=False, default=0.0)
    safety_threshold = Column(Float, nullable=False, default=0.0)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bom_items = relationship("ProcessBOM", back_populates="material")
    stock_transactions = relationship("StockTransaction", back_populates="material")


class ProcessBOM(Base):
    __tablename__ = "process_boms"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity_per_batch = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    process = relationship("Process")
    material = relationship("Material", back_populates="bom_items")


class StockTransactionType(str, enum.Enum):
    DEDUCT = "deduct"
    ROLLBACK = "rollback"
    RESTOCK = "restock"


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True)
    batch_number = Column(String, index=True, nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    process_id = Column(Integer, ForeignKey("processes.id"))
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    transaction_type = Column(Enum(StockTransactionType), nullable=False)
    related_transaction_id = Column(Integer, ForeignKey("stock_transactions.id"))
    remark = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    booking = relationship("Booking")
    process = relationship("Process")
    material = relationship("Material", back_populates="stock_transactions")
    related_transaction = relationship("StockTransaction", remote_side=[id])
