from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import success, success_page
from app import crud
from app.schemas.schemas import MemberProfile, ExperienceRecordSchema, Certificate, LeaderboardEntry, ApiResponse, PageResponse
from app.crud.crud import get_next_level_points, LEVEL_THRESHOLDS


router = APIRouter(prefix="/members", tags=["members"])


@router.get("/profile/{user_id}", response_model=ApiResponse[MemberProfile])
def get_member_profile(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="会员不存在")
    
    next_level_points = get_next_level_points(user.member_level, user.experience_points)
    
    profile = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "experience_points": user.experience_points,
        "member_level": user.member_level,
        "next_level_points": next_level_points,
        "created_at": user.created_at
    }
    return success(data=profile, message="获取会员资料成功")


@router.get("/{user_id}/experience", response_model=ApiResponse[PageResponse[ExperienceRecordSchema]])
def get_member_experience(
    user_id: int,
    page: int = 1,
    pageSize: int = 100,
    db: Session = Depends(get_db)
):
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="会员不存在")
    
    skip = (page - 1) * pageSize
    items, total = crud.get_member_experience_records(db, user_id=user_id, skip=skip, limit=pageSize)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取会员经验记录成功")


@router.get("/{user_id}/certificates", response_model=ApiResponse[PageResponse[Certificate]])
def get_member_certificates(
    user_id: int,
    page: int = 1,
    pageSize: int = 100,
    db: Session = Depends(get_db)
):
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="会员不存在")
    
    skip = (page - 1) * pageSize
    items, total = crud.get_member_certificates(db, user_id=user_id, skip=skip, limit=pageSize)
    return success_page(items=items, total=total, page=page, page_size=pageSize, message="获取会员证书成功")


@router.get("/leaderboard", response_model=ApiResponse[list[LeaderboardEntry]])
def get_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    results = crud.get_leaderboard(db, limit=limit)
    
    leaderboard = []
    for rank, (user_id, username, full_name, experience_points, member_level) in enumerate(results, start=1):
        leaderboard.append({
            "rank": rank,
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "experience_points": experience_points,
            "member_level": member_level
        })
    
    return success(data=leaderboard, message="获取排行榜成功")


@router.get("/levels/thresholds", response_model=ApiResponse[dict])
def get_level_thresholds():
    thresholds = {
        level: points
        for level, points in LEVEL_THRESHOLDS.items()
    }
    return success(data=thresholds, message="获取等级阈值成功")
