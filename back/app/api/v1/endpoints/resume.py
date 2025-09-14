# -*- coding:utf-8 -*-
# -*- coding=utf-8 -*-
# coding:gbk
'''
project_name : Report
file name : resume
Author : Administrator
date : 2025/09/11  17:19
'''
import io
import json
import os
import uuid
from datetime import datetime, timedelta

import pdfplumber
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from openai import AsyncOpenAI
from passlib.context import CryptContext

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.prompt.attr_extract import resume
from app.services.resume_analyzer import ResumeAnalyzer

router = APIRouter()


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
    JobMatch, JobMatch_Pydantic, JobMatchIn_Pydantic,
    Education,Education_Pydantic,EducationIn_Pydantic
)

# ========================================
# 认证和授权配置
# ========================================

SECRET_KEY = "your-secret-key-here"  # 生产环境中应从环境变量获取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
client = AsyncOpenAI(
    base_url="https://api.deepseek.com",
    api_key="sk-f8feaed213c942388b68be7e034ad0f9"
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ========================================
# 工具函数
# ========================================

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


def calculate_match_score(job_skills: List[str], resume_skills: List[Dict]) -> float:
    """计算岗位技能和简历技能的匹配度"""
    if not job_skills:
        return 0

    # 获取简历中的所有技能项
    resume_skill_items = []
    for skill_category in resume_skills:
        resume_skill_items.extend(skill_category.get("items", []))

    # 计算匹配的技能数量
    matched_count = sum(1 for skill in job_skills if skill in resume_skill_items)

    # 计算匹配分数 (匹配的技能数 / 岗位要求的技能总数)
    match_score = (matched_count / len(job_skills)) * 100

    return round(match_score, 2)
# ========================================
# 简历库管理
# ========================================

# 确保上传目录存在
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/analyze-resume/",response_model=Resume_Pydantic,
             summary="上传和分析简历",
             description="上传和分析简历",
             responses={200: {"msg": "上传和分析简历"}, }
             )
async def analyze_resume(file: UploadFile = File(...)):
    """分析上传的简历文件"""
    if file.content_type not in ["text/plain", "application/pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件格式，请上传文本文件或PDF文件"
        )

    try:
        # 读取文件内容
        content = await file.read()
        # text = content.decode("utf-8")
        text=""
        if file.filename.lower().endswith('.pdf'):
            try:
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"

            except Exception as e:
                print(f"PDF读取错误: {e}")
                text = f"PDF解析错误: {str(e)}"
        else:
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")
        # 保存文件到本地
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "txt"
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(content)

        # 创建简历记录
        resume = await Resume.create(
            original_filename=file.filename,
            file_path=file_path,
            file_type=file_extension,
            raw_text=text,
            analysis_status="processing",
            user_id= 1
        )

        # 分析简历内容
        analyzer = ResumeAnalyzer()

        # 提取联系信息
        contact_info_data = analyzer.extract_contact_info(text)
        contact_info = await ContactInfo.create(
            resume=resume,
            **contact_info_data
        )

        # 提取工作经历
        work_experiences_data = analyzer.extract_work_experiences(text)
        for exp_data in work_experiences_data:
            await WorkExperience.create(resume=resume, **exp_data)

        # 提取项目经历
        project_experiences_data = analyzer.extract_project_experiences(text)
        for project_data in project_experiences_data:
            await ProjectExperience.create(resume=resume, **project_data)

        # 提取技能
        skills_data = analyzer.extract_skills(text)
        for skill_data in skills_data:
            await Skill.create(resume=resume, **skill_data)

        # 生成分析结果
        career_timeline = analyzer.generate_career_timeline(work_experiences_data)
        project_summary = analyzer.generate_project_summary(project_experiences_data)
        core_skills = analyzer.extract_core_skills(skills_data)

        # 保存分析结果
        analysis_result = await AnalysisResult.create(
            resume=resume,
            career_timeline=career_timeline,
            project_summary=project_summary,
            core_skills=core_skills
        )

        # 更新简历状态
        resume.analysis_status = "completed"
        await resume.save()

        return await Resume_Pydantic.from_tortoise_orm(resume)

    except Exception as e:
        # 如果发生错误，更新简历状态
        if 'resume' in locals():
            resume.analysis_status = "failed"
            await resume.save()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析简历时出错: {str(e)}"
        )


@router.post("/resume/{resume_id}",response_model=Resume_Pydantic,
             summary="获取简历信息",
             description="获取简历信息",
             responses={200: {"msg": "获取简历信息"}, }
             )
async def get_resume(resume_id: int):
    """获取简历信息"""
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在"
        )

    return await Resume_Pydantic.from_tortoise_orm(resume)


@router.get("/resume/{resume_id}/contact", response_model=ContactInfo_Pydantic,summary="获取联系信息",
             description="获取联系信息",)
async def get_contact_info(resume_id: int):
    """获取联系信息"""
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在"
        )

    contact_info = await ContactInfo.get_or_none(resume=resume)
    if not contact_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="联系信息不存在"
        )

    return await ContactInfo_Pydantic.from_tortoise_orm(contact_info)


