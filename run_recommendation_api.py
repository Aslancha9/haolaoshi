#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
考研推荐系统API服务入口
"""

import os
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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
    "*",  # 允许所有来源，实际生产环境应限制
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "考研推荐系统API正在运行",
        "docs_url": "/docs",
        "gpu_available": USE_GPU,
        "environment": "development"
    }

@app.get("/health")
async def health_check():
    """健康检查，确保服务正常"""
    try:
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务不健康: {str(e)}")

@app.get("/gpu_info")
async def gpu_info():
    """获取GPU信息"""
    if USE_GPU:
        return {
            "gpu_available": True,
            "gpu_name": torch.cuda.get_device_name(0),
            "cuda_version": torch.version.cuda,
            "gpu_count": torch.cuda.device_count(),
            "gpu_memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB",
            "gpu_memory_allocated": f"{torch.cuda.memory_allocated() / 1024**3:.1f} GB",
            "gpu_memory_reserved": f"{torch.cuda.memory_reserved() / 1024**3:.1f} GB"
        }
    else:
        return {
            "gpu_available": False,
            "message": "GPU不可用，将使用CPU运行模型"
        }

if __name__ == "__main__":
    # 使用uvicorn启动服务
    uvicorn.run(
        "run_recommendation_api:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )