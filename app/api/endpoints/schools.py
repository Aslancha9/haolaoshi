#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学校API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.base import get_db
from app.models.school import School
from app.models.major import Major
from app.models.score_line import ScoreLine
from app.schemas.school import School as SchoolSchema, SchoolDetail
from app.schemas.major import Major as MajorSchema

router = APIRouter()


@router.get("/", response_model=List[SchoolSchema])
async def get_schools(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    province: Optional[str] = None,
    is_985: Optional[bool] = None,
    is_211: Optional[bool] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取学校列表"""
    query = select(School)

    # 应用过滤条件
    if name:
        query = query.filter(School.name.contains(name))
    if province:
        query = query.filter(School.province == province)
    if is_985 is not None:
        query = query.filter(School.is_985 == is_985)
    if is_211 is not None:
        query = query.filter(School.is_211 == is_211)
    if type:
        query = query.filter(School.type == type)

    # 默认按排名排序
    query = query.order_by(School.rank)

    result = await db.execute(query.offset(skip).limit(limit))
    schools = result.scalars().all()
    return schools


@router.get("/{school_id}", response_model=SchoolDetail)
async def get_school(school_id: int, db: AsyncSession = Depends(get_db)):
    """获取学校详细信息"""
    result = await db.execute(select(School).filter(School.id == school_id))
    school = result.scalars().first()

    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")

    return school


@router.get("/{school_id}/majors", response_model=List[MajorSchema])
async def get_school_majors(
    school_id: int, category: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    """获取学校专业列表"""
    # 确认学校存在
    result = await db.execute(select(School).filter(School.id == school_id))
    school = result.scalars().first()

    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")

    # 查询专业
    query = select(Major).filter(Major.school_id == school_id)

    if category:
        query = query.filter(Major.category == category)

    result = await db.execute(query)
    majors = result.scalars().all()

    return majors


@router.get("/{school_id}/score_lines")
async def get_school_score_lines(
    school_id: int,
    province: Optional[str] = None,
    year: Optional[int] = None,
    major_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取学校分数线"""
    # 确认学校存在
    result = await db.execute(select(School).filter(School.id == school_id))
    school = result.scalars().first()

    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")

    # 查询分数线
    query = select(ScoreLine).filter(ScoreLine.school_id == school_id)

    if province:
        query = query.filter(ScoreLine.province == province)
    if year:
        query = query.filter(ScoreLine.year == year)
    if major_id:
        query = query.filter(ScoreLine.major_id == major_id)
    else:
        # 默认查询学校总体分数线
        query = query.filter(ScoreLine.major_id == None)

    # 按年份降序排序
    query = query.order_by(ScoreLine.year.desc())

    result = await db.execute(query)
    score_lines = result.scalars().all()

    return [
        {
            "id": sl.id,
            "school_id": sl.school_id,
            "major_id": sl.major_id,
            "year": sl.year,
            "province": sl.province,
            "batch": sl.batch,
            "subject_type": sl.subject_type,
            "min_score": sl.min_score,
            "min_rank": sl.min_rank,
            "provincial_line": sl.provincial_line,
        }
        for sl in score_lines
    ]


@router.get("/compare")
async def compare_schools(
    school_ids: List[int] = Query(...), db: AsyncSession = Depends(get_db)
):
    """比较多所学校信息"""
    if len(school_ids) < 2 or len(school_ids) > 5:
        raise HTTPException(status_code=400, detail="请选择2-5所学校进行比较")

    # 查询学校
    query = select(School).filter(School.id.in_(school_ids))
    result = await db.execute(query)
    schools = result.scalars().all()

    if len(schools) != len(school_ids):
        raise HTTPException(status_code=404, detail="部分学校不存在")

    # 准备比较数据
    comparison_data = []

    for school in schools:
        # 获取专业数量
        major_query = select(Major).filter(Major.school_id == school.id)
        major_result = await db.execute(major_query)
        majors = major_result.scalars().all()

        # 获取最新分数线（简化处理）
        score_query = (
            select(ScoreLine)
            .filter(ScoreLine.school_id == school.id, ScoreLine.major_id == None)
            .order_by(ScoreLine.year.desc())
        )
        score_result = await db.execute(score_query)
        score_line = score_result.scalars().first()

        school_data = {
            "id": school.id,
            "name": school.name,
            "level": school.level,
            "type": school.type,
            "province": school.province,
            "city": school.city,
            "is_211": school.is_211,
            "is_985": school.is_985,
            "is_double_first_class": school.is_double_first_class,
            "rank": school.rank,
            "major_count": len(majors),
            "latest_score_line": score_line.min_score if score_line else None,
            "latest_score_year": score_line.year if score_line else None,
        }

        comparison_data.append(school_data)

    # 按排名排序
    comparison_data.sort(key=lambda x: x["rank"] if x["rank"] else 9999)

    return comparison_data
