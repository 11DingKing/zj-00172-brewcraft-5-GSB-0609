from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.models import User, Process, Master, Course, Schedule, Booking, Certificate, course_process_association, UserRole, CourseType, ScheduleType, MemberLevel, CourseDifficulty, Material, ProcessBOM
from app.core.security import get_password_hash


def seed_materials_and_boms(db: Session, processes: list):
    if db.query(Material).count() > 0:
        return
    
    materials = [
        Material(
            name="优质糯米",
            code="MAT001",
            unit="kg",
            stock_quantity=500.0,
            safety_threshold=100.0,
            description="精选东北圆糯米，颗粒饱满"
        ),
        Material(
            name="麸皮",
            code="MAT002",
            unit="kg",
            stock_quantity=200.0,
            safety_threshold=50.0,
            description="新鲜小麦麸皮"
        ),
        Material(
            name="大麦",
            code="MAT003",
            unit="kg",
            stock_quantity=150.0,
            safety_threshold=30.0,
            description="优质带壳大麦"
        ),
        Material(
            name="豌豆",
            code="MAT004",
            unit="kg",
            stock_quantity=100.0,
            safety_threshold=20.0,
            description="白豌豆，制曲原料"
        ),
        Material(
            name="传统醋曲",
            code="MAT005",
            unit="kg",
            stock_quantity=80.0,
            safety_threshold=20.0,
            description="自制优质醋曲，传承百年工艺"
        ),
        Material(
            name="纯净水",
            code="MAT006",
            unit="L",
            stock_quantity=1000.0,
            safety_threshold=200.0,
            description="反渗透净化水"
        ),
        Material(
            name="食用盐",
            code="MAT007",
            unit="kg",
            stock_quantity=60.0,
            safety_threshold=15.0,
            description="精制食用盐"
        ),
        Material(
            name="炒米色",
            code="MAT008",
            unit="kg",
            stock_quantity=40.0,
            safety_threshold=10.0,
            description="手工炒制焦糖色"
        )
    ]
    for mat in materials:
        db.add(mat)
    db.commit()
    
    process_map = {p.code: p for p in processes}
    material_map = {m.code: m for m in materials}
    
    boms = [
        (process_map["P001"], material_map["MAT001"], 2.0),
        (process_map["P001"], material_map["MAT006"], 3.0),
        (process_map["P002"], material_map["MAT002"], 1.5),
        (process_map["P002"], material_map["MAT003"], 1.0),
        (process_map["P002"], material_map["MAT004"], 0.5),
        (process_map["P002"], material_map["MAT005"], 0.3),
        (process_map["P002"], material_map["MAT006"], 1.0),
        (process_map["P003"], material_map["MAT005"], 0.2),
        (process_map["P003"], material_map["MAT006"], 2.0),
        (process_map["P004"], material_map["MAT007"], 0.1),
        (process_map["P005"], material_map["MAT006"], 5.0),
        (process_map["P005"], material_map["MAT008"], 0.2),
        (process_map["P006"], material_map["MAT007"], 0.05),
    ]
    for process, material, qty in boms:
        db.add(ProcessBOM(process_id=process.id, material_id=material.id, quantity_per_batch=qty))
    db.commit()


