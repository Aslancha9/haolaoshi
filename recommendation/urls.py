#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
URL配置
"""

from django.urls import path
from . import views

urlpatterns = [
    # 首页
    path('', views.index, name='index'),
    
    # 学生相关路由
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('students/new/', views.StudentCreateView.as_view(), name='student_new'),
    path('students/<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    path('students/<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    path('students/<int:student_id>/recommend/', views.recommend_schools, name='recommend_schools'),
    
    # 学校相关路由
    path('schools/', views.SchoolListView.as_view(), name='school_list'),
    path('schools/<int:pk>/', views.SchoolDetailView.as_view(), name='school_detail'),
    
    # AI大数据择校功能
    path('ai-recommendation/', views.ai_recommendation_form, name='ai_recommendation_form'),
]