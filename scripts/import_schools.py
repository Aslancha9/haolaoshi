#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
从Excel文件导入院校数据到数据库
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
from recommendation.models import School, Province, SchoolType

def import_schools_from_excel(excel_file):
    """从Excel文件导入院校数据"""
    if not os.path.exists(excel_file):
        print(f"错误: 文件不存在 - {excel_file}")
        return False
    
    try:
        # 读取Excel文件
        print(f"正在读取Excel文件: {excel_file}")
        df = pd.read_excel(excel_file)
        
        # 显示数据基本信息
        print(f"读取到 {len(df)} 条院校数据")
        print("数据列名:", df.columns.tolist())
        
        # 统计导入前的数据
        schools_before = School.objects.count()
        print(f"导入前数据库中有 {schools_before} 所院校")
        
        # 导入数据
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        
        for _, row in df.iterrows():
            try:
                # 提取基本数据
                name = str(row.get('学校名称', '')).strip()
                if not name:
                    print("警告: 跳过没有名称的行")
                    skipped_count += 1
                    continue
                
                # 检查学校是否已存在
                school, created = School.objects.get_or_create(name=name)
                
                # 更新或创建学校信息
                if created:
                    print(f"创建新学校: {name}")
                    imported_count += 1
                else:
                    print(f"更新学校信息: {name}")
                    updated_count += 1
                
                # 更新基本信息
                if '所在省份' in df.columns and pd.notna(row.get('所在省份')):
                    province_name = str(row.get('所在省份')).strip()
                    province, _ = Province.objects.get_or_create(name=province_name)
                    school.province = province
                
                if '学校类型' in df.columns and pd.notna(row.get('学校类型')):
                    type_name = str(row.get('学校类型')).strip()
                    school_type, _ = SchoolType.objects.get_or_create(name=type_name)
                    school.school_type = school_type
                
                # 更新其他可能的字段
                fields_mapping = {
                    '学校代码': 'code',
                    '学校英文名': 'english_name',
                    '创建时间': 'founded_year',
                    '主管部门': 'authority',
                    '所在城市': 'city',
                    '学校地址': 'address',
                    '学校网址': 'website',
                    '学校简介': 'description',
                    '研究生院': 'has_graduate_school',
                    '博士点数量': 'doctoral_programs_count',
                    '硕士点数量': 'master_programs_count',
                    '院士数量': 'academician_count',
                    '重点学科数': 'key_disciplines_count',
                    '双一流学科数': 'double_first_class_count',
                    '985': 'is_985',
                    '211': 'is_211',
                    '双一流': 'is_double_first_class',
                }
                
                for excel_field, db_field in fields_mapping.items():
                    if excel_field in df.columns and pd.notna(row.get(excel_field)):
                        value = row.get(excel_field)
                        
                        # 特殊处理布尔类型
                        if db_field in ['is_985', 'is_211', 'is_double_first_class', 'has_graduate_school']:
                            if isinstance(value, str):
                                value = value.lower() in ['是', 'yes', 'true', '1', 'y', 't']
                            else:
                                value = bool(value)
                        
                        # 特殊处理日期类型
                        if db_field == 'founded_year' and isinstance(value, str):
                            try:
                                if value.isdigit() and len(value) == 4:
                                    value = int(value)
                                else:
                                    # 尝试解析各种日期格式
                                    date_formats = ['%Y', '%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日', '%Y年']
                                    for fmt in date_formats:
                                        try:
                                            dt = datetime.strptime(value, fmt)
                                            value = dt.year
                                            break
                                        except ValueError:
                                            continue
                            except:
                                # 如果无法解析，保留原始值
                                pass
                        
                        # 设置属性
                        setattr(school, db_field, value)
                
                # 保存学校信息
                school.save()
                
            except Exception as e:
                print(f"导入学校 {row.get('学校名称', '未知')} 时出错: {str(e)}")
                skipped_count += 1
        
        # 统计导入结果
        schools_after = School.objects.count()
        print("\n导入完成!")
        print(f"导入前院校数量: {schools_before}")
        print(f"导入后院校数量: {schools_after}")
        print(f"新增院校: {imported_count}")
        print(f"更新院校: {updated_count}")
        print(f"跳过院校: {skipped_count}")
        
        return True
        
    except Exception as e:
        print(f"导入过程中出错: {str(e)}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python import_schools.py <Excel文件路径>")
        return
    
    excel_file = sys.argv[1]
    import_schools_from_excel(excel_file)

if __name__ == "__main__":
    main()