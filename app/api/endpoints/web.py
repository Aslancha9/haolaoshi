#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web页面路由
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

# 获取模板目录的绝对路径
templates_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "templates",
)
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/student/new", response_class=HTMLResponse)
async def new_student(request: Request):
    """学生信息填写页面"""
    return templates.TemplateResponse("student_form.html", {"request": request})


@router.get("/student/{student_id}/recommendation", response_class=HTMLResponse)
async def recommendation(request: Request, student_id: int):
    """院校推荐结果页面"""
    return templates.TemplateResponse(
        "recommendation.html", {"request": request, "student_id": student_id}
    )


@router.get("/student/{student_id}/study-plan", response_class=HTMLResponse)
async def study_plan(request: Request, student_id: int):
    """学习计划页面"""
    return templates.TemplateResponse(
        "study_plan.html", {"request": request, "student_id": student_id}
    )


@router.get("/schools/{school_id}", response_class=HTMLResponse)
async def school_detail(request: Request, school_id: int):
    """学校详情页面"""
    # TODO: 实现学校详情页面
    return templates.TemplateResponse(
        "index.html", {"request": request, "message": "学校详情页面将在后续版本实现"}
    )


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """关于我们页面"""
    # TODO: 实现关于我们页面
    return templates.TemplateResponse(
        "index.html", {"request": request, "message": "关于我们页面将在后续版本实现"}
    )


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """联系我们页面"""
    # TODO: 实现联系我们页面
    return templates.TemplateResponse(
        "index.html", {"request": request, "message": "联系我们页面将在后续版本实现"}
    )
