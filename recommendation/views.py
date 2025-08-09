#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视图定义
"""

import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Student, School, Major, Recommendation, StudyPlan
from .forms import StudentForm, RecommendationForm, AIRecommendationForm
from .recommender import SchoolRecommender

def index(request):
    """首页"""
    students_count = Student.objects.count()
    schools_count = School.objects.count()
    recommendations_count = Recommendation.objects.count()
    
    context = {
        'students_count': students_count,
        'schools_count': schools_count,
        'recommendations_count': recommendations_count,
    }
    return render(request, 'recommendation/index.html', context)

class StudentListView(ListView):
    """学生列表视图"""
    model = Student
    template_name = 'recommendation/student_list.html'
    context_object_name = 'students'
    ordering = ['-created_at']
    paginate_by = 10

class StudentDetailView(DetailView):
    """学生详情视图"""
    model = Student
    template_name = 'recommendation/student_detail.html'
    context_object_name = 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        recommendations = Recommendation.objects.filter(student=student).order_by('-match_score')
        context['recommendations'] = recommendations
        return context

class StudentCreateView(CreateView):
    """创建学生视图"""
    model = Student
    form_class = StudentForm
    template_name = 'recommendation/student_form.html'
    success_url = reverse_lazy('student_list')
    
    def form_valid(self, form):
        messages.success(self.request, "学生信息创建成功！")
        return super().form_valid(form)

class StudentUpdateView(UpdateView):
    """更新学生视图"""
    model = Student
    form_class = StudentForm
    template_name = 'recommendation/student_form.html'
    
    def get_success_url(self):
        return reverse_lazy('student_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, "学生信息更新成功！")
        return super().form_valid(form)

class StudentDeleteView(DeleteView):
    """删除学生视图"""
    model = Student
    template_name = 'recommendation/student_confirm_delete.html'
    success_url = reverse_lazy('student_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "学生信息已删除！")
        return super().delete(request, *args, **kwargs)

def recommend_schools(request, student_id):
    """学校推荐视图"""
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = RecommendationForm(request.POST)
        if form.is_valid():
            strategy = form.cleaned_data['strategy']
            num_recommendations = form.cleaned_data['num_recommendations']
            
            recommender = SchoolRecommender()
            result = recommender.recommend_schools(
                student_id=student_id,
                strategy=strategy,
                num_recommendations=num_recommendations
            )
            
            if result['status'] == 'success':
                return render(request, 'recommendation/recommendation_result.html', {
                    'student': student,
                    'result': result,
                    'strategy': dict(form.fields['strategy'].choices)[strategy],
                })
            else:
                messages.error(request, result['message'])
                return redirect('student_detail', pk=student_id)
    else:
        form = RecommendationForm()
    
    return render(request, 'recommendation/recommend_form.html', {
        'form': form,
        'student': student,
    })

class SchoolListView(ListView):
    """学校列表视图"""
    model = School
    template_name = 'recommendation/school_list.html'
    context_object_name = 'schools'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = School.objects.all()
        
        # 获取筛选参数
        school_type = self.request.GET.get('type')
        province = self.request.GET.get('province')
        subject_category = self.request.GET.get('subject')
        search_query = self.request.GET.get('q')
        
        # 按学校类型筛选
        if school_type:
            if school_type == '985':
                queryset = queryset.filter(is_985=True)
            elif school_type == '211':
                queryset = queryset.filter(is_211=True)
            elif school_type == 'double_first_class':
                queryset = queryset.filter(is_double_first_class=True)
            elif school_type != 'all':
                queryset = queryset.filter(type=school_type)
        
        # 按省份筛选
        if province and province != 'all':
            queryset = queryset.filter(province=province)
        
        # 按学科类别筛选
        if subject_category and subject_category != 'all':
            # 通过专业关联筛选学校
            queryset = queryset.filter(majors__category=subject_category).distinct()
        
        # 搜索功能
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(majors__name__icontains=search_query)
            ).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取当前筛选参数
        context['current_type'] = self.request.GET.get('type', 'all')
        context['current_province'] = self.request.GET.get('province', 'all')
        context['current_subject'] = self.request.GET.get('subject', 'all')
        context['search_query'] = self.request.GET.get('q', '')
        
        # 获取所有省份列表
        provinces = School.objects.values_list('province', flat=True).distinct().order_by('province')
        context['provinces'] = provinces
        
        # 获取学校类型列表
        school_types = [
            {'value': 'all', 'display': '全部'},
            {'value': '985', 'display': '985工程'},
            {'value': '211', 'display': '211工程'},
            {'value': 'double_first_class', 'display': '双一流'},
            {'value': '普通本科', 'display': '普通本科'}
        ]
        context['school_types'] = school_types
        
        # 获取学科类别列表
        subject_categories = [
            {'value': 'all', 'display': '全部'},
            {'value': '综合类', 'display': '综合类'},
            {'value': '理工类', 'display': '理工类'},
            {'value': '师范类', 'display': '师范类'},
            {'value': '农林类', 'display': '农林类'},
            {'value': '医药类', 'display': '医药类'},
            {'value': '财经类', 'display': '财经类'},
            {'value': '政法类', 'display': '政法类'},
            {'value': '语言类', 'display': '语言类'},
            {'value': '民族类', 'display': '民族类'},
            {'value': '艺术类', 'display': '艺术类'},
            {'value': '体育类', 'display': '体育类'}
        ]
        context['subject_categories'] = subject_categories
        
        return context

class SchoolDetailView(DetailView):
    """学校详情视图"""
    model = School
    template_name = 'recommendation/school_detail.html'
    context_object_name = 'school'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school = self.get_object()
        return context


def ai_recommendation_form(request):
    """AI大数据择校表单视图"""
    print('\n当前视图函数：ai_recommendation_form')
    print('请求方法：', request.method)
    print('是否AJAX请求：', request.headers.get('X-Requested-With') == 'XMLHttpRequest')
    if request.method == 'POST':
        # 调试输出请求数据
        print('\n收到POST请求：', request.POST)
        print('当前请求路径：', request.path)
        
        # 调试表单提交数据
        print('\n表单数据：')
        for key, value in request.POST.items():
            print(f"{key}: {value}")
        form = AIRecommendationForm(request.POST)
        print('表单是否有效：', form.is_valid())
        if form.is_valid():
            print('表单已验证通过')
        else:
            print('表单验证错误：', form.errors)
            
        if form.is_valid():
            # 创建学生记录
            student = Student(
                # 基本信息
                name=form.cleaned_data['name'],
                gender=form.cleaned_data['gender'],
                province=form.cleaned_data['province'],
                education_path='考研',  # 固定为考研
                
                # 1. 用户画像
                current_school=form.cleaned_data['current_school'],
                current_major=form.cleaned_data['current_major'],
                gpa=form.cleaned_data.get('gpa'),
                gpa_ranking=form.cleaned_data['grade_rank'],
                english_level=form.cleaned_data.get('english_level'),
                math_level=form.cleaned_data.get('math_level'),
                
                # 2. 目标方向
                career_direction=form.cleaned_data.get('career_direction'),
                academic_preference=form.cleaned_data.get('academic_preference', False),
                
                # 3. 城市偏好
                target_cities=form.cleaned_data.get('target_cities'),
                target_city=form.cleaned_data.get('target_city'),  # 优先城市
                
                # 4. 就业目标
                target_companies=form.cleaned_data.get('target_companies'),
                overseas_plan=form.cleaned_data.get('overseas_plan', False),
                
                # 5. 经济条件
                economic_condition=form.cleaned_data.get('economic_condition'),
                
                # 6. 考试能力评估
                estimated_score=form.cleaned_data.get('estimated_score'),
                previous_score=form.cleaned_data.get('previous_score'),
                
                # 7. 院校梯度偏好
                strategy_preference=form.cleaned_data.get('strategy_preference'),
                
                # 考研规划
                academic_status=form.cleaned_data['academic_status'],
                exam_year=form.cleaned_data['exam_year'],
                study_mode=form.cleaned_data['study_mode'],
                target_major_category=form.cleaned_data['target_major_category'],
                target_type=form.cleaned_data['target_type'],
                
                # 其他信息
                interests=form.cleaned_data.get('interests'),
                career_goals=form.cleaned_data.get('career_goals'),
            )
            student.save()
            
            # 使用推荐引擎生成推荐
            recommender = SchoolRecommender()
            
            # 调试输出
            print('\n创建的学生ID:', student.id)
            
            # 根据用户选择的策略偏好调整推荐策略
            strategy = 'balanced'  # 默认平衡策略
            if student.strategy_preference == '冲刺':
                strategy = 'aggressive'
            elif student.strategy_preference == '保守':
                strategy = 'conservative'
                
            result = recommender.recommend_schools(
                student_id=student.id,
                strategy=strategy,
                num_recommendations=9
            )
            
            if result['status'] == 'success':
                print('成功生成推荐结果:', result['recommendations'][:2])  # 调试输出
                print('推荐类别统计:', {
                    'safety': len([r for r in result['recommendations'] if r['category'] == 'safety']),
                    'match': len([r for r in result['recommendations'] if r['category'] == 'match']),
                    'challenge': len([r for r in result['recommendations'] if r['category'] == 'challenge'])
                })
                
                return render(request, 'recommendation/ai_recommendation_result.html', {
                    'student': student,
                    'result': result,
                })
            else:
                messages.error(request, result['message'])
                return redirect('ai_recommendation_form')
    else:
        today = datetime.date.today()
        
        # 根据当前日期设置默认考研年份
        default_year = today.year + 2 if today.month >= 8 else today.year + 1
        
        # 初始化表单时设置默认年份
        form = AIRecommendationForm(initial={'exam_year': default_year})
    
    # 添加3年内的考研年份信息
    exam_years = []
    if 'exam_years' in request.GET:
        exam_years = [int(y) for y in request.GET.getlist('exam_years')]
    else:
        today = datetime.date.today()
        current_year = today.year
        if today.month >= 8:
            exam_years = [current_year + 1, current_year + 2, current_year + 3]
        else:
            exam_years = [current_year, current_year + 1, current_year + 2]
    
    return render(request, 'recommendation/ai_recommendation_form.html', {
        'form': form,
        'exam_years': exam_years,
    })

    from django.http import JsonResponse
from django.http import JsonResponse