@router.get("/resume/{resume_id}/work-experiences", response_model=List[WorkExperience_Pydantic],summary="获取工作经历",
             description="获取工作经历",)
async def get_work_experiences(resume_id: int):
    """获取工作经历"""
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在"
        )

    work_experiences = await WorkExperience.filter(resume=resume)
    return [await WorkExperience_Pydantic.from_tortoise_orm(exp) for exp in work_experiences]


@router.get("/resume/{resume_id}/project-experiences", response_model=List[ProjectExperience_Pydantic],summary="获取项目经历",
             description="获取项目经历",)
async def get_project_experiences(resume_id: int):
    """获取项目经历"""
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在"
        )

    project_experiences = await ProjectExperience.filter(resume=resume)
    return [await ProjectExperience_Pydantic.from_tortoise_orm(exp) for exp in project_experiences]


@router.get("/resume/{resume_id}/skills", response_model=List[Skill_Pydantic],summary="获取技能信息",
             description="获取技能信息",)
async def get_skills(resume_id: int):
    """获取技能信息"""
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在"
        )

    skills = await Skill.filter(resume=resume)
    return [await Skill_Pydantic.from_tortoise_orm(skill) for skill in skills]


@router.get("/resume/{resume_id}/analysis", response_model=AnalysisResult_Pydantic,summary="获取分析结果",
             description="获取分析结果",)
async def get_analysis_result(resume_id: int):
    """获取分析结果"""
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在"
        )

    analysis_result = await AnalysisResult.get_or_none(resume=resume)
    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在"
        )

    return await AnalysisResult_Pydantic.from_tortoise_orm(analysis_result)


@router.get("/resume/{resume_id}/full",summary="获取完整的简历信息",
             description="获取完整的简历信息",)
async def get_full_resume_info(resume_id: int):
    """获取完整的简历信息"""
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在"
        )

    contact_info = await ContactInfo.get_or_none(resume=resume)
    work_experiences = await WorkExperience.filter(resume=resume)
    project_experiences = await ProjectExperience.filter(resume=resume)
    skills = await Skill.filter(resume=resume)
    analysis_result = await AnalysisResult.get_or_none(resume=resume)

    return {
        "resume": await Resume_Pydantic.from_tortoise_orm(resume),
        "contact_info": await ContactInfo_Pydantic.from_tortoise_orm(contact_info) if contact_info else None,
        "work_experiences": [await WorkExperience_Pydantic.from_tortoise_orm(exp) for exp in work_experiences],
        "project_experiences": [await ProjectExperience_Pydantic.from_tortoise_orm(exp) for exp in project_experiences],
        "skills": [await Skill_Pydantic.from_tortoise_orm(skill) for skill in skills],
        "analysis_result": await AnalysisResult_Pydantic.from_tortoise_orm(analysis_result) if analysis_result else None
    }
class ReportData(BaseModel):
    userId: str
    data:dict

@router.post("/user_resume",summary="获取完整的简历信息",
             description="获取完整的简历信息",)
async def post_user_resume_info(request:ReportData):
    """获取完整的简历信息"""
    try:
        data=json.loads(request.json())
        resume = await Resume.create(
            original_filename="json",
            file_path="json",
            file_type="json",
            raw_text=data["data"],
            analysis_status="processing",
            user_id=int(data["userId"])
        )
        # 保存联系信息
        contact_info_data={"items":data["data"].get("Information",{})}
        await ContactInfo.create(resume=resume, **contact_info_data)

        work_experiences_data={"items":data["data"].get("workData",[])}
        await WorkExperience.create(resume=resume, **work_experiences_data)
        # 保存项目经历
        project_experiences_data={"items":data["data"].get("projectData",[])}
        await ProjectExperience.create(resume=resume, **project_experiences_data)
        # 保存教育
        edu_experiences_data={"items":data["data"].get("educationData",[])}
        await Education.create(resume=resume, **edu_experiences_data)
        # 保存技能
        skills_data ={"items":data["data"].get("certificate",[])}
        await Skill.create(resume=resume, **skills_data)
        return {
            "code":200,
            "msg":"保存成功",
            "data":{"resumeId":resume.id}
        }
    except Exception as e:
        return {
            "code": 404,
            "msg": e
        }

# AI评估相关接口
@router.post("/ai-evaluations")
async def post_ai_evaluations(request:ReportData):
    data = json.loads(request.json())
    completion = await client.chat.completions.create(
        model="deepseek-chat",  # deepseek-chat \deepseek-reasoner
        messages=[
            {
                "role": "system",
                "content": resume.replace("{}",str(data["data"]))
            },
            {
                "role": "user",
                "content": "返回json"
            }
        ]
    )
    text = completion.choices[0].message.content.replace("```", "").replace("json", "")
    print(text)
    text = json.loads(text, strict=False)
    return {"code":200,"data":text}

@router.get("/")
async def root():
    """根端点"""
    return {"message": "欢迎使用简历分析系统"}

