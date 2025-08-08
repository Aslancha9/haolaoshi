#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学校推荐引擎 - 轻量级实现
实现基于多种因素的院校推荐功能
"""

from .models import School, Major, ScoreLine, Student, Recommendation

class SchoolRecommender:
    """院校推荐引擎"""
    
    def __init__(self):
        """初始化推荐引擎"""
        pass
    
    def _calculate_user_profile_match(self, student, school, major=None):
        """
        计算用户画像与学校/专业匹配度
        1. 用户画像：本科专业、院校、GPA、四六级、数学基础等
        """
        match_score = 50  # 基础匹配分
        
        # 1.1 计算学校层次匹配度
        # 根据学生当前学校层次和目标学校层次的差距来计算
        student_school_tier = self._get_school_tier(student.current_school)
        target_school_tier = self._get_school_tier(school.name)
        
        # 层次提升或相当
        tier_diff = target_school_tier - student_school_tier
        if tier_diff <= 0:  # 目标学校层次低于或等于现在的学校
            tier_match = 90
        elif tier_diff == 1:  # 提升一个层次
            tier_match = 70
        elif tier_diff == 2:  # 提升两个层次
            tier_match = 50
        else:  # 提升三个层次以上
            tier_match = 30
        
        # 1.2 计算专业背景匹配度
        major_match = 50
        if major and student.current_major:
            if self._is_same_major_category(student.current_major, major.name):
                major_match = 90  # 跨度小，同类专业
            elif self._is_related_major(student.current_major, major.name):
                major_match = 70  # 相关专业
            else:
                major_match = 30  # 跨度大
                
        # 1.3 计算GPA/排名匹配度
        gpa_match = 50
        if student.gpa_ranking:
            if student.gpa_ranking == '前15%':
                gpa_match = 90
            elif student.gpa_ranking == '前30%':
                gpa_match = 75
            elif student.gpa_ranking == '前50%':
                gpa_match = 60
            else:  # 后50%
                gpa_match = 40
                
        # 根据英语水平和数学基础调整
        english_bonus = 0
        if student.english_level:
            if '六级' in student.english_level or '雅思' in student.english_level or '托福' in student.english_level:
                english_bonus = 10
            elif '四级' in student.english_level:
                english_bonus = 5
                
        math_bonus = 0
        if student.math_level:
            if '较好' in student.math_level:
                math_bonus = 10
            elif '一般' in student.math_level:
                math_bonus = 5
        
        # 综合用户画像匹配分数
        profile_match = (tier_match * 0.4) + (major_match * 0.3) + (gpa_match * 0.2) + english_bonus + math_bonus
        return min(100, profile_match)
    
    def _calculate_career_match(self, student, school, major=None):
        """
        计算职业目标与学校/专业的匹配度
        2. 目标方向：是偏学术、就业、体制内、技术岗等
        4. 就业目标：想进哪些类型公司，如外企、大厂、事业单位等
        """
        if not student.career_direction:
            return 50  # 没有职业目标信息，默认匹配度
            
        match_score = 50  # 基础分
        
        # 2.1 学术方向匹配
        if student.academic_preference and school.is_985:
            match_score += 20  # 学术导向与985高校匹配
        elif student.academic_preference and (school.is_211 or school.is_double_first_class):
            match_score += 15  # 学术导向与211/双一流高校匹配
            
        # 2.2 就业方向匹配
        if student.career_direction:
            # 学术科研方向更适合985/211
            if student.career_direction == '学术科研':
                if school.is_985:
                    match_score += 20
                elif school.is_211 or school.is_double_first_class:
                    match_score += 15
            # 公务员/事业单位方向匹配度检查
            elif student.career_direction in ['公务员', '事业单位']:
                if '师范' in school.type or '政法' in school.type:
                    match_score += 15
            # 企业就业方向检查
            elif student.career_direction in ['企业就业', '大厂']:
                if school.is_985 or school.is_211:
                    match_score += 15
                if school.province in ['北京', '上海', '广东', '浙江', '江苏']:
                    match_score += 10  # 就业机会多的地区
            # 外企方向检查
            elif student.career_direction == '外企':
                if school.is_985 or school.is_211:
                    match_score += 15
                if school.province in ['北京', '上海', '广东']:
                    match_score += 15  # 外企集中地区
                    
        # 2.3 海外发展计划
        if student.overseas_plan:
            if school.is_985:
                match_score += 15  # 海外认可度高
            elif school.is_211:
                match_score += 10
                
        return min(100, match_score)
        
    def _calculate_location_match(self, student, school):
        """
        计算地理位置匹配度
        3. 城市偏好：对一线城市或特定地区（如上海、成都等）的偏好
        """
        if not student.target_cities:
            return 50  # 没有位置偏好，默认匹配度
            
        # 检查学校所在城市是否在学生偏好城市列表中
        preferred_cities = [city.strip() for city in student.target_cities.split(',')]
        
        if school.city in preferred_cities or school.province in preferred_cities:
            return 100  # 完全匹配城市偏好
        
        # 检查是否是一线城市偏好
        tier1_cities = ['北京', '上海', '广州', '深圳']
        if '一线城市' in preferred_cities and school.city in tier1_cities:
            return 90
            
        # 检查是否在同一省份
        for city in preferred_cities:
            if city in school.province:
                return 80  # 同省份不同城市
        
        return 40  # 不在偏好城市列表
    
    def _calculate_economic_match(self, student, school):
        """
        计算经济条件匹配度
        5. 经济条件：能否接受高学费/生活成本较高的城市
        """
        if not student.economic_condition:
            return 50  # 没有经济条件信息，默认匹配度
            
        # 高消费城市列表
        high_cost_cities = ['北京', '上海', '深圳', '广州', '杭州']
        # 中等消费城市
        medium_cost_cities = ['南京', '武汉', '成都', '重庆', '西安', '天津', '苏州', '厦门']
        
        if student.economic_condition == '高':
            return 100  # 可以接受任何城市
        elif student.economic_condition == '中':
            if school.city in high_cost_cities:
                return 60  # 能接受但压力较大
            elif school.city in medium_cost_cities:
                return 90  # 比较合适
            else:
                return 100  # 低消费城市，完全匹配
        else:  # 经济条件有限
            if school.city in high_cost_cities:
                return 30  # 不太适合
            elif school.city in medium_cost_cities:
                return 60  # 有一定压力
            else:
                return 90  # 较为适合
                
    def _calculate_score_match(self, student, school, major=None):
        """
        计算考研分数匹配度
        6. 历年分数线匹配：目标学校专业的复试线与用户匹配程度
        """
        if not student.estimated_score:
            return 50  # 没有预估分数，默认匹配度
            
        # 获取该校相关专业的历年复试线
        cutoff_score = self._get_major_cutoff_score(school, major)
        
        # 计算学生预估分数与复试线的差距
        score_diff = student.estimated_score - cutoff_score
        
        if score_diff >= 20:  # 大幅超过复试线
            return 90  # 非常有把握
        elif score_diff >= 10:  # 明显超过复试线
            return 80  # 把握较大
        elif score_diff >= 0:  # 达到或略超复试线
            return 70  # 有一定把握
        elif score_diff >= -10:  # 略低于复试线
            return 50  # 有风险，需努力
        elif score_diff >= -20:  # 明显低于复试线
            return 30  # 风险较大
        else:  # 大幅低于复试线
            return 10  # 极高风险
    
    def _calculate_strategy_match(self, student, school, score_match):
        """
        根据学生的策略偏好调整最终匹配度
        7. 院校梯度偏好：是否更倾向于"保守/冲刺/稳妥"策略
        """
        if not student.strategy_preference:
            return score_match  # 没有策略偏好，不调整
            
        # 根据分数匹配度确定学校类型
        if score_match >= 80:
            school_type = "保底"
        elif score_match >= 60:
            school_type = "匹配"
        else:
            school_type = "冲刺"
            
        # 根据策略偏好调整匹配度
        if student.strategy_preference == '保守' and school_type == "保底":
            return min(100, score_match * 1.2)  # 提升保底学校的匹配度
        elif student.strategy_preference == '冲刺' and school_type == "冲刺":
            return min(100, score_match * 1.2)  # 提升冲刺学校的匹配度
        elif student.strategy_preference == '均衡':
            if school_type == "匹配":
                return min(100, score_match * 1.1)  # 略微提升匹配学校
                
        return score_match  # 不调整
    
    def _get_school_tier(self, school_name):
        """获取学校层次，返回1-4的整数，1为最高层次"""
        # 985高校列表(示例)
        tier1_schools = ['清华大学', '北京大学', '复旦大学', '上海交通大学', '浙江大学', '南京大学', 
                        '中国科学技术大学', '哈尔滨工业大学', '西安交通大学', '中山大学']
        
        # 211高校但非985(示例)
        tier2_schools = ['北京师范大学', '北京理工大学', '重庆大学', '东北大学', '华中师范大学',
                        '厦门大学', '四川大学', '华南理工大学', '中央民族大学']
                        
        # 双一流但非211(示例)
        tier3_schools = ['上海财经大学', '中国传媒大学', '中央音乐学院', '北京体育大学']
        
        if school_name in tier1_schools:
            return 1
        elif school_name in tier2_schools:
            return 2
        elif school_name in tier3_schools:
            return 3
        else:
            return 4
            
    def _is_same_major_category(self, major1, major2):
        """判断两个专业是否属于同一大类"""
        # 专业大类划分
        major_categories = {
            '计算机类': ['计算机科学与技术', '软件工程', '人工智能', '数据科学', '网络工程', '信息安全'],
            '经济类': ['经济学', '金融学', '国际经济与贸易', '财政学', '金融工程'],
            '管理类': ['工商管理', '市场营销', '会计学', '财务管理', '人力资源管理'],
            '文学类': ['中国语言文学', '新闻学', '英语', '日语', '俄语', '法语'],
            '理学类': ['数学', '物理学', '化学', '生物学', '地理科学', '心理学'],
            '工学类': ['机械工程', '电气工程', '土木工程', '化学工程', '材料科学与工程'],
            '医学类': ['临床医学', '口腔医学', '中医学', '药学', '护理学'],
            '法学类': ['法学', '知识产权', '国际法'],
            '教育学类': ['教育学', '学前教育', '特殊教育', '教育技术学']
        }
        
        # 查找每个专业所属的大类
        category1 = None
        category2 = None
        
        for category, majors in major_categories.items():
            if any(m in major1 for m in majors):
                category1 = category
            if any(m in major2 for m in majors):
                category2 = category
                
        return category1 == category2 and category1 is not None
        
    def _is_related_major(self, major1, major2):
        """判断两个专业是否相关"""
        # 相关专业组合
        related_majors = [
            ['计算机科学与技术', '电子工程', '通信工程', '软件工程', '数据科学'],
            ['经济学', '金融学', '会计学', '财务管理'],
            ['中文', '新闻学', '传播学', '广告学'],
            ['机械工程', '自动化', '机电工程'],
            ['法学', '政治学', '社会学']
        ]
        
        for group in related_majors:
            if any(m in major1 for m in group) and any(m in major2 for m in group):
                return True
                
        return False
        
    def _get_major_cutoff_score(self, school, major=None):
        """获取学校专业的历年复试分数线"""
        # 根据学校层次预估分数线
        base_score = 0
        if school.is_985:
            base_score = 350  # 985院校复试线预估
        elif school.is_211:
            base_score = 330  # 211院校复试线预估
        elif school.is_double_first_class:
            base_score = 320  # 双一流院校复试线预估
        else:
            base_score = 300  # 其他院校复试线预估
            
        # 如果是热门专业，分数线上浮
        if major:
            hot_majors = ['计算机科学与技术', '人工智能', '软件工程', '金融学', '会计学']
            if major.name in hot_majors:
                base_score += 15
                
        return base_score
    
    def recommend_schools(self, student_id, strategy="balanced", num_recommendations=9):
        """
        根据学生情况推荐考研院校
        
        参数:
            student_id: 学生ID
            strategy: 推荐策略，可选值：
                - "aggressive": 偏向冲刺
                - "conservative": 偏向保底
                - "balanced": 平衡策略（默认）
            num_recommendations: 推荐学校数量
            
        返回:
            包含推荐结果的字典
        """
        try:
            # 获取学生信息
            student = Student.objects.get(id=student_id)
            
            # 获取所有学校
            schools = School.objects.all()
            
            results = []
            for school in schools:
                # 获取该校热门专业
                majors_queryset = Major.objects.filter(schools=school)
                majors = list(majors_queryset[:3])  # 最多考虑3个专业，转换为列表防止后续查询问题
                
                # 每个学校计算多个维度的匹配度
                # 1. 用户画像维度（本科专业、院校、GPA等）
                profile_match = self._calculate_user_profile_match(student, school, majors[0] if majors else None)
                
                # 2. 职业目标维度（学术、就业导向等）
                career_match = self._calculate_career_match(student, school, majors[0] if majors else None)
                
                # 3. 地域偏好维度
                location_match = self._calculate_location_match(student, school)
                
                # 5. 经济条件维度
                economic_match = self._calculate_economic_match(student, school)
                
                # 6. 考试分数维度
                score_match = self._calculate_score_match(student, school, majors[0] if majors else None)
                
                # 综合计算最终匹配度（不同维度的加权平均）
                # 根据学生的具体情况调整各维度权重
                weights = {
                    'profile': 0.25,   # 用户画像
                    'career': 0.15,    # 职业目标
                    'location': 0.15,  # 地域偏好
                    'economic': 0.05,  # 经济条件
                    'score': 0.4       # 分数匹配
                }
                
                # 如果学生特别关注某些维度，可以调整权重
                if student.career_direction and student.career_direction in ['学术科研', '外企']:
                    weights['career'] = 0.25  # 提高职业目标维度权重
                    weights['profile'] = 0.20
                    weights['score'] = 0.35
                
                if student.target_cities:
                    weights['location'] = 0.20  # 提高地域偏好维度权重
                    weights['profile'] = 0.20
                    weights['score'] = 0.35
                
                # 计算综合匹配分数
                match_score = (
                    profile_match * weights['profile'] +
                    career_match * weights['career'] +
                    location_match * weights['location'] +
                    economic_match * weights['economic'] +
                    score_match * weights['score']
                )
                
                # 7. 根据学生的策略偏好调整最终匹配度
                match_score = self._calculate_strategy_match(student, school, match_score)
                
                # 确定院校类别（冲刺、匹配、保底）
                # 设置更低的分数门槛，确保有不同类别
                if score_match >= 60:
                    category = "safety"  # 保底院校
                elif score_match >= 40:
                    category = "match"   # 匹配院校
                else:
                    category = "challenge"  # 冲刺院校
                    
                # 策略偏好会影响院校分类
                if strategy == "aggressive":
                    if score_match >= 50:  # 降低保底院校标准
                        category = "safety"
                    elif score_match >= 30:  # 降低匹配院校标准
                        category = "match"
                elif strategy == "conservative":
                    if score_match < 50:  # 提高冲刺院校标准
                        category = "challenge"
                    elif score_match < 70:  # 提高匹配院校标准
                        category = "match"
                
                # 录取概率计算（主要基于分数匹配度）
                admission_probability = score_match  # 简单起见，可以将分数匹配度直接作为录取概率的指标
                
                # 生成推荐理由
                reason = self._generate_recommendation_reason(student, school, match_score, 
                                                           profile_match, career_match, 
                                                           location_match, score_match)
                
                results.append({
                    'school': school,
                    'match_score': round(match_score, 2),
                    'admission_probability': round(admission_probability, 2),
                    'category': category,
                    'reason': reason,
                    'recommended_majors': list(majors),
                    'dimension_scores': {  # 保存各维度得分，用于前端展示
                        'profile_match': round(profile_match, 2),
                        'career_match': round(career_match, 2),
                        'location_match': round(location_match, 2),
                        'economic_match': round(economic_match, 2),
                        'score_match': round(score_match, 2)
                    }
                })
            
            # 根据匹配度排序
            results = sorted(results, key=lambda x: x['match_score'], reverse=True)
            
            # 强制根据分数分配不同类别，确保至少有一个底、匹配和冲刺院校
            total = len(results)
            if total >= 3:  # 至少需要3个学校才能分类
                # 将学校按匹配度分为三部分
                third = total // 3
                for i, result in enumerate(results):
                    if i < third:  # 前1/3为保底院校
                        result['category'] = 'safety'
                    elif i < 2 * third:  # 中间1/3为匹配院校
                        result['category'] = 'match'
                    else:  # 后1/3为冲刺院校
                        result['category'] = 'challenge'
            
            # 根据策略筛选学校
            safety = [r for r in results if r['category'] == 'safety']
            match = [r for r in results if r['category'] == 'match']
            challenge = [r for r in results if r['category'] == 'challenge']
            
            # 默认比例：3保底+3匹配+3冲刺
            safety_count = 3
            match_count = 3
            challenge_count = 3
            
            # 根据策略调整各类别数量
            if strategy == "aggressive":
                safety_count = 2
                match_count = 2
                challenge_count = 5
            elif strategy == "conservative":
                safety_count = 5
                match_count = 2
                challenge_count = 2
                
            # 取各类别的前N个学校
            final_safety = safety[:safety_count]
            final_match = match[:match_count]
            final_challenge = challenge[:challenge_count]
            
            # 如果某类别不足，从其他类别补充
            remaining = num_recommendations - len(final_safety) - len(final_match) - len(final_challenge)
            if remaining > 0:
                # 优先从match类别补充
                if len(match) > match_count:
                    additional = match[match_count:match_count + remaining]
                    final_match.extend(additional)
                    remaining -= len(additional)
                
                # 其次从safety类别补充
                if remaining > 0 and len(safety) > safety_count:
                    additional = safety[safety_count:safety_count + remaining]
                    final_safety.extend(additional)
                    remaining -= len(additional)
                
                # 最后从challenge类别补充
                if remaining > 0 and len(challenge) > challenge_count:
                    additional = challenge[challenge_count:challenge_count + remaining]
                    final_challenge.extend(additional)
            
            # 合并结果
            final_results = final_safety + final_match + final_challenge
            
            # 限制总数量
            final_results = final_results[:num_recommendations]
            
            # 删除该学生的旧推荐记录，确保不会影响分类显示
            Recommendation.objects.filter(student=student).delete()
            
            # 保存推荐结果到数据库
            for result in final_results:
                school = result['school']
                major = result['recommended_majors'][0] if result['recommended_majors'] else None
                
                # 创建推荐记录
                Recommendation.objects.create(
                    student=student,
                    school=school,
                    major=major,
                    recommendation_type=result['category'],
                    match_score=result['match_score'],
                    admission_probability=result['admission_probability'],
                    recommendation_reason=result['reason'],
                )
            
            return {
                'status': 'success',
                'recommendations': final_results,
                'student_profile': {
                    'name': student.name,
                    'current_school': student.current_school,
                    'current_major': student.current_major,
                    'grade_rank': student.gpa_ranking or student.grade_rank,
                    'target_major': student.target_major_category
                }
            }
            
        except Student.DoesNotExist:
            return {
                'status': 'error',
                'message': f'学生ID {student_id} 不存在'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'推荐过程中发生错误: {str(e)}'
            }
            
    def _generate_recommendation_reason(self, student, school, match_score, 
                                       profile_match, career_match, 
                                       location_match, score_match):
        """根据多维度匹配情况生成推荐理由"""
        reasons = []
        
        # 根据整体匹配度
        if match_score >= 85:
            reasons.append(f"该校与您的整体情况匹配度极高（{match_score:.0f}%），是非常理想的选择")
        elif match_score >= 70:
            reasons.append(f"该校与您的整体情况匹配度较高（{match_score:.0f}%），是很好的选择")
        elif match_score >= 60:
            reasons.append(f"该校与您的整体情况匹配度一般（{match_score:.0f}%），可以考虑")
        else:
            reasons.append(f"该校与您的整体情况匹配度较低（{match_score:.0f}%），建议慎重考虑")
        
        # 分析最突出的优势维度
        dimensions = {
            '学业背景': profile_match,
            '职业目标': career_match,
            '地理位置': location_match,
            '分数匹配': score_match
        }
        
        # 找出最高的两个维度
        top_dimensions = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)[:2]
        for dim_name, dim_score in top_dimensions:
            if dim_score >= 80:
                reasons.append(f"{dim_name}匹配度非常高（{dim_score:.0f}%）")
            elif dim_score >= 70:
                reasons.append(f"{dim_name}匹配度较高（{dim_score:.0f}%）")
        
        # 根据学校特点补充说明
        if school.is_985:
            reasons.append("985高校，学术资源丰富，就业认可度高")
        elif school.is_211:
            reasons.append("211高校，师资力量较强，就业前景好")
        elif school.is_double_first_class:
            reasons.append("双一流高校，优势学科实力突出")
        
        # 根据就业目标补充
        if student.career_direction:
            if student.career_direction == '学术科研' and (school.is_985 or school.is_211):
                reasons.append("适合您的学术研究发展方向")
            elif student.career_direction in ['公务员', '事业单位'] and hasattr(school, 'type') and school.type and ('师范' in school.type or '政法' in school.type):
                reasons.append("该校毕业生在公职考试中表现出色")
            elif student.career_direction == '外企' and hasattr(school, 'city') and school.city and school.city in ['北京', '上海', '深圳', '广州']:
                reasons.append("所在城市外企资源丰富，对接国际就业市场")
            elif student.career_direction in ['企业就业', '大厂'] and hasattr(school, 'city') and school.city and school.city in ['北京', '上海', '深圳', '杭州']:
                reasons.append("地处就业机会丰富的城市，大型企业集中")
        
        return "；".join(reasons) + "。"