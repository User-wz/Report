from fastapi import APIRouter

from app.api.v1.endpoints import users, groups, others, websockets,logins,resume,answer,files,legal,hunter

# ========================================
# 说明: 路由引入
# ========================================

api_router = APIRouter()
api_router.include_router(logins.router, prefix="/logins", tags=["Logins"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(resume.router, prefix="/resume", tags=["Resume"])
api_router.include_router(answer.router, prefix="/answer",  tags=["Answer"])
api_router.include_router(files.router, prefix="/files", tags=["Files"])
api_router.include_router(legal.router, prefix="/legal", tags=["Legal"])
api_router.include_router(hunter.router, prefix="/hunter", tags=["Hunter"])
api_router.include_router(groups.router, prefix="/groups", tags=["Groups"])
api_router.include_router(others.router, prefix="/others", tags=["Others"])
api_router.include_router(websockets.router, prefix="/ws", tags=["ws"])
