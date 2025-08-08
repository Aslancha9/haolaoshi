import os
import torch
import numpy as np
import time
from app.models.user_profile import UserProfiler
from app.models.recommender_model import HybridRecommender
from app.models.semantic_matcher import SemanticMatcher
from app.models.model_trainer import ModelTrainer

def test_gpu_availability():
    """测试GPU是否可用"""
    print("\n=== GPU可用性测试 ===")
    if torch.cuda.is_available():
        print(f"GPU可用: {torch.cuda.get_device_name(0)}")
        print(f"CUDA版本: {torch.version.cuda}")
        print(f"可用GPU数量: {torch.cuda.device_count()}")
        
        # 简单性能测试
        # 创建随机矩阵
        size = 5000
        a = torch.randn(size, size, device="cuda")
        b = torch.randn(size, size, device="cuda")
        
        # GPU计时
        torch.cuda.synchronize()
        start = time.time()
        c = torch.matmul(a, b)
        torch.cuda.synchronize()
        gpu_time = time.time() - start
        
        # CPU计时
        a_cpu = a.cpu()
        b_cpu = b.cpu()
        start = time.time()
        c_cpu = torch.matmul(a_cpu, b_cpu)
        cpu_time = time.time() - start
        
        print(f"矩阵乘法 ({size}x{size}):")
        print(f"  GPU时间: {gpu_time:.4f} 秒")
        print(f"  CPU时间: {cpu_time:.4f} 秒")
        print(f"  加速比: {cpu_time/gpu_time:.1f}x")
    else:
        print("警告: GPU不可用，将使用CPU运行模型")

def test_user_profiler():
    """测试用户画像模块"""
    print("\n=== 用户画像模块测试 ===")
    # 创建用户画像模型
    profiler = UserProfiler(use_gpu=True)
    
    # 测试用户数据
    user_data = {
        "name": "测试用户",
        "total_score": 650,
        "math_score": 130,
        "english_score": 120,
        "specialized_score": 140,
        "province": "北京",
        "interests": ["人工智能", "数据科学", "金融科技"],
        "strengths": ["数学", "编程", "英语"],
        "weaknesses": ["物理"],
        "career_goals": "从事人工智能研究或大数据分析工作",
        "risk_preference": "balanced"
    }
    
    # 提取特征
    print("提取用户特征...")
    start_time = time.time()
    features = profiler.extract_features(user_data)
    print(f"特征提取完成，用时 {time.time() - start_time:.4f} 秒")
    print(f"特征数量: {len(features)}")
    print("前10个特征:")
    for i, (name, value) in enumerate(list(features.items())[:10]):
        print(f"  {name}: {value:.4f}")
    
    # 向量化用户
    print("\n用户向量化...")
    start_time = time.time()
    vector = profiler.vectorize_user(user_data)
    print(f"向量化完成，用时 {time.time() - start_time:.4f} 秒")
    print(f"向量维度: {len(vector)}")
    return profiler, user_data

def test_semantic_matcher():
    """测试语义匹配模块"""
    print("\n=== 语义匹配模块测试 ===")
    # 创建语义匹配模型
    matcher = SemanticMatcher(use_gpu=True)
    
    # 测试数据
    user_interests = ["人工智能", "机器学习", "数据分析"]
    career_goals = "从事人工智能研究或大数据分析工作"
    
    # 模拟专业数据
    majors = [
        {
            "id": 1,
            "name": "计算机科学与技术",
            "description": "计算机科学与技术专业培养掌握计算机科学与技术包括计算机硬件、软件与应用的基本理论、基本知识和基本技能与方法，能在科研部门、教育单位、企业、事业、技术和行政管理部门等单位从事计算机教学、科学研究和应用的计算机科学与技术学科的高级科学技术人才。",
            "career_prospects": "毕业生可在IT企业、互联网公司从事软件开发、系统架构设计、技术研发等工作。"
        },
        {
            "id": 2,
            "name": "软件工程",
            "description": "软件工程专业以计算机科学与技术学科为基础，强调软件开发的工程性，使学生在掌握计算机科学与技术方面知识和技能的基础上，熟悉软件开发的流程和管理，具备软件分析、设计、编码、测试与维护的基本能力。",
            "career_prospects": "毕业生可在各类企业从事软件设计、开发、测试、维护等工作。"
        },
        {
            "id": 3,
            "name": "人工智能",
            "description": "人工智能专业培养具备良好的数学基础和扎实的计算机科学基础，掌握人工智能的基本理论、方法与技术，具有一定的创新能力，能够在企业、高校和科研院所从事人工智能系统、产品或解决方案的设计、开发与应用研究的高级专门人才。",
            "career_prospects": "毕业生可在AI研究机构、科技公司从事机器学习、深度学习、计算机视觉等研发工作。"
        },
        {
            "id": 4,
            "name": "金融学",
            "description": "金融学专业培养具备金融学方面的理论知识和业务技能，能在银行、证券、投资、保险及其他经济管理部门和企业从事相关工作的专门人才。",
            "career_prospects": "毕业生可在银行、证券公司、投资公司等金融机构从事投资分析、风险管理等工作。"
        },
        {
            "id": 5,
            "name": "数据科学与大数据技术",
            "description": "数据科学与大数据技术专业培养掌握数据科学与大数据技术的基本理论和方法，具备大数据采集、处理、分析和应用的基本能力，能够从事大数据相关产品、技术的研究、开发和应用的高级专门人才。",
            "career_prospects": "毕业生可在互联网企业、金融机构等从事数据分析、数据挖掘、商业智能等工作。"
        }
    ]
    
    # 测试兴趣匹配
    print("测试兴趣与专业匹配...")
    start_time = time.time()
    interest_matches = matcher.match_interests_to_majors(user_interests, majors)
    print(f"匹配完成，用时 {time.time() - start_time:.4f} 秒")
    print("兴趣匹配结果:")
    for match in interest_matches:
        print(f"  {match['major']['name']}: {match['similarity']:.4f}")
    
    # 测试职业目标匹配
    print("\n测试职业目标与专业匹配...")
    start_time = time.time()
    career_matches = matcher.match_career_goals_to_majors(career_goals, majors)
    print(f"匹配完成，用时 {time.time() - start_time:.4f} 秒")
    print("职业目标匹配结果:")
    for match in career_matches:
        print(f"  {match['major']['name']}: {match['similarity']:.4f}")
    
    # 测试综合推荐
    print("\n测试综合专业推荐...")
    user_data = {
        "interests": user_interests,
        "career_goals": career_goals
    }
    start_time = time.time()
    recommendations = matcher.get_major_recommendations(user_data, majors)
    print(f"推荐完成，用时 {time.time() - start_time:.4f} 秒")
    print("专业推荐结果:")
    for rec in recommendations:
        print(f"  {rec['major']['name']}: {rec['score']:.4f} (兴趣:{rec['interest_score']:.4f}, 职业:{rec['career_score']:.4f})")
    
    return matcher

