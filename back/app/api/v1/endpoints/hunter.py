# -*- coding:utf-8 -*-
# -*- coding=utf-8 -*-
# coding:gbk
'''
project_name : back
file name : hunter
Author : Administrator
date : 2025/09/12  14:06
'''


from datetime import datetime, timedelta

from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# 导入模型和工具函数
from app.models import (
    User, User_Pydantic, UserIn_Pydantic,
    HunterProfile, HunterProfile_Pydantic, HunterProfileIn_Pydantic,
    JobPosting, JobPosting_Pydantic, JobPostingIn_Pydantic,
    Resume, Resume_Pydantic,
    ContactInfo, ContactInfo_Pydantic,
    WorkExperience, WorkExperience_Pydantic,
    ProjectExperience, ProjectExperience_Pydantic,
    Skill, Skill_Pydantic,
    AnalysisResult, AnalysisResult_Pydantic,
    ResumeAccess, ResumeAccess_Pydantic, ResumeAccessIn_Pydantic,
    JobMatch, JobMatch_Pydantic, JobMatchIn_Pydantic
)
SECRET_KEY = "your-secret-key-here"  # 生产环境中应从环境变量获取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter()
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def authenticate_user(username: str, password: str):
    user = await User.get_or_none(username=username)
    if not user or not verify_password(password, user.password_hash):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await User.get_or_none(username=username)
    if user is None:
        raise credentials_exception
    return user
async def get_current_hunter(user: User = Depends(get_current_user)):
    if user.role != "hunter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )
    return user

@router.get("/hunter/profile", response_model=HunterProfile_Pydantic)
async def get_hunter_profile(hunter: User = Depends(get_current_hunter)):
    profile = await HunterProfile.get_or_none(user=hunter)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hunter profile not found"
        )
    return await HunterProfile_Pydantic.from_tortoise_orm(profile)


@router.post("/hunter/profile", response_model=HunterProfile_Pydantic)
async def create_or_update_hunter_profile(
        profile_in: HunterProfileIn_Pydantic,
        hunter: User = Depends(get_current_hunter)
):
    profile = await HunterProfile.get_or_none(user=hunter)

    if profile:
        # 更新现有资料
        await profile.update_from_dict(profile_in.dict(exclude_unset=True))
        await profile.save()
    else:
        # 创建新资料
        profile_data = profile_in.dict()
        profile_data["user_id"] = hunter.id
        profile = await HunterProfile.create(**profile_data)

    return await HunterProfile_Pydantic.from_tortoise_orm(profile)


# ========================================
# 岗位管理
# ========================================

@router.get("/hunter/jobs", response_model=List[JobPosting_Pydantic])
async def get_job_postings(
        hunter: User = Depends(get_current_hunter),
        skip: int = 0,
        limit: int = 10,
        active_only: bool = True
):
    query = JobPosting.filter(hunter=hunter)
    if active_only:
        query = query.filter(is_active=True)

    jobs = await query.offset(skip).limit(limit)
    return [await JobPosting_Pydantic.from_tortoise_orm(job) for job in jobs]


@router.post("/hunter/jobs", response_model=JobPosting_Pydantic)
async def create_job_posting(
        job_in: JobPostingIn_Pydantic,
        hunter: User = Depends(get_current_hunter)
):
    job_data = job_in.dict()
    job_data["hunter_id"] = hunter.id
    job = await JobPosting.create(**job_data)
    return await JobPosting_Pydantic.from_tortoise_orm(job)


@router.get("/hunter/jobs/{job_id}", response_model=JobPosting_Pydantic)
async def get_job_posting(
        job_id: int,
        hunter: User = Depends(get_current_hunter)
):
    job = await JobPosting.get_or_none(id=job_id, hunter=hunter)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found"
        )
    return await JobPosting_Pydantic.from_tortoise_orm(job)


@router.put("/hunter/jobs/{job_id}", response_model=JobPosting_Pydantic)
async def update_job_posting(
        job_id: int,
        job_in: JobPostingIn_Pydantic,
        hunter: User = Depends(get_current_hunter)
):
    job = await JobPosting.get_or_none(id=job_id, hunter=hunter)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found"
        )

    await job.update_from_dict(job_in.dict(exclude_unset=True))
    await job.save()
    return await JobPosting_Pydantic.from_tortoise_orm(job)


@router.delete("/hunter/jobs/{job_id}")
async def delete_job_posting(
        job_id: int,
        hunter: User = Depends(get_current_hunter)
):
    job = await JobPosting.get_or_none(id=job_id, hunter=hunter)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found"
        )

    await job.delete()
    return {"message": "Job posting deleted successfully"}