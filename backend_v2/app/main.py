"""
MindPal Backend V2 - FastAPI Main Entry
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

from app.config import settings
from app.database import engine, Base
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时: 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"[{datetime.now()}] MindPal Backend V2 started")
    yield
    # 关闭时: 清理资源
    await engine.dispose()
    print(f"[{datetime.now()}] MindPal Backend V2 stopped")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="MindPal - 面向元宇宙的智能体数字人交互平台 API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 40001,
            "message": "Internal server error",
            "error_detail": str(exc) if settings.DEBUG else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


# 注册API路由
app.include_router(api_router, prefix="/api/v1")


# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


# 根路径
@app.get("/", tags=["系统"])
async def root():
    """API根路径"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/v1/auth",
            "digital_humans": "/api/v1/digital-humans",
            "voice": "/api/v1/voice",
            "payment": "/api/v1/payment",
            "analytics": "/api/v1/analytics",
        }
    }


# 运行入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
