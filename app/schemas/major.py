#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
专业数据模式
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class MajorBase(BaseModel):
    """专业基本信息"""

    name: str
    code: Optional[str] = None
    school_id: int
    category: Optional[str] = None
    subcategory: Optional[str] = None


class MajorCreate(MajorBase):
    """创建专业模型"""

    degree_type: Optional[str] = None
    study_period: Optional[int] = None

    description: Optional[str] = None
    core_courses: Optional[List[str]] = None
    research_directions: Optional[List[str]] = None

    career_prospects: Optional[str] = None
    employment_rate: Optional[float] = None
    employment_fields: Optional[List[str]] = None
    salary_range: Optional[Dict[str, float]] = None


class MajorUpdate(BaseModel):
    """更新专业模型"""

    name: Optional[str] = None
    code: Optional[str] = None
    school_id: Optional[int] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None

    degree_type: Optional[str] = None
    study_period: Optional[int] = None

    description: Optional[str] = None
    core_courses: Optional[List[str]] = None
    research_directions: Optional[List[str]] = None

    career_prospects: Optional[str] = None
    employment_rate: Optional[float] = None
    employment_fields: Optional[List[str]] = None
    salary_range: Optional[Dict[str, float]] = None


class Major(MajorBase):
    """专业信息响应模型"""

    id: int
    degree_type: Optional[str] = None
    study_period: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class MajorDetail(Major):
    """专业详细信息"""

    description: Optional[str] = None
    core_courses: Optional[List[str]] = None
    research_directions: Optional[List[str]] = None

    career_prospects: Optional[str] = None
    employment_rate: Optional[float] = None
    employment_fields: Optional[List[str]] = None
    salary_range: Optional[Dict[str, float]] = None

    school_name: Optional[str] = None

    class Config:
        orm_mode = True
