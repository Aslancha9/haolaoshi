#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
大语言模型服务接口
"""

import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from app.core.config import settings


async def get_llm_recommendation(
    student_data: Dict[str, Any], strategy: str = "balanced"
) -> Dict[str, Any]:
    """使用LLM获取学校推荐

    Args:
        student_data: 学生信息数据
        strategy: 推荐策略

    Returns:
        推荐结果
    """
    # 构建提示词
    student_name = student_data.get('name', '学生')
    total_score = student_data.get('total_score', 'N/A')
    province = student_data.get('province', 'N/A')
    interests = ', '.join(student_data.get('interests', []))
    strengths = ', '.join(student_data.get('strengths', []))
    weaknesses = ', '.join(student_data.get('weaknesses', []))
    career_goals = student_data.get('career_goals', 'N/A')
    
    prompt = """
    作为一个专业的升学顾问，请根据学生信息为其推荐适合的院校。
    
    学生信息:
    - 姓名: """ + student_name + """
    - 总分: """ + str(total_score) + """
    - 省份: """ + province + """
    - 兴趣爱好: """ + interests + """
    - 学科优势: """ + strengths + """
    - 学科弱点: """ + weaknesses + """
    - 职业目标: """ + str(career_goals) + """
    
    推荐策略: """ + strategy + """（balanced=平衡推荐，aggressive=激进冲刺，conservative=保守稳妥）
    
    请推荐:
    1. 3所冲刺院校（挑战性强，需要努力）
    2. 3所匹配院校（与学生水平相当）
    3. 3所保底院校（把握较大的选择）
    
    对于每所院校，请提供以下信息:
    - 学校名称
    - 学校类型
    - 推荐理由
    - 录取可能性评估
    - 2-3个适合的专业推荐
    
    以JSON格式返回结果，示例格式略。
    """

    # 检查是否配置了API密钥
    if not settings.OPENAI_API_KEY:
        # 模拟一个推荐结果
        return _mock_llm_recommendation(student_data, strategy)

    try:
        # 调用OpenAI API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": "Bearer " + str(settings.OPENAI_API_KEY),
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.DEFAULT_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一个专业的升学顾问助手，负责根据学生信息推荐合适的院校。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
            ) as response:
                result = await response.json()
                content = result["choices"][0]["message"]["content"]

                # 解析JSON格式的回复
                try:
                    recommendation = json.loads(content)
                    return recommendation
                except json.JSONDecodeError:
                    # 如果解析失败，使用模拟数据
                    return _mock_llm_recommendation(student_data, strategy)

    except Exception as e:
        print("调用LLM API出错: " + str(e))
        return _mock_llm_recommendation(student_data, strategy)


def _mock_llm_recommendation(
    student_data: Dict[str, Any], strategy: str
) -> Dict[str, Any]:
    """模拟LLM推荐结果（当API调用失败或未配置时使用）"""

    # 根据学生职业目标选择学校类型
    career_goals = student_data.get("career_goals", "")
    if isinstance(career_goals, dict):
        career_goal = career_goals.get("goal", "")
    else:
        career_goal = str(career_goals)

    school_type = "综合"
    if "IT" in career_goal or "计算机" in career_goal:
        school_type = "理工"
    elif "医" in career_goal or "护理" in career_goal:
        school_type = "医药"
    elif "教育" in career_goal or "教师" in career_goal:
        school_type = "师范"
    elif "艺术" in career_goal or "设计" in career_goal:
        school_type = "艺术"

    # 根据学生兴趣推荐专业
    interests = student_data.get("interests", [])

    recommended_majors = []
    if "计算机" in interests or "科学" in interests:
        recommended_majors.extend(
            [{"name": "计算机科学与技术"}, {"name": "软件工程"}, {"name": "人工智能"}]
        )
    if "医学" in interests or "生物" in interests:
        recommended_majors.extend([{"name": "临床医学"}, {"name": "生物科学"}, {"name": "护理学"}])
    if "文学" in interests or "写作" in interests:
        recommended_majors.extend(
            [{"name": "中国语言文学"}, {"name": "新闻学"}, {"name": "编辑出版学"}]
        )
    if "经济" in interests or "金融" in interests:
        recommended_majors.extend([{"name": "金融学"}, {"name": "经济学"}, {"name": "会计学"}])

    # 确保至少有一些专业推荐
    if not recommended_majors:
        recommended_majors = [{"name": "计算机科学与技术"}, {"name": "经济学"}, {"name": "外国语言文学"}]

    # 根据策略生成推荐
    challenge_schools = [
        {
            "school_id": 1,
            "name": "北京大学",
            "type": "综合",
            "reason": "作为中国顶尖学府，" + student_data.get('name', '该学生') + "的优势学科与该校强项匹配度高，是值得冲刺的目标。",
            "match": 0.65,
            "admission_probability": "30%以下",
            "recommended_majors": recommended_majors[:2],
        },
        {
            "school_id": 2,
            "name": "清华大学",
            "type": "理工",
            "reason": "国内理工科最顶尖的学府，" + student_data.get('name', '该学生') + "对科学的兴趣与该校培养方向契合。",
            "match": 0.6,
            "admission_probability": "25%以下",
            "recommended_majors": recommended_majors[1:3],
        },
        {
            "school_id": 3,
            "name": "复旦大学",
            "type": "综合",
            "reason": "人文社科实力雄厚，适合有跨学科学习意愿的学生。",
            "match": 0.7,
            "admission_probability": "35%左右",
            "recommended_majors": recommended_majors[:2],
        },
    ]

    match_schools = [
        {
            "school_id": 6,
            "name": "四川大学",
            "type": school_type,
            "reason": "西南名校，综合实力强，特别是" + school_type + "领域，与学生能力水平较为匹配。",
            "match": 0.85,
            "admission_probability": "60-70%",
            "recommended_majors": recommended_majors[:2],
        },
        {
            "school_id": 5,
            "name": "重庆大学",
            "type": "理工",
            "reason": "211工程院校，工科实力较强，区位优势明显。",
            "match": 0.8,
            "admission_probability": "65%左右",
            "recommended_majors": recommended_majors[1:3],
        },
        {
            "school_id": 10,
            "name": "电子科技大学",
            "type": "理工",
            "reason": "信息与电子领域顶尖院校，就业前景好，学术氛围浓厚。",
            "match": 0.75,
            "admission_probability": "55-65%",
            "recommended_majors": recommended_majors[:2],
        },
    ]

    safety_schools = [
        {
            "school_id": 7,
            "name": "重庆师范大学",
            "type": "师范",
            "reason": "教师教育特色鲜明，就业稳定，是较为稳妥的选择。",
            "match": 0.95,
            "admission_probability": "85%以上",
            "recommended_majors": recommended_majors[:2],
        },
        {
            "school_id": 9,
            "name": "上海外国语大学",
            "type": "语言",
            "reason": "外语教育全国知名，就业前景广阔，录取概率较高。",
            "match": 0.9,
            "admission_probability": "80%左右",
            "recommended_majors": recommended_majors[1:3],
        },
        {
            "school_id": 8,
            "name": "中央美术学院",
            "type": "艺术",
            "reason": "艺术教育顶级院校，对艺术感兴趣的学生可以考虑。",
            "match": 0.85,
            "admission_probability": "75%左右",
            "recommended_majors": recommended_majors[:2],
        },
    ]

    # 根据策略调整推荐结果
    if strategy == "aggressive":
        # 更多挑战性院校
        return {
            "challenge": challenge_schools,
            "match": match_schools[:2],
            "safety": safety_schools[:1],
        }
    elif strategy == "conservative":
        # 更多保底院校
        return {
            "challenge": challenge_schools[:1],
            "match": match_schools[:2],
            "safety": safety_schools,
        }
    else:
        # 平衡策略
        return {
            "challenge": challenge_schools,
            "match": match_schools,
            "safety": safety_schools,
        }


async def get_llm_study_plan(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """使用LLM生成学习计划

    Args:
        plan_data: 计划参数数据

    Returns:
        学习计划数据
    """
    # 构建不同类型计划的提示词
    student = plan_data.get("student", {})
    plan_type = plan_data.get("type", "overall")

    if plan_type == "overall":
        duration = plan_data.get('duration', '3个月')
        student_name = student.get('name', '学生')
        total_score = student.get('total_score', 'N/A')
        target_score = plan_data.get('target_score', student.get('total_score', 0) + 30)
        strengths = ', '.join(student.get('strengths', []))
        weaknesses = ', '.join(student.get('weaknesses', []))
        focus_subjects = ', '.join(plan_data.get('focus_subjects', []))
        
        prompt = """
        作为专业的学习规划师，请根据以下学生信息制定一个""" + str(duration) + """的总体学习计划。
        
        学生信息:
        - 姓名: """ + str(student_name) + """
        - 当前分数: """ + str(total_score) + """
        - 目标分数: """ + str(target_score) + """
        - 优势学科: """ + strengths + """
        - 弱势学科: """ + weaknesses + """
        - 重点提升科目: """ + focus_subjects + """
        
        请提供:
        1. 总体学习规划概述
        2. 每周学习安排建议
        3. 明确的学习目标清单
        4. 推荐的学习资源和材料
        5. 学习进度里程碑
        
        以JSON格式返回结果。
        """
    elif plan_type == "weekly":
        student_name = student.get('name', '学生')
        total_score = student.get('total_score', 'N/A')
        strengths = ', '.join(student.get('strengths', []))
        weaknesses = ', '.join(student.get('weaknesses', []))
        focus_subjects = ', '.join(plan_data.get('focus_subjects', []))
        
        prompt = """
        作为专业的学习规划师，请根据以下学生信息制定一周详细的学习计划安排。
        
        学生信息:
        - 姓名: """ + str(student_name) + """
        - 当前分数: """ + str(total_score) + """
        - 优势学科: """ + strengths + """
        - 弱势学科: """ + weaknesses + """
        - 重点提升科目: """ + focus_subjects + """
        
        请提供一周七天的详细学习计划，包括:
        1. 每天上午、下午、晚上的学习内容
        2. 每天的具体任务和目标
        3. 学习资源推荐
        
        以JSON格式返回结果，按周一到周日组织。
        """
    else:  # subject
        subject = plan_data.get("subject", "")
        duration = plan_data.get('duration', '1个月')
        student_name = student.get('name', '学生')
        subject_score = student.get('subject_score', 'N/A')
        is_weakness = "是" if subject in student.get('weaknesses', []) else "否"
        is_strength = "是" if subject in student.get('strengths', []) else "否"
        
        prompt = """
        作为专业的学习规划师，请根据以下学生信息制定一个""" + duration + """的""" + subject + """学科提升计划。
        
        学生信息:
        - 姓名: """ + str(student_name) + """
        - """ + subject + """当前分数: """ + str(subject_score) + """
        - 该学科是否为弱项: """ + is_weakness + """
        - 该学科是否为优势: """ + is_strength + """
        
        请提供:
        1. """ + subject + """学科学习计划概述
        2. 具体的提升目标
        3. 学习重点和难点分析
        4. 推荐的学习资源和材料
        5. 学习进度里程碑
        
        以JSON格式返回结果。
        """

    # 检查是否配置了API密钥
    if not settings.OPENAI_API_KEY:
        # 模拟学习计划
        return _mock_llm_study_plan(plan_data)

    try:
        # 调用OpenAI API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": "Bearer " + str(settings.OPENAI_API_KEY),
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.DEFAULT_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一个专业的学习规划师，负责制定个性化学习计划。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
            ) as response:
                result = await response.json()
                content = result["choices"][0]["message"]["content"]

                # 解析JSON格式的回复
                try:
                    study_plan = json.loads(content)
                    return study_plan
                except json.JSONDecodeError:
                    # 如果解析失败，使用模拟数据
                    return _mock_llm_study_plan(plan_data)

    except Exception as e:
        print("调用LLM API出错: " + str(e))
        return _mock_llm_study_plan(plan_data)


def _mock_llm_study_plan(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """模拟LLM学习计划（当API调用失败或未配置时使用）"""

    student = plan_data.get("student", {})
    plan_type = plan_data.get("type", "overall")

    if plan_type == "overall":
        duration = plan_data.get("duration", "3个月")
        focus_subjects = plan_data.get("focus_subjects", [])
        if not focus_subjects and "weaknesses" in student:
            focus_subjects = student.get("weaknesses", [])

        # 生成一个总体学习计划
        return {
            "overview": "本计划旨在帮助" + student.get('name', '学生') + "在" + duration + "内实现从" + str(student.get('total_score', '当前分数')) + "到" + str(plan_data.get('target_score', '目标分数')) + "的提升。计划将重点关注" + (', '.join(focus_subjects) if focus_subjects else '全面能力') + "的提高，同时巩固已有优势科目。通过科学规划、阶段目标设定和有效反馈机制，确保学习效果最大化。",
            "weekly_schedule": {
                "第一周": "诊断评估和目标设定",
                "第二周": "基础知识夯实",
                "第三周": "重点难点突破",
                "第四周": "模拟测试与调整",
                "第五周至第八周": "系统学习与专项训练",
                "第九周至第十二周": "综合提升与冲刺",
            },
            "goals": [
                "总分提升至少30分",
                f"重点科目{', '.join(focus_subjects[:2]) if focus_subjects else '薄弱学科'}提高至少20%",
                "掌握各科核心考点和解题技巧",
                "建立高效学习方法和习惯",
                "增强考试心理素质和应试能力",
            ],
            "learning_resources": [
                {"name": "五三高考复习资料", "type": "教材", "priority": "高"},
                {"name": "中国大学MOOC平台", "type": "在线课程", "priority": "中"},
                {"name": "猿辅导App", "type": "移动应用", "priority": "中"},
                {"name": "历年高考真题集", "type": "练习题", "priority": "高"},
            ],
            "recommended_materials": [
                {"subject": "数学", "materials": ["《高考数学一本通》", "《数学解题方法与技巧》"]},
                {"subject": "英语", "materials": ["《高考英语词汇手册》", "《英语听力特训》"]},
                {"subject": "物理", "materials": ["《物理考点精讲》", "《物理实验与解题》"]},
            ],
            "milestones": [
                {"week": 4, "target": "完成基础知识梳理，各科成绩稳步提升"},
                {"week": 8, "target": "关键考点掌握率80%以上，模拟考试成绩提升15%"},
                {"week": 12, "target": "达到目标分数，具备应对各类题型的能力"},
            ],
        }

    elif plan_type == "weekly":
        focus_subjects = plan_data.get("focus_subjects", [])

        # 生成一周的详细计划
        return {
            "周一": {
                "morning": f"{focus_subjects[0] if focus_subjects else '主科1'}系统复习",
                "afternoon": f"{focus_subjects[1] if len(focus_subjects) > 1 else '主科2'}重点突破",
                "evening": "自主复习与作业完成",
            },
            "周二": {
                "morning": f"{focus_subjects[1] if len(focus_subjects) > 1 else '主科2'}系统复习",
                "afternoon": f"{focus_subjects[0] if focus_subjects else '主科1'}重点突破",
                "evening": "错题集整理与复习",
            },
            "周三": {
                "morning": "英语阅读与听力训练",
                "afternoon": "数学专项练习",
                "evening": "英语词汇记忆与巩固",
            },
            "周四": {
                "morning": "理科综合复习",
                "afternoon": "语文写作与阅读训练",
                "evening": "自主学习与知识点整理",
            },
            "周五": {"morning": "模拟测试", "afternoon": "测试结果分析与弱点针对", "evening": "放松与适度休息"},
            "周六": {"morning": "薄弱科目强化训练", "afternoon": "综合能力提升", "evening": "家庭作业与预习"},
            "周日": {"morning": "一周内容复习巩固", "afternoon": "休息与调整", "evening": "下周计划制定"},
            "daily_tasks": {
                "morning_routine": "7:00起床，7:30-8:00复习前一天知识点",
                "breaks": "每45分钟学习后休息10分钟",
                "evening_reflection": "每天睡前15分钟反思当天学习情况",
            },
            "learning_resources": [
                {"name": "学科教材", "usage": "系统学习"},
                {"name": "错题集", "usage": "针对性复习"},
                {"name": "线上课程", "usage": "辅助学习"},
            ],
        }

    else:  # subject plan
        subject = plan_data.get("subject", "未指定学科")
        duration = plan_data.get("duration", "1个月")

        # 针对特定学科的提升计划
        if subject == "数学":
            return {
                "overview": f"本计划针对{student.get('name', '学生')}的数学学习制定，通过{duration}的系统学习，重点提升解题能力和应试技巧，突破数学学习瓶颈。",
                "goals": [
                    "掌握函数、导数等核心概念",
                    "提高解析几何和立体几何能力",
                    "熟练掌握数列和不等式解题技巧",
                    "通过模拟训练提升应试能力",
                ],
                "learning_resources": [
                    {"name": "《数学解题方法与技巧》", "type": "教材", "priority": "高"},
                    {"name": "《高考数学真题解析》", "type": "练习题", "priority": "高"},
                    {"name": "数学思维导图", "type": "辅助材料", "priority": "中"},
                ],
                "milestones": [
                    {"week": 1, "target": "完成基础知识梳理，掌握核心概念"},
                    {"week": 2, "target": "解决重点难点问题，提升解题速度"},
                    {"week": 4, "target": "通过模拟测试，成绩提升至少15分"},
                ],
            }
        elif subject == "英语":
            return {
                "overview": f"本计划针对{student.get('name', '学生')}的英语学习制定，通过{duration}的系统学习，重点提升词汇量、阅读理解和写作能力。",
                "goals": ["扩充词汇量至少500个核心词", "提高阅读理解速度和准确率", "掌握高分作文写作技巧", "提升听力理解能力"],
                "learning_resources": [
                    {"name": "《高频词汇手册》", "type": "词汇", "priority": "高"},
                    {"name": "《英语阅读理解专项训练》", "type": "阅读", "priority": "高"},
                    {"name": "每日英语听力App", "type": "听力", "priority": "中"},
                    {"name": "《高分作文模板》", "type": "写作", "priority": "高"},
                ],
                "milestones": [
                    {"week": 1, "target": "掌握200个核心词汇，完成基础阅读训练"},
                    {"week": 2, "target": "提高阅读速度，开始写作训练"},
                    {"week": 4, "target": "通过模拟测试，成绩提升至少10分"},
                ],
            }
        else:
            return {
                "overview": f"本计划针对{student.get('name', '学生')}的{subject}学习制定，通过{duration}的系统学习，提升整体能力和应试水平。",
                "goals": ["掌握核心知识点和解题方法", "提高专项能力和应用能力", "通过模拟训练提升应试能力", "建立系统的知识框架"],
                "learning_resources": [
                    {"name": f"{subject}专项训练教材", "type": "教材", "priority": "高"},
                    {"name": f"{subject}真题解析", "type": "练习题", "priority": "高"},
                    {"name": f"{subject}知识点总结", "type": "辅助材料", "priority": "中"},
                ],
                "milestones": [
                    {"week": 1, "target": "完成基础知识梳理，掌握核心概念"},
                    {"week": 2, "target": "解决重点难点问题，提升解题能力"},
                    {"week": 4, "target": "通过模拟测试，成绩有明显提升"},
                ],
            }
