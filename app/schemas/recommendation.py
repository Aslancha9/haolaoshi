#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
推荐结果数据模式
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel
from datetime import datetime


class SchoolRecommendation(BaseModel):
    """学校推荐信息"""

    school_id: int
    name: str
    match: float
    score: Optional[float] = None
    admission_probability: Optional[str] = None
    recommended_majors: Optional[List[Dict[str, Any]]] = None


class RecommendationBase(BaseModel):
    """推荐基本信息"""

    student_id: int
    recommendation_type: str  # school, major, etc.
    strategy: Optional[str] = "balanced"  # balanced, aggressive, conservative


class RecommendationCreate(RecommendationBase):
    """创建推荐模型"""

    challenge_schools: Optional[
        List[Union[Dict[str, Any], SchoolRecommendation]]
    ] = None
    match_schools: Optional[List[Union[Dict[str, Any], SchoolRecommendation]]] = None
    safety_schools: Optional[List[Union[Dict[str, Any], SchoolRecommendation]]] = None

    recommended_majors: Optional[List[Dict[str, Any]]] = None

    analysis: Optional[str] = None

    llm_recommendation: Optional[Dict[str, Any]] = None
    collaborative_filtering: Optional[Dict[str, Any]] = None
    content_based: Optional[Dict[str, Any]] = None
    score_prediction: Optional[Dict[str, Any]] = None


class RecommendationUpdate(BaseModel):
    """更新推荐模型"""

    recommendation_type: Optional[str] = None
    strategy: Optional[str] = None

    challenge_schools: Optional[
        List[Union[Dict[str, Any], SchoolRecommendation]]
    ] = None
    match_schools: Optional[List[Union[Dict[str, Any], SchoolRecommendation]]] = None
    safety_schools: Optional[List[Union[Dict[str, Any], SchoolRecommendation]]] = None

    recommended_majors: Optional[List[Dict[str, Any]]] = None

    analysis: Optional[str] = None

    llm_recommendation: Optional[Dict[str, Any]] = None
    collaborative_filtering: Optional[Dict[str, Any]] = None
    content_based: Optional[Dict[str, Any]] = None
    score_prediction: Optional[Dict[str, Any]] = None


class Recommendation(RecommendationBase):
    """推荐信息响应模型"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class RecommendationDetail(Recommendation):
    """推荐详细信息"""

    challenge_schools: Optional[List[Dict[str, Any]]] = None
    match_schools: Optional[List[Dict[str, Any]]] = None
    safety_schools: Optional[List[Dict[str, Any]]] = None

    recommended_majors: Optional[List[Dict[str, Any]]] = None

    analysis: Optional[str] = None

    class Config:
        orm_mode = True


class RecommendRequest(BaseModel):
    """推荐请求模型"""

    strategy: Optional[str] = "balanced"  # balanced, aggressive, conservative
    num_recommendations: Optional[int] = 9
    include_majors: Optional[bool] = True
    prefer_provinces: Optional[List[str]] = None
    prefer_school_types: Optional[List[str]] = None
