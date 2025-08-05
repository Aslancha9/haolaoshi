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

def test_recommendation():
    """测试推荐功能"""
    # 确保有学生数据
    students = Student.objects.filter(education_path='考研')
    
    if not students.exists():
        print("没有找到考研学生数据，无法测试")
        return
    
    student = students.first()
    print(f"测试学生: {student.name}")
    
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
        else:
            print(f"推荐失败: {result['message']}")

if __name__ == "__main__":
    test_recommendation()