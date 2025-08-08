#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生成样本数据的命令
使用方法: python manage.py generate_sample_data
"""

import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from recommendation.models import School, Major, ScoreLine, Student

class Command(BaseCommand):
    help = '生成示例学校、专业和学生数据'

    def handle(self, *args, **options):
        self.stdout.write('开始生成示例数据...')
        
        # 创建专业
        self.create_majors()
        
        # 创建学校
        self.create_schools()
        
        # 创建分数线
        self.create_score_lines()
        
        # 创建学生
        self.create_students()
        
        self.stdout.write(self.style.SUCCESS('示例数据生成成功!'))

    def create_majors(self):
        """创建示例专业"""
        if Major.objects.count() > 0:
            self.stdout.write('专业数据已存在，跳过创建')
            return
            
        majors_data = [
            {
                'name': '计算机科学与技术',
                'code': '080901',
                'category': '工学',
                'subject': '计算机类',
                'description': '计算机科学与技术专业培养掌握计算机科学与技术包括计算机硬件、软件与应用的基本理论、基本知识和基本技能与方法，能在科研部门、教育单位、企业、事业、技术和行政管理部门等单位从事计算机教学、科学研究和应用的计算机科学与技术学科的高级专门科学技术人才。',
                'career_prospects': '毕业生可在IT企业、互联网公司、金融机构等从事软件开发、系统分析、网络管理等工作。'
            },
            {
                'name': '软件工程',
                'code': '080902',
                'category': '工学',
                'subject': '计算机类',
                'description': '软件工程专业培养具备计算机、软件工程等方面的知识，能在软件开发领域从事软件分析、设计、开发、维护等工作的应用型专门人才。',
                'career_prospects': '毕业生可在软件企业、互联网公司、IT服务企业从事软件设计、开发、测试、项目管理等工作。'
            },
            {
                'name': '人工智能',
                'code': '080910T',
                'category': '工学',
                'subject': '计算机类',
                'description': '人工智能专业培养掌握计算机科学、数学、认知科学等多学科理论与技术，能在人工智能相关领域从事研发与应用的高级专门人才。',
                'career_prospects': '毕业生可在人工智能研究机构、大型互联网企业、智能制造企业等从事算法研发、智能系统开发等工作。'
            },
            {
                'name': '临床医学',
                'code': '100201',
                'category': '医学',
                'subject': '临床医学类',
                'description': '临床医学专业培养具备基础医学、临床医学的基本理论和医疗技能，能在医疗卫生机构从事医疗、预防和保健等工作的医学专门人才。',
                'career_prospects': '毕业生可在医院、医疗卫生机构、医学院校等从事医疗、教学、科研工作。'
            },
            {
                'name': '会计学',
                'code': '120203',
                'category': '管理学',
                'subject': '工商管理类',
                'description': '会计学专业培养掌握会计学、审计学、财务管理等方面的知识和技能，能在企事业单位从事会计、审计、财务管理等工作的专门人才。',
                'career_prospects': '毕业生可在企业、事业单位、会计师事务所、金融机构等从事会计、审计、财务管理等工作。'
            },
            {
                'name': '金融学',
                'code': '020301',
                'category': '经济学',
                'subject': '金融学类',
                'description': '金融学专业培养掌握金融学理论与实务，能在银行、证券、保险等金融机构从事业务、管理、研究等工作的专门人才。',
                'career_prospects': '毕业生可在银行、证券公司、保险公司、基金公司等金融机构从事相关工作。'
            },
            {
                'name': '汉语言文学',
                'code': '050101',
                'category': '文学',
                'subject': '中国语言文学类',
                'description': '汉语言文学专业培养掌握汉语和中国文学方面的基本知识，具备较高的文学素养和语言表达能力，能在文化、教育、出版等部门从事研究、教学、编辑等工作的专门人才。',
                'career_prospects': '毕业生可在学校、出版社、媒体、文化企业等单位从事教学、编辑、写作等工作。'
            },
            {
                'name': '英语',
                'code': '050201',
                'category': '文学',
                'subject': '外国语言文学类',
                'description': '英语专业培养具有扎实的英语语言基础和广泛的科学文化知识，能在外事、经贸、文化、教育、科研等部门从事翻译、教学、管理等工作的英语专门人才。',
                'career_prospects': '毕业生可在外资企业、教育机构、翻译公司、涉外机构等从事翻译、教学、对外交流等工作。'
            },
            {
                'name': '机械设计制造及其自动化',
                'code': '080202',
                'category': '工学',
                'subject': '机械类',
                'description': '机械设计制造及其自动化专业培养具备机械设计制造基础知识与应用能力，能在工业生产一线从事机械产品设计制造、科技开发、应用研究等方面工作的高级工程技术人才。',
                'career_prospects': '毕业生可在机械、汽车、航空等制造企业从事产品设计、制造工艺、生产管理等工作。'
            },
            {
                'name': '法学',
                'code': '030101',
                'category': '法学',
                'subject': '法学类',
                'description': '法学专业培养掌握法学知识和法律实务技能，能在国家机关、企事业单位和社会团体从事法律工作的专门人才。',
                'career_prospects': '毕业生可在司法机关、律师事务所、企事业法务部门等从事法律实务工作。'
            }
        ]
        
        for major_data in majors_data:
            Major.objects.create(**major_data)
            
        self.stdout.write(self.style.SUCCESS(f'已创建 {len(majors_data)} 个专业'))

    def create_schools(self):
        """创建示例学校"""
        if School.objects.count() > 0:
            self.stdout.write('学校数据已存在，跳过创建')
            return
            
        schools_data = [
            {
                'name': '清华大学',
                'code': '10003',
                'province': '北京',
                'city': '北京',
                'level': '本科',
                'type': '综合',
                'is_985': True,
                'is_211': True,
                'is_double_first_class': True,
                'description': '清华大学是中国著名高等学府，坐落于北京市海淀区，是一所综合性、研究型大学。',
                'website': 'https://www.tsinghua.edu.cn/'
            },
            {
                'name': '北京大学',
                'code': '10001',
                'province': '北京',
                'city': '北京',
                'level': '本科',
                'type': '综合',
                'is_985': True,
                'is_211': True,
                'is_double_first_class': True,
                'description': '北京大学创办于1898年，初名京师大学堂，是中国第一所国立综合性大学，也是当时中国最高教育行政机关。',
                'website': 'https://www.pku.edu.cn/'
            },
            {
                'name': '复旦大学',
                'code': '10246',
                'province': '上海',
                'city': '上海',
                'level': '本科',
                'type': '综合',
                'is_985': True,
                'is_211': True,
                'is_double_first_class': True,
                'description': '复旦大学是中国最顶尖的高校之一，创建于1905年，是中国人自主创办的第一所高等院校。',
                'website': 'https://www.fudan.edu.cn/'
            },
            {
                'name': '重庆大学',
                'code': '10611',
                'province': '重庆',
                'city': '重庆',
                'level': '本科',
                'type': '理工',
                'is_985': False,
                'is_211': True,
                'is_double_first_class': True,
                'description': '重庆大学是教育部直属的全国重点大学，是国家"双一流"建设高校、"211工程"和"985工程优势学科创新平台"重点建设大学。',
                'website': 'https://www.cqu.edu.cn/'
            },
            {
                'name': '四川大学',
                'code': '10610',
                'province': '四川',
                'city': '成都',
                'level': '本科',
                'type': '综合',
                'is_985': True,
                'is_211': True,
                'is_double_first_class': True,
                'description': '四川大学是教育部直属全国重点大学，是国家布局在中国西部的重点建设的高水平研究型综合大学。',
                'website': 'https://www.scu.edu.cn/'
            },
            {
                'name': '电子科技大学',
                'code': '10614',
                'province': '四川',
                'city': '成都',
                'level': '本科',
                'type': '理工',
                'is_985': False,
                'is_211': True,
                'is_double_first_class': True,
                'description': '电子科技大学是教育部直属、国家"双一流"和"211工程"重点建设大学，以电子信息科学技术为核心，工、理、管、文协调发展的多科性研究型全国重点大学。',
                'website': 'https://www.uestc.edu.cn/'
            },
            {
                'name': '重庆邮电大学',
                'code': '10617',
                'province': '重庆',
                'city': '重庆',
                'level': '本科',
                'type': '理工',
                'is_985': False,
                'is_211': False,
                'is_double_first_class': False,
                'description': '重庆邮电大学是重庆市属高校，以信息学科为特色，工学为主，工、管、理、经、文、艺、法多学科协调发展的教学研究型大学。',
                'website': 'https://www.cqupt.edu.cn/'
            },
            {
                'name': '南京大学',
                'code': '10284',
                'province': '江苏',
                'city': '南京',
                'level': '本科',
                'type': '综合',
                'is_985': True,
                'is_211': True,
                'is_double_first_class': True,
                'description': '南京大学是中国历史最悠久的高等学府之一，是一所享誉海内外的著名高等学府。',
                'website': 'https://www.nju.edu.cn/'
            },
            {
                'name': '西南大学',
                'code': '10635',
                'province': '重庆',
                'city': '重庆',
                'level': '本科',
                'type': '综合',
                'is_985': False,
                'is_211': True,
                'is_double_first_class': True,
                'description': '西南大学是教育部直属，教育部、农业部、重庆市共建的重点综合大学。',
                'website': 'https://www.swu.edu.cn/'
            },
            {
                'name': '重庆师范大学',
                'code': '10637',
                'province': '重庆',
                'city': '重庆',
                'level': '本科',
                'type': '师范',
                'is_985': False,
                'is_211': False,
                'is_double_first_class': False,
                'description': '重庆师范大学是重庆市属重点高校，是一所具有教师教育特色的综合性大学。',
                'website': 'https://www.cqnu.edu.cn/'
            }
        ]
        
        for school_data in schools_data:
            School.objects.create(**school_data)
            
        self.stdout.write(self.style.SUCCESS(f'已创建 {len(schools_data)} 所学校'))

    def create_score_lines(self):
        """创建示例分数线"""
        if ScoreLine.objects.count() > 0:
            self.stdout.write('分数线数据已存在，跳过创建')
            return
            
        schools = School.objects.all()
        provinces = ['北京', '上海', '重庆', '四川', '江苏', '湖北', '广东', '浙江']
        years = [2021, 2022, 2023]
        batches = ['本科一批', '本科二批']
        
        score_lines = []
        
        for school in schools:
            base_score = 0
            if school.is_985:
                base_score = 650
            elif school.is_211:
                base_score = 630
            elif school.is_double_first_class:
                base_score = 610
            else:
                base_score = 580
                
            for province in provinces:
                # 根据省份调整基础分
                if province == school.province:
                    province_score = base_score - 10  # 本省略低一些
                elif province in ['北京', '上海']:
                    province_score = base_score + 10  # 北京上海分数线高一些
                else:
                    province_score = base_score
                
                for year in years:
                    # 每年略有波动
                    year_variation = random.randint(-15, 15)
                    final_score = province_score + year_variation
                    
                    # 限制分数在合理范围内
                    final_score = max(500, min(700, final_score))
                    
                    # 计算位次（估算）
                    if final_score > 650:
                        min_rank = random.randint(100, 5000)
                    elif final_score > 600:
                        min_rank = random.randint(5000, 20000)
                    else:
                        min_rank = random.randint(20000, 80000)
                    
                    # 创建分数线记录
                    score_line = ScoreLine(
                        school=school,
                        year=year,
                        province=province,
                        batch='本科一批' if final_score > 600 else '本科二批',
                        score=final_score,
                        min_rank=min_rank
                    )
                    score_lines.append(score_line)
        
        # 批量创建
        ScoreLine.objects.bulk_create(score_lines)
        
        self.stdout.write(self.style.SUCCESS(f'已创建 {len(score_lines)} 条分数线数据'))

    def create_students(self):
        """创建示例学生"""
        if Student.objects.count() > 0:
            self.stdout.write('学生数据已存在，跳过创建')
            return
            
        student_names = ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十', '郑十一', '王小明']
        provinces = ['北京', '上海', '重庆', '四川', '江苏', '湖北', '广东', '浙江']
        education_paths = ['高考', '专升本', '考研', '艺考']
        genders = ['男', '女']
        
        interests_list = [
            '计算机、编程、人工智能',
            '文学、写作、阅读',
            '医学、生物学、健康科学',
            '经济学、金融、投资',
            '艺术、设计、创意',
            '法律、政治、社会学',
            '机械、电子、工程学',
            '教育、心理学、人文科学',
            '运动、体育管理',
            '数学、物理、自然科学'
        ]
        
        career_goals_list = [
            '成为软件工程师，在大型互联网公司就业',
            '从事教师工作，培养下一代',
            '成为医生，在三甲医院就职',
            '从事金融分析师，在投行或基金公司工作',
            '成为设计师，开设个人工作室',
            '从事律师工作，专注知识产权领域',
            '成为机械工程师，在制造业工作',
            '从事科研工作，攻读博士学位',
            '成为企业管理者，负责公司运营',
            '从事创业，开发创新产品'
        ]
        
        students = []
        
        for i in range(10):
            # 基本信息
            name = student_names[i]
            gender = random.choice(genders)
            province = random.choice(provinces)
            education_path = random.choice(education_paths)
            
            # 成绩信息
            total_score = random.randint(500, 700)
            chinese_score = random.randint(90, 150)
            math_score = random.randint(90, 150)
            english_score = random.randint(90, 150)
            comprehensive_score = random.randint(180, 300)
            
            # 确保各科成绩总和与总分相近
            while abs(chinese_score + math_score + english_score + comprehensive_score - total_score) > 50:
                total_score = chinese_score + math_score + english_score + comprehensive_score - random.randint(0, 50)
            
            # 位次（根据总分估算）
            if total_score > 650:
                rank = random.randint(1000, 10000)
            elif total_score > 600:
                rank = random.randint(10000, 50000)
            else:
                rank = random.randint(50000, 200000)
            
            # 兴趣爱好和职业规划
            interests = interests_list[i]
            career_goals = career_goals_list[i]
            
            # 创建日期（过去30天内的随机日期）
            days_ago = random.randint(1, 30)
            created_at = timezone.now() - timedelta(days=days_ago)
            
            # 创建学生对象
            student = Student(
                name=name,
                gender=gender,
                province=province,
                education_path=education_path,
                total_score=total_score,
                chinese_score=chinese_score,
                math_score=math_score,
                english_score=english_score,
                comprehensive_score=comprehensive_score,
                interests=interests,
                career_goals=career_goals,
                rank=rank,
                created_at=created_at
            )
            students.append(student)
        
        # 批量创建
        Student.objects.bulk_create(students)
        
        self.stdout.write(self.style.SUCCESS(f'已创建 {len(students)} 名学生'))