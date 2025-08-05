#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学校数据模式
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime


class SchoolBase(BaseModel):
    """学校基本信息"""

    name: str
    code: Optional[str] = None
    level: Optional[str] = None
    type: Optional[str] = None
    nature: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None


class SchoolCreate(SchoolBase):
    """创建学校模型"""

    address: Optional[str] = None
    website: Optional[str] = None

    is_211: Optional[bool] = False
    is_985: Optional[bool] = False
    is_double_first_class: Optional[bool] = False
    rank: Optional[int] = None
    features: Optional[Dict[str, Any]] = None

    admission_office_phone: Optional[str] = None
    admission_office_email: Optional[str] = None
    admission_site: Optional[str] = None

    introduction: Optional[str] = None
    history: Optional[str] = None
    facilities: Optional[Dict[str, Any]] = None
    campus_environment: Optional[str] = None


class SchoolUpdate(BaseModel):
    """更新学校模型"""

    name: Optional[str] = None
    code: Optional[str] = None
    level: Optional[str] = None
    type: Optional[str] = None
    nature: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None

    is_211: Optional[bool] = None
    is_985: Optional[bool] = None
    is_double_first_class: Optional[bool] = None
    rank: Optional[int] = None
    features: Optional[Dict[str, Any]] = None

    admission_office_phone: Optional[str] = None
    admission_office_email: Optional[str] = None
    admission_site: Optional[str] = None

    introduction: Optional[str] = None
    history: Optional[str] = None
    facilities: Optional[Dict[str, Any]] = None
    campus_environment: Optional[str] = None


class School(SchoolBase):
    """学校信息响应模型"""

    id: int
    is_211: bool
    is_985: bool
    is_double_first_class: bool
    rank: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class SchoolDetail(School):
    """学校详细信息"""

    address: Optional[str] = None
    website: Optional[str] = None
    features: Optional[Dict[str, Any]] = None

    admission_office_phone: Optional[str] = None
    admission_office_email: Optional[str] = None
    admission_site: Optional[str] = None

    introduction: Optional[str] = None
    history: Optional[str] = None
    facilities: Optional[Dict[str, Any]] = None
    campus_environment: Optional[str] = None

    class Config:
        orm_mode = True
