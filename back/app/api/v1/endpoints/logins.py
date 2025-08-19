# -*- coding:utf-8 -*-
# -*- coding=utf-8 -*-
# coding:gbk
'''
project_name : back
file name : logins
Author : Administrator
date : 2025/08/19  19:59
'''
from datetime import datetime, timedelta
from fastapi import  Depends, HTTPException, status, APIRouter
from fastapi.security import  OAuth2PasswordRequestForm
from redis import Redis

from app.config import settings
from app.core.redis import get_redis
# 路由处理
from app.schemas.login import Token, User
from app.services.login import authenticate_user, create_access_token, get_current_active_user, oauth2_scheme


router = APIRouter()
@router.post("/login", response_model=Token,
             summary="用户登录",
             description="用户登录API 接口，返回token",
             responses={200: {"描述": "用户登录成功"}, }
             )
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),redis: Redis = Depends(get_redis)):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    # 将token存储到Redis，设置30分钟过期
    await redis.setex(access_token, access_token_expires, user.username)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout",
             summary="用户退出登录",
             description="用户退出登录API 接口",
             responses={200: {"message": "Successfully logged out"}, }
             )
async def logout(current_user: User = Depends(get_current_active_user), token: str = Depends(oauth2_scheme),redis: Redis = Depends(get_redis)):
    # 从Redis中删除token使其失效
    await redis.delete(token)
    return {"message": "Successfully logged out"}


@router.post("/users/me",response_model=User,
             summary="用户信息认证",
             description="用户信息认证API 接口",
             responses={200: {"username": "用户名"}, }
             )
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


# 健康检查端点
@router.get("/health")
async def health_check(redis: Redis = Depends(get_redis)):
    # 异步方式ping Redis
    try:
        await redis.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"disconnected: {str(e)}"

    return {"status": "healthy", "redis": redis_status}
