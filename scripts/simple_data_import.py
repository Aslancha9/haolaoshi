#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单的Excel数据导入脚本，不依赖Django ORM
"""

import os
import sys
import pandas as pd
import sqlite3
import time

# 设置文件路径
excel_file = "data/数据.xlsx"
if len(sys.argv) > 1:
    excel_file = sys.argv[1]

# 确保文件存在
if not os.path.exists(excel_file):
    print(f"错误: 文件不存在 - {excel_file}")
    sys.exit(1)

# 连接SQLite数据库
print("正在连接数据库...")
try:
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    print("数据库连接成功")
except Exception as e:
    print(f"连接数据库出错: {e}")
    sys.exit(1)

# 检查数据表是否存在
print("检查数据表...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recommendation_school'")
if not cursor.fetchone():
    print("错误: recommendation_school表不存在")
    sys.exit(1)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recommendation_major'")
if not cursor.fetchone():
    print("错误: recommendation_major表不存在")
    sys.exit(1)

# 读取Excel文件
print(f"正在读取Excel文件: {excel_file}")
try:
    df = pd.read_excel(excel_file)
    print(f"成功读取数据，共{len(df)}行")
    print("数据列名:", df.columns.tolist())
except Exception as e:
    print(f"读取Excel文件出错: {e}")
    sys.exit(1)

# 统计导入前数量
cursor.execute("SELECT COUNT(*) FROM recommendation_school")
schools_before = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM recommendation_major")
majors_before = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM recommendation_scoreline")
score_lines_before = cursor.fetchone()[0]

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

# 为了提高性能，批处理插入
start_time = time.time()
batch_size = 100
processed = 0

try:
    conn.execute("BEGIN TRANSACTION")
    
    # 处理每一行数据
    for idx, row in df.iterrows():
        try:
            # 每100行提交一次事务并显示进度
            if idx > 0 and idx % batch_size == 0:
                conn.execute("COMMIT")
                conn.execute("BEGIN TRANSACTION")
                elapsed = time.time() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                estimated = (len(df) - idx) / rate if rate > 0 else "未知"
                print(f"已处理 {idx}/{len(df)} 行 ({idx/len(df)*100:.1f}%)... 速率: {rate:.1f}行/秒, 预计剩余时间: {estimated:.1f}秒")
            
            # 获取学校名称
            school_name = row.get(school_col, "")
            if pd.isna(school_name) or not str(school_name).strip():
                continue
            
            school_name = str(school_name).strip()
            
            # 提取985/211/双一流信息
            is_985 = False
            is_211 = False
            is_double_first_class = False
            province = None
            city = None
            
            for col in df.columns:
                if '985' in col and not pd.isna(row.get(col)):
                    val = str(row.get(col)).strip().lower()
                    is_985 = val in ['是', 'yes', 'true', '1', 'y', 't', '√', 'x']
                
                if '211' in col and not pd.isna(row.get(col)):
                    val = str(row.get(col)).strip().lower()
                    is_211 = val in ['是', 'yes', 'true', '1', 'y', 't', '√', 'x']
                
                if '双一流' in col and not pd.isna(row.get(col)):
                    val = str(row.get(col)).strip().lower()
                    is_double_first_class = val in ['是', 'yes', 'true', '1', 'y', 't', '√', 'x']
                
                if '地区' in col or '省份' in col or '所在地' in col:
                    if not pd.isna(row.get(col)):
                        province = str(row.get(col)).strip()
            
            # 如果没有找到省份，设置默认值
            if not province:
                province = "未知"
            
            # 查询学校是否已存在
            cursor.execute("SELECT id FROM recommendation_school WHERE name = ?", (school_name,))
            school_result = cursor.fetchone()
            
            if school_result:
                # 更新现有学校
                school_id = school_result[0]
                cursor.execute("""
                    UPDATE recommendation_school
                    SET is_985 = ?, is_211 = ?, is_double_first_class = ?, province = ?
                    WHERE id = ?
                """, (is_985, is_211, is_double_first_class, province, school_id))
                updated_schools += 1
            else:
                # 创建新学校
                cursor.execute("""
                    INSERT INTO recommendation_school (name, province, city, is_985, is_211, is_double_first_class)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (school_name, province, city or "未知", is_985, is_211, is_double_first_class))
                school_id = cursor.lastrowid
                new_schools += 1
            
            # 查找专业列
            major_col = None
            for col in df.columns:
                if '专业' in col:
                    major_col = col
                    break
            
            if major_col and not pd.isna(row.get(major_col)):
                major_name = str(row.get(major_col)).strip()
                if major_name:
                    # 检查专业是否已存在
                    cursor.execute("SELECT id FROM recommendation_major WHERE name = ?", (major_name,))
                    major_result = cursor.fetchone()
                    
                    if major_result:
                        major_id = major_result[0]
                    else:
                        # 创建新专业
                        cursor.execute("INSERT INTO recommendation_major (name) VALUES (?)", (major_name,))
                        major_id = cursor.lastrowid
                        new_majors += 1
                    
                    # 关联学校和专业
                    # 先检查是否已关联
                    cursor.execute("""
                        SELECT 1 FROM recommendation_school_majors WHERE school_id = ? AND major_id = ?
                    """, (school_id, major_id))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO recommendation_school_majors (school_id, major_id)
                            VALUES (?, ?)
                        """, (school_id, major_id))
                    
                    # 查找分数线信息
                    score_value = None
                    year_value = 2025  # 默认年份
                    
                    # 查找分数线信息
                    for col_name in df.columns:
                        if ('分数线' in col_name or '总分' in col_name) and not pd.isna(row.get(col_name)):
                            try:
                                score_value = int(float(row.get(col_name)))
                                break
                            except (ValueError, TypeError):
                                pass
                        
                        if '年份' in col_name and not pd.isna(row.get(col_name)):
                            try:
                                year_value = int(row.get(col_name))
                            except (ValueError, TypeError):
                                pass
                    
                    # 创建分数线记录
                    if score_value is not None:
                        cursor.execute("""
                            SELECT id FROM recommendation_scoreline 
                            WHERE school_id = ? AND major_id = ? AND year = ? AND province = ?
                        """, (school_id, major_id, year_value, province))
                        
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT INTO recommendation_scoreline 
                                (school_id, major_id, year, province, score)
                                VALUES (?, ?, ?, ?, ?)
                            """, (school_id, major_id, year_value, province, score_value))
                            new_score_lines += 1
            
            processed += 1
            
        except Exception as e:
            print(f"处理第{idx+1}行时出错: {e}")
    
    # 提交最后一批
    conn.execute("COMMIT")
    
except Exception as e:
    conn.execute("ROLLBACK")
    print(f"导入过程中出错，已回滚事务: {e}")

# 统计导入后数量
cursor.execute("SELECT COUNT(*) FROM recommendation_school")
schools_after = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM recommendation_major")
majors_after = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM recommendation_scoreline")
score_lines_after = cursor.fetchone()[0]

# 关闭数据库连接
conn.close()

# 计算耗时
total_time = time.time() - start_time

print("\n导入完成!")
print(f"总耗时: {total_time:.2f}秒, 平均速度: {processed/total_time:.2f}行/秒")
print(f"导入前: {schools_before}所学校, {majors_before}个专业, {score_lines_before}条分数线")
print(f"导入后: {schools_after}所学校, {majors_after}个专业, {score_lines_after}条分数线")
print(f"新增: {new_schools}所学校, {new_majors}个专业, {new_score_lines}条分数线")
print(f"更新: {updated_schools}所学校")

print("\n导入过程完成！")