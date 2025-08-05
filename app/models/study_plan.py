#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学习计划模型
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


class StudyPlan(Base):
    """学习计划模型"""

    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)

    # 关联
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    student = relationship("Student", back_populates="study_plans")

    # 计划信息
    title = Column(String(200), nullable=False)  # 计划标题
    plan_type = Column(String(50))  # 计划类型：overall, weekly, subject, etc.
    duration = Column(String(50))  # 计划时长：1周、1个月、3个月等

    # 计划内容
    overview = Column(Text)  # 总体规划
    weekly_schedule = Column(JSON)  # 每周安排
    daily_tasks = Column(JSON)  # 每日任务

    # 目标和重点
    goals = Column(JSON)  # 学习目标
    focus_areas = Column(JSON)  # 重点领域
    weak_subjects = Column(JSON)  # 薄弱学科

    # 资源和工具
    learning_resources = Column(JSON)  # 学习资源
    recommended_materials = Column(JSON)  # 推荐材料

    # 进度跟踪
    milestones = Column(JSON)  # 里程碑
    progress_tracking = Column(JSON)  # 进度跟踪
    evaluation_method = Column(Text)  # 评估方法

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
