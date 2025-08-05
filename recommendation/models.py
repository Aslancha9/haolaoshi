from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# 学校模型
class School(models.Model):
    name = models.CharField("学校名称", max_length=100)
    code = models.CharField("学校代码", max_length=20, blank=True, null=True)
    province = models.CharField("所在省份", max_length=20)
    city = models.CharField("所在城市", max_length=20)
    level = models.CharField("学校等级", max_length=20, blank=True, null=True)
    type = models.CharField("学校类型", max_length=20, blank=True, null=True)
    is_985 = models.BooleanField("985工程", default=False)
    is_211 = models.BooleanField("211工程", default=False)
    is_double_first_class = models.BooleanField("双一流", default=False)
    description = models.TextField("学校简介", blank=True, null=True)
    website = models.URLField("官网网址", blank=True, null=True)
    majors = models.ManyToManyField('Major', verbose_name="开设专业", related_name="schools", blank=True)

    class Meta:
        verbose_name = "学校"
        verbose_name_plural = "学校"
        
    def __str__(self):
        return self.name

# 专业模型
class Major(models.Model):
    name = models.CharField("专业名称", max_length=100)
    code = models.CharField("专业代码", max_length=20, blank=True, null=True)
    category = models.CharField("学科门类", max_length=50, blank=True, null=True)
    subject = models.CharField("学科", max_length=50, blank=True, null=True)
    description = models.TextField("专业描述", blank=True, null=True)
    career_prospects = models.TextField("就业前景", blank=True, null=True)
    
    class Meta:
        verbose_name = "专业"
        verbose_name_plural = "专业"
        
    def __str__(self):
        return self.name

# 历年分数线
class ScoreLine(models.Model):
    school = models.ForeignKey(School, verbose_name="学校", on_delete=models.CASCADE, related_name="score_lines")
    major = models.ForeignKey(Major, verbose_name="专业", on_delete=models.CASCADE, related_name="score_lines", null=True, blank=True)
    year = models.IntegerField("年份")
    province = models.CharField("招生省份", max_length=20)
    batch = models.CharField("批次", max_length=20, blank=True, null=True)
    score = models.IntegerField("录取分数")
    min_rank = models.IntegerField("最低位次", blank=True, null=True)
    
    class Meta:
        verbose_name = "分数线"
        verbose_name_plural = "分数线"
        
    def __str__(self):
        return f"{self.school.name} {self.major.name if self.major else '所有专业'} {self.year}年 {self.province}"

