#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
分数线模型
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ScoreLine(Base):
    """分数线信息模型"""

    __tablename__ = "score_lines"

    id = Column(Integer, primary_key=True, index=True)

    # 关联
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    school = relationship("School", back_populates="score_lines")
    major_id = Column(Integer, ForeignKey("majors.id"), nullable=True)
    major = relationship("Major", back_populates="score_lines")

    # 分数线信息
    year = Column(Integer, nullable=False)  # 年份
    province = Column(String(20), nullable=False)  # 省份
    batch = Column(String(50))  # 批次
    subject_type = Column(String(20))  # 科目类型

    # 录取数据
    min_score = Column(Float)  # 最低分
    min_rank = Column(Integer)  # 最低位次
    avg_score = Column(Float)  # 平均分
    max_score = Column(Float)  # 最高分

    # 对比数据
    provincial_line = Column(Float)  # 省控线
    score_difference = Column(Float)  # 高出省控线分数

    # 招生计划
    plan_count = Column(Integer)  # 计划招生人数
    actual_count = Column(Integer)  # 实际录取人数

    # 附加信息
    additional_info = Column(JSON)  # 附加信息

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
