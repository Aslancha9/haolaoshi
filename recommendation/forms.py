#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
表单定义
"""

import datetime
from django import forms
from .models import Student, School, Major


def get_default_exam_year():
    """根据当前日期确定默认的考研年份"""
    today = datetime.date.today()
    # 如果当前已过8月，则下次考研年份为明年；否则为今年
    # 考虑准备时间，默认相对充裕的时间
    if today.month >= 8:
        return today.year + 2
    else:
        return today.year + 1

class StudentForm(forms.ModelForm):
    """学生信息表单"""
    
    class Meta:
        model = Student
        fields = [
            'name', 'gender', 'province', 'education_path',
            'total_score', 'chinese_score', 'math_score', 
            'english_score', 'comprehensive_score', 
            'interests', 'career_goals', 'rank',
            'current_school', 'current_major', 'grade_rank', 'academic_status',
            'exam_year', 'study_mode', 'target_major_category', 'target_type',
            'target_cities'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入姓名'}),
            'gender': forms.Select(attrs={'class': 'form-control'}, choices=[('', '请选择'), ('男', '男'), ('女', '女')]),
            'province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '如：北京、上海、四川'}),
            'education_path': forms.Select(attrs={'class': 'form-control'}),
            
            # 考研学生特有字段
            'current_school': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入您的就读院校'}),
            'current_major': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入您的就读专业'}),
            'grade_rank': forms.Select(attrs={'class': 'form-control'}),
            'academic_status': forms.Select(attrs={'class': 'form-control'}),
            'exam_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '计划参加哪一年的考研，如：2025'}),
            'study_mode': forms.Select(attrs={'class': 'form-control'}),
            'target_major_category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '目标专业，如：计算机科学、金融学等'}),
            'target_type': forms.Select(attrs={'class': 'form-control'}),
            'target_cities': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '目标城市，如：北京、上海等'}),
            
            # 常规字段
            'total_score': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '请输入总分'}),
            'chinese_score': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '请输入语文分数'}),
            'math_score': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '请输入数学分数'}),
            'english_score': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '请输入英语分数'}),
            'comprehensive_score': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '请输入综合分数'}),
            'interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入您的兴趣爱好，如：计算机、文学、经济等'}),
            'career_goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入您的职业规划'}),
            'rank': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '如果知道位次请填写'}),
        }

class RecommendationForm(forms.Form):
    """推荐设置表单"""
    
    STRATEGY_CHOICES = [
        ('balanced', '平衡策略'),
        ('aggressive', '激进策略 (偏向冲刺院校)'),
        ('conservative', '保守策略 (偏向保底院校)'),
    ]
    
    strategy = forms.ChoiceField(
        label='推荐策略',
        choices=STRATEGY_CHOICES,
        initial='balanced',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    num_recommendations = forms.IntegerField(
        label='推荐数量',
        initial=9,
        min_value=3,
        max_value=15,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class AIRecommendationForm(forms.Form):
    """AI大数据择校表单"""
    
    ACADEMIC_STATUS_CHOICES = Student.ACADEMIC_STATUS_CHOICES
    GRADE_RANK_CHOICES = Student.GRADE_RANK_CHOICES
    STUDY_MODE_CHOICES = Student.STUDY_MODE_CHOICES
    TARGET_TYPE_CHOICES = Student.TARGET_TYPE_CHOICES
    CAREER_GOAL_CHOICES = Student.CAREER_GOAL_CHOICES
    ECONOMIC_CONDITION_CHOICES = Student.ECONOMIC_CONDITION_CHOICES
    STRATEGY_PREFERENCE_CHOICES = Student.STRATEGY_PREFERENCE_CHOICES
    MATH_LEVEL_CHOICES = [('较好', '较好'), ('一般', '一般'), ('较差', '较差')]
    
    # 基本信息
    name = forms.CharField(
        label='姓名',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入姓名'})
    )
    
    gender = forms.ChoiceField(
        label='性别',
        choices=[('', '请选择'), ('男', '男'), ('女', '女')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    province = forms.CharField(
        label='所在省份',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '如：北京、上海、四川'})
    )
    
    # 1. 用户画像
    current_school = forms.CharField(
        label='就读院校',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入您的就读院校'})
    )
    
    current_major = forms.CharField(
        label='所学专业',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入您的就读专业'})
    )
    
    gpa = forms.FloatField(
        label='GPA成绩',
        required=False,
        min_value=0,
        max_value=4.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '如有，请填写您的GPA成绩，如3.5', 'step': '0.01'})
    )
    
    grade_rank = forms.ChoiceField(
        label='专业成绩排名',
        choices=GRADE_RANK_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    english_level = forms.CharField(
        label='英语水平',
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '如：四级/六级/雅思/托福等'})
    )
    
    math_level = forms.ChoiceField(
        label='数学基础',
        required=False,
        choices=MATH_LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    academic_status = forms.ChoiceField(
        label='学业状态',
        choices=ACADEMIC_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # 2. 目标方向
    career_direction = forms.ChoiceField(
        label='目标方向',
        choices=CAREER_GOAL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    academic_preference = forms.BooleanField(
        label='偏好学术研究',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # 3. 城市偏好
    target_cities = forms.CharField(
        label='目标城市',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入您希望的城市，如：北京,上海,成都（用逗号分隔）'})
    )
    
    target_city = forms.CharField(
        label='优先城市',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '最优先考虑的城市'})
    )
    
    # 4. 就业目标
    target_companies = forms.CharField(
        label='目标公司类型',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '如：BAT、外企、国企等'})
    )
    
    overseas_plan = forms.BooleanField(
        label='有海外发展计划',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # 5. 经济条件
    economic_condition = forms.ChoiceField(
        label='经济条件',
        choices=ECONOMIC_CONDITION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # 6. 考试能力评估
    estimated_score = forms.IntegerField(
        label='预估考研分数',
        required=False,
        min_value=0,
        max_value=500,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '请输入您的预估考研成绩，如360'})
    )
    
    previous_score = forms.IntegerField(
        label='往年考试分数',
        required=False,
        min_value=0,
        max_value=500,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '如有往年考研经历，请填写分数'})
    )
    
    # 7. 院校梯度偏好
    strategy_preference = forms.ChoiceField(
        label='择校策略',
        choices=STRATEGY_PREFERENCE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # 考研计划
    exam_year = forms.IntegerField(
        label='考研年份',
        min_value=2025,
        max_value=2030,
        initial=get_default_exam_year(),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '计划参加哪一年的考研'})
    )
    
    study_mode = forms.ChoiceField(
        label='就读方式',
        choices=STUDY_MODE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    target_major_category = forms.CharField(
        label='目标专业',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '如：计算机科学、金融学等'})
    )
    
    target_type = forms.ChoiceField(
        label='目标院校类型',
        choices=TARGET_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # 其他信息
    interests = forms.CharField(
        label='兴趣爱好',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入您的兴趣爱好，如：计算机、文学、经济等'})
    )
    
    career_goals = forms.CharField(
        label='职业规划详情',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请详细描述您的职业规划目标'})
    )