from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional
import torch
import numpy as np
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.user_profile import UserProfiler
from app.models.recommender_model import HybridRecommender
from app.models.semantic_matcher import SemanticMatcher
from app.models.collaborative_filtering import CollaborativeFiltering
from app.core.config import settings

router = APIRouter()

# 检查GPU是否可用
USE_GPU = torch.cuda.is_available()
DEVICE = torch.device("cuda" if USE_GPU else "cpu")

# 初始化模型
user_profiler = UserProfiler(use_gpu=USE_GPU)
hybrid_recommender = HybridRecommender(use_gpu=USE_GPU)
semantic_matcher = SemanticMatcher(use_gpu=USE_GPU)
collaborative_filter = None  # 延迟初始化，因为需要用户行为数据

# 请求模型
class UserProfileRequest(BaseModel):
    """用户画像请求模型"""
    name: str = Field(..., description="用户姓名")
    total_score: Optional[float] = Field(None, description="总分")
    math_score: Optional[float] = Field(None, description="数学分数")
    english_score: Optional[float] = Field(None, description="英语分数")
    specialized_score: Optional[float] = Field(None, description="专业课分数")
    province: Optional[str] = Field(None, description="所在省份")
    interests: Optional[List[str]] = Field(None, description="兴趣爱好")
    strengths: Optional[List[str]] = Field(None, description="学科优势")
    weaknesses: Optional[List[str]] = Field(None, description="学科弱点")
    career_goals: Optional[str] = Field(None, description="职业目标")
    risk_preference: Optional[str] = Field("balanced", description="风险偏好", enum=["conservative", "balanced", "aggressive"])

class SchoolRecommendRequest(BaseModel):
    """学校推荐请求模型"""
    strategy: Optional[str] = Field("balanced", description="推荐策略", enum=["conservative", "balanced", "aggressive"])
    num_recommendations: Optional[int] = Field(9, description="推荐数量")
    include_majors: Optional[bool] = Field(True, description="是否包含专业推荐")
    prefer_provinces: Optional[List[str]] = Field(None, description="偏好省份")
    prefer_school_types: Optional[List[str]] = Field(None, description="偏好学校类型")

class MajorRecommendRequest(BaseModel):
    """专业推荐请求模型"""
    interests: List[str] = Field(..., description="兴趣领域")
    career_goals: Optional[str] = Field(None, description="职业目标")
    num_recommendations: Optional[int] = Field(5, description="推荐数量")

class StudyPlanRequest(BaseModel):
    """学习计划请求模型"""
    target_school: str = Field(..., description="目标院校")
    target_major: Optional[str] = Field(None, description="目标专业")
    remaining_days: int = Field(..., description="距离考试剩余天数")
    current_level: Dict[str, float] = Field(..., description="当前水平评估")
    focus_areas: Optional[List[str]] = Field(None, description="需要重点提高的领域")

class FeedbackRequest(BaseModel):
    """用户反馈请求模型"""
    user_id: int = Field(..., description="用户ID")
    item_id: int = Field(..., description="项目ID")
    interaction_type: str = Field(..., description="交互类型", enum=["click", "favorite", "apply", "ignore"])
    rating: Optional[float] = Field(None, description="评分")

