#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学生API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.base import get_db
from app.models.student import Student
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    Student as StudentSchema,
    StudentDetail,
)
from app.schemas.recommendation import RecommendRequest
from app.services.recommender import SchoolRecommender

router = APIRouter()


@router.post("/", response_model=StudentSchema)
async def create_student(student: StudentCreate, db: AsyncSession = Depends(get_db)):
    """创建学生信息"""
    db_student = Student(**student.dict())
    db.add(db_student)
    await db.commit()
    await db.refresh(db_student)
    return db_student


@router.get("/", response_model=List[StudentSchema])
async def get_students(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    province: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取学生列表"""
    query = select(Student)

    # 应用过滤条件
    if name:
        query = query.filter(Student.name.contains(name))
    if province:
        query = query.filter(Student.province == province)

    result = await db.execute(query.offset(skip).limit(limit))
    students = result.scalars().all()
    return students


@router.get("/{student_id}", response_model=StudentDetail)
async def get_student(student_id: int, db: AsyncSession = Depends(get_db)):
    """获取学生详细信息"""
    result = await db.execute(select(Student).filter(Student.id == student_id))
    student = result.scalars().first()

    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    return student


@router.put("/{student_id}", response_model=StudentSchema)
async def update_student(
    student_id: int, student_data: StudentUpdate, db: AsyncSession = Depends(get_db)
):
    """更新学生信息"""
    result = await db.execute(select(Student).filter(Student.id == student_id))
    student = result.scalars().first()

    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 更新学生数据
    for key, value in student_data.dict(exclude_unset=True).items():
        setattr(student, key, value)

    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/{student_id}")
async def delete_student(student_id: int, db: AsyncSession = Depends(get_db)):
    """删除学生信息"""
    result = await db.execute(select(Student).filter(Student.id == student_id))
    student = result.scalars().first()

    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    await db.delete(student)
    await db.commit()

    return {"message": "学生删除成功"}


@router.post("/{student_id}/recommend_schools")
async def recommend_schools(
    student_id: int, request: RecommendRequest, db: AsyncSession = Depends(get_db)
):
    """为学生推荐学校"""
    result = await db.execute(select(Student).filter(Student.id == student_id))
    student = result.scalars().first()

    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 调用推荐服务
    recommender = SchoolRecommender(db)
    recommendations = await recommender.recommend_schools(
        student_id=student_id,
        strategy=request.strategy,
        num_recommendations=request.num_recommendations,
        include_majors=request.include_majors,
        prefer_provinces=request.prefer_provinces,
        prefer_school_types=request.prefer_school_types,
    )

    return recommendations
