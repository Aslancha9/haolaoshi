#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库基础配置
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建异步引擎
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# 创建会话
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 声明Base模型
Base = declarative_base()

# 获取数据库会话
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
