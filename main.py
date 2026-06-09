from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.database import get_db, migrate_database
from app.core.seed_data import seed_database
from app.core.exceptions import (
    BusinessException,
    business_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.api import auth, processes, masters, courses, schedules, bookings, certificates, statistics, members, materials

migrate_database()

db = next(get_db())
seed_database(db)
db.close()

app = FastAPI(
    title="酿造工艺体验管理 API",
    description="醋文化博物馆酿造车间体验管理系统",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(auth.router)
app.include_router(processes.router)
app.include_router(masters.router)
app.include_router(courses.router)
app.include_router(schedules.router)
app.include_router(bookings.router)
app.include_router(certificates.router)
app.include_router(statistics.router)
app.include_router(members.router)
app.include_router(materials.router)


@app.get("/")
def read_root():
    return {"code": 200, "message": "Success", "data": {"message": "欢迎使用酿造工艺体验管理系统 API", "docs": "/docs"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
