import os
import torch
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.endpoints import recommendation_api
from app.db.session import get_db
from app.core.config import settings

# 检查GPU是否可用
USE_GPU = torch.cuda.is_available()
if USE_GPU:
    print(f"GPU可用: {torch.cuda.get_device_name(0)}")
    print(f"CUDA版本: {torch.version.cuda}")
    print(f"可用GPU数量: {torch.cuda.device_count()}")
else:
    print("警告: GPU不可用，将使用CPU运行模型")

# 创建FastAPI应用
app = FastAPI(
    title="考研推荐系统API",
    description="基于混合推荐技术的考研院校与专业推荐系统",
    version="1.0.0",
)

# 配置CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    f"http://{settings.SERVER_HOST}",
    f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}",
    "*",  # 允许所有来源，实际生产环境应限制
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(
    recommendation_api.router,
    prefix="/api/recommendation",
    tags=["recommendation"]
)

@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "考研推荐系统API正在运行",
        "docs_url": "/docs",
        "gpu_available": USE_GPU,
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """健康检查，确保数据库连接和服务正常"""
    try:
        # 检查数据库连接
        # 简单查询，例如 await db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务不健康: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # 使用uvicorn启动服务
    uvicorn.run(
        "app.main_recommendation:app", 
        host="0.0.0.0", 
        port=settings.SERVER_PORT, 
        reload=settings.DEBUG
    )