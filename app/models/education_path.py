#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
教育路径模型
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class EducationPath(Base):
    """教育路径模型，如高考、专升本、考研、艺考等"""

    __tablename__ = "education_paths"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(50), nullable=False)  # 路径名称
    description = Column(Text)  # 路径描述

    # 详细信息
    duration = Column(String(50))  # 持续时间
    requirements = Column(Text)  # 要求条件
    process = Column(JSON)  # 流程步骤
    key_points = Column(JSON)  # 关键点

    # 关联
    students = relationship("Student", back_populates="education_path")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
