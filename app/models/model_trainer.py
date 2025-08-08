import os
import pickle
import json
import torch
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sklearn.model_selection import train_test_split
import pandas as pd
import mlflow
import optuna
from .recommender_model import HybridRecommender
from .user_profile import UserProfiler
from .semantic_matcher import SemanticMatcher

class ModelTrainer:
    """模型训练与管理类，负责模型训练、评估、保存和加载"""
    
    def __init__(self, model_dir: str = "models", use_gpu: bool = True):
        self.model_dir = model_dir
        self.use_gpu = use_gpu
        
        # 创建模型目录
        os.makedirs(model_dir, exist_ok=True)
        
        # 初始化组件
        self.recommender = HybridRecommender(use_gpu=use_gpu)
        self.user_profiler = UserProfiler(use_gpu=use_gpu)
        self.semantic_matcher = SemanticMatcher(use_gpu=use_gpu)
        
    def load_dataset(self, 
                    user_data_path: str, 
                    school_data_path: str, 
                    training_data_path: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """加载训练数据集"""
        # 加载用户数据
        with open(user_data_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        # 加载学校数据
        with open(school_data_path, 'r', encoding='utf-8') as f:
            school_data = json.load(f)
        
        # 加载训练样本
        with open(training_data_path, 'r', encoding='utf-8') as f:
            training_samples = json.load(f)
        
        return user_data, school_data, training_samples
    
    def train_recommender(self, 
                         user_data: List[Dict], 
                         school_data: List[Dict], 
                         training_samples: List[Dict],
                         epochs: int = 10,
                         batch_size: int = 64) -> HybridRecommender:
        """训练推荐模型"""
        print("开始训练推荐模型...")
        
        # 确定用户和学校特征维度
        sample_user = self.user_profiler.vectorize_user(user_data[0])
        sample_school = self.recommender._vectorize_school(school_data[0])
        user_dim = len(sample_user)
        school_dim = len(sample_school)
        
        # 构建模型
        self.recommender.build_models(user_dim, school_dim)
        
        # 启动MLflow追踪
        mlflow.set_experiment("recommender_training")
        with mlflow.start_run():
            # 记录超参数
            mlflow.log_param("epochs", epochs)
            mlflow.log_param("batch_size", batch_size)
            mlflow.log_param("deep_model_weight", self.recommender.deep_model_weight)
            mlflow.log_param("lgbm_model_weight", self.recommender.lgbm_model_weight)
            
            # 训练模型
            self.recommender.train(
                user_data=user_data,
                school_data=school_data,
                training_samples=training_samples,
                epochs=epochs,
                batch_size=batch_size
            )
            
            # 评估模型
            metrics = self.evaluate_model(user_data, school_data, training_samples)
            
            # 记录评估指标
            for key, value in metrics.items():
                mlflow.log_metric(key, value)
        
        return self.recommender
    
    def hyperparameter_tuning(self, 
                             user_data: List[Dict], 
                             school_data: List[Dict], 
                             training_samples: List[Dict],
                             n_trials: int = 20) -> Dict[str, Any]:
        """使用Optuna进行超参数调优"""
        def objective(trial):
            # 定义超参数空间
            epochs = trial.suggest_int("epochs", 5, 20)
            batch_size = trial.suggest_int("batch_size", 16, 128, log=True)
            deep_model_weight = trial.suggest_float("deep_model_weight", 0.1, 0.9)
            hidden_dim_1 = trial.suggest_int("hidden_dim_1", 64, 512, log=True)
            hidden_dim_2 = trial.suggest_int("hidden_dim_2", 32, 256, log=True)
            learning_rate = trial.suggest_float("learning_rate", 1e-5, 1e-2, log=True)
            
            # 创建临时推荐模型
            temp_recommender = HybridRecommender(use_gpu=self.use_gpu)
            temp_recommender.deep_model_weight = deep_model_weight
            temp_recommender.lgbm_model_weight = 1.0 - deep_model_weight
            
            # 确定特征维度
            sample_user = self.user_profiler.vectorize_user(user_data[0])
            sample_school = temp_recommender._vectorize_school(school_data[0])
            user_dim = len(sample_user)
            school_dim = len(sample_school)
            
            # 构建模型
            combined_input_dim = user_dim + school_dim
            temp_recommender.build_models(user_dim, school_dim)
            
            # 分割训练集和验证集
            train_samples, val_samples = train_test_split(training_samples, test_size=0.2, random_state=42)
            
            # 训练模型
            temp_recommender.train(
                user_data=user_data,
                school_data=school_data,
                training_samples=train_samples,
                epochs=epochs,
                batch_size=batch_size
            )
            
            # 评估模型
            metrics = self.evaluate_model(user_data, school_data, val_samples, recommender=temp_recommender)
            
            # 返回主要指标作为优化目标
            return metrics['auc']
        
        # 创建Optuna研究
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)
        
        # 获取最佳超参数
        best_params = study.best_params
        print(f"Best parameters: {best_params}")
        print(f"Best AUC: {study.best_value}")
        
        return best_params
    
    def evaluate_model(self, 
                      user_data: List[Dict], 
                      school_data: List[Dict], 
                      test_samples: List[Dict],
                      recommender: Optional[HybridRecommender] = None) -> Dict[str, float]:
        """评估模型性能"""
        from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
        
        if recommender is None:
            recommender = self.recommender
        
        # 准备预测和实际标签
        y_true = []
        y_pred = []
        
        for sample in test_samples:
            user_id = sample['user_id']
            school_id = sample['school_id']
            is_admitted = sample['is_admitted']
            
            # 获取用户和学校数据
            user = next((u for u in user_data if u['id'] == user_id), None)
            school = next((s for s in school_data if s['id'] == school_id), None)
            
            if user and school:
                # 获取用户向量
                user_vector = self.user_profiler.vectorize_user(user)
                
                # 计算推荐分数
                score = recommender._calculate_recommendation_score(user_vector, school)
                
                y_true.append(is_admitted)
                y_pred.append(score)
        
        # 计算AUC
        auc = roc_auc_score(y_true, y_pred)
        
        # 使用0.5作为阈值，将预测分数转换为二元标签
        y_pred_binary = [1 if p >= 0.5 else 0 for p in y_pred]
        
        # 计算精确率、召回率和F1分数
        precision = precision_score(y_true, y_pred_binary)
        recall = recall_score(y_true, y_pred_binary)
        f1 = f1_score(y_true, y_pred_binary)
        
        metrics = {
            'auc': auc,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
        
        return metrics
    
    def save_model(self, model_name: str = None) -> str:
        """保存模型"""
        if model_name is None:
            # 生成默认模型名称，使用时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = f"recommender_model_{timestamp}"
        
        # 完整模型路径
        model_path = os.path.join(self.model_dir, f"{model_name}.pkl")
        
        # 保存模型
        with open(model_path, 'wb') as f:
            pickle.dump({
                'recommender': self.recommender,
                'user_profiler': self.user_profiler,
                'semantic_matcher': self.semantic_matcher
            }, f)
        
        print(f"模型已保存到: {model_path}")
        return model_path
    
    def load_model(self, model_path: str) -> None:
        """加载模型"""
        try:
            with open(model_path, 'rb') as f:
                models = pickle.load(f)
            
            self.recommender = models['recommender']
            self.user_profiler = models['user_profiler']
            self.semantic_matcher = models['semantic_matcher']
            
            print(f"模型已从 {model_path} 加载")
        except Exception as e:
            print(f"加载模型时出错: {e}")
    
    def generate_synthetic_data(self, 
                               num_users: int = 1000, 
                               num_schools: int = 100, 
                               num_samples: int = 5000) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """生成合成数据用于测试和开发"""
        print(f"生成 {num_users} 个用户, {num_schools} 所学校, {num_samples} 个训练样本...")
        
        # 生成用户数据
        users = []
        for i in range(num_users):
            # 随机总分 (300-750)
            total_score = np.random.randint(300, 750)
            
            # 随机学科分数
            math_score = np.random.randint(50, 150)
            english_score = np.random.randint(50, 150)
            specialized_score = np.random.randint(100, 300)
            
            # 随机省份
            provinces = ['北京', '上海', '广东', '江苏', '浙江', '山东', '四川', '湖北', '湖南', '河北']
            province = np.random.choice(provinces)
            
            # 随机兴趣
            all_interests = ['计算机科学', '人工智能', '数据科学', '金融学', '经济学', 
                           '文学', '历史', '物理', '化学', '生物', '医学', '法律', 
                           '工程学', '艺术', '设计', '心理学', '社会学', '教育学']
            interests = np.random.choice(all_interests, size=np.random.randint(1, 5), replace=False).tolist()
            
            # 随机优势和弱点
            all_subjects = ['数学', '英语', '物理', '化学', '生物', '政治', '历史', '地理', '计算机']
            strengths = np.random.choice(all_subjects, size=np.random.randint(1, 4), replace=False).tolist()
            weaknesses = np.random.choice([s for s in all_subjects if s not in strengths], 
                                         size=np.random.randint(1, 3), replace=False).tolist()
            
            # 随机职业目标
            career_goals = np.random.choice([
                '软件工程师', '数据分析师', '金融分析师', '医生', '律师', '教师', 
                '研究员', '工程师', '设计师', '管理咨询', '创业', '公务员'
            ])
            
            users.append({
                'id': i + 1,
                'name': f'用户_{i+1}',
                'total_score': total_score,
                'math_score': math_score,
                'english_score': english_score,
                'specialized_score': specialized_score,
                'province': province,
                'interests': interests,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'career_goals': career_goals,
                'risk_preference': np.random.choice(['conservative', 'balanced', 'aggressive'])
            })
        
        # 生成学校数据
        schools = []
        for i in range(num_schools):
            # 随机录取分数线 (350-700)
            min_score = np.random.randint(350, 700)
            
            # 学校排名 (1-500)
            rank = i + 1 if i < 100 else np.random.randint(100, 500)
            
            # 学校类型
            if rank <= 42:  # 大约前42所是985高校
                school_type = '985'
            elif rank <= 116:  # 大约前116所是211高校
                school_type = '211'
            elif rank <= 200:  
                school_type = '双一流'
            else:
                school_type = '普通本科'
            
            # 随机省份
            provinces = ['北京', '上海', '广东', '江苏', '浙江', '山东', '四川', '湖北', '湖南', '河北']
            province = np.random.choice(provinces)
            
            # 随机学科强度 (1-10)
            schools.append({
                'id': i + 1,
                'name': f'学校_{i+1}',
                'rank': rank,
                'type': school_type,
                'province': province,
                'min_score': min_score,
                'avg_score': min_score + np.random.randint(10, 50),
                'admission_rate': np.random.uniform(0.05, 0.8),
                'math_strength': np.random.randint(1, 11),
                'cs_strength': np.random.randint(1, 11),
                'physics_strength': np.random.randint(1, 11),
                'economics_strength': np.random.randint(1, 11),
                'literature_strength': np.random.randint(1, 11)
            })
        
        # 生成训练样本
        samples = []
        for i in range(num_samples):
            # 随机选择用户和学校
            user_id = np.random.randint(1, num_users + 1)
            school_id = np.random.randint(1, num_schools + 1)
            
            # 获取用户和学校
            user = next(u for u in users if u['id'] == user_id)
            school = next(s for s in schools if s['id'] == school_id)
            
            # 生成录取标签（简化模型：分数高于最低分则录取）
            is_admitted = 1 if user['total_score'] >= school['min_score'] else 0
            
            # 增加一些随机性
            if np.random.rand() < 0.1:  # 10% 的随机性
                is_admitted = 1 - is_admitted
            
            samples.append({
                'user_id': user_id,
                'school_id': school_id,
                'is_admitted': is_admitted
            })
        
        return users, schools, samples