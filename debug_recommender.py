#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "haolaoshi_django.settings")
django.setup()

# 导入所需模型和类
from recommendation.models import Student, School, Recommendation
from recommendation.recommender import SchoolRecommender
import pprint

def debug_recommendation():
    """调试推荐功能"""
    # 获取所有学生
    students = Student.objects.filter(education_path='考研')
    
    if not students.exists():
        print("没有找到考研学生数据，创建测试学生...")
        # 创建测试学生
        student = Student(
            name="测试学生",
            gender="男",
            province="北京",
            education_path='考研',
            current_school="测试大学",
            current_major="计算机科学",
            gpa=3.5,
            gpa_ranking="前15%",
            english_level="六级",
            math_level="较好",
            career_direction="企业就业",
            academic_preference=False,
            target_cities="北京,上海,成都",
            estimated_score=350,
            strategy_preference="均衡",
            academic_status="未毕业",
            exam_year=2024,
            study_mode="全日制",
            target_major_category="计算机科学",
            target_type="985"
        )
        student.save()
    else:
        student = students.first()
    
    print(f"测试学生: {student.name}, ID: {student.id}")
    
    # 检查是否有足够的学校数据
    schools_count = School.objects.count()
    print(f"数据库中学校总数: {schools_count}")
    
    if schools_count < 9:
        print("警告：学校数量不足，可能无法生成有效的推荐结果")
        
        # 添加一些测试学校数据
        school_data = [
            {"name": "测试985大学", "province": "北京", "city": "北京", "is_985": True, "is_211": True, "is_double_first_class": True},
            {"name": "测试211大学", "province": "上海", "city": "上海", "is_985": False, "is_211": True, "is_double_first_class": True},
            {"name": "测试双一流大学", "province": "广东", "city": "广州", "is_985": False, "is_211": False, "is_double_first_class": True},
            {"name": "测试普通大学1", "province": "四川", "city": "成都", "is_985": False, "is_211": False, "is_double_first_class": False},
            {"name": "测试普通大学2", "province": "浙江", "city": "杭州", "is_985": False, "is_211": False, "is_double_first_class": False},
            {"name": "测试普通大学3", "province": "江苏", "city": "南京", "is_985": False, "is_211": False, "is_double_first_class": False},
        ]
        
        for data in school_data:
            if not School.objects.filter(name=data["name"]).exists():
                school = School(**data)
                school.save()
                print(f"创建测试学校: {school.name}")
    
    # 测试推荐引擎
    recommender = SchoolRecommender()
    
    # 测试不同策略
    strategies = ['balanced', 'aggressive', 'conservative']
    for strategy in strategies:
        print(f"\n测试策略: {strategy}")
        result = recommender.recommend_schools(
            student_id=student.id,
            strategy=strategy,
            num_recommendations=9
        )
        
        if result['status'] == 'success':
            recommendations = result['recommendations']
            
            # 按类型统计
            safety = [r for r in recommendations if r['category'] == 'safety']
            match = [r for r in recommendations if r['category'] == 'match']
            challenge = [r for r in recommendations if r['category'] == 'challenge']
            
            print(f"推荐总数: {len(recommendations)}")
            print(f"保底院校: {len(safety)} - {[s['school'].name for s in safety]}")
            print(f"匹配院校: {len(match)} - {[s['school'].name for s in match]}")
            print(f"冲刺院校: {len(challenge)} - {[s['school'].name for s in challenge]}")
            
            # 打印第一个推荐的详细信息
            if recommendations:
                print("\n第一个推荐的详细信息:")
                first_rec = recommendations[0]
                for key, value in first_rec.items():
                    if key == 'school':
                        print(f"school: {value.name}")
                    elif key == 'recommended_majors':
                        print(f"recommended_majors: {[m.name if m else 'None' for m in value]}")
                    elif key == 'dimension_scores':
                        print("dimension_scores:")
                        for score_key, score_val in value.items():
                            print(f"  {score_key}: {score_val}")
                    else:
                        print(f"{key}: {value}")
        else:
            print(f"推荐失败: {result['message']}")
    
    # 检查数据库中的推荐记录
    recs = Recommendation.objects.filter(student=student)
    print(f"\n数据库中的推荐记录数: {recs.count()}")
    rec_types = {}
    for rec in recs:
        rec_type = rec.recommendation_type
        if rec_type not in rec_types:
            rec_types[rec_type] = 0
        rec_types[rec_type] += 1
    
    print("推荐类型统计:")
    for rec_type, count in rec_types.items():
        print(f"  {rec_type}: {count}个")

if __name__ == "__main__":
    debug_recommendation()