# 学生模型
class Student(models.Model):
    EDUCATION_PATH_CHOICES = [
        ('专升本', '专升本'),
        ('考研', '考研'),
        ('艺考', '艺考'),
    ]
    
    ACADEMIC_STATUS_CHOICES = [
        ('未毕业', '未毕业'),
        ('已毕业', '已毕业'),
        ('在职', '在职'),
    ]
    
    GRADE_RANK_CHOICES = [
        ('前15%', '前15%'),
        ('前30%', '前30%'),
        ('前50%', '前50%'),
        ('后50%', '后50%'),
    ]
    
    STUDY_MODE_CHOICES = [
        ('全日制', '全日制'),
        ('非全日制', '非全日制'),
    ]
    
    TARGET_TYPE_CHOICES = [
        ('985', '985高校'),
        ('211', '211高校'),
        ('双一流', '双一流高校'),
        ('普通院校', '普通院校'),
    ]
    
    CAREER_GOAL_CHOICES = [
        ('学术科研', '学术科研'),
        ('企业就业', '企业就业'),
        ('公务员', '公务员'),
        ('事业单位', '事业单位'),
        ('外企', '外企'),
        ('大厂', '大厂'),
        ('创业', '创业'),
        ('其他', '其他'),
    ]
    
    ECONOMIC_CONDITION_CHOICES = [
        ('高', '可接受高学费/高生活成本'),
        ('中', '适中学费/生活成本'),
        ('低', '需要考虑经济条件'),
    ]
    
    STRATEGY_PREFERENCE_CHOICES = [
        ('保守', '保守策略'),
        ('均衡', '均衡策略'),
        ('冲刺', '冲刺策略'),
    ]
    
    # 基本信息
    name = models.CharField("姓名", max_length=50)
    gender = models.CharField("性别", max_length=10, blank=True, null=True)
    province = models.CharField("所在省份", max_length=20)
    education_path = models.CharField("教育路径", max_length=20, choices=EDUCATION_PATH_CHOICES, default='考研')
    
    # 1. 用户画像
    current_school = models.CharField("就读院校", max_length=100, blank=True, null=True)
    current_major = models.CharField("所学专业", max_length=100, blank=True, null=True)
    gpa = models.FloatField("GPA", blank=True, null=True)
    gpa_ranking = models.CharField("GPA排名", max_length=20, choices=GRADE_RANK_CHOICES, blank=True, null=True)
    grade_rank = models.CharField("专业成绩排名", max_length=20, choices=GRADE_RANK_CHOICES, blank=True, null=True)  # 兼容旧字段
    english_level = models.CharField("英语水平", max_length=20, blank=True, null=True)  # 如"四级/六级/雅思/托福"
    math_level = models.CharField("数学基础", max_length=20, blank=True, null=True)  # 如"较好/一般/较差"
    
    # 2. 目标方向
    career_direction = models.CharField("目标方向", max_length=50, choices=CAREER_GOAL_CHOICES, blank=True, null=True)
    academic_preference = models.BooleanField("偏好学术研究", default=False)
    
    # 3. 城市偏好
    target_cities = models.TextField("目标城市", blank=True, null=True)  # 存储多个城市，以逗号分隔
    target_city = models.CharField("优先城市", max_length=50, blank=True, null=True)
    
    # 4. 就业目标
    target_companies = models.TextField("目标公司类型", blank=True, null=True)
    overseas_plan = models.BooleanField("海外发展计划", default=False)
    
    # 5. 经济条件
    economic_condition = models.CharField("经济条件", max_length=20, choices=ECONOMIC_CONDITION_CHOICES, blank=True, null=True)
    
    # 6. 考试能力评估
    estimated_score = models.IntegerField("预估分数", blank=True, null=True)
    previous_score = models.IntegerField("往年考试分数", blank=True, null=True)
    
    # 7. 院校梯度偏好
    strategy_preference = models.CharField("策略偏好", max_length=20, choices=STRATEGY_PREFERENCE_CHOICES, default='均衡')
    
    # 考研规划
    academic_status = models.CharField("学业状态", max_length=20, choices=ACADEMIC_STATUS_CHOICES, blank=True, null=True)
    exam_year = models.IntegerField("考研年份", blank=True, null=True)
    study_mode = models.CharField("就读方式", max_length=20, choices=STUDY_MODE_CHOICES, blank=True, null=True)
    target_major_category = models.CharField("目标专业类别", max_length=100, blank=True, null=True)
    target_type = models.CharField("目标院校类型", max_length=20, choices=TARGET_TYPE_CHOICES, blank=True, null=True)
    
    # 其他信息
    interests = models.TextField("兴趣爱好", blank=True, null=True)
    career_goals = models.TextField("职业规划", blank=True, null=True)
    
    # 保留的高考相关字段，设为可选
    total_score = models.IntegerField("高考总分", validators=[MinValueValidator(0), MaxValueValidator(750)], blank=True, null=True)
    chinese_score = models.IntegerField("语文成绩", validators=[MinValueValidator(0), MaxValueValidator(150)], blank=True, null=True)
    math_score = models.IntegerField("数学成绩", validators=[MinValueValidator(0), MaxValueValidator(150)], blank=True, null=True)
    english_score = models.IntegerField("英语成绩", validators=[MinValueValidator(0), MaxValueValidator(150)], blank=True, null=True)
    comprehensive_score = models.IntegerField("综合成绩", validators=[MinValueValidator(0), MaxValueValidator(300)], blank=True, null=True)
    rank = models.IntegerField("位次", blank=True, null=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)
    
    class Meta:
        verbose_name = "学生"
        verbose_name_plural = "学生"
        
    def __str__(self):
        return self.name

# 推荐结果
class Recommendation(models.Model):
    RECOMMENDATION_TYPE_CHOICES = [
        ('safety', '保底'),
        ('match', '匹配'),
        ('challenge', '冲刺'),
    ]
    
    student = models.ForeignKey(Student, verbose_name="学生", on_delete=models.CASCADE, related_name="recommendations")
    school = models.ForeignKey(School, verbose_name="推荐学校", on_delete=models.CASCADE)
    major = models.ForeignKey(Major, verbose_name="推荐专业", on_delete=models.CASCADE, null=True, blank=True)
    recommendation_type = models.CharField("推荐类型", max_length=20, choices=RECOMMENDATION_TYPE_CHOICES)
    match_score = models.FloatField("匹配度", validators=[MinValueValidator(0), MaxValueValidator(100)])
    admission_probability = models.FloatField("录取概率", validators=[MinValueValidator(0), MaxValueValidator(100)])
    recommendation_reason = models.TextField("推荐理由", blank=True, null=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)
    
    class Meta:
        verbose_name = "推荐结果"
        verbose_name_plural = "推荐结果"
        
    def __str__(self):
        return f"{self.student.name} - {self.school.name} - {self.major.name if self.major else '无专业'}"

# 学习计划
class StudyPlan(models.Model):
    student = models.ForeignKey(Student, verbose_name="学生", on_delete=models.CASCADE, related_name="study_plans")
    title = models.CharField("计划标题", max_length=100)
    target_school = models.ForeignKey(School, verbose_name="目标学校", on_delete=models.SET_NULL, null=True, blank=True)
    target_major = models.ForeignKey(Major, verbose_name="目标专业", on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField("计划描述")
    start_date = models.DateField("开始日期", default=timezone.now)
    end_date = models.DateField("结束日期", blank=True, null=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)
    
    class Meta:
        verbose_name = "学习计划"
        verbose_name_plural = "学习计划"
        
    def __str__(self):
        return self.title
