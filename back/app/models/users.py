from app.models.base import BaseDBModel
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator


# ========================================
# 说明: 数据模型
# ========================================


# TODO：================= 用户 & 用户组 =======================#

class User(BaseDBModel):
    """
    TODO 示例：用户
    """
    username = fields.CharField(max_length=20, unique=True, description="用户名")
    nickname = fields.CharField(max_length=50, null=True, description="昵称")
    email = fields.CharField(max_length=255, null=True, description="联系邮箱")
    weixin_id= fields.CharField(max_length=255, null=True, description="微信id")
    weixin_user= fields.CharField(max_length=255, null=True, description="微信用户")
    password = fields.CharField(max_length=128, description="密码")
    phone = fields.CharField(max_length=20, null=True,description="手机号")
    last_login = fields.DatetimeField(null=True, description="上次登录")
    is_active = fields.BooleanField(default=True, description="是否活跃")
    is_superuser = fields.BooleanField(default=False, description="是否管理员")
    is_confirmed = fields.BooleanField(default=False, description="是否确认")
    avatar = fields.CharField(max_length=512, null=True, description="头像")
    group = fields.ForeignKeyField('models.Org', related_name='users')

    class Meta:
        table = "users"
        table_description = "用户"


class Org(BaseDBModel):
    """
    TODO 示例：用户组
    """
    name = fields.CharField(max_length=50, unique=True)
    class Meta:
        table = "orgs"
        table_description = "用户组"


# Users_Pydantic = pydantic_model_creator(User, name="UserOutList")
