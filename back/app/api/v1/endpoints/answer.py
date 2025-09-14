# -*- coding:utf-8 -*-
# -*- coding=utf-8 -*-
# coding:gbk
'''
project_name : FaLvAi
file name : dialogue
Author : Administrator
date : 2025/07/07  10:45
'''
import json
import os
import smtplib
import subprocess
import uuid
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# 加载 .env 文件
from fastapi import APIRouter, status, HTTPException, Form, Request
from starlette.responses import JSONResponse

from app import settings
from app.prompt.attr_extract import sys_title_info, sys_content,sys_template_
from app.schemas.answer import AgentModel, ReportData
from app.services.DocumentLoad import DocumentLoad

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
SMTP_SERVER = settings.SMTP_SERVER
SMTP_PORT = settings.SMTP_PORT
EMAIL_USER = settings.EMAIL_USER
EMAIL_PASSWORD = settings.EMAIL_PASSWORD
API_URL = settings.API_URL
API_KEY = settings.API_KEY
pandoc_path = settings.pandoc_path
from openai import OpenAI,AsyncOpenAI

client = AsyncOpenAI(
    base_url=API_URL,
    api_key=API_KEY
)


@router.post("/generate-report",
             summary="招聘报告生成",
             description="招聘报告生成",
             status_code=status.HTTP_200_OK,
             responses={404: {"描述": "对话接口请求异常"}}
             )
async def generate_report(request: ReportData):
    # 获取JSON数据
    data = json.loads(request.json())
    try:
        # 简历
        recruitment = data["recruitment"]
        recruitment_file = os.path.join(UPLOAD_DIR, "recruitment", recruitment)
        report_path = os.path.join(UPLOAD_DIR, "report")
        sys_template = os.path.join(UPLOAD_DIR, "sys_template")
        if not os.path.exists(report_path):
            os.makedirs(report_path)
        # 岗位职责
        jd = data["jd"]
        jd_file = os.path.join(UPLOAD_DIR, "jd", jd)

        # 模板文件
        template = data["template"] if data["template"] else "template.docx"
        template_file = os.path.join(UPLOAD_DIR, "template", template)
        file_text = ""
        # 读取简历文件
        if recruitment.endswith("pdf"):
            file_text = DocumentLoad().pdf_loads(recruitment_file)
        elif recruitment.endswith("docx"):
            file_text = DocumentLoad().docx_loads(recruitment_file)
        jd_text=""
        # 读取jd文件
        if jd.endswith("pdf"):
            jd_text = DocumentLoad().pdf_loads(jd_file)
        elif jd.endswith("docx"):
            jd_text = DocumentLoad().docx_loads(jd_file)
        elif jd.endswith("txt"):
            jd_text = DocumentLoad().txt_load(jd_file)
        template_text = ""
        # 读取模板文件
        if template.endswith("pdf"):
            template_text = DocumentLoad().pdf_loads(template_file)
        elif template.endswith("docx"):
            template_text = subprocess.run(
                [pandoc_path, template_file, "-t", "markdown"],
                capture_output=True,
                text=True,
                encoding="utf-8"
            ).stdout
        # # 上传文件（支持 PDF、TXT、DOCX 等）
        completion = await  client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {
                    "role": "system",
                    "content": sys_template_.format(jd_text,template_text)
                },
                {
                    "role": "user",
                    "content": file_text
                }
            ]
        )
        file_md = uuid.uuid4().hex
        text = completion.choices[0].message.content.replace("```", "").replace("markdown", "")
        with open(os.path.join(report_path,f"{file_md}.md"), "w", encoding="utf-8")as p:
            p.write(text)

        subprocess.run(
            [pandoc_path, os.path.join(report_path, file_md + ".md"), "-o",
             os.path.join(report_path, file_md + ".docx"),
             f"--reference-doc={os.path.join(sys_template, 'custom-template.docx')}"])

        completion = await  client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": sys_title_info
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )
        title_file = completion.choices[0].message.content + "-" + datetime.now().strftime("%Y-%m-%d") + ".docx"

        completion_1 = await  client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": sys_content
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        return {
            "status": "success",
            "message": "招聘报告生成成功",
            "report_url": f"/api/v1/files/download/{file_md}.docx",  # 实际项目中返回生成的报告URL
            "file_uid": file_md + ".docx",
            "filename": title_file.replace("/", "、"),
            "editor_content": completion_1.choices[0].message.content
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"报告生成失败: {str(e)}"
        }


@router.post("/send-email",
             summary="邮件发送",
             description="邮件发送",
             status_code=status.HTTP_200_OK,
             responses={404: {"描述": "邮件发送异常"}, }
             )
async def send_email(
        request: Request,
        recipient: str = Form(...),
        subject: str = Form(...),
        content: str = Form(...),
        attachment: str = Form(...),
        file_name: str = Form(...)
):
    try:
        # 验证必填字段
        if not all([recipient, subject, content]):
            raise HTTPException(status_code=400, detail="缺少必填字段")

        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = recipient
        msg['Subject'] = subject

        # 添加HTML内容
        msg.attach(MIMEText(content, 'html'))

        # 处理附件
        # 添加附件
        if attachment:
            attachment_path = os.path.join(UPLOAD_DIR, "report", attachment)

            # Verify attachment exists
            if not os.path.exists(attachment_path):
                raise HTTPException(
                    status_code=400,
                    detail=f"Attachment file not found: {attachment}"
                )

            with open(attachment_path, 'rb') as f:
                part = MIMEApplication(
                    f.read(),
                    Name=os.path.basename(file_name)
                )
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_name)}"'
                msg.attach(part)

        # 发送邮件
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, recipient, msg.as_string())

        return JSONResponse(content={'success': True})

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=401, detail="SMTP认证失败，请检查邮箱和密码")
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"SMTP错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# docker run -d \
#   --name report_as \
#   -p 8101:8101 \
#   -v /root/Report:/app \
#   python:3.10 \
#   tail -f /dev/null