#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库初始化与样本数据生成
"""

import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import engine, Base, async_session
from app.models.student import Student
from app.models.school import School
from app.models.major import Major
from app.models.score_line import ScoreLine
from app.models.study_plan import StudyPlan
from app.models.recommendation import Recommendation
from app.models.education_path import EducationPath


async def init_db():
    """初始化数据库"""
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 检查数据库中是否已有数据
    async with async_session() as session:
        result = await session.execute("SELECT COUNT(*) FROM schools")
        count = result.scalar()

        if count == 0:
            print("数据库为空，开始生成示例数据...")
            await generate_sample_data(session)
        else:
            print(f"数据库中已有数据，跳过数据生成...")


async def generate_sample_data(session: AsyncSession):
    """生成示例数据"""
    # 创建学习路径数据
    await create_education_paths(session)

    # 创建学校数据
    await create_schools(session)

    # 创建专业数据
    await create_majors(session)

    # 创建分数线数据
    await create_score_lines(session)

    # 创建学生数据
    await create_students(session)

    print("示例数据生成完成！")


async def create_education_paths(session: AsyncSession):
    """创建学习路径数据"""
    paths = [
        {
            "name": "高考",
            "description": "普通高等学校招生全国统一考试",
            "duration": "3年",
            "requirements": "高中毕业或同等学历",
        },
        {
            "name": "专升本",
            "description": "专科层次学生升入本科层次学习",
            "duration": "2年",
            "requirements": "专科毕业",
        },
        {
            "name": "考研",
            "description": "全国硕士研究生统一招生考试",
            "duration": "2-3年",
            "requirements": "本科毕业或同等学历",
        },
        {
            "name": "艺考",
            "description": "艺术类专业考试",
            "duration": "3年",
            "requirements": "高中毕业，具备艺术专长",
        },
        {
            "name": "出国留学",
            "description": "申请国外高校学习",
            "duration": "1-4年",
            "requirements": "对应阶段学历，外语能力达标",
        },
    ]

    for path_data in paths:
        path = EducationPath(**path_data)
        session.add(path)

    await session.commit()
    print(f"创建了 {len(paths)} 条学习路径数据")


async def create_schools(session: AsyncSession):
    """创建学校数据"""
    schools_data = [
        {
            "name": "北京大学",
            "code": "10001",
            "level": "本科",
            "type": "综合",
            "nature": "公立",
            "province": "北京",
            "city": "北京",
            "address": "北京市海淀区颐和园路5号",
            "website": "https://www.pku.edu.cn",
            "is_211": True,
            "is_985": True,
            "is_double_first_class": True,
            "rank": 1,
            "features": {"strengths": ["人文学科", "基础科学", "医学", "信息科学"]},
            "admission_office_phone": "010-12345678",
            "introduction": "中国最早的综合性大学，学科齐全，师资力量雄厚",
        },
        {
            "name": "清华大学",
            "code": "10003",
            "level": "本科",
            "type": "理工",
            "nature": "公立",
            "province": "北京",
            "city": "北京",
            "address": "北京市海淀区清华园1号",
            "website": "https://www.tsinghua.edu.cn",
            "is_211": True,
            "is_985": True,
            "is_double_first_class": True,
            "rank": 2,
            "features": {"strengths": ["工程学科", "基础科学", "经济管理", "信息科学"]},
            "admission_office_phone": "010-87654321",
            "introduction": "中国理工科顶尖学府，工科实力强大",
        },
        {
            "name": "复旦大学",
            "code": "10246",
            "level": "本科",
            "type": "综合",
            "nature": "公立",
            "province": "上海",
            "city": "上海",
            "address": "上海市杨浦区邯郸路220号",
            "website": "https://www.fudan.edu.cn",
            "is_211": True,
            "is_985": True,
            "is_double_first_class": True,
            "rank": 3,
            "features": {"strengths": ["人文学科", "医学", "经济管理", "新闻传播"]},
            "admission_office_phone": "021-12345678",
            "introduction": "中国东部地区顶尖高校，人文社科和医学实力强",
        },
        {
            "name": "浙江大学",
            "code": "10335",
            "level": "本科",
            "type": "综合",
            "nature": "公立",
            "province": "浙江",
            "city": "杭州",
            "address": "浙江省杭州市西湖区余杭塘路866号",
            "website": "https://www.zju.edu.cn",
            "is_211": True,
            "is_985": True,
            "is_double_first_class": True,
            "rank": 4,
            "features": {"strengths": ["工程学科", "农业科学", "医学", "信息技术"]},
            "admission_office_phone": "0571-12345678",
            "introduction": "综合性研究型大学，学科门类齐全",
        },
        {
            "name": "重庆大学",
            "code": "10611",
            "level": "本科",
            "type": "理工",
            "nature": "公立",
            "province": "重庆",
            "city": "重庆",
            "address": "重庆市沙坪坝区沙正街174号",
            "website": "https://www.cqu.edu.cn",
            "is_211": True,
            "is_985": False,
            "is_double_first_class": True,
            "rank": 30,
            "features": {"strengths": ["工程学科", "建筑", "机械制造", "电气工程"]},
            "admission_office_phone": "023-12345678",
            "introduction": "重庆市综合实力最强的高校，工科见长",
        },
        {
            "name": "四川大学",
            "code": "10610",
            "level": "本科",
            "type": "综合",
            "nature": "公立",
            "province": "四川",
            "city": "成都",
            "address": "四川省成都市武侯区望江路29号",
            "website": "https://www.scu.edu.cn",
            "is_211": True,
            "is_985": True,
            "is_double_first_class": True,
            "rank": 12,
            "features": {"strengths": ["医学", "文学", "历史学", "工程学科"]},
            "admission_office_phone": "028-12345678",
            "introduction": "西南地区最著名的高校之一，医学和人文学科实力强",
        },
        {
            "name": "重庆师范大学",
            "code": "10637",
            "level": "本科",
            "type": "师范",
            "nature": "公立",
            "province": "重庆",
            "city": "重庆",
            "address": "重庆市沙坪坝区大学城中路37号",
            "website": "https://www.cqnu.edu.cn",
            "is_211": False,
            "is_985": False,
            "is_double_first_class": False,
            "rank": 158,
            "features": {"strengths": ["教育学", "文学", "历史", "地理科学"]},
            "admission_office_phone": "023-87654321",
            "introduction": "重庆市重点师范院校，教师教育特色鲜明",
        },
        {
            "name": "中央美术学院",
            "code": "10047",
            "level": "本科",
            "type": "艺术",
            "nature": "公立",
            "province": "北京",
            "city": "北京",
            "address": "北京市朝阳区花家地南街8号",
            "website": "https://www.cafa.edu.cn",
            "is_211": False,
            "is_985": False,
            "is_double_first_class": True,
            "rank": 1,  # 艺术类排名
            "features": {"strengths": ["美术", "设计", "建筑", "艺术理论"]},
            "admission_office_phone": "010-64771056",
            "introduction": "中国最高等级的美术学院，培养高级美术专门人才",
        },
        {
            "name": "上海外国语大学",
            "code": "10271",
            "level": "本科",
            "type": "语言",
            "nature": "公立",
            "province": "上海",
            "city": "上海",
            "address": "上海市虹口区大连西路550号",
            "website": "https://www.shisu.edu.cn",
            "is_211": True,
            "is_985": False,
            "is_double_first_class": True,
            "rank": 10,  # 语言类院校排名
            "features": {"strengths": ["外国语言文学", "国际关系", "国际贸易", "翻译"]},
            "admission_office_phone": "021-65315080",
            "introduction": "以培养外语人才为主的多科性大学，外语专业实力强大",
        },
        {
            "name": "电子科技大学",
            "code": "10614",
            "level": "本科",
            "type": "理工",
            "nature": "公立",
            "province": "四川",
            "city": "成都",
            "address": "四川省成都市高新区西源大道2006号",
            "website": "https://www.uestc.edu.cn",
            "is_211": True,
            "is_985": True,
            "is_double_first_class": True,
            "rank": 15,
            "features": {"strengths": ["电子信息", "通信工程", "计算机", "人工智能"]},
            "admission_office_phone": "028-61831199",
            "introduction": "中国电子类院校排名第一，信息与通信工程全国领先",
        },
    ]

    for school_data in schools_data:
        school = School(**school_data)
        session.add(school)

    await session.commit()
    print(f"创建了 {len(schools_data)} 所学校数据")


async def create_majors(session: AsyncSession):
    """创建专业数据"""
    # 获取所有学校
    result = await session.execute("SELECT id, name FROM schools")
    schools = result.fetchall()

    majors_template = [
        {
            "name": "计算机科学与技术",
            "code": "080901",
            "category": "工学",
            "subcategory": "计算机类",
            "degree_type": "理学学士",
            "study_period": 4,
            "description": "培养具备计算机科学与技术的基本理论知识和应用能力的高级专门人才",
            "career_prospects": "软件开发、人工智能研究、算法工程师、数据分析师等",
        },
        {
            "name": "软件工程",
            "code": "080902",
            "category": "工学",
            "subcategory": "计算机类",
            "degree_type": "工学学士",
            "study_period": 4,
            "description": "培养从事软件开发、测试、维护和项目管理的复合型人才",
            "career_prospects": "软件工程师、测试工程师、产品经理、项目经理等",
        },
        {
            "name": "人工智能",
            "code": "080910T",
            "category": "工学",
            "subcategory": "计算机类",
            "degree_type": "工学学士",
            "study_period": 4,
            "description": "培养具备人工智能理论和技术的高级专门人才",
            "career_prospects": "AI算法工程师、机器学习工程师、深度学习研究员等",
        },
        {
            "name": "临床医学",
            "code": "100201",
            "category": "医学",
            "subcategory": "临床医学类",
            "degree_type": "医学学士",
            "study_period": 5,
            "description": "培养具有基础医学和临床医学知识的医疗人才",
            "career_prospects": "临床医生、医学研究员、医疗管理人员等",
        },
        {
            "name": "金融学",
            "code": "020301",
            "category": "经济学",
            "subcategory": "金融学类",
            "degree_type": "经济学学士",
            "study_period": 4,
            "description": "培养具备金融理论知识和实践能力的专门人才",
            "career_prospects": "银行业务、投资分析、风险管理、保险精算等",
        },
        {
            "name": "法学",
            "code": "030101",
            "category": "法学",
            "subcategory": "法学类",
            "degree_type": "法学学士",
            "study_period": 4,
            "description": "培养具备法律专业知识的应用型法律人才",
            "career_prospects": "律师、法官、检察官、企业法务等",
        },
        {
            "name": "汉语言文学",
            "code": "050101",
            "category": "文学",
            "subcategory": "中国语言文学类",
            "degree_type": "文学学士",
            "study_period": 4,
            "description": "培养具有扎实的汉语言文学基础知识和应用能力的专门人才",
            "career_prospects": "教师、编辑、作家、文化工作者等",
        },
        {
            "name": "英语",
            "code": "050201",
            "category": "文学",
            "subcategory": "外国语言文学类",
            "degree_type": "文学学士",
            "study_period": 4,
            "description": "培养具有扎实的英语语言基础和广泛的文化知识的专门人才",
            "career_prospects": "外贸、翻译、外企、教育、外交等",
        },
        {
            "name": "绘画",
            "code": "130402",
            "category": "艺术学",
            "subcategory": "美术学类",
            "degree_type": "艺术学学士",
            "study_period": 4,
            "description": "培养具备绘画创作和研究能力的专门人才",
            "career_prospects": "艺术创作、艺术教育、艺术策划等",
        },
        {
            "name": "音乐表演",
            "code": "130201",
            "category": "艺术学",
            "subcategory": "音乐与舞蹈学类",
            "degree_type": "艺术学学士",
            "study_period": 4,
            "description": "培养具有音乐表演和艺术创作能力的专门人才",
            "career_prospects": "音乐表演、音乐教育、音乐制作等",
        },
    ]

    count = 0
    for school_id, school_name in schools:
        # 根据学校类型选择专业
        if "师范" in school_name:
            selected_majors = [
                m for m in majors_template if m["name"] in ["汉语言文学", "英语"]
            ]
            # 添加教育学专业
            selected_majors.append(
                {
                    "name": "教育学",
                    "code": "040101",
                    "category": "教育学",
                    "subcategory": "教育学类",
                    "degree_type": "教育学学士",
                    "study_period": 4,
                    "description": "培养具备教育理论知识和教学能力的教育专业人才",
                    "career_prospects": "中小学教师、教育研究员、教育行政管理等",
                }
            )
        elif "艺术" in school_name:
            selected_majors = [m for m in majors_template if m["category"] == "艺术学"]
            # 添加艺术设计专业
            selected_majors.append(
                {
                    "name": "艺术设计学",
                    "code": "130501",
                    "category": "艺术学",
                    "subcategory": "设计学类",
                    "degree_type": "艺术学学士",
                    "study_period": 4,
                    "description": "培养具备艺术设计理论和实践能力的专业人才",
                    "career_prospects": "设计师、艺术总监、创意总监等",
                }
            )
        elif "语言" in school_name:
            selected_majors = [
                m for m in majors_template if "外国语言文学类" in m.get("subcategory", "")
            ]
            # 添加多种语言专业
            selected_majors.extend(
                [
                    {
                        "name": "日语",
                        "code": "050207",
                        "category": "文学",
                        "subcategory": "外国语言文学类",
                        "degree_type": "文学学士",
                        "study_period": 4,
                        "description": "培养具备扎实的日语语言基础和文化知识的专门人才",
                        "career_prospects": "翻译、外贸、涉日企业、教育等",
                    },
                    {
                        "name": "法语",
                        "code": "050204",
                        "category": "文学",
                        "subcategory": "外国语言文学类",
                        "degree_type": "文学学士",
                        "study_period": 4,
                        "description": "培养具备扎实的法语语言基础和文化知识的专门人才",
                        "career_prospects": "翻译、外贸、涉法企业、教育、外交等",
                    },
                ]
            )
        elif "理工" in school_name:
            selected_majors = [m for m in majors_template if m["category"] == "工学"]
            # 添加物理学专业
            selected_majors.append(
                {
                    "name": "物理学",
                    "code": "070201",
                    "category": "理学",
                    "subcategory": "物理学类",
                    "degree_type": "理学学士",
                    "study_period": 4,
                    "description": "培养具备物理学基本理论和实验技能的专门人才",
                    "career_prospects": "科研、高等教育、技术研发等",
                }
            )
        else:  # 综合类学校选择多种类型的专业
            selected_majors = random.sample(
                majors_template, min(5, len(majors_template))
            )

        # 为每所学校添加专业
        for major_data in selected_majors:
            major_data_copy = major_data.copy()
            major_data_copy["school_id"] = school_id
            major = Major(**major_data_copy)
            session.add(major)
            count += 1

    await session.commit()
    print(f"创建了 {count} 个专业数据")


async def create_score_lines(session: AsyncSession):
    """创建分数线数据"""
    # 获取所有学校
    result = await session.execute("SELECT id, name, rank FROM schools")
    schools = result.fetchall()

    # 获取所有专业
    result = await session.execute("SELECT id, name, school_id FROM majors")
    majors = result.fetchall()

    # 按学校ID组织专业
    school_majors = {}
    for major_id, major_name, school_id in majors:
        if school_id not in school_majors:
            school_majors[school_id] = []
        school_majors[school_id].append((major_id, major_name))

    current_year = datetime.now().year
    provinces = ["重庆", "四川", "北京", "上海", "浙江", "江苏"]

    count = 0
    for school_id, school_name, school_rank in schools:
        for province in provinces:
            for year in range(current_year - 3, current_year + 1):
                # 根据学校排名设置基准分数
                if school_rank and school_rank <= 10:
                    base_score = random.randint(640, 680)
                elif school_rank and school_rank <= 50:
                    base_score = random.randint(600, 640)
                else:
                    base_score = random.randint(550, 600)

                # 添加年份和省份的随机波动
                year_variation = random.randint(-5, 5)
                province_factor = 0
                if province in ["北京", "上海"]:
                    province_factor = random.randint(-20, -10)  # 北京上海分数线偏低
                elif province in ["重庆", "四川"]:
                    province_factor = random.randint(0, 10)  # 重庆四川分数线偏高

                min_score = base_score + year_variation + province_factor
                provincial_line = min_score - random.randint(40, 80)  # 省控线

                # 创建学校总体分数线
                score_line = ScoreLine(
                    school_id=school_id,
                    year=year,
                    province=province,
                    batch="本科一批",
                    subject_type="理科",
                    min_score=min_score,
                    min_rank=random.randint(5000, 50000),
                    provincial_line=provincial_line,
                )
                session.add(score_line)
                count += 1

                # 为该校专业添加分数线（仅添加部分)
                if province in ["重庆", "四川"] and year >= current_year - 2:
                    if school_id in school_majors:
                        for major_id, major_name in school_majors[school_id]:
                            # 专业分数线略高于学校整体分数线
                            major_variation = random.randint(0, 15)
                            major_score_line = ScoreLine(
                                school_id=school_id,
                                major_id=major_id,
                                year=year,
                                province=province,
                                batch="本科一批",
                                subject_type="理科",
                                min_score=min_score + major_variation,
                                min_rank=random.randint(3000, 40000),
                                provincial_line=provincial_line,
                            )
                            session.add(major_score_line)
                            count += 1

    await session.commit()
    print(f"创建了 {count} 条分数线数据")


async def create_students(session: AsyncSession):
    """创建学生数据"""
    # 获取所有学习路径
    result = await session.execute("SELECT id, name FROM education_paths")
    education_paths = result.fetchall()

    provinces = ["重庆", "四川", "北京", "上海", "浙江", "江苏"]
    schools_list = ["重庆一中", "重庆南开中学", "成都七中", "北京四中", "上海中学"]

    students = []
    for i in range(10):
        # 基本信息
        gender = random.choice(["男", "女"])
        province = random.choice(provinces)
        education_path = random.choice(education_paths)

        # 成绩信息
        total_score = random.randint(500, 680)
        chinese = random.randint(100, 150)
        math = random.randint(100, 150)
        english = random.randint(100, 150)

        # 学科强项和弱项
        subjects = ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理"]
        strengths = random.sample(subjects, 2)
        remaining = [s for s in subjects if s not in strengths]
        weaknesses = random.sample(remaining, 2)

        # 兴趣和职业规划
        interests = random.sample(
            ["计算机", "文学", "艺术", "科学", "医学", "经济", "法律", "教育"], random.randint(2, 4)
        )
        career_goals = random.choice(["IT行业", "医疗卫生", "金融行业", "教育工作", "公务员", "法律行业"])

        # 创建学生
        student = Student(
            name=f"学生{i+1}",
            gender=gender,
            age=random.randint(16, 22),
            current_school=random.choice(schools_list),
            province=province,
            city=province[:2],  # 简化处理
            phone=f"1391234{i+1:04d}",
            email=f"student{i+1}@example.com",
            education_path_id=education_path[0],
            total_score=total_score,
            chinese_score=chinese,
            math_score=math,
            english_score=english,
            strengths=strengths,
            weaknesses=weaknesses,
            interests=interests,
            career_goals=career_goals,
            target_score=total_score + random.randint(10, 30),  # 目标分数略高于当前分数
        )
        session.add(student)
        students.append(student)

    await session.commit()
    print(f"创建了 {len(students)} 名学生数据")
