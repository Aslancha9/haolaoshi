#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
专业模型
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    JSON,
    Text,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Major(Base):
    """专业信息模型"""

    __tablename__ = "majors"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(100), nullable=False)
    code = Column(String(20))  # 专业代码
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    school = relationship("School", back_populates="majors")

    # 专业特征
    category = Column(String(50))  # 学科门类
    subcategory = Column(String(50))  # 学科类别
    degree_type = Column(String(20))  # 学位类型
    study_period = Column(Integer)  # 学制年限

    # 专业详情
    description = Column(Text)  # 专业描述
    core_courses = Column(JSON)  # 核心课程
    research_directions = Column(JSON)  # 研究方向

    # 就业信息
    career_prospects = Column(Text)  # 就业前景
    employment_rate = Column(Float)  # 就业率
    employment_fields = Column(JSON)  # 就业领域
    salary_range = Column(JSON)  # 薪资范围

    # 关联
    score_lines = relationship("ScoreLine", back_populates="major")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
