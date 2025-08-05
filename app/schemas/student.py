#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学生数据模式
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class StudentBase(BaseModel):
    """学生基本信息模型"""

    name: str
    gender: Optional[str] = None
    age: Optional[int] = None
    current_school: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    education_path_id: Optional[int] = None


class StudentCreate(StudentBase):
    """创建学生模型"""

    # 学习成绩
    total_score: Optional[float] = None
    chinese_score: Optional[float] = None
    math_score: Optional[float] = None
    english_score: Optional[float] = None
    physics_score: Optional[float] = None
    chemistry_score: Optional[float] = None
    biology_score: Optional[float] = None
    history_score: Optional[float] = None
    geography_score: Optional[float] = None
    politics_score: Optional[float] = None

    # 专业能力
    art_score: Optional[float] = None
    sports_score: Optional[float] = None

    # 学习特征
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    learning_style: Optional[Dict[str, Any]] = None

    # 个人偏好
    interests: Optional[List[str]] = None
    career_goals: Optional[Union[str, Dict[str, Any]]] = None

    # 目标规划
    target_score: Optional[float] = None
    target_schools: Optional[List[Union[str, int]]] = None
    target_majors: Optional[List[Union[str, int]]] = None


class StudentUpdate(BaseModel):
    """更新学生模型"""

    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    current_school: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    education_path_id: Optional[int] = None

    # 学习成绩
    total_score: Optional[float] = None
    chinese_score: Optional[float] = None
    math_score: Optional[float] = None
    english_score: Optional[float] = None
    physics_score: Optional[float] = None
    chemistry_score: Optional[float] = None
    biology_score: Optional[float] = None
    history_score: Optional[float] = None
    geography_score: Optional[float] = None
    politics_score: Optional[float] = None

    # 专业能力
    art_score: Optional[float] = None
    sports_score: Optional[float] = None

    # 学习特征
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    learning_style: Optional[Dict[str, Any]] = None

    # 个人偏好
    interests: Optional[List[str]] = None
    career_goals: Optional[Union[str, Dict[str, Any]]] = None

    # 目标规划
    target_score: Optional[float] = None
    target_schools: Optional[List[Union[str, int]]] = None
    target_majors: Optional[List[Union[str, int]]] = None


class Student(StudentBase):
    """学生信息响应模型"""

    id: int
    uuid: str
    education_path_id: Optional[int] = None

    # 学习成绩
    total_score: Optional[float] = None
    chinese_score: Optional[float] = None
    math_score: Optional[float] = None
    english_score: Optional[float] = None

    # 学习特征
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None

    # 个人偏好
    interests: Optional[List[str]] = None
    career_goals: Optional[Union[str, Dict[str, Any]]] = None

    # 目标规划
    target_score: Optional[float] = None

    # 时间戳
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class StudentDetail(Student):
    """学生详细信息"""

    physics_score: Optional[float] = None
    chemistry_score: Optional[float] = None
    biology_score: Optional[float] = None
    history_score: Optional[float] = None
    geography_score: Optional[float] = None
    politics_score: Optional[float] = None

    art_score: Optional[float] = None
    sports_score: Optional[float] = None

    learning_style: Optional[Dict[str, Any]] = None
    target_schools: Optional[List[Union[str, int]]] = None
    target_majors: Optional[List[Union[str, int]]] = None

    class Config:
        orm_mode = True
