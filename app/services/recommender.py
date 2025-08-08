#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
推荐系统服务
集成多种推荐算法：LLM推荐、协同过滤、基于内容推荐、分数预测
"""

import random
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.student import Student
from app.models.school import School
from app.models.major import Major
from app.models.score_line import ScoreLine
from app.models.recommendation import Recommendation
from app.services.llm_service import get_llm_recommendation
from app.core.config import settings


class SchoolRecommender:
    """学校推荐系统"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def recommend_schools(
        self,
        student_id: int,
        strategy: str = "balanced",
        num_recommendations: int = 9,
        include_majors: bool = True,
        prefer_provinces: Optional[List[str]] = None,
        prefer_school_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """为学生推荐学校

        Args:
            student_id: 学生ID
            strategy: 推荐策略（aggressive=冲刺, balanced=平衡, conservative=保守）
            num_recommendations: 推荐学校总数
            include_majors: 是否包含专业推荐
            prefer_provinces: 优先推荐省份列表
            prefer_school_types: 优先推荐学校类型

        Returns:
            包含推荐学校的字典
        """
        # 获取学生信息
        result = await self.db.execute(select(Student).where(Student.id == student_id))
        student = result.scalars().first()

        if not student:
            return {"status": "error", "message": "未找到学生信息"}

        # 确定推荐数量分配（冲刺/稳妥/保底）
        if strategy == "aggressive":
            # 激进策略：更多冲刺院校
            category_counts = {"challenge": 5, "match": 3, "safety": 1}
        elif strategy == "conservative":
            # 保守策略：更多保底院校
            category_counts = {"challenge": 1, "match": 3, "safety": 5}
        else:
            # 平衡策略：均衡分配
            category_counts = {"challenge": 3, "match": 3, "safety": 3}

        # 确保总数正确
        total = sum(category_counts.values())
        if total != num_recommendations:
            # 按比例调整
            for key in category_counts:
                category_counts[key] = max(
                    1, int(round(category_counts[key] * num_recommendations / total))
                )
            # 调整可能的误差
            adjust_key = "match"  # 默认调整匹配院校数量
            category_counts[adjust_key] += num_recommendations - sum(
                category_counts.values()
            )

        # 获取学生成绩和省份
        student_score = student.total_score
        province = student.province or "全国"

        if not student_score:
            return {"status": "error", "message": "无法获取有效的学生分数"}

        # 使用多种推荐方法

        # 1. 使用LLM进行推荐
        llm_results = await self._get_llm_recommendations(student, strategy)

        # 2. 使用协同过滤进行推荐
        cf_results = await self._get_collaborative_filtering(student, strategy)

        # 3. 基于内容的推荐
        content_results = await self._get_content_based_recommendations(
            student, strategy
        )

        # 4. 使用分数预测模型
        prediction_results = await self._get_score_prediction_recommendations(
            student, strategy
        )

        # 整合多种推荐结果
        integrated_results = await self._integrate_recommendations(
            student,
            llm_results,
            cf_results,
            content_results,
            prediction_results,
            category_counts,
            prefer_provinces,
            prefer_school_types,
        )

        # 如果需要，为每所学校添加推荐专业
        if include_majors:
            integrated_results = await self._add_major_recommendations(
                integrated_results
            )

        # 保存推荐结果
        recommendation = Recommendation(
            student_id=student_id,
            recommendation_type="school",
            strategy=strategy,
            challenge_schools=integrated_results.get("challenge", []),
            match_schools=integrated_results.get("match", []),
            safety_schools=integrated_results.get("safety", []),
            llm_recommendation=llm_results,
            collaborative_filtering=cf_results,
            content_based=content_results,
            score_prediction=prediction_results,
            analysis=f"基于{student.name}的分数{student_score}和个人特点，使用{strategy}策略生成推荐。",
        )
        self.db.add(recommendation)
        await self.db.commit()
        await self.db.refresh(recommendation)

        return {
            "status": "success",
            "recommendation_id": recommendation.id,
            "strategy": strategy,
            "student_score": student_score,
            "challenge_schools": integrated_results.get("challenge", []),
            "match_schools": integrated_results.get("match", []),
            "safety_schools": integrated_results.get("safety", []),
        }

    async def _get_llm_recommendations(
        self, student: Student, strategy: str
    ) -> Dict[str, Any]:
        """使用LLM进行推荐"""
        try:
            # 调用LLM服务获取推荐
            student_data = {
                "name": student.name,
                "total_score": student.total_score,
                "province": student.province,
                "interests": student.interests,
                "strengths": student.strengths,
                "weaknesses": student.weaknesses,
                "career_goals": student.career_goals,
            }

            recommendations = await get_llm_recommendation(student_data, strategy)
            return recommendations
        except Exception as e:
            print(f"LLM推荐出错: {str(e)}")
            return {}

    async def _get_collaborative_filtering(
        self, student: Student, strategy: str
    ) -> Dict[str, Any]:
        """使用协同过滤进行推荐"""
        # 简化实现：根据相似学生的选择进行推荐
        try:
            # 获取分数相近的其他学生(±30分)
            result = await self.db.execute(
                select(Student)
                .where(
                    Student.id != student.id,
                    Student.total_score.between(
                        student.total_score - 30, student.total_score + 30
                    ),
                )
                .limit(10)
            )
            similar_students = result.scalars().all()

            # 收集这些学生的目标学校
            target_schools = []
            for similar_student in similar_students:
                if similar_student.target_schools:
                    if isinstance(similar_student.target_schools, list):
                        target_schools.extend(similar_student.target_schools)
                    elif isinstance(similar_student.target_schools, dict):
                        for category, schools in similar_student.target_schools.items():
                            if isinstance(schools, list):
                                target_schools.extend(schools)

            # 获取这些学校的实际数据
            if target_schools:
                # 转换为整数ID列表
                school_ids = []
                for item in target_schools:
                    if isinstance(item, int):
                        school_ids.append(item)
                    elif isinstance(item, dict) and "id" in item:
                        school_ids.append(item["id"])
                    elif isinstance(item, dict) and "school_id" in item:
                        school_ids.append(item["school_id"])

                if school_ids:
                    result = await self.db.execute(
                        select(School).where(School.id.in_(school_ids))
                    )
                    cf_schools = result.scalars().all()

                    # 转换为简单结构
                    school_list = [
                        {
                            "school_id": school.id,
                            "name": school.name,
                            "type": school.type,
                            "province": school.province,
                            "is_985": school.is_985,
                            "is_211": school.is_211,
                            "rank": school.rank,
                        }
                        for school in cf_schools
                    ]

                    # 根据学生分数，将学校分为不同类别
                    challenge = []
                    match = []
                    safety = []

                    for school_data in school_list:
                        # 获取该校分数线
                        result = await self.db.execute(
                            select(ScoreLine)
                            .where(
                                ScoreLine.school_id == school_data["school_id"],
                                ScoreLine.major_id == None,
                                ScoreLine.province == student.province
                                if student.province
                                else True,
                            )
                            .order_by(ScoreLine.year.desc())
                        )
                        score_line = result.scalars().first()

                        if score_line:
                            school_data["score"] = score_line.min_score

                            # 根据分数差异分类
                            score_diff = student.total_score - score_line.min_score

                            if score_diff >= 20:
                                school_data["match"] = 0.9
                                school_data["admission_probability"] = "90%以上"
                                safety.append(school_data)
                            elif score_diff >= -20:
                                school_data["match"] = 0.7
                                school_data["admission_probability"] = "50%-80%"
                                match.append(school_data)
                            else:
                                school_data["match"] = 0.5
                                school_data["admission_probability"] = "30%以下"
                                challenge.append(school_data)

                    return {"challenge": challenge, "match": match, "safety": safety}

            # 没有找到有效推荐
            return {}

        except Exception as e:
            print(f"协同过滤推荐出错: {str(e)}")
            return {}

    async def _get_content_based_recommendations(
        self, student: Student, strategy: str
    ) -> Dict[str, Any]:
        """基于内容的推荐"""
        try:
            # 获取所有学校
            result = await self.db.execute(select(School))
            all_schools = result.scalars().all()

            # 计算每所学校与学生兴趣的匹配度
            scored_schools = []

            for school in all_schools:
                # 计算兴趣匹配度
                interest_match = await self._calculate_interest_match(student, school)

                # 计算区域匹配度
                location_match = await self._calculate_location_match(student, school)

                # 计算职业目标匹配度
                career_match = await self._calculate_career_match(student, school)

                # 综合评分
                total_match = (
                    interest_match * 0.5 + location_match * 0.3 + career_match * 0.2
                )

                scored_schools.append(
                    {
                        "school_id": school.id,
                        "name": school.name,
                        "type": school.type,
                        "province": school.province,
                        "is_985": school.is_985,
                        "is_211": school.is_211,
                        "rank": school.rank,
                        "match": total_match,
                        "interest_match": interest_match,
                        "location_match": location_match,
                        "career_match": career_match,
                    }
                )

            # 按匹配度排序
            scored_schools.sort(key=lambda x: x["match"], reverse=True)

            # 分类为不同类型的推荐
            # 简化处理：前1/3为挑战，中间1/3为匹配，后1/3为保底
            total = len(scored_schools)
            if total == 0:
                return {}

            chunk = max(1, total // 3)

            return {
                "challenge": scored_schools[:chunk],
                "match": scored_schools[chunk : 2 * chunk],
                "safety": scored_schools[2 * chunk :],
            }

        except Exception as e:
            print(f"基于内容推荐出错: {str(e)}")
            return {}

    async def _calculate_interest_match(
        self, student: Student, school: School
    ) -> float:
        """计算兴趣匹配度"""
        if not student.interests or not school.features:
            return 0.5  # 默认中等匹配度

        # 提取学校特征关键词
        school_keywords = []
        if isinstance(school.features, dict) and "strengths" in school.features:
            school_keywords = school.features["strengths"]

        # 兴趣关键词
        student_interests = (
            student.interests if isinstance(student.interests, list) else []
        )

        # 计算匹配项
        matches = 0
        for interest in student_interests:
            for keyword in school_keywords:
                # 简单字符串匹配
                if (interest.lower() in keyword.lower()) or (
                    keyword.lower() in interest.lower()
                ):
                    matches += 1
                    break

        # 计算匹配度
        if not student_interests:
            return 0.5

        match_ratio = min(1.0, matches / len(student_interests))
        return 0.5 + match_ratio * 0.5  # 范围：0.5-1.0

    async def _calculate_location_match(
        self, student: Student, school: School
    ) -> float:
        """计算地理位置匹配度"""
        if not student.province or not school.province:
            return 0.5  # 默认中等匹配度

        if student.province == school.province:
            return 1.0  # 同省最高匹配

        # 简化的区域划分
        regions = {
            "北方": ["北京", "天津", "河北", "山西", "内蒙古"],
            "东部": ["上海", "江苏", "浙江", "安徽", "福建", "江西", "山东"],
            "南方": ["广东", "广西", "海南"],
            "中部": ["河南", "湖北", "湖南"],
            "西南": ["重庆", "四川", "贵州", "云南", "西藏"],
            "西北": ["陕西", "甘肃", "青海", "宁夏", "新疆"],
            "东北": ["辽宁", "吉林", "黑龙江"],
        }

        # 检查是否在同一区域
        for region, provinces in regions.items():
            if student.province in provinces and school.province in provinces:
                return 0.8  # 同区域较高匹配

        return 0.5  # 不同区域一般匹配

    async def _calculate_career_match(self, student: Student, school: School) -> float:
        """计算职业目标匹配度"""
        if not student.career_goals:
            return 0.5  # 默认中等匹配度

        # 提取职业目标
        career_goal = ""
        if isinstance(student.career_goals, str):
            career_goal = student.career_goals
        elif isinstance(student.career_goals, dict) and "goal" in student.career_goals:
            career_goal = student.career_goals["goal"]

        if not career_goal:
            return 0.5

        # 简单的学校类型与职业匹配规则
        career_school_map = {
            "IT行业": ["理工", "综合"],
            "医疗卫生": ["医药", "综合"],
            "金融行业": ["财经", "综合"],
            "教育工作": ["师范", "综合"],
            "法律行业": ["政法", "综合"],
            "艺术设计": ["艺术", "综合"],
        }

        # 检查是否匹配
        if (
            career_goal in career_school_map
            and school.type in career_school_map[career_goal]
        ):
            return 0.9  # 高匹配度

        # 针对"综合"类型学校的特殊处理
        if school.type == "综合":
            return 0.7  # 综合类学校与各种职业都有一定匹配度

        return 0.5  # 默认中等匹配度

    async def _get_score_prediction_recommendations(
        self, student: Student, strategy: str
    ) -> Dict[str, Any]:
        """基于分数预测的推荐"""
        try:
            # 获取学生所在省份的分数线
            student_province = student.province or "重庆"  # 默认省份
            result = await self.db.execute(
                select(ScoreLine)
                .where(
                    ScoreLine.province == student_province, ScoreLine.major_id == None
                )
                .order_by(ScoreLine.year.desc())
            )
            score_lines = result.scalars().all()

            if not score_lines:
                return {}

            # 计算每所学校的录取可能性
            school_chances = []
            for score_line in score_lines:
                # 获取学校信息
                result = await self.db.execute(
                    select(School).where(School.id == score_line.school_id)
                )
                school = result.scalars().first()

                if school:
                    # 计算分数差异
                    score_diff = student.total_score - score_line.min_score

                    # 基于分数差异计算录取概率
                    if score_diff >= 30:
                        probability = 0.95  # 95%概率录取
                    elif score_diff >= 20:
                        probability = 0.9  # 90%概率录取
                    elif score_diff >= 10:
                        probability = 0.8  # 80%概率录取
                    elif score_diff >= 0:
                        probability = 0.7  # 70%概率录取
                    elif score_diff >= -10:
                        probability = 0.5  # 50%概率录取
                    elif score_diff >= -20:
                        probability = 0.3  # 30%概率录取
                    elif score_diff >= -30:
                        probability = 0.2  # 20%概率录取
                    else:
                        probability = 0.1  # 10%概率录取

                    # 分类
                    category = (
                        "safety"
                        if probability >= 0.8
                        else "match"
                        if probability >= 0.4
                        else "challenge"
                    )

                    school_chances.append(
                        {
                            "school_id": school.id,
                            "name": school.name,
                            "type": school.type,
                            "province": school.province,
                            "is_985": school.is_985,
                            "is_211": school.is_211,
                            "rank": school.rank,
                            "score": score_line.min_score,
                            "score_diff": score_diff,
                            "probability": probability,
                            "admission_probability": f"{int(probability*100)}%",
                            "match": probability,
                            "category": category,
                        }
                    )

            # 按分类组织结果
            challenge = [s for s in school_chances if s["category"] == "challenge"]
            match = [s for s in school_chances if s["category"] == "match"]
            safety = [s for s in school_chances if s["category"] == "safety"]

            # 按匹配度排序
            challenge.sort(key=lambda x: x["match"], reverse=True)
            match.sort(key=lambda x: x["match"], reverse=True)
            safety.sort(key=lambda x: x["match"], reverse=True)

            return {"challenge": challenge, "match": match, "safety": safety}

        except Exception as e:
            print(f"分数预测推荐出错: {str(e)}")
            return {}

    async def _integrate_recommendations(
        self,
        student: Student,
        llm_results: Dict[str, Any],
        cf_results: Dict[str, Any],
        content_results: Dict[str, Any],
        prediction_results: Dict[str, Any],
        category_counts: Dict[str, int],
        prefer_provinces: Optional[List[str]] = None,
        prefer_school_types: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """整合多种推荐结果"""
        integrated_results = {"challenge": [], "match": [], "safety": []}

        # 设置各方法权重
        weights = settings.MODULE_WEIGHTS

        # 合并所有学校列表，按ID去重
        all_schools = {}

        for category in ["challenge", "match", "safety"]:
            # 整合LLM推荐
            if category in llm_results and isinstance(llm_results[category], list):
                for school in llm_results[category]:
                    if "school_id" in school:
                        school_id = school["school_id"]
                        if school_id not in all_schools:
                            all_schools[school_id] = {
                                "school_id": school_id,
                                "name": school.get("name", ""),
                                "category": category,
                                "scores": {
                                    "llm": school.get("match", 0)
                                    * weights["llm_recommendation"],
                                    "cf": 0,
                                    "content": 0,
                                    "prediction": 0,
                                },
                                "data": {"llm": school},
                            }
                        else:
                            # 更新已存在的学校信息
                            all_schools[school_id]["scores"]["llm"] = (
                                school.get("match", 0) * weights["llm_recommendation"]
                            )
                            all_schools[school_id]["data"]["llm"] = school

            # 整合协同过滤推荐
            if category in cf_results and isinstance(cf_results[category], list):
                for school in cf_results[category]:
                    if "school_id" in school:
                        school_id = school["school_id"]
                        if school_id not in all_schools:
                            all_schools[school_id] = {
                                "school_id": school_id,
                                "name": school.get("name", ""),
                                "category": category,
                                "scores": {
                                    "llm": 0,
                                    "cf": school.get("match", 0)
                                    * weights["collaborative_filtering"],
                                    "content": 0,
                                    "prediction": 0,
                                },
                                "data": {"cf": school},
                            }
                        else:
                            # 更新已存在的学校信息
                            all_schools[school_id]["scores"]["cf"] = (
                                school.get("match", 0)
                                * weights["collaborative_filtering"]
                            )
                            all_schools[school_id]["data"]["cf"] = school

            # 整合基于内容推荐
            if category in content_results and isinstance(
                content_results[category], list
            ):
                for school in content_results[category]:
                    if "school_id" in school:
                        school_id = school["school_id"]
                        if school_id not in all_schools:
                            all_schools[school_id] = {
                                "school_id": school_id,
                                "name": school.get("name", ""),
                                "category": category,
                                "scores": {
                                    "llm": 0,
                                    "cf": 0,
                                    "content": school.get("match", 0)
                                    * weights["content_based"],
                                    "prediction": 0,
                                },
                                "data": {"content": school},
                            }
                        else:
                            # 更新已存在的学校信息
                            all_schools[school_id]["scores"]["content"] = (
                                school.get("match", 0) * weights["content_based"]
                            )
                            all_schools[school_id]["data"]["content"] = school

            # 整合预测分数推荐
            if category in prediction_results and isinstance(
                prediction_results[category], list
            ):
                for school in prediction_results[category]:
                    if "school_id" in school:
                        school_id = school["school_id"]
                        if school_id not in all_schools:
                            all_schools[school_id] = {
                                "school_id": school_id,
                                "name": school.get("name", ""),
                                "category": category,
                                "scores": {
                                    "llm": 0,
                                    "cf": 0,
                                    "content": 0,
                                    "prediction": school.get("match", 0)
                                    * weights["score_prediction"],
                                },
                                "data": {"prediction": school},
                            }
                        else:
                            # 更新已存在的学校信息
                            all_schools[school_id]["scores"]["prediction"] = (
                                school.get("match", 0) * weights["score_prediction"]
                            )
                            all_schools[school_id]["data"]["prediction"] = school

        # 计算每所学校的总分
        school_list = []
        for school_id, school_data in all_schools.items():
            scores = school_data["scores"]
            total_score = sum(scores.values())

            # 整合各种数据源的信息
            merged_data = {
                "school_id": school_id,
                "name": school_data["name"],
                "match": total_score,  # 综合匹配度
                "category": school_data["category"],  # 初始分类
            }

            # 添加其他可能有用的字段
            for data_source in ["llm", "cf", "content", "prediction"]:
                if data_source in school_data["data"]:
                    source_data = school_data["data"][data_source]
                    for key in [
                        "type",
                        "province",
                        "is_985",
                        "is_211",
                        "rank",
                        "score",
                    ]:
                        if key in source_data and key not in merged_data:
                            merged_data[key] = source_data[key]

            # 录取可能性评估
            admission_values = []
            for data_source in ["llm", "cf", "content", "prediction"]:
                if (
                    data_source in school_data["data"]
                    and "admission_probability" in school_data["data"][data_source]
                ):
                    admission_values.append(
                        school_data["data"][data_source]["admission_probability"]
                    )

            if admission_values:
                merged_data["admission_probability"] = max(
                    admission_values, key=admission_values.count
                )

            school_list.append(merged_data)

        # 根据学生分数重新分类
        for school in school_list:
            if "score" in school:
                score_diff = student.total_score - school["score"]
                if score_diff >= 20:
                    school["category"] = "safety"
                elif score_diff >= -20:
                    school["category"] = "match"
                else:
                    school["category"] = "challenge"

        # 应用偏好过滤
        if prefer_provinces or prefer_school_types:
            # 增加符合偏好的学校匹配度
            for school in school_list:
                boost = 0

                if prefer_provinces and "province" in school:
                    if school["province"] in prefer_provinces:
                        boost += 0.1

                if prefer_school_types and "type" in school:
                    if school["type"] in prefer_school_types:
                        boost += 0.1

                if boost > 0:
                    school["match"] += boost

        # 按类别和匹配度排序
        for category in ["challenge", "match", "safety"]:
            category_schools = [s for s in school_list if s["category"] == category]
            category_schools.sort(key=lambda x: x["match"], reverse=True)
            integrated_results[category] = category_schools[: category_counts[category]]

        return integrated_results

    async def _add_major_recommendations(
        self, recommendations: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """为推荐的学校添加专业推荐"""
        result = recommendations.copy()

        for category in ["challenge", "match", "safety"]:
            for i, school in enumerate(result[category]):
                if "school_id" in school:
                    # 获取该校专业
                    query_result = await self.db.execute(
                        select(Major)
                        .where(Major.school_id == school["school_id"])
                        .limit(3)
                    )
                    majors = query_result.scalars().all()

                    # 添加推荐专业
                    result[category][i]["recommended_majors"] = [
                        {
                            "major_id": major.id,
                            "name": major.name,
                            "code": major.code,
                            "category": major.category,
                        }
                        for major in majors
                    ]

        return result
