#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
从Excel文件导入考研专业复试分数线数据
"""

import os
import sys
import django
import pandas as pd
from datetime import datetime

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'haolaoshi_django.settings')
django.setup()

# 导入Django模型
from recommendation.models import School, Major, ScoreLine
from django.db import transaction

def import_scorelines_from_excel(excel_file):
    """从Excel文件导入专业复试分数线数据"""
    if not os.path.exists(excel_file):
        print(f"错误: 文件不存在 - {excel_file}")
        return False
    
    try:
        # 读取Excel文件
        print(f"正在读取Excel文件: {excel_file}")
        df = pd.read_excel(excel_file)
        
        # 显示数据基本信息
        print(f"读取到 {len(df)} 条数据")
        print("数据列名:", df.columns.tolist())
        
        # 统计导入前的数据
        schools_before = School.objects.count()
        majors_before = Major.objects.count()
        scorelines_before = ScoreLine.objects.count()
        
        print(f"导入前数据库中有:")
        print(f"- {schools_before} 所学校")
        print(f"- {majors_before} 个专业")
        print(f"- {scorelines_before} 条分数线记录")
        
        # 导入数据
        schools_created = 0
        majors_created = 0
        scorelines_created = 0
        skipped_count = 0
        
        # 查找与表头相关的列
        school_col = next((col for col in df.columns if '学校' in col or '院校' in col or '大学' in col), None)
        major_col = next((col for col in df.columns if '专业' in col), None)
        score_col = next((col for col in df.columns if '分数线' in col or '分数' in col), None)
        province_col = next((col for col in df.columns if '省份' in col or '地区' in col), None)
        year_col = next((col for col in df.columns if '年份' in col or '年度' in col), None)
        is_985_col = next((col for col in df.columns if '985' in col), None)
        is_211_col = next((col for col in df.columns if '211' in col), None)
        is_double_first_class_col = next((col for col in df.columns if '双一流' in col), None)
        
        print("\n找到的列名映射:")
        print(f"学校列: {school_col}")
        print(f"专业列: {major_col}")
        print(f"分数线列: {score_col}")
        print(f"省份列: {province_col}")
        print(f"年份列: {year_col}")
        print(f"985列: {is_985_col}")
        print(f"211列: {is_211_col}")
        print(f"双一流列: {is_double_first_class_col}")
        
        if not school_col or not major_col:
            print("错误: 找不到学校或专业列")
            return False
        
        # 设置默认年份为2025年
        default_year = 2025
        
        # 批量处理以提高性能
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # 提取基本数据
                    school_name = str(row.get(school_col, '')).strip()
                    if not school_name:
                        print(f"警告: 行 {index+2} 跳过没有学校名称的行")
                        skipped_count += 1
                        continue
                    
                    major_name = str(row.get(major_col, '')).strip() if major_col else None
                    if not major_name:
                        print(f"警告: 行 {index+2} 跳过没有专业名称的行")
                        skipped_count += 1
                        continue
                    
                    # 获取省份信息
                    province = str(row.get(province_col, '未知')).strip() if province_col else '未知'
                    
                    # 获取年份信息
                    if year_col and pd.notna(row.get(year_col)):
                        year_value = row.get(year_col)
                        # 处理不同类型的年份数据
                        if isinstance(year_value, (int, float)):
                            year = int(year_value)
                        elif isinstance(year_value, str):
                            # 尝试从字符串中提取年份
                            year_match = next((int(s) for s in year_value.split() if s.isdigit()), default_year)
                            year = year_match
                        else:
                            year = default_year
                    else:
                        year = default_year
                    
                    # 处理分数线数据
                    if score_col and pd.notna(row.get(score_col)):
                        try:
                            score = int(float(row.get(score_col)))
                        except (ValueError, TypeError):
                            score_str = str(row.get(score_col)).strip()
                            # 尝试从字符串中提取数字
                            import re
                            score_match = re.search(r'\d+', score_str)
                            if score_match:
                                score = int(score_match.group())
                            else:
                                print(f"警告: 行 {index+2} 无法解析分数: {score_str}")
                                score = 0
                    else:
                        score = 0
                    
                    # 处理学校信息
                    # 检查是否是985/211/双一流
                    is_985 = False
                    if is_985_col and pd.notna(row.get(is_985_col)):
                        value = row.get(is_985_col)
                        is_985 = str(value).lower() in ['是', 'yes', 'true', '1', 'y', 't']
                    
                    is_211 = False
                    if is_211_col and pd.notna(row.get(is_211_col)):
                        value = row.get(is_211_col)
                        is_211 = str(value).lower() in ['是', 'yes', 'true', '1', 'y', 't']
                    
                    is_double_first_class = False
                    if is_double_first_class_col and pd.notna(row.get(is_double_first_class_col)):
                        value = row.get(is_double_first_class_col)
                        is_double_first_class = str(value).lower() in ['是', 'yes', 'true', '1', 'y', 't']
                    
                    # 创建或获取学校
                    school, school_created = School.objects.get_or_create(name=school_name)
                    if school_created:
                        schools_created += 1
                        school.province = province
                        school.is_985 = is_985
                        school.is_211 = is_211
                        school.is_double_first_class = is_double_first_class
                        school.save()
                    
                    # 创建或获取专业
                    major, major_created = Major.objects.get_or_create(name=major_name)
                    if major_created:
                        majors_created += 1
                    
                    # 创建分数线记录
                    scoreline, created = ScoreLine.objects.get_or_create(
                        school=school,
                        major=major,
                        year=year,
                        province=province,
                        defaults={
                            'score': score
                        }
                    )
                    
                    if created:
                        scorelines_created += 1
                    else:
                        # 更新已有的分数线
                        if score > 0:
                            scoreline.score = score
                            scoreline.save()
                    
                    # 处理进度
                    if (index + 1) % 100 == 0:
                        print(f"已处理 {index + 1} 条记录...")
                
                except Exception as e:
                    print(f"处理行 {index+2} 时出错: {str(e)}")
                    skipped_count += 1
        
        # 统计导入结果
        schools_after = School.objects.count()
        majors_after = Major.objects.count()
        scorelines_after = ScoreLine.objects.count()
        
        print("\n导入完成!")
        print(f"导入前:")
        print(f"- {schools_before} 所学校")
        print(f"- {majors_before} 个专业")
        print(f"- {scorelines_before} 条分数线记录")
        
        print(f"\n导入后:")
        print(f"- {schools_after} 所学校 (新增 {schools_created} 所)")
        print(f"- {majors_after} 个专业 (新增 {majors_created} 个)")
        print(f"- {scorelines_after} 条分数线记录 (新增 {scorelines_created} 条)")
        print(f"- 跳过 {skipped_count} 条记录")
        
        return True
        
    except Exception as e:
        print(f"导入过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python import_major_scores.py <Excel文件路径>")
        return
    
    excel_file = sys.argv[1]
    import_scorelines_from_excel(excel_file)

if __name__ == "__main__":
    main()