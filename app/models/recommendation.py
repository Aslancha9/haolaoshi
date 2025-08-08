#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
推荐结果模型
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    JSON,
    DateTime,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Recommendation(Base):
    """推荐结果模型"""

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)

    # 关联
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    student = relationship("Student", back_populates="recommendations")

    # 推荐信息
    recommendation_type = Column(String(50), nullable=False)  # 推荐类型：school, major, etc.
    strategy = Column(String(50))  # 推荐策略：balanced, aggressive, conservative

    # 推荐结果
    challenge_schools = Column(JSON)  # 冲刺院校
    match_schools = Column(JSON)  # 匹配院校
    safety_schools = Column(JSON)  # 保底院校

    recommended_majors = Column(JSON)  # 推荐专业

    # 推荐分析
    analysis = Column(Text)  # 推荐分析

    # 推荐方法
    llm_recommendation = Column(JSON)  # LLM推荐结果
    collaborative_filtering = Column(JSON)  # 协同过滤推荐结果
    content_based = Column(JSON)  # 基于内容推荐结果
    score_prediction = Column(JSON)  # 分数预测模型结果

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
