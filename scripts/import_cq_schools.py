#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
导入重庆地区院校数据
"""

import os
import sys
import django
import pandas as pd
from django.db import transaction

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'haolaoshi_django.settings')
django.setup()

# 导入模型
from recommendation.models import School, Major

def import_cq_schools(file_path):
    """
    导入重庆地区院校数据
    
    参数:
        file_path: Excel文件路径
    """
    print(f"正在从 {file_path} 导入重庆地区院校数据...")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        print(f"成功读取Excel文件，共有{len(df)}条记录")
        
        # 打印列名，以便检查
        print("Excel文件列名:", df.columns.tolist())
        
        # 显示前5行数据进行检查
        print("\n前5行数据:")
        print(df.head())
        
        # 记录导入的学校和专业
        schools_added = 0
        schools_updated = 0
        majors_added = 0
        
        # 创建学校名称到School对象的映射
        school_map = {}
        
        # 开始批量处理
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # 根据Excel文件的实际结构获取数据
                    school_name = row['院校']
                    region = row['地区']
                    college_name = row['学院名称']
                    major_code = row['专业代码']
                    major_name = row['专业名称']
                    score_500 = row['总分（满分500）']
                    score_300 = row['总分（满分300）']
                    
                    # 设置学校基本信息
                    province = '重庆'  # 默认为重庆
                    city = '重庆'  # 默认为重庆
                    
                    # 学校类型判断（根据学校名称判断）
                    is_985 = False
                    is_211 = False
                    is_double_first_class = False
                    school_type = ""
                    
                    # 根据学校名称确定学校类型
                    if '重庆大学' == school_name:
                        is_985 = True
                        is_211 = True
                        is_double_first_class = True
                        school_type = '综合'
                    elif '西南大学' == school_name:
                        is_211 = True
                        is_double_first_class = True
                        school_type = '综合'
                    elif '重庆医科大学' == school_name:
                        is_double_first_class = True
                        school_type = '医药'
                    elif '西南政法大学' == school_name:
                        is_double_first_class = True
                        school_type = '政法'
                    elif '重庆师范大学' == school_name:
                        school_type = '师范'
                    elif '重庆邮电大学' == school_name:
                        school_type = '工科'
                    elif '重庆交通大学' == school_name:
                        school_type = '工科'
                    elif '四川美术学院' == school_name:
                        school_type = '艺术'
                    elif '重庆工商大学' == school_name:
                        school_type = '财经'
                    elif '重庆理工大学' == school_name:
                        school_type = '工科'
                    
                    # 如果已经处理过该学校，则直接使用已有对象
                    if school_name in school_map:
                        school = school_map[school_name]
                    else:
                        # 尝试查找现有学校，若存在则更新，不存在则创建
                        school, created = School.objects.update_or_create(
                            name=school_name,
                            defaults={
                                'code': '',  # 暂无学校代码
                                'province': province,
                                'city': city,
                                'level': '一流学科' if is_double_first_class else '普通本科',
                                'type': school_type,
                                'is_985': is_985,
                                'is_211': is_211,
                                'is_double_first_class': is_double_first_class,
                                'description': f"{school_name}位于{province}{city}，{college_name}开设有{major_name}等专业。",
                                'website': '',  # 暂无官网信息
                            }
                        )
                        
                        # 将学校添加到映射中
                        school_map[school_name] = school
                        
                        if created:
                            schools_added += 1
                            print(f"添加学校: {school_name}")
                        else:
                            schools_updated += 1
                            print(f"更新学校: {school_name}")
                    
                    # 处理专业信息
                    if major_name:
                        major, created = Major.objects.get_or_create(
                            name=major_name,
                            defaults={
                                'code': major_code if major_code else '',
                                'category': college_name,  # 使用学院名称作为学科门类
                                'description': f"{major_name}，开设于{school_name}{college_name}"
                            }
                        )
                        
                        if created:
                            majors_added += 1
                            print(f"添加专业: {major_name}")
                        
                        # 将专业与学校关联
                        if not hasattr(school, 'majors'):
                            # 如果school对象没有majors属性，可能需要先保存
                            print(f"尝试为学校添加专业: {school_name} -> {major_name}")
                        else:
                            try:
                                if not school.majors.filter(id=major.id).exists():
                                    school.majors.add(major)
                                    print(f"关联专业到学校: {major_name} -> {school_name}")
                            except Exception as e:
                                print(f"关联专业时出错: {str(e)}")
                                
                    # 添加分数线信息
                    try:
                        if not pd.isna(score_500) and score_500 != '/':
                            from recommendation.models import ScoreLine
                            # 添加满分500分的分数线
                            ScoreLine.objects.update_or_create(
                                school=school,
                                major=major if major_name else None,
                                year=2025,  # 使用当前年份
                                province=province,
                                defaults={
                                    'score': int(score_500),
                                    'batch': '考研',
                                }
                            )
                            print(f"添加500分制分数线: {school_name}-{major_name if major_name else '所有专业'} {score_500}分")
                    except Exception as e:
                        print(f"添加分数线时出错: {str(e)}")
                
                except Exception as e:
                    print(f"处理第{index+1}行数据时出错: {str(e)}")
        
        print(f"\n导入完成！新增学校: {schools_added}，更新学校: {schools_updated}，新增专业: {majors_added}")
    
    except Exception as e:
        print(f"导入过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "D:\\python\\data\\cqschools.xlsx"
    
    import_cq_schools(file_path)