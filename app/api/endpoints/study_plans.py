#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学习计划API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.base import get_db
from app.models.student import Student
from app.models.study_plan import StudyPlan
from app.schemas.study_plan import (
    StudyPlanCreate,
    StudyPlan as StudyPlanSchema,
    StudyPlanDetail,
    StudyPlanRequest,
)
from app.services.study_plan_generator import StudyPlanGenerator

router = APIRouter()


@router.post("/generate", response_model=dict)
async def generate_study_plan(
    request: StudyPlanRequest, student_id: int, db: AsyncSession = Depends(get_db)
):
    """生成学习计划"""
    # 确认学生存在
    result = await db.execute(select(Student).filter(Student.id == student_id))
    student = result.scalars().first()

    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 调用学习计划生成服务
    generator = StudyPlanGenerator(db)
    plan = await generator.generate_study_plan(
        student_id=student_id,
        plan_type=request.plan_type,
        duration=request.duration,
        focus_subjects=request.focus_subjects,
        target_score=request.target_score,
        target_schools=request.target_schools,
        target_majors=request.target_majors,
    )

    return plan


@router.get("/", response_model=List[StudyPlanSchema])
async def get_study_plans(
    student_id: Optional[int] = None,
    plan_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """获取学习计划列表"""
    query = select(StudyPlan)

    # 应用过滤条件
    if student_id:
        query = query.filter(StudyPlan.student_id == student_id)
    if plan_type:
        query = query.filter(StudyPlan.plan_type == plan_type)

    # 按创建时间降序排序
    query = query.order_by(StudyPlan.created_at.desc())

    result = await db.execute(query.offset(skip).limit(limit))
    plans = result.scalars().all()

    return plans


@router.get("/{plan_id}", response_model=StudyPlanDetail)
async def get_study_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    """获取学习计划详情"""
    result = await db.execute(select(StudyPlan).filter(StudyPlan.id == plan_id))
    plan = result.scalars().first()

    if not plan:
        raise HTTPException(status_code=404, detail="学习计划不存在")

    return plan


@router.put("/{plan_id}", response_model=StudyPlanSchema)
async def update_study_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    """更新学习计划（标记完成情况等）"""
    result = await db.execute(select(StudyPlan).filter(StudyPlan.id == plan_id))
    plan = result.scalars().first()

    if not plan:
        raise HTTPException(status_code=404, detail="学习计划不存在")

    # 更新进度跟踪信息
    if not plan.progress_tracking:
        plan.progress_tracking = {}

    plan.progress_tracking["last_updated"] = "now()"  # 实际应使用datetime.now()的字符串

    await db.commit()
    await db.refresh(plan)

    return plan


@router.delete("/{plan_id}")
async def delete_study_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    """删除学习计划"""
    result = await db.execute(select(StudyPlan).filter(StudyPlan.id == plan_id))
    plan = result.scalars().first()

    if not plan:
        raise HTTPException(status_code=404, detail="学习计划不存在")

    await db.delete(plan)
    await db.commit()

    return {"message": "学习计划删除成功"}
