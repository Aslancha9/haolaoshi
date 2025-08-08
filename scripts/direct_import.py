#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接导入Excel数据到院校库的最简单脚本
"""

import os
import sys
import pandas as pd

# 检查环境设置
print("正在检查环境...")
print(f"当前工作目录: {os.getcwd()}")

# 设置文件路径
excel_file = "data/数据.xlsx"
if len(sys.argv) > 1:
    excel_file = sys.argv[1]

# 确保文件存在
if not os.path.exists(excel_file):
    print(f"错误: 文件不存在 - {excel_file}")
    sys.exit(1)

# 读取Excel文件
try:
    print(f"正在读取Excel文件: {excel_file}")
    df = pd.read_excel(excel_file)
    print(f"成功读取数据，共{len(df)}行")
    print("数据列名:", df.columns.tolist())
except Exception as e:
    print(f"读取Excel文件时出错: {e}")
    sys.exit(1)

# 准备Django环境
try:
    print("正在设置Django环境...")
    import django
    # 确保Django设置被正确加载
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "haolaoshi_django.settings")
    django.setup()
    from recommendation.models import School, Major, ScoreLine
    print("Django环境加载成功")
except Exception as e:
    print(f"加载Django环境时出错: {e}")
    sys.exit(1)

# 统计导入前数量
schools_before = School.objects.count()
majors_before = Major.objects.count()
score_lines_before = ScoreLine.objects.count()
print(f"导入前: {schools_before}所学校, {majors_before}个专业, {score_lines_before}条分数线")

# 计数器
new_schools = 0
new_majors = 0
new_score_lines = 0
updated_schools = 0

# 查找关键列
school_col = None
for col in df.columns:
    if '学校' in col or '院校' in col or '大学' in col:
        school_col = col
        break

if not school_col:
    print("警告: 找不到学校列，尝试使用第一列")
    school_col = df.columns[0]

print(f"使用'{school_col}'作为学校名称列")

# 处理每一行数据
for idx, row in df.iterrows():
    try:
        # 获取学校名称
        school_name = row.get(school_col, "")
        if pd.isna(school_name) or not str(school_name).strip():
            print(f"跳过第{idx+1}行：学校名称为空")
            continue
        
        school_name = str(school_name).strip()
        print(f"处理第{idx+1}行：{school_name}")
        
        # 查找已有数据
        school = None
        try:
            school = School.objects.filter(name=school_name).first()
        except Exception as e:
            print(f"查询学校时出错: {e}")
        
        is_new_school = False
        
        if not school:
            print(f"创建新学校: {school_name}")
            school = School(name=school_name)
            is_new_school = True
        else:
            print(f"更新现有学校: {school_name}")
        
        # 找985/211/双一流信息
        for col in df.columns:
            try:
                if '985' in col and not pd.isna(row.get(col)):
                    val = str(row.get(col)).strip().lower()
                    school.is_985 = val in ['是', 'yes', 'true', '1', 'y', 't', '√', 'x']
                
                if '211' in col and not pd.isna(row.get(col)):
                    val = str(row.get(col)).strip().lower()
                    school.is_211 = val in ['是', 'yes', 'true', '1', 'y', 't', '√', 'x']
                
                if '双一流' in col and not pd.isna(row.get(col)):
                    val = str(row.get(col)).strip().lower()
                    school.is_double_first_class = val in ['是', 'yes', 'true', '1', 'y', 't', '√', 'x']
            except Exception as e:
                print(f"处理学校属性时出错: {e}")
        
        # 寻找省份/城市列
        for col in df.columns:
            try:
                if '省份' in col or '地区' in col:
                    if not pd.isna(row.get(col)):
                        school.province = str(row.get(col)).strip()
                
                if '城市' in col:
                    if not pd.isna(row.get(col)):
                        school.city = str(row.get(col)).strip()
            except Exception as e:
                print(f"处理地区信息时出错: {e}")
        
        # 保存学校
        try:
            school.save()
            if is_new_school:
                new_schools += 1
            else:
                updated_schools += 1
        except Exception as e:
            print(f"保存学校时出错: {e}")
            continue
        
        # 处理专业信息
        try:
            for col in df.columns:
                if '专业' in col and not pd.isna(row.get(col)):
                    major_name = str(row.get(col)).strip()
                    if not major_name:
                        continue
                    
                    print(f"处理专业: {major_name}")
                    major, created = Major.objects.get_or_create(name=major_name)
                    if created:
                        new_majors += 1
                    
                    # 将专业与学校关联
                    if not school.majors.filter(id=major.id).exists():
                        school.majors.add(major)
                    
                    # 查找分数线信息
                    score_value = None
                    year_value = 2025  # 默认年份
                    
                    for col_name in df.columns:
                        if '分数线' in col_name and not pd.isna(row.get(col_name)):
                            try:
                                score_value = float(row.get(col_name))
                            except (ValueError, TypeError):
                                print(f"无法转换分数线: {row.get(col_name)}")
                        
                        if '年份' in col_name and not pd.isna(row.get(col_name)):
                            try:
                                year_value = int(row.get(col_name))
                            except (ValueError, TypeError):
                                print(f"无法转换年份: {row.get(col_name)}")
                    
                    # 创建分数线记录
                    if score_value is not None:
                        print(f"创建分数线记录: {school_name} - {major_name} - {year_value}年 - {score_value}分")
                        score_line, created = ScoreLine.objects.get_or_create(
                            school=school,
                            major=major,
                            year=year_value,
                            province=school.province,
                            defaults={
                                'score': int(score_value),
                            }
                        )
                        if created:
                            new_score_lines += 1
        except Exception as e:
            print(f"处理专业和分数线时出错: {e}")

        # 每10行打印一次进度
        if (idx + 1) % 10 == 0:
            print(f"已处理 {idx + 1}/{len(df)} 行...")
    
    except Exception as e:
        print(f"处理第{idx+1}行时出错: {e}")

# 统计导入后数量
schools_after = School.objects.count()
majors_after = Major.objects.count()
score_lines_after = ScoreLine.objects.count()

print("\n导入完成!")
print(f"导入前: {schools_before}所学校, {majors_before}个专业, {score_lines_before}条分数线")
print(f"导入后: {schools_after}所学校, {majors_after}个专业, {score_lines_after}条分数线")
print(f"新增: {new_schools}所学校, {new_majors}个专业, {new_score_lines}条分数线")
print(f"更新: {updated_schools}所学校")

print("\n导入过程完成！")