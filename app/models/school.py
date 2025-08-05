#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学校模型
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    JSON,
    Text,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class School(Base):
    """学校信息模型"""

    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(100), index=True, nullable=False, unique=True)
    code = Column(String(20), index=True)  # 院校代码
    level = Column(String(50))  # 办学层次
    type = Column(String(50))  # 办学类型
    nature = Column(String(50))  # 办学性质
    province = Column(String(20))
    city = Column(String(50))
    address = Column(String(200))
    website = Column(String(200))

    # 学校特征
    is_211 = Column(Boolean, default=False)
    is_985 = Column(Boolean, default=False)
    is_double_first_class = Column(Boolean, default=False)
    rank = Column(Integer)  # 全国排名
    features = Column(JSON)  # 学校特色

    # 招生信息
    admission_office_phone = Column(String(50))
    admission_office_email = Column(String(100))
    admission_site = Column(String(200))

    # 详细描述
    introduction = Column(Text)
    history = Column(Text)
    facilities = Column(JSON)
    campus_environment = Column(Text)

    # 关联
    majors = relationship("Major", back_populates="school")
    score_lines = relationship("ScoreLine", back_populates="school")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
