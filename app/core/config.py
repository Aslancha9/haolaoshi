#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
系统配置文件
"""

import os
from pydantic_settings import BaseSettings
from typing import List, Optional, Union, Dict, Any


class Settings(BaseSettings):
    # 项目基本信息
    PROJECT_NAME: str = "智能升学择校辅助系统"
    PROJECT_DESCRIPTION: str = "基于LLM、推荐系统、预测模型和NLP等多种AI技术的智能升学辅助平台"
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./haolaoshi.db")

    # 跨域配置
    CORS_ORIGINS: List[str] = ["*"]

    # LLM配置
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")

    # 用户验证
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # 特征权重配置
    FEATURE_WEIGHTS: Dict[str, float] = {
        "score_match": 0.6,  # 分数匹配权重
        "interest_match": 0.2,  # 兴趣匹配权重
        "location_match": 0.1,  # 地理位置匹配权重
        "career_match": 0.1,  # 职业规划匹配权重
    }

    # 学习路径类型
    EDUCATION_PATHS: List[str] = ["高考", "专升本", "考研", "艺考", "出国留学", "职业教育"]

    # 系统模块权重
    MODULE_WEIGHTS: Dict[str, float] = {
        "llm_recommendation": 0.4,  # LLM推荐结果权重
        "collaborative_filtering": 0.2,  # 协同过滤推荐权重
        "content_based": 0.2,  # 基于内容推荐权重
        "score_prediction": 0.2,  # 分数预测模型权重
    }

    class Config:
        case_sensitive = True


# 实例化配置对象
settings = Settings()
