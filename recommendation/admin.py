#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
管理员后台配置
"""

from django.contrib import admin
from .models import School, Major, ScoreLine, Student, Recommendation, StudyPlan

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'province', 'city', 'is_985', 'is_211', 'is_double_first_class')
    list_filter = ('province', 'is_985', 'is_211', 'is_double_first_class')
    search_fields = ('name', 'code')

@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'subject')
    list_filter = ('category', 'subject')
    search_fields = ('name', 'code')

@admin.register(ScoreLine)
class ScoreLineAdmin(admin.ModelAdmin):
    list_display = ('school', 'major', 'year', 'province', 'batch', 'score')
    list_filter = ('year', 'province', 'batch')
    search_fields = ('school__name', 'major__name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'province', 'education_path', 'total_score', 'rank', 'created_at')
    list_filter = ('province', 'education_path')
    search_fields = ('name',)
    date_hierarchy = 'created_at'

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('student', 'school', 'major', 'recommendation_type', 'match_score', 'admission_probability')
    list_filter = ('recommendation_type',)
    search_fields = ('student__name', 'school__name', 'major__name')

@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'target_school', 'start_date', 'end_date')
    list_filter = ('start_date',)
    search_fields = ('title', 'student__name', 'target_school__name')