def seed_database(db: Session):
    if db.query(User).count() > 0:
        if db.query(Process).count() > 0:
            processes = db.query(Process).all()
            seed_materials_and_boms(db, processes)
        return
    
    admin_user = User(
        username="admin",
        hashed_password=get_password_hash("admin123456"),
        full_name="系统管理员",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin_user)
    
    master_user1 = User(
        username="master1",
        hashed_password=get_password_hash("master123456"),
        full_name="王师傅",
        role=UserRole.MASTER,
        is_active=True
    )
    db.add(master_user1)
    
    master_user2 = User(
        username="master2",
        hashed_password=get_password_hash("master123456"),
        full_name="李师傅",
        role=UserRole.MASTER,
        is_active=True
    )
    db.add(master_user2)
    
    master_user3 = User(
        username="master3",
        hashed_password=get_password_hash("master123456"),
        full_name="张师傅",
        role=UserRole.MASTER,
        is_active=True
    )
    db.add(master_user3)
    
    master_user4 = User(
        username="master4",
        hashed_password=get_password_hash("master123456"),
        full_name="陈师傅",
        role=UserRole.MASTER,
        is_active=True
    )
    db.add(master_user4)
    
    member_user1 = User(
        username="member1",
        hashed_password=get_password_hash("member123456"),
        full_name="周会员",
        role=UserRole.MEMBER,
        is_active=True,
        experience_points=1500,
        member_level=MemberLevel.CRAFTSMAN
    )
    db.add(member_user1)
    
    member_user2 = User(
        username="member2",
        hashed_password=get_password_hash("member123456"),
        full_name="吴会员",
        role=UserRole.MEMBER,
        is_active=True,
        experience_points=6000,
        member_level=MemberLevel.MASTER_BREWER
    )
    db.add(member_user2)
    
    member_user3 = User(
        username="member3",
        hashed_password=get_password_hash("member123456"),
        full_name="郑会员",
        role=UserRole.MEMBER,
        is_active=True,
        experience_points=500,
        member_level=MemberLevel.APPRENTICE
    )
    db.add(member_user3)
    
    member_user4 = User(
        username="member4",
        hashed_password=get_password_hash("member123456"),
        full_name="王会员",
        role=UserRole.MEMBER,
        is_active=True,
        experience_points=800,
        member_level=MemberLevel.APPRENTICE
    )
    db.add(member_user4)
    
    db.commit()
    
    processes = [
        Process(
            name="蒸饭",
            code="P001",
            description="精选优质糯米，经过淘洗、浸泡后，采用传统木甑蒸煮",
            min_temperature=20.0,
            max_temperature=30.0,
            min_humidity=50.0,
            max_humidity=70.0,
            duration_minutes=120,
            operation_points="1. 淘洗至水清；2. 浸泡4-6小时；3. 木甑蒸煮至熟透",
            safety_notes="注意防止蒸汽烫伤"
        ),
        Process(
            name="制曲",
            code="P002",
            description="采用传统固态发酵工艺，制作优质醋曲",
            min_temperature=25.0,
            max_temperature=35.0,
            min_humidity=60.0,
            max_humidity=80.0,
            duration_minutes=180,
            operation_points="1. 混合麸皮、大麦、豌豆；2. 接种曲母；3. 入曲房培养",
            safety_notes="保持通风，注意曲房温度监控"
        ),
        Process(
            name="发酵",
            code="P003",
            description="将蒸熟的米饭与醋曲混合，入缸进行酒精发酵",
            min_temperature=28.0,
            max_temperature=38.0,
            min_humidity=55.0,
            max_humidity=75.0,
            duration_minutes=240,
            operation_points="1. 按比例拌曲；2. 入缸压实；3. 每日翻拌监控温度",
            safety_notes="注意酒精气体防爆"
        ),
        Process(
            name="翻醅",
            code="P004",
            description="醋酸发酵阶段的关键工序，每日翻醅控温",
            min_temperature=30.0,
            max_temperature=45.0,
            min_humidity=50.0,
            max_humidity=70.0,
            duration_minutes=150,
            operation_points="1. 每日定时翻醅；2. 监控品温；3. 调节通风量",
            safety_notes="注意高温防烫伤"
        ),
        Process(
            name="淋醋",
            code="P005",
            description="采用三套淋工艺，提取醋液精华",
            min_temperature=20.0,
            max_temperature=35.0,
            min_humidity=45.0,
            max_humidity=65.0,
            duration_minutes=180,
            operation_points="1. 头淋套二淋；2. 二淋套三淋；3. 三淋套新醅",
            safety_notes="注意防滑，小心操作"
        ),
        Process(
            name="陈酿",
            code="P006",
            description="夏伏晒，冬捞冰，自然陈酿增香",
            min_temperature=-10.0,
            max_temperature=40.0,
            min_humidity=30.0,
            max_humidity=80.0,
            duration_minutes=60,
            operation_points="1. 入坛密封；2. 定期检查；3. 陈酿至少1年",
            safety_notes="注意坛口密封，防止杂菌污染"
        )
    ]
    
    for p in processes:
        db.add(p)
    db.commit()
    
    seed_materials_and_boms(db, processes)
    
    masters = [
        Master(
            user_id=master_user1.id,
            skill_tags="蒸饭,制曲",
            max_daily_tours=2,
            rating=4.8,
            total_reviews=15,
            bio="从事酿醋工艺30余年，国家级非物质文化遗产传承人"
        ),
        Master(
            user_id=master_user2.id,
            skill_tags="发酵,翻醅",
            max_daily_tours=3,
            rating=4.9,
            total_reviews=23,
            bio="酿醋世家第四代传人，精通发酵控制技术"
        ),
        Master(
            user_id=master_user3.id,
            skill_tags="淋醋,陈酿",
            max_daily_tours=2,
            rating=4.7,
            total_reviews=18,
            bio="专注于淋醋与陈酿工艺20年，经验丰富"
        ),
        Master(
            user_id=master_user4.id,
            skill_tags="全工序",
            max_daily_tours=1,
            rating=5.0,
            total_reviews=10,
            bio="醋厂总技师，精通所有酿造工序"
        )
    ]
    
    for m in masters:
        db.add(m)
    db.commit()
    
    courses = [
        Course(
            name="醋文化观摩体验",
            code="C001",
            description="参观百年醋厂，了解传统酿醋工艺",
            course_type=CourseType.OBSERVATION,
            difficulty=CourseDifficulty.BEGINNER,
            required_level=MemberLevel.APPRENTICE,
            max_participants=20,
            price=98.0,
            duration_minutes=90,
            master_id=masters[0].id
        ),
        Course(
            name="手工酿醋动手体验",
            code="C002",
            description="亲手参与蒸饭、制曲等关键工序",
            course_type=CourseType.HANDS_ON,
            difficulty=CourseDifficulty.INTERMEDIATE,
            required_level=MemberLevel.APPRENTICE,
            max_participants=10,
            min_age=12,
            price=298.0,
            duration_minutes=240,
            master_id=masters[1].id
        ),
        Course(
            name="大师精品课程",
            code="C003",
            description="传承人亲授，完整体验六道工序",
            course_type=CourseType.HANDS_ON,
            difficulty=CourseDifficulty.ADVANCED,
            required_level=MemberLevel.CRAFTSMAN,
            max_participants=6,
            min_age=16,
            price=598.0,
            duration_minutes=360,
            master_id=masters[3].id
        )
    ]
    
    for c in courses:
        db.add(c)
    db.commit()
    
    db.execute(course_process_association.insert().values(course_id=courses[0].id, process_id=processes[0].id))
    db.execute(course_process_association.insert().values(course_id=courses[0].id, process_id=processes[2].id))
    db.execute(course_process_association.insert().values(course_id=courses[0].id, process_id=processes[5].id))
    
    db.execute(course_process_association.insert().values(course_id=courses[1].id, process_id=processes[0].id))
    db.execute(course_process_association.insert().values(course_id=courses[1].id, process_id=processes[1].id))
    db.execute(course_process_association.insert().values(course_id=courses[1].id, process_id=processes[2].id))
    
    for p in processes:
        db.execute(course_process_association.insert().values(course_id=courses[2].id, process_id=p.id))
    
    db.commit()
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for day in range(14):
        current_date = today + timedelta(days=day)
        
        production_start = current_date.replace(hour=8, minute=0)
        production_end = current_date.replace(hour=12, minute=0)
        db.add(Schedule(
            workshop_code="WS001",
            schedule_type=ScheduleType.PRODUCTION,
            start_time=production_start,
            end_time=production_end,
            description="日常生产 - 发酵车间"
        ))
        
        production_start2 = current_date.replace(hour=14, minute=0)
        production_end2 = current_date.replace(hour=18, minute=0)
        db.add(Schedule(
            workshop_code="WS001",
            schedule_type=ScheduleType.PRODUCTION,
            start_time=production_start2,
            end_time=production_end2,
            description="日常生产 - 蒸饭车间"
        ))
    
    db.commit()
    
    historical_bookings = [
        {
            "course_id": courses[0].id,
            "customer_name": "张三",
            "customer_phone": "138******01",
            "participant_count": 2,
            "participant_names": "张三、李四",
            "days_ago": 30,
            "hour": 10,
            "rating": 5,
            "review": "非常有意义的体验，学到了很多醋文化知识"
        },
        {
            "course_id": courses[1].id,
            "customer_name": "王五",
            "customer_phone": "138******02",
            "participant_count": 4,
            "participant_names": "王五一家",
            "days_ago": 20,
            "hour": 14,
            "rating": 4,
            "review": "动手体验很有趣，师傅讲解很耐心"
        },
        {
            "course_id": courses[2].id,
            "customer_name": "赵六",
            "customer_phone": "138******03",
            "participant_count": 2,
            "participant_names": "赵六、钱七",
            "days_ago": 10,
            "hour": 9,
            "rating": 5,
            "review": "大师课程名不虚传，强烈推荐！"
        },
        {
            "course_id": courses[0].id,
            "customer_name": "孙八",
            "customer_phone": "138******04",
            "participant_count": 3,
            "participant_names": "孙八全家",
            "days_ago": 5,
            "hour": 11,
            "rating": None,
            "review": None
        }
    ]
    
    for booking_data in historical_bookings:
        booking_date = today - timedelta(days=booking_data["days_ago"])
        start_time = booking_date.replace(hour=booking_data["hour"])
        course = db.query(Course).filter(Course.id == booking_data["course_id"]).first()
        end_time = start_time + timedelta(minutes=course.duration_minutes)
        
        total_price = course.price * booking_data["participant_count"]
        
        db_booking = Booking(
            course_id=booking_data["course_id"],
            customer_name=booking_data["customer_name"],
            customer_phone=booking_data["customer_phone"],
            participant_count=booking_data["participant_count"],
            participant_names=booking_data["participant_names"],
            status="completed",
            total_price=total_price,
            rating=booking_data["rating"],
            review=booking_data["review"],
            created_at=start_time
        )
        db.add(db_booking)
        db.commit()
        
        db_schedule = Schedule(
            workshop_code="WS002",
            schedule_type=ScheduleType.EXPERIENCE,
            start_time=start_time,
            end_time=end_time,
            description=f"体验课程: {course.name}",
            booking_id=db_booking.id
        )
        db.add(db_schedule)
        db.commit()
        
        if booking_data["rating"]:
            cert_number = f"CERT-{start_time.strftime('%Y%m%d%H%M%S')}-{db_booking.id}"
            experience_content = f"完成 {course.name} 体验课程，包含以下工序：" + "、".join([p.name for p in course.processes])
            
            db_certificate = Certificate(
                booking_id=db_booking.id,
                certificate_number=cert_number,
                issue_date=end_time,
                participant_names=booking_data["participant_names"],
                experience_content=experience_content,
                tasting_notes="香气浓郁，口感醇厚，回味悠长",
                master_name=course.master.user.full_name if course.master and course.master.user else None
            )
            db.add(db_certificate)
    
    db.commit()
