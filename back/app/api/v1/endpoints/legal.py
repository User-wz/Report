# -*- coding:utf-8 -*-
# -*- coding=utf-8 -*-
# coding:gbk
'''
project_name : Report
file name : legal
Author : Administrator
date : 2025/07/24  16:46
'''
import json
import os
import subprocess
import uuid
from datetime import datetime
from typing import List, Optional
from app.prompt.attr_extract import legal_sys,legal_sys_title

from starlette.responses import JSONResponse, HTMLResponse, StreamingResponse, FileResponse

from fastapi import APIRouter, status, UploadFile, HTTPException, File, Form, Request, Depends

from app import settings
from app.services.DocumentLoad import DocumentLoad

router = APIRouter()
# 获取当前应用所在目录
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
legal_path = os.path.join(UPLOAD_DIR, "legal")
if not os.path.exists(legal_path):
    os.makedirs(legal_path, exist_ok=True)
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
API_URL = settings.API_URL
API_KEY = settings.API_KEY
pandoc_path = settings.pandoc_path
from openai import OpenAI,AsyncOpenAI

client = AsyncOpenAI(
    base_url=API_URL,
    api_key=API_KEY
)


def generate_unique_filename(filename: str) -> str:
    """生成唯一的文件名"""
    ext = os.path.splitext(filename)[1]
    return f"{uuid.uuid4().hex}{ext}"


@router.post("/generate-application")
async def generate_application(judgment: UploadFile = File(...),template: UploadFile = File(...)):
    try:
        sys_template = os.path.join(UPLOAD_DIR, "sys_template")
        file_type_dir = os.path.join(UPLOAD_DIR, "judgment")
        if not os.path.exists(file_type_dir):
            os.makedirs(file_type_dir, exist_ok=True)
        judgment_file=await handle_upload(judgment, "judgment" )
        judgment_path=os.path.join(UPLOAD_DIR,"judgment",judgment_file)

        file_type_dir = os.path.join(UPLOAD_DIR, "template_l")
        if not os.path.exists(file_type_dir):
            os.makedirs(file_type_dir, exist_ok=True)
        template_file=await handle_upload(template, "template_l" )
        template_path=os.path.join(UPLOAD_DIR,"template_l",template_file)

        if not template_file or not judgment_file:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "文件上传失败，",
                }
            )
        temple_text=""
        if template_file.endswith("pdf"):
            temple_text = DocumentLoad().pdf_loads(template_path)
        elif template_file.endswith("docx"):
            temple_text = DocumentLoad().docx_load(template_path)
        judgment_text=""
        if judgment_file.endswith("pdf"):
            judgment_text = DocumentLoad().pdf_loads(judgment_path)
        elif judgment_file.endswith("docx"):
            judgment_text = DocumentLoad().docx_load(judgment_path)

        # # 上传文件（支持 PDF、TXT、DOCX 等）
        completion = await  client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {
                    "role": "system",
                    "content": legal_sys.format(temple_text)
                },
                {
                    "role": "user",
                    "content": str(judgment_text)
                }
            ]
        )
        file_md = uuid.uuid4().hex
        text = completion.choices[0].message.content.replace("```", "").replace("markdown", "")
        with open(os.path.join(legal_path,f"{file_md}.md"), "w", encoding="utf-8")as p:
            p.write(text)
        subprocess.run(
            [pandoc_path, os.path.join(legal_path, file_md + ".md"), "-o",
             os.path.join(legal_path, file_md + ".docx"),
             f"--reference-doc={os.path.join(sys_template, 'custom-template.docx')}"])

        # completion = client.chat.completions.create(
        #     model="deepseek-chat",
        #     messages=[
        #         {
        #             "role": "system",
        #             "content": legal_sys_title
        #         },
        #         {
        #             "role": "user",
        #             "content": text
        #         }
        #     ]
        # )
        # title_file = completion.choices[0].message.content + "-" + datetime.now().strftime("%Y-%m-%d") + ".docx"
        return {
            "status": "success",
            "message": "申请书生成成功",
            "legal_url": f"/api/v1/files/download/{file_md}.docx?filetype=legal",  # 实际项目中返回生成的报告URL
            "file_uid": file_md + ".docx",
            # "filename": title_file.replace("/", "、")
        }
    except Exception as e:
        return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"文件处理失败，{e}"
                }
            )

async def handle_upload(file: UploadFile,filetype:str):
    try:
        # 验证文件类型
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            return None

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

        return unique_filename
    except Exception as e:
        return None
    finally:
        try:
            await file.close()
        except:
            pass