# API端点
@router.post("/profile", response_model=Dict[str, Any])
async def create_user_profile(
    request: UserProfileRequest, 
    db: AsyncSession = Depends(get_db)
):
    """创建用户画像"""
    try:
        # 将请求数据转换为字典
        user_data = request.model_dump()
        
        # 使用用户画像模型处理数据
        profile_vector = user_profiler.vectorize_user(user_data)
        
        # 将向量转为Python列表
        profile_vector = profile_vector.tolist() if isinstance(profile_vector, np.ndarray) else profile_vector
        
        # 这里可以保存用户画像到数据库
        # await save_user_profile(db, user_id, profile_vector)
        
        return {
            "status": "success",
            "message": "用户画像创建成功",
            "profile_features": {
                "feature_count": len(profile_vector),
                "sample_features": profile_vector[:10] if len(profile_vector) > 10 else profile_vector
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建用户画像失败: {str(e)}")

@router.post("/recommend/schools", response_model=Dict[str, Any])
async def recommend_schools(
    user_profile: UserProfileRequest,
    request: SchoolRecommendRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """推荐学校"""
    try:
        # 获取用户数据
        user_data = user_profile.model_dump()
        
        # 获取所有学校数据
        # 实际应用中应该从数据库获取
        # schools = await get_schools_from_db(db, request.prefer_provinces, request.prefer_school_types)
        
        # 临时使用假数据进行测试
        schools = _get_mock_schools(
            prefer_provinces=request.prefer_provinces,
            prefer_school_types=request.prefer_school_types
        )
        
        # 使用推荐模型
        recommendations = hybrid_recommender.recommend(
            user_data=user_data,
            school_pool=schools,
            strategy=request.strategy,
            top_n=request.num_recommendations
        )
        
        # 如果需要包含专业推荐
        if request.include_majors:
            for rec in recommendations:
                # 获取学校的专业列表
                school_id = rec["school"]["id"]
                # majors = await get_majors_by_school_id(db, school_id)
                majors = _get_mock_majors_for_school(school_id)
                
                # 推荐专业
                if user_data.get("interests") or user_data.get("career_goals"):
                    major_recommendations = semantic_matcher.get_major_recommendations(
                        user_data=user_data,
                        majors_data=majors,
                        top_n=3  # 每个学校推荐3个专业
                    )
                    rec["recommended_majors"] = major_recommendations
        
        # 使用协同过滤进行推荐增强（如果模型已初始化）
        if collaborative_filter is not None and "id" in user_data:
            cf_recommendations = collaborative_filter.recommend_items_for_user(
                user_id=user_data["id"],
                n_recommendations=request.num_recommendations
            )
            # 这里简化处理，实际应用中需要将协同过滤结果与基于内容的推荐结果融合
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "strategy": request.strategy,
            "count": len(recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐学校失败: {str(e)}")

@router.post("/recommend/majors", response_model=Dict[str, Any])
async def recommend_majors(
    request: MajorRecommendRequest,
    db: AsyncSession = Depends(get_db)
):
    """推荐专业"""
    try:
        # 构造用户数据
        user_data = {
            "interests": request.interests,
            "career_goals": request.career_goals or ""
        }
        
        # 获取所有专业数据
        # majors = await get_all_majors(db)
        majors = _get_mock_majors()
        
        # 使用语义匹配模型推荐专业
        recommendations = semantic_matcher.get_major_recommendations(
            user_data=user_data,
            majors_data=majors,
            top_n=request.num_recommendations
        )
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐专业失败: {str(e)}")

@router.post("/generate/study_plan", response_model=Dict[str, Any])
async def generate_study_plan(
    request: StudyPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    """生成学习计划"""
    try:
        # 这里应该实现学习计划生成逻辑
        # 可以使用LLM或规则引擎
        
        # 临时返回模拟数据
        plan = _generate_mock_study_plan(
            target_school=request.target_school,
            target_major=request.target_major,
            remaining_days=request.remaining_days,
            current_level=request.current_level,
            focus_areas=request.focus_areas
        )
        
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成学习计划失败: {str(e)}")

@router.post("/feedback", response_model=Dict[str, Any])
async def record_user_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """记录用户反馈"""
    try:
        # 保存用户反馈到数据库
        # await save_user_feedback(db, request.user_id, request.item_id, request.interaction_type, request.rating)
        
        # 将反馈转换为评分
        rating = request.rating if request.rating is not None else {
            "click": 0.5,
            "favorite": 1.0,
            "apply": 1.0,
            "ignore": 0.0
        }.get(request.interaction_type, 0.5)
        
        # 如果协同过滤模型已初始化，更新模型
        if collaborative_filter is not None:
            collaborative_filter.update_with_new_interaction(
                user_id=request.user_id,
                item_id=request.item_id,
                rating=rating
            )
        
        return {
            "status": "success",
            "message": "反馈已记录"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录反馈失败: {str(e)}")

@router.get("/model/info", response_model=Dict[str, Any])
async def get_model_info():
    """获取模型信息"""
    return {
        "status": "success",
        "models": {
            "user_profiler": "已加载",
            "hybrid_recommender": "已加载",
            "semantic_matcher": "已加载",
            "collaborative_filter": "已加载" if collaborative_filter is not None else "未加载",
        },
        "gpu_available": USE_GPU,
        "device": str(DEVICE)
    }

# 辅助函数
def _get_mock_schools(prefer_provinces=None, prefer_school_types=None) -> List[Dict[str, Any]]:
    """获取模拟学校数据"""
    schools = []
    for i in range(1, 31):
        # 随机生成学校数据
        if i <= 10:
            school_type = "985"
            rank = i
        elif i <= 20:
            school_type = "211"
            rank = i
        else:
            school_type = "普通本科"
            rank = i + 30
        
        province = ["北京", "上海", "广东", "江苏", "浙江"][i % 5]
        
        school = {
            "id": i,
            "name": f"示例大学{i}",
            "rank": rank,
            "type": school_type,
            "province": province,
            "min_score": 550 - i * 5,
            "avg_score": 580 - i * 5,
            "admission_rate": 0.3 + i * 0.02,
            # 其他属性...
        }
        
        # 应用筛选条件
        if prefer_provinces and province not in prefer_provinces:
            continue
        
        if prefer_school_types and school_type not in prefer_school_types:
            continue
        
        schools.append(school)
    
    return schools

def _get_mock_majors() -> List[Dict[str, Any]]:
    """获取模拟专业数据"""
    majors = []
    major_names = ["计算机科学与技术", "软件工程", "人工智能", "数据科学与大数据技术", 
                  "电子信息工程", "自动化", "机械工程", "土木工程", "生物工程", 
                  "金融学", "会计学", "经济学", "法学", "医学", "心理学"]
    
    for i, name in enumerate(major_names):
        major = {
            "id": i + 1,
            "name": name,
            "description": f"{name}是一门融合多学科的专业，培养具备扎实理论基础和专业技能的人才。",
            "career_prospects": f"毕业生可在相关领域从事技术开发、研究、管理等工作，就业前景广阔。",
            # 其他属性...
        }
        majors.append(major)
    
    return majors

def _get_mock_majors_for_school(school_id: int) -> List[Dict[str, Any]]:
    """获取学校的模拟专业数据"""
    all_majors = _get_mock_majors()
    # 简化处理，每个学校随机选取5-10个专业
    import random
    num_majors = random.randint(5, 10)
    selected_majors = random.sample(all_majors, num_majors)
    
    # 为每个专业添加学校特定的属性
    for major in selected_majors:
        major["school_id"] = school_id
        major["school_rank"] = f"全国第{random.randint(1, 50)}名"
    
    return selected_majors

def _generate_mock_study_plan(target_school: str, target_major: str, 
                             remaining_days: int, current_level: Dict[str, float],
                             focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
    """生成模拟学习计划"""
    # 确定每个科目的学习时间分配
    total_hours = remaining_days * 8  # 假设每天8小时
    
    subjects = list(current_level.keys())
    if focus_areas:
        # 重点关注的领域占60%时间
        focus_subjects = [s for s in subjects if s in focus_areas]
        other_subjects = [s for s in subjects if s not in focus_areas]
        
        focus_hours = total_hours * 0.6
        other_hours = total_hours * 0.4
        
        focus_hours_per_subject = focus_hours / len(focus_subjects) if focus_subjects else 0
        other_hours_per_subject = other_hours / len(other_subjects) if other_subjects else 0
        
        hours_allocation = {
            s: focus_hours_per_subject if s in focus_areas else other_hours_per_subject
            for s in subjects
        }
    else:
        # 根据当前水平反比分配时间
        total_gap = sum(1 - level for level in current_level.values())
        if total_gap == 0:
            hours_allocation = {s: total_hours / len(subjects) for s in subjects}
        else:
            hours_allocation = {
                s: (1 - current_level[s]) / total_gap * total_hours
                for s in subjects
            }
    
    # 生成每周计划
    weeks = remaining_days // 7 + (1 if remaining_days % 7 > 0 else 0)
    weekly_plans = []
    
    for week in range(1, weeks + 1):
        days_in_week = 7 if week < weeks else remaining_days % 7 or 7
        week_plan = {
            "week": week,
            "days": days_in_week,
            "subjects": {}
        }
        
        for subject in subjects:
            subject_hours = hours_allocation[subject] / weeks
            if subject_hours > 0:
                week_plan["subjects"][subject] = {
                    "hours": round(subject_hours, 1),
                    "focus": subject in (focus_areas or []),
                    "tasks": [
                        f"完成{subject}基础知识复习",
                        f"做{subject}练习题10道",
                        f"复习{subject}重点难点"
                    ]
                }
        
        weekly_plans.append(week_plan)
    
    return {
        "target_school": target_school,
        "target_major": target_major,
        "remaining_days": remaining_days,
        "total_study_hours": total_hours,
        "current_level": current_level,
        "focus_areas": focus_areas,
        "weekly_plans": weekly_plans,
        "estimated_improvement": {
            subject: min(1.0, level + (hours_allocation[subject] / total_hours) * 0.5)
            for subject, level in current_level.items()
        }
    }