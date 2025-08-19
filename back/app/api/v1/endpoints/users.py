from fastapi import APIRouter, status, HTTPException

from app.models.users import User
from app.schemas.users import UserUpdate, UserOut, UserIn
from app.services.users import UserService

# ========================================
# 说明: 定义项目HTTP请求相关的路由；
# ========================================

router = APIRouter()


# TODO：================= 用户 API 接口 =======================#
@router.post("/", response_model=UserOut,
             summary="User创建用户",
             description="User创建用户 API 接口",
             responses={200: {"描述": "用户注册成功"}, }
             )
async def create_user(user: UserIn):
    # TODO User创建用户，Service 层，封装复杂业务逻辑
    exam_user_obj = await UserService.create_user(user)
    return exam_user_obj


@router.get("/", response_model=list[UserOut],
            summary="User获取用户列表",
            description="User获取用户列表",
            status_code=status.HTTP_200_OK)
async def get_users():
    # TODO User获取用户列表
    # 其他方式：return await Users_Pydantic.from_queryset(User.all())
    return [UserOut.from_orm(user) for user in await User.all()]


@router.get("/{user_id}", response_model=UserOut,
            summary="User根据用户 ID 检索用户",
            description="User根据用户 ID 检索 API 接口",
            status_code=status.HTTP_200_OK)
async def get_user(user_id: int):
    # TODO User获取用户详情
    return await UserService.get_user(user_id)


@router.put("/{user_id}",
            response_model=UserOut,
            summary="User根据用户 ID 检索用户",
            description="User根据用户 ID 检索 API 接口",
            status_code=status.HTTP_200_OK)
async def update_user(user_id: int, user_in: UserUpdate):
    # TODO User更新用户
    user = await User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在，请联系管理员！")
    user = user.update_from_dict(user_in.dict(exclude_unset=True))
    await user.save()
    return UserOut.from_orm(user)


@router.delete("/{user_id}",
               response_model=dict,
               summary="User根据 ID 删除用户",
               description="User根据 ID 删除用户",
               status_code=status.HTTP_200_OK)
async def delete_user(user_id: int):
    # TODO User删除用户
    user = await User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在，请联系管理员！")
    await user.delete()
    return {"detail": "用户删除成功"}
