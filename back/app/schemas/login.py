# -*- coding:utf-8 -*-
# -*- coding=utf-8 -*-
# coding:gbk
'''
project_name : back
file name : login
Author : Administrator
date : 2025/08/19  20:11
'''
# 数据模型
from typing import Optional

from openai import BaseModel


class User(BaseModel):
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None