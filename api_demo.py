#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
推荐系统API演示
这是一个独立的FastAPI应用，用于展示推荐系统的API结构
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import random

# 创建FastAPI应用
app = FastAPI(
    title="推荐系统API演示",
    description="学校和专业推荐系统API示例",
    version="1.0.0",
    docs_url="/docs",
)

# 定义数据模型
class SchoolRecommendation(BaseModel):
    """学校推荐信息"""
    school_id: int
    name: str
    match: float
    score: Optional[float] = None
    admission_probability: Optional[str] = None
    recommended_majors: Optional[List[Dict[str, Any]]] = None

class RecommendRequest(BaseModel):
    """推荐请求模型"""
    strategy: Optional[str] = "balanced"  # balanced, aggressive, conservative
    num_recommendations: Optional[int] = 9
    include_majors: Optional[bool] = True
    prefer_provinces: Optional[List[str]] = None
    prefer_school_types: Optional[List[str]] = None

class StudyPlanRequest(BaseModel):
    """学习计划请求模型"""
    plan_type: str
    duration: int
    focus_subjects: List[str]
    target_score: Optional[int] = None
    target_schools: Optional[List[int]] = None
    target_majors: Optional[List[int]] = None

# 示例数据
example_schools = [
    {"school_id": 1, "name": "清华大学", "type": "985", "province": "北京"},
    {"school_id": 2, "name": "北京大学", "type": "985", "province": "北京"},
    {"school_id": 3, "name": "上海交通大学", "type": "985", "province": "上海"},
    {"school_id": 4, "name": "复旦大学", "type": "985", "province": "上海"},
    {"school_id": 5, "name": "南京大学", "type": "985", "province": "江苏"},
    {"school_id": 6, "name": "浙江大学", "type": "985", "province": "浙江"},
    {"school_id": 7, "name": "中国人民大学", "type": "985", "province": "北京"},
    {"school_id": 8, "name": "武汉大学", "type": "985", "province": "湖北"},
    {"school_id": 9, "name": "华中科技大学", "type": "985", "province": "湖北"},
]

example_majors = [
    {"id": 101, "name": "计算机科学与技术", "category": "工学"},
    {"id": 102, "name": "软件工程", "category": "工学"},
    {"id": 103, "name": "人工智能", "category": "工学"},
    {"id": 104, "name": "数据科学与大数据技术", "category": "工学"},
    {"id": 105, "name": "电子信息工程", "category": "工学"},
    {"id": 201, "name": "金融学", "category": "经济学"},
    {"id": 202, "name": "经济学", "category": "经济学"},
    {"id": 301, "name": "临床医学", "category": "医学"},
]

# API端点
@app.post("/api/students/{student_id}/recommend_schools")
async def recommend_schools(
    student_id: int, request: RecommendRequest
):
    """为学生推荐学校"""
    # 生成模拟数据
    strategy = request.strategy
    num_recommendations = request.num_recommendations
    include_majors = request.include_majors
    
    # 根据策略分配学校数量
    if strategy == "aggressive":
        category_counts = {"challenge": 5, "match": 3, "safety": 1}
    elif strategy == "conservative":
        category_counts = {"challenge": 1, "match": 3, "safety": 5}
    else:  # balanced
        category_counts = {"challenge": 3, "match": 3, "safety": 3}
    
    # 优先考虑偏好
    prefer_provinces = request.prefer_provinces or []
    prefer_school_types = request.prefer_school_types or []
    
    # 生成推荐结果
    recommendations = {
        "challenge_schools": [],
        "match_schools": [],
        "safety_schools": []
    }
    
    # 随机选择学校进行推荐
    all_schools = example_schools.copy()
    random.shuffle(all_schools)
    
    for category, count in category_counts.items():
        schools_for_category = []
        for _ in range(count):
            if not all_schools:
                break
            
            # 尝试优先选择符合偏好的学校
            preferred_school = None
            for i, school in enumerate(all_schools):
                if (not prefer_provinces or school["province"] in prefer_provinces) or \
                   (not prefer_school_types or school["type"] in prefer_school_types):
                    preferred_school = all_schools.pop(i)
                    break
            
            # 如果没有符合偏好的学校，就取第一个
            if not preferred_school and all_schools:
                preferred_school = all_schools.pop(0)
            
            if preferred_school:
                # 添加匹配度和录取概率
                if category == "challenge":
                    match = round(random.uniform(0.75, 0.85), 2)
                    prob = f"{random.randint(20, 40)}%"
                elif category == "match":
                    match = round(random.uniform(0.85, 0.95), 2)
                    prob = f"{random.randint(40, 70)}%"
                else:  # safety
                    match = round(random.uniform(0.95, 0.99), 2)
                    prob = f"{random.randint(70, 95)}%"
                
                # 添加推荐专业
                recommended_majors = []
                if include_majors:
                    random.shuffle(example_majors)
                    for major in example_majors[:3]:
                        recommended_majors.append({
                            "id": major["id"],
                            "name": major["name"],
                            "match": round(random.uniform(0.7, 0.99), 2)
                        })
                
                schools_for_category.append({
                    "school_id": preferred_school["school_id"],
                    "name": preferred_school["name"],
                    "match": match,
                    "score": random.randint(550, 680),
                    "admission_probability": prob,
                    "recommended_majors": recommended_majors if include_majors else None
                })
        
        recommendations[f"{category}_schools"] = schools_for_category
    
    # 添加分析
    recommendations["analysis"] = f"根据学生{student_id}的成绩和兴趣，推荐了{num_recommendations}所院校。"
    
    return recommendations

@app.post("/api/study_plans/generate")
async def generate_study_plan(
    request: StudyPlanRequest, student_id: int
):
    """生成学习计划"""
    # 生成模拟数据
    plan_type = request.plan_type
    duration = request.duration
    focus_subjects = request.focus_subjects
    
    # 生成每周学习计划
    weeks = duration // 7
    weekly_plans = []
    
    for week in range(1, weeks + 1):
        weekly_plan = {
            "week": week,
            "focus": random.choice(focus_subjects),
            "tasks": []
        }
        
        # 为每天添加任务
        for day in range(1, 8):
            tasks = []
            for subject in focus_subjects:
                tasks.append({
                    "subject": subject,
                    "content": f"{subject}练习题 {random.randint(20, 50)}题",
                    "duration_minutes": random.randint(30, 120),
                    "priority": random.choice(["高", "中", "低"])
                })
            
            weekly_plan["tasks"].append({
                "day": day,
                "date": f"第{week}周第{day}天",
                "tasks": tasks
            })
        
        weekly_plans.append(weekly_plan)
    
    return {
        "plan_id": random.randint(1000, 9999),
        "student_id": student_id,
        "plan_type": plan_type,
        "duration": duration,
        "focus_subjects": focus_subjects,
        "weekly_plans": weekly_plans,
        "target_score": request.target_score,
        "target_schools": [
            {"id": school_id, "name": next((s["name"] for s in example_schools if s["school_id"] == school_id), "未知学校")}
            for school_id in (request.target_schools or [])
        ],
        "recommendation": "建议每天保持5-6小时的高效学习时间，注意劳逸结合。"
    }

if __name__ == "__main__":
    # 启动服务器
    uvicorn.run("api_demo:app", host="0.0.0.0", port=8080, reload=True)