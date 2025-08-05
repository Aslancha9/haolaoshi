#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API路由主文件
"""

from fastapi import APIRouter

from app.api.endpoints import students, schools, study_plans, web

api_router = APIRouter()

# 注册API路由
api_router.include_router(students.router, prefix="/api/students", tags=["students"])
api_router.include_router(schools.router, prefix="/api/schools", tags=["schools"])
api_router.include_router(
    study_plans.router, prefix="/api/study_plans", tags=["study_plans"]
)

# 注册Web页面路由
api_router.include_router(web.router, tags=["web"])
