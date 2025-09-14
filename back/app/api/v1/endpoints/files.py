# -*- coding:utf-8 -*-
# -*- coding=utf-8 -*-
# coding:gbk
'''
project_name : FaLvAi
file name : files
Author : Administrator
date : 2025/07/09  19:10
'''
import json
import os
import uuid
from typing import List, Optional

from starlette.responses import JSONResponse, HTMLResponse, StreamingResponse, FileResponse

from fastapi import APIRouter, status, UploadFile, HTTPException, File, Form, Request, Depends


router = APIRouter()
# 获取当前应用所在目录
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
# 允许的文件类型
ALLOWED_CONTENT_TYPES = {
    # 文档类型
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/plain": ".txt",

    # 图片类型
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",

    # 压缩文件
    "application/zip": ".zip",
    "application/x-rar-compressed": ".rar",
    "application/x-tar": ".tar",
    "application/gzip": ".gz"
}

# 最大文件大小 15MB
MAX_FILE_SIZE = 1024 * 1024 * 15


def generate_unique_filename(filename: str) -> str:
    """生成唯一的文件名"""
    ext = os.path.splitext(filename)[1]
    return f"{uuid.uuid4().hex}{ext}"


@router.post("/upload/recruitment")
async def upload_recruitment(file: UploadFile = File(...)):
    file_type_dir = os.path.join(UPLOAD_DIR, "recruitment")
    if not os.path.exists(file_type_dir):
        os.makedirs(file_type_dir, exist_ok=True)
    return await handle_upload(file, "recruitment")
@router.post("/upload/logo")
async def upload_recruitment(file: UploadFile = File(...)):
    file_type_dir = os.path.join(UPLOAD_DIR, "logo")
    if not os.path.exists(file_type_dir):
        os.makedirs(file_type_dir, exist_ok=True)
    return await handle_upload(file, "logo")
@router.post("/upload/jd")
async def upload_jd(file: UploadFile = File(None),company_name: str = Form(None),
    job_title: str = Form(None),
    job_responsibilities: str = Form(""),
    job_requirements: Optional[str] = Form("")):
    file_type_dir = os.path.join(UPLOAD_DIR, "jd")
    if not os.path.exists(file_type_dir):
        os.makedirs(file_type_dir, exist_ok=True)
    # 保存表单数据到文本文件
    if company_name and job_title and job_responsibilities :
        filename=f"info_{uuid.uuid4().hex}.txt"
        info_path = os.path.join(file_type_dir,filename )
        with open(info_path, "w", encoding="utf-8") as f:
            f.write(f"公司名称: {company_name}\n")
            f.write(f"岗位名称: {job_title}\n")
            f.write("\n岗位职责:\n")
            f.write(job_responsibilities.replace("\n", "\n- ") + "\n")
            f.write("\n岗位要求:\n")
            f.write(job_requirements.replace("\n", "\n- ") + "\n")
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "文件上传成功",
                "original_filename": filename,
                "saved_filename": filename,
                "content_type": "jd",
                "size": 100,
                "saved_path": f"uploads/jd/{filename}",
                "HR_type": "jd"
            }
        )
    else:
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": "内容信息填写不完整,请重新填写提交",
            }
        )

@router.post("/upload/template")
async def upload_template(file: UploadFile = File(...)):
    # 创建JD子目录
    file_type_dir = os.path.join(UPLOAD_DIR, "template")
    if not os.path.exists(file_type_dir):
        os.makedirs(file_type_dir, exist_ok=True)

    return await handle_upload(file, "template")


async def handle_upload(file: UploadFile,filetype:str):
    try:
        # 验证文件类型
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。允许的类型: {ALLOWED_CONTENT_TYPES}"
            )

        # 验证文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        await file.seek(0)  # 重置文件指针

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件太大。最大允许: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # 生成安全的唯一文件名
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(UPLOAD_DIR,filetype, unique_filename)



        # 保存文件
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        return JSONResponse(
            status_code=200,
            content={
                "status":"success",
                "message": "文件上传成功",
                "original_filename": file.filename,
                "saved_filename": unique_filename,
                "content_type": file.content_type,
                "size": file_size,
                "saved_path": f"uploads/{filetype}/{unique_filename}",
                "HR_type":filetype
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )
    finally:
        try:
            await file.close()
        except:
            pass


@router.post("/upload/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        try:
            # 验证逻辑同上
            if file.content_type not in ALLOWED_CONTENT_TYPES:
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": "不支持的文件类型"
                })
                continue

            file.file.seek(0, 2)
            file_size = file.file.tell()
            await file.seek(0)

            if file_size > MAX_FILE_SIZE:
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": "文件太大"
                })
                continue

            unique_filename = generate_unique_filename(file.filename)
            file_path = os.path.join(UPLOAD_DIR, unique_filename)

            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            results.append({
                "original_filename": file.filename,
                "saved_filename": unique_filename,
                "content_type": file.content_type,
                "size": file_size,
                "status": "success"
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })

    return {"files": results}


@router.get("/files/list")
async def list_uploaded_files():
    """列出已上传的所有文件"""
    if not os.path.exists(UPLOAD_DIR):
        return {"files": []}

    files = []
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            files.append({
                "filename": filename,
                "size": os.path.getsize(file_path),
                "path": f"uploads/{filename}"
            })

    return {"files": files}


@router.get("/download/{filename}")
async def download_file(
        filename: str,
        as_attachment: bool = True,
        download_name: Optional[str] = None,
        filetype: Optional[str] = "report",
):
    """文件下载接口

    Args:
        filename: 服务器保存的文件名
        as_attachment: 是否作为附件下载（浏览器会触发下载）
        download_name: 下载时显示的文件名（不传则使用服务器文件名）
    """
    file_path = os.path.join(UPLOAD_DIR, filetype, filename)

    # 检查文件是否存在
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=404,
            detail="文件不存在或已被删除"
        )

    # 设置下载文件名
    if download_name is None:
        download_name = filename

    # 使用FileResponse简单高效
    return FileResponse(
        path=file_path,
        filename=download_name if as_attachment else None,
        media_type="application/octet-stream"  # 通用二进制类型
    )

