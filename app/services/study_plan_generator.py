#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学习计划生成服务
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.student import Student
from app.models.school import School
from app.models.major import Major
from app.models.score_line import ScoreLine
from app.models.study_plan import StudyPlan
from app.services.llm_service import get_llm_study_plan


class StudyPlanGenerator:
    """学习计划生成器"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_study_plan(
        self,
        student_id: int,
        plan_type: str = "overall",
        duration: str = "3个月",
        focus_subjects: Optional[List[str]] = None,
        target_score: Optional[float] = None,
        target_schools: Optional[List[int]] = None,
        target_majors: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """生成学习计划

        Args:
            student_id: 学生ID
            plan_type: 计划类型(overall-总体计划, weekly-周计划, subject-学科计划)
            duration: 计划时长
            focus_subjects: 重点科目
            target_score: 目标分数
            target_schools: 目标学校IDs
            target_majors: 目标专业IDs

        Returns:
            学习计划数据
        """
        # 获取学生信息
        result = await self.db.execute(select(Student).where(Student.id == student_id))
        student = result.scalars().first()

        if not student:
            return {"status": "error", "message": "未找到学生信息"}

        # 获取学生的目标院校信息
        target_school_data = []
        if target_schools:
            result = await self.db.execute(
                select(School).where(School.id.in_(target_schools))
            )
            schools = result.scalars().all()
            target_school_data = [
                {"id": s.id, "name": s.name, "rank": s.rank} for s in schools
            ]

        # 获取学生的目标专业信息
        target_major_data = []
        if target_majors:
            result = await self.db.execute(
                select(Major).where(Major.id.in_(target_majors))
            )
            majors = result.scalars().all()
            target_major_data = [
                {"id": m.id, "name": m.name, "category": m.category} for m in majors
            ]

        # 如果没有指定目标分数，使用学生当前分数增加一定值
        if not target_score and student.total_score:
            target_score = student.total_score + 30  # 默认目标是提高30分

        # 获取学生的弱项学科
        weak_subjects = student.weaknesses or []

        # 如果没有指定重点科目，则使用弱项学科作为重点
        if not focus_subjects and weak_subjects:
            focus_subjects = weak_subjects if isinstance(weak_subjects, list) else []

        # 根据计划类型生成不同的学习计划
        plan_data = {}

        if plan_type == "overall":
            # 生成总体学习计划
            plan_data = await self._generate_overall_plan(
                student,
                duration,
                focus_subjects,
                target_score,
                target_school_data,
                target_major_data,
            )
        elif plan_type == "weekly":
            # 生成每周学习计划
            plan_data = await self._generate_weekly_plan(
                student, focus_subjects, target_score
            )
        elif plan_type == "subject":
            # 生成学科学习计划
            if focus_subjects and len(focus_subjects) > 0:
                plan_data = await self._generate_subject_plan(
                    student, focus_subjects[0], duration  # 取第一个科目作为重点
                )
            else:
                return {"status": "error", "message": "请指定需要重点提升的学科"}
        else:
            return {"status": "error", "message": f"不支持的计划类型: {plan_type}"}

        # 创建学习计划记录
        plan_title = f"{duration}{plan_type.capitalize()}学习计划"
        if plan_type == "subject" and focus_subjects:
            plan_title = f"{focus_subjects[0]}学科{duration}提升计划"

        study_plan = StudyPlan(
            student_id=student_id,
            title=plan_title,
            plan_type=plan_type,
            duration=duration,
            overview=plan_data.get("overview"),
            weekly_schedule=plan_data.get("weekly_schedule"),
            daily_tasks=plan_data.get("daily_tasks"),
            goals=plan_data.get("goals"),
            focus_areas=focus_subjects,
            weak_subjects=weak_subjects,
            learning_resources=plan_data.get("learning_resources"),
            recommended_materials=plan_data.get("recommended_materials"),
            milestones=plan_data.get("milestones"),
            progress_tracking=plan_data.get("progress_tracking"),
        )

        self.db.add(study_plan)
        await self.db.commit()
        await self.db.refresh(study_plan)

        return {
            "status": "success",
            "plan_id": study_plan.id,
            "plan_type": plan_type,
            "title": plan_title,
            "overview": plan_data.get("overview"),
            "weekly_schedule": plan_data.get("weekly_schedule"),
            "daily_tasks": plan_data.get("daily_tasks"),
            "goals": plan_data.get("goals"),
            "focus_areas": focus_subjects,
            "learning_resources": plan_data.get("learning_resources"),
        }

    async def _generate_overall_plan(
        self,
        student: Student,
        duration: str,
        focus_subjects: Optional[List[str]],
        target_score: Optional[float],
        target_schools: Optional[List[Dict[str, Any]]],
        target_majors: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """生成总体学习计划"""
        # 准备学生数据
        student_data = {
            "name": student.name,
            "total_score": student.total_score,
            "chinese_score": student.chinese_score,
            "math_score": student.math_score,
            "english_score": student.english_score,
            "strengths": student.strengths,
            "weaknesses": student.weaknesses,
            "target_score": target_score,
        }

        # 调用LLM服务生成学习计划
        plan_data = {
            "type": "overall",
            "duration": duration,
            "student": student_data,
            "focus_subjects": focus_subjects,
            "target_schools": target_schools,
            "target_majors": target_majors,
        }

        llm_plan = await get_llm_study_plan(plan_data)

        # 整理计划数据
        return {
            "overview": llm_plan.get("overview", ""),
            "weekly_schedule": llm_plan.get("weekly_schedule", {}),
            "goals": llm_plan.get("goals", []),
            "learning_resources": llm_plan.get("learning_resources", []),
            "recommended_materials": llm_plan.get("recommended_materials", []),
            "milestones": llm_plan.get("milestones", []),
        }

    async def _generate_weekly_plan(
        self,
        student: Student,
        focus_subjects: Optional[List[str]],
        target_score: Optional[float],
    ) -> Dict[str, Any]:
        """生成每周学习计划"""
        # 准备学生数据
        student_data = {
            "name": student.name,
            "total_score": student.total_score,
            "strengths": student.strengths,
            "weaknesses": student.weaknesses,
            "target_score": target_score,
        }

        # 调用LLM服务生成每周计划
        plan_data = {
            "type": "weekly",
            "student": student_data,
            "focus_subjects": focus_subjects,
        }

        llm_plan = await get_llm_study_plan(plan_data)

        # 整理每周计划数据
        weekly_schedule = {}
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for day in days:
            if day in llm_plan:
                weekly_schedule[day] = llm_plan[day]
            else:
                # 创建默认日程
                weekly_schedule[day] = {
                    "morning": "自主学习",
                    "afternoon": "自主学习",
                    "evening": "自主学习",
                }

        return {
            "weekly_schedule": weekly_schedule,
            "daily_tasks": llm_plan.get("daily_tasks", {}),
            "learning_resources": llm_plan.get("learning_resources", []),
        }

    async def _generate_subject_plan(
        self, student: Student, subject: str, duration: str
    ) -> Dict[str, Any]:
        """生成学科学习计划"""
        # 获取该学科的成绩
        subject_score = None
        if subject == "语文":
            subject_score = student.chinese_score
        elif subject == "数学":
            subject_score = student.math_score
        elif subject == "英语":
            subject_score = student.english_score
        elif subject == "物理":
            subject_score = student.physics_score
        elif subject == "化学":
            subject_score = student.chemistry_score
        elif subject == "生物":
            subject_score = student.biology_score

        # 准备学生数据
        student_data = {
            "name": student.name,
            "total_score": student.total_score,
            "subject": subject,
            "subject_score": subject_score,
            "strengths": student.strengths,
            "weaknesses": student.weaknesses,
        }

        # 调用LLM服务生成学科计划
        plan_data = {
            "type": "subject",
            "duration": duration,
            "student": student_data,
            "subject": subject,
        }

        llm_plan = await get_llm_study_plan(plan_data)

        # 整理学科计划数据
        return {
            "overview": llm_plan.get("overview", ""),
            "goals": llm_plan.get("goals", []),
            "learning_resources": llm_plan.get("learning_resources", []),
            "recommended_materials": llm_plan.get("recommended_materials", []),
            "milestones": llm_plan.get("milestones", []),
        }