def test_hybrid_recommender(profiler, user_data):
    """测试混合推荐模型"""
    print("\n=== 混合推荐模型测试 ===")
    # 创建混合推荐模型
    recommender = HybridRecommender(use_gpu=True)
    
    # 模拟学校数据
    schools = []
    for i in range(1, 31):
        min_score = 550 - i * 5  # 学校分数递减
        
        # 根据排名确定学校类型
        if i <= 10:
            school_type = "985"
        elif i <= 20:
            school_type = "211"
        else:
            school_type = "双一流" if i <= 25 else "普通本科"
        
        # 生成学校数据
        schools.append({
            "id": i,
            "name": f"测试大学{i}",
            "rank": i,
            "type": school_type,
            "province": ["北京", "上海", "广东", "江苏", "浙江"][i % 5],
            "min_score": min_score,
            "avg_score": min_score + 20,
            "admission_rate": 0.8 - i * 0.02,
            "math_strength": np.random.randint(1, 11),
            "cs_strength": np.random.randint(1, 11),
            "physics_strength": np.random.randint(1, 11),
            "economics_strength": np.random.randint(1, 11),
            "literature_strength": np.random.randint(1, 11)
        })
    
    # 初始化模型结构
    # 向量化一个样本用户和学校，以确定维度
    user_vector = profiler.vectorize_user(user_data)
    school_vector = recommender._vectorize_school(schools[0])
    
    user_dim = len(user_vector)
    school_dim = len(school_vector)
    
    print(f"用户向量维度: {user_dim}")
    print(f"学校向量维度: {school_dim}")
    
    recommender.build_models(user_dim, school_dim)
    
    # 生成简化的训练数据
    users = [user_data]
    user_data["id"] = 1
    training_samples = []
    
    # 为每所学校生成一个训练样本
    for school in schools:
        # 简单规则：如果用户总分高于学校最低分，则被录取
        is_admitted = 1 if user_data["total_score"] >= school["min_score"] else 0
        training_samples.append({
            "user_id": 1,
            "school_id": school["id"],
            "is_admitted": is_admitted
        })
    
    # 训练模型
    print("训练混合推荐模型...")
    start_time = time.time()
    recommender.train(users, schools, training_samples, epochs=2, batch_size=8)
    print(f"训练完成，用时 {time.time() - start_time:.4f} 秒")
    
    # 测试推荐
    print("\n测试学校推荐...")
    for strategy in ["conservative", "balanced", "aggressive"]:
        print(f"\n策略: {strategy}")
        start_time = time.time()
        recommendations = recommender.recommend(user_data, schools, strategy=strategy, top_n=9)
        print(f"推荐完成，用时 {time.time() - start_time:.4f} 秒")
        print("推荐结果:")
        for rec in recommendations[:3]:  # 只显示前3个
            school = rec["school"]
            print(f"  {school['name']} (排名:{school['rank']}, 类型:{school['type']}), 分数:{rec['score']:.4f}, 风险:{rec['risk_level']}")
    
    return recommender

def test_model_trainer():
    """测试模型训练器"""
    print("\n=== 模型训练器测试 ===")
    # 创建模型训练器
    trainer = ModelTrainer(use_gpu=True)
    
    # 测试生成合成数据
    print("生成合成训练数据...")
    start_time = time.time()
    users, schools, samples = trainer.generate_synthetic_data(num_users=50, num_schools=20, num_samples=200)
    print(f"数据生成完成，用时 {time.time() - start_time:.4f} 秒")
    print(f"生成 {len(users)} 个用户, {len(schools)} 所学校, {len(samples)} 个训练样本")
    
    # 训练推荐模型
    print("\n训练推荐模型...")
    start_time = time.time()
    trainer.train_recommender(users, schools, samples, epochs=2, batch_size=32)
    print(f"训练完成，用时 {time.time() - start_time:.4f} 秒")
    
    # 评估模型
    print("\n评估模型...")
    metrics = trainer.evaluate_model(users, schools, samples)
    print("评估指标:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.4f}")
    
    # 保存模型
    model_path = trainer.save_model()
    print(f"\n模型已保存至: {model_path}")

if __name__ == "__main__":
    # 运行测试
    test_gpu_availability()
    profiler, user_data = test_user_profiler()
    matcher = test_semantic_matcher()
    recommender = test_hybrid_recommender(profiler, user_data)
    # 注释掉训练器测试，因为需要更多时间
    # test_model_trainer()  # 取消注释以运行模型训练器测试