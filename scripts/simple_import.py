#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单导入脚本 - 从Excel直接导入院校信息到数据库
"""

import os
import sys
import django
import pandas as pd
import traceback

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'haolaoshi_django.settings')
django.setup()

# 导入Django模型
from recommendation.models import School, Major

def import_excel_data(excel_file):
    """从Excel导入数据"""
    if not os.path.exists(excel_file):
        print(f"错误: 文件不存在 - {excel_file}")
        return False
    
    print(f"正在读取Excel文件: {excel_file}")
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_file)
        print(f"成功读取数据，共{len(df)}行")
        print("数据列名:", df.columns.tolist())

        # 统计导入前数量
        schools_before = School.objects.count()
        majors_before = Major.objects.count()
        print(f"导入前: {schools_before}所学校, {majors_before}个专业")
        
        # 计数器
        new_schools = 0
        new_majors = 0
        
        # 处理每一行数据
        for idx, row in df.iterrows():
            try:
                # 识别列名
                school_col = None
                for col in df.columns:
                    if '学校' in col or '院校' in col or '大学' in col:
                        school_col = col
                        break
                
                if not school_col:
                    print("警告: 找不到学校列，尝试使用第一列")
                    school_col = df.columns[0]
                
                # 获取学校名称
                school_name = row.get(school_col, "")
                if pd.isna(school_name) or not str(school_name).strip():
                    continue
                
                school_name = str(school_name).strip()
                print(f"处理学校: {school_name}")
                
                # 找985/211/双一流信息
                is_985 = False
                is_211 = False
                is_double_first_class = False
                
                for col in df.columns:
                    if '985' in col and pd.notna(row.get(col)):
                        val = row.get(col)
                        is_985 = str(val).lower() in ['是', 'yes', 'true', '1', 'y', 't', '√']
                    
                    if '211' in col and pd.notna(row.get(col)):
                        val = row.get(col)
                        is_211 = str(val).lower() in ['是', 'yes', 'true', '1', 'y', 't', '√']
                    
                    if '双一流' in col and pd.notna(row.get(col)):
                        val = row.get(col)
                        is_double_first_class = str(val).lower() in ['是', 'yes', 'true', '1', 'y', 't', '√']
                
                # 寻找专业列和地区列
                major_col = None
                province_col = None
                
                for col in df.columns:
                    if '专业' in col:
                        major_col = col
                    if '省份' in col or '地区' in col:
                        province_col = col
                
                # 获取地区信息
                province = None
                if province_col and pd.notna(row.get(province_col)):
                    province = str(row.get(province_col)).strip()
                
                # 创建或更新学校
                school, created = School.objects.get_or_create(name=school_name)
                if created:
                    new_schools += 1
                    # 填充学校信息
                    school.is_985 = is_985
                    school.is_211 = is_211
                    school.is_double_first_class = is_double_first_class
                    if province:
                        school.province = province
                    school.save()
                
                # 处理专业信息
                if major_col and pd.notna(row.get(major_col)):
                    major_name = str(row.get(major_col)).strip()
                    if major_name:
                        major, created = Major.objects.get_or_create(name=major_name)
                        if created:
                            new_majors += 1
                        
                        # 将专业与学校关联
                        if major not in school.majors.all():
                            school.majors.add(major)
                
                # 每100行显示一次进度
                if (idx + 1) % 100 == 0:
                    print(f"已处理 {idx + 1} 行...")
            
            except Exception as e:
                print(f"处理第{idx+1}行时出错: {str(e)}")
        
        # 统计导入后数量
        schools_after = School.objects.count()
        majors_after = Major.objects.count()
        
        print("\n导入完成!")
        print(f"导入前: {schools_before}所学校, {majors_before}个专业")
        print(f"导入后: {schools_after}所学校, {majors_after}个专业")
        print(f"新增: {new_schools}所学校, {new_majors}个专业")
        
        return True
    
    except Exception as e:
        print(f"导入过程中出错: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python simple_import.py <Excel文件路径>")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    import_excel_data(excel_file)