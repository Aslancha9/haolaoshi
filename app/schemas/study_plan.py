#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学习计划数据模式
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class StudyPlanBase(BaseModel):
    """学习计划基本信息"""

    student_id: int
    title: str
    plan_type: str  # overall, weekly, subject, etc.
    duration: Optional[str] = None


class StudyPlanCreate(StudyPlanBase):
    """创建学习计划模型"""

    overview: Optional[str] = None
    weekly_schedule: Optional[Dict[str, Any]] = None
    daily_tasks: Optional[Dict[str, Any]] = None

    goals: Optional[List[str]] = None
    focus_areas: Optional[List[str]] = None
    weak_subjects: Optional[List[str]] = None

    learning_resources: Optional[List[Dict[str, Any]]] = None
    recommended_materials: Optional[List[Dict[str, Any]]] = None

    milestones: Optional[List[Dict[str, Any]]] = None
    progress_tracking: Optional[Dict[str, Any]] = None
    evaluation_method: Optional[str] = None


class StudyPlanUpdate(BaseModel):
    """更新学习计划模型"""

    title: Optional[str] = None
    plan_type: Optional[str] = None
    duration: Optional[str] = None

    overview: Optional[str] = None
    weekly_schedule: Optional[Dict[str, Any]] = None
    daily_tasks: Optional[Dict[str, Any]] = None

    goals: Optional[List[str]] = None
    focus_areas: Optional[List[str]] = None
    weak_subjects: Optional[List[str]] = None

    learning_resources: Optional[List[Dict[str, Any]]] = None
    recommended_materials: Optional[List[Dict[str, Any]]] = None

    milestones: Optional[List[Dict[str, Any]]] = None
    progress_tracking: Optional[Dict[str, Any]] = None
    evaluation_method: Optional[str] = None


class StudyPlan(StudyPlanBase):
    """学习计划信息响应模型"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class StudyPlanDetail(StudyPlan):
    """学习计划详细信息"""

    overview: Optional[str] = None
    weekly_schedule: Optional[Dict[str, Any]] = None
    daily_tasks: Optional[Dict[str, Any]] = None

    goals: Optional[List[str]] = None
    focus_areas: Optional[List[str]] = None
    weak_subjects: Optional[List[str]] = None

    learning_resources: Optional[List[Dict[str, Any]]] = None
    recommended_materials: Optional[List[Dict[str, Any]]] = None

    milestones: Optional[List[Dict[str, Any]]] = None
    progress_tracking: Optional[Dict[str, Any]] = None
    evaluation_method: Optional[str] = None

    class Config:
        orm_mode = True


class StudyPlanRequest(BaseModel):
    """学习计划生成请求"""

    plan_type: str = "overall"  # overall, weekly, subject
    duration: Optional[str] = "3个月"  # 计划时长
    focus_subjects: Optional[List[str]] = None  # 重点科目
    target_score: Optional[float] = None  # 目标分数
    target_schools: Optional[List[int]] = None  # 目标学校IDs
    target_majors: Optional[List[int]] = None  # 目标专业IDs
