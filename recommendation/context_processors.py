#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

def date_context(request):
    """
    为模板添加当前日期相关的上下文变量
    """
    today = datetime.date.today()
    
    # 计算未来三年的考研年份
    current_year = today.year
    if today.month >= 8:  # 8月以后准备最近一次考研可能较紧张，因此从下一年开始计算
        exam_years = [current_year + 1, current_year + 2, current_year + 3]
    else:
        exam_years = [current_year, current_year + 1, current_year + 2]
    
    return {
        'today': today,
        'current_year': current_year,
        'exam_years': exam_years,
    }