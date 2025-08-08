#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学生模型
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    ForeignKey,
    JSON,
    Text,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Student(Base):
    """学生信息模型"""

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True
    )

    # 基本信息
    name = Column(String(50), index=True, nullable=False)
    gender = Column(String(10))
    age = Column(Integer)
    current_school = Column(String(100))  # 当前就读学校
    province = Column(String(20))
    city = Column(String(50))
    address = Column(String(200))
    phone = Column(String(20))
    email = Column(String(100))

    # 学习路径
    education_path_id = Column(Integer, ForeignKey("education_paths.id"))
    education_path = relationship("EducationPath", back_populates="students")

    # 学习成绩
    total_score = Column(Float)  # 总分
    chinese_score = Column(Float)  # 语文
    math_score = Column(Float)  # 数学
    english_score = Column(Float)  # 英语
    physics_score = Column(Float)  # 物理
    chemistry_score = Column(Float)  # 化学
    biology_score = Column(Float)  # 生物
    history_score = Column(Float)  # 历史
    geography_score = Column(Float)  # 地理
    politics_score = Column(Float)  # 政治

    # 专业能力
    art_score = Column(Float)  # 艺术类专业分数
    sports_score = Column(Float)  # 体育类专业分数

    # 学习特征
    strengths = Column(JSON)  # 优势学科
    weaknesses = Column(JSON)  # 弱势学科
    learning_style = Column(JSON)  # 学习风格

    # 个人偏好
    interests = Column(JSON)  # 兴趣爱好
    career_goals = Column(JSON)  # 职业目标

    # 目标规划
    target_score = Column(Float)  # 目标分数
    target_schools = Column(JSON)  # 目标院校
    target_majors = Column(JSON)  # 目标专业

    # 系统生成的建议
    recommendations = relationship("Recommendation", back_populates="student")
    study_plans = relationship("StudyPlan", back_populates="student")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
