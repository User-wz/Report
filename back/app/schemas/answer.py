# -*- coding:utf-8 -*-
# -*- coding=utf-8 -*-
# coding:gbk
'''
project_name : FaLvAi
file name : awser
Author : Administrator
date : 2025/07/07  10:53
'''
from typing import Union

from pydantic import BaseModel


class AgentModel(BaseModel):
    param: Union[dict, str]

class ReportData(BaseModel):
    recruitment: str
    jd: str
    template: str
    logo: str