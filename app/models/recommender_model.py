import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Any, Optional, Tuple
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from .user_profile import UserProfiler

class MLPMatchingModel(nn.Module):
    """深度学习匹配模型，用于用户与院校专业的匹配度计算"""
    
    def __init__(self, input_dim: int, hidden_dims: List[int]):
        super(MLPMatchingModel, self).__init__()
        self.layers = nn.ModuleList()
        
        # 构建隐藏层
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            self.layers.append(nn.Linear(prev_dim, hidden_dim))
            self.layers.append(nn.ReLU())
            self.layers.append(nn.BatchNorm1d(hidden_dim))
            self.layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim
        
        # 输出层，输出单一匹配分数
        self.output_layer = nn.Linear(prev_dim, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, user_vec: torch.Tensor, school_vec: torch.Tensor) -> torch.Tensor:
        """前向传播计算匹配分数"""
        # 拼接用户向量和学校向量
        combined = torch.cat([user_vec, school_vec], dim=1)
        
        # 通过隐藏层
        x = combined
        for layer in self.layers:
            x = layer(x)
        
        # 输出分数 (0-1)
        score = self.sigmoid(self.output_layer(x))
        return score


class HybridRecommender:
    """混合推荐系统模型"""
    
    def __init__(self, use_gpu: bool = True):
        self.device = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")
        self.user_profiler = UserProfiler(use_gpu=use_gpu)
        
        # 初始化模型组件
        self.deep_model = None
        self.lgbm_model = None
        self.school_features_scaler = StandardScaler()
        self.user_features_scaler = StandardScaler()
        
        # 模型权重
        self.deep_model_weight = 0.6
        self.lgbm_model_weight = 0.4
    
    def build_models(self, user_input_dim: int, school_input_dim: int):
        """初始化模型结构"""
        # 创建深度匹配模型
        combined_input_dim = user_input_dim + school_input_dim
        self.deep_model = MLPMatchingModel(
            input_dim=combined_input_dim,
            hidden_dims=[256, 128, 64]
        ).to(self.device)
    
    def train(self, 
              user_data: List[Dict[str, Any]], 
              school_data: List[Dict[str, Any]], 
              training_samples: List[Dict[str, Any]], 
              epochs: int = 10, 
              batch_size: int = 64):
        """训练混合推荐模型"""
        # 准备训练数据
        X_train, y_train = self._prepare_training_data(user_data, school_data, training_samples)
        X_train_lgbm, y_train_lgbm = self._prepare_lgbm_data(user_data, school_data, training_samples)
        
        # 拟合标准化器
        self.user_profiler.fit_normalizer(user_data)
        
        # 分割训练集和验证集
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42
        )
        
        # 训练LightGBM模型
        lgb_train = lgb.Dataset(X_train_lgbm, y_train_lgbm)
        lgb_params = {
            'boosting_type': 'gbdt',
            'objective': 'binary',
            'metric': 'auc',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'device_type': 'gpu' if torch.cuda.is_available() else 'cpu'
        }
        self.lgbm_model = lgb.train(lgb_params, lgb_train, num_boost_round=100)
        
        # 训练深度学习模型
        self.deep_model.train()
        optimizer = torch.optim.Adam(self.deep_model.parameters(), lr=0.001)
        criterion = nn.BCELoss()
        
        # 准备PyTorch数据
        X_user = torch.tensor(X_train[:, :X_train.shape[1]//2], dtype=torch.float32).to(self.device)
        X_school = torch.tensor(X_train[:, X_train.shape[1]//2:], dtype=torch.float32).to(self.device)
        y = torch.tensor(y_train, dtype=torch.float32).to(self.device).view(-1, 1)
        
        # 训练循环
        for epoch in range(epochs):
            total_loss = 0
            # 批次处理
            for i in range(0, len(X_train), batch_size):
                user_batch = X_user[i:i+batch_size]
                school_batch = X_school[i:i+batch_size]
                y_batch = y[i:i+batch_size]
                
                # 前向传播
                predictions = self.deep_model(user_batch, school_batch)
                loss = criterion(predictions, y_batch)
                
                # 反向传播与优化
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(X_train):.4f}")
    
    def recommend(self, 
                  user_data: Dict[str, Any], 
                  school_pool: List[Dict[str, Any]], 
                  strategy: str = "balanced",
                  top_n: int = 9) -> List[Dict[str, Any]]:
        """为用户推荐学校"""
        # 根据策略设置模型权重
        self._adjust_weights_by_strategy(strategy)
        
        # 准备用户特征向量
        user_vector = self.user_profiler.vectorize_user(user_data)
        
        # 计算每个学校的推荐得分
        scores = []
        for school in school_pool:
            score = self._calculate_recommendation_score(user_vector, school)
            scores.append({
                'school': school,
                'score': score,
                'risk_level': self._assess_risk_level(score)
            })
        
        # 排序并选择前N个
        scores.sort(key=lambda x: x['score'], reverse=True)
        top_recommendations = scores[:top_n]
        
        # 按风险级别分组推荐
        return self._group_recommendations_by_risk(top_recommendations)
    
    def _prepare_training_data(self, 
                              user_data: List[Dict[str, Any]], 
                              school_data: List[Dict[str, Any]],
                              training_samples: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """准备深度学习模型训练数据"""
        X = []
        y = []
        
        for sample in training_samples:
            user_id = sample['user_id']
            school_id = sample['school_id']
            label = sample['is_admitted']  # 1表示录取，0表示未录取
            
            # 获取用户和学校数据
            user = next((u for u in user_data if u['id'] == user_id), None)
            school = next((s for s in school_data if s['id'] == school_id), None)
            
            if user and school:
                # 向量化
                user_vector = self.user_profiler.vectorize_user(user)
                school_vector = self._vectorize_school(school)
                
                # 拼接特征
                combined = np.concatenate([user_vector, school_vector])
                X.append(combined)
                y.append(label)
        
        return np.array(X), np.array(y)
    
    def _prepare_lgbm_data(self, 
                          user_data: List[Dict[str, Any]], 
                          school_data: List[Dict[str, Any]],
                          training_samples: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """准备LightGBM模型训练数据"""
        X = []
        y = []
        
        for sample in training_samples:
            user_id = sample['user_id']
            school_id = sample['school_id']
            label = sample['is_admitted']
            
            # 获取用户和学校数据
            user = next((u for u in user_data if u['id'] == user_id), None)
            school = next((s for s in school_data if s['id'] == school_id), None)
            
            if user and school:
                # 提取有意义的特征，更适合树模型
                features = [
                    user.get('total_score', 0),
                    user.get('math_score', 0),
                    user.get('english_score', 0),
                    user.get('specialized_score', 0),
                    school.get('min_score', 0),
                    school.get('avg_score', 0),
                    school.get('admission_rate', 0),
                    school.get('rank', 999),  # 学校排名
                    1 if user.get('province') == school.get('province') else 0,  # 是否同省
                    # 可以添加更多特征
                ]
                X.append(features)
                y.append(label)
        
        return np.array(X), np.array(y)
    
    def _vectorize_school(self, school: Dict[str, Any]) -> np.ndarray:
        """将学校数据向量化"""
        features = []
        
        # 数值特征
        features.append(school.get('min_score', 0))
        features.append(school.get('avg_score', 0))
        features.append(school.get('admission_rate', 0))
        features.append(1.0 / (school.get('rank', 999) + 1))  # 排名归一化
        
        # 学校类型one-hot编码
        school_type = school.get('type', '')
        school_types = ['985', '211', '双一流', '普通本科', '专科']
        for t in school_types:
            features.append(1.0 if school_type == t else 0.0)
        
        # 省份编码
        province = school.get('province', '')
        provinces = ['北京', '上海', '广东', '江苏', '浙江', '山东', '四川', '湖北', '湖南', '河北']
        for p in provinces:
            features.append(1.0 if province == p else 0.0)
        
        # 学校专业强度向量（简化版）
        subject_strengths = {
            'math': school.get('math_strength', 0),
            'cs': school.get('cs_strength', 0),
            'physics': school.get('physics_strength', 0),
            'economics': school.get('economics_strength', 0),
            'literature': school.get('literature_strength', 0),
        }
        for subject, strength in subject_strengths.items():
            features.append(strength)
        
        return np.array(features)
    
    def _calculate_recommendation_score(self, user_vector: np.ndarray, school: Dict[str, Any]) -> float:
        """计算推荐分数"""
        # 学校向量化
        school_vector = self._vectorize_school(school)
        
        # LightGBM预测
        lgbm_features = np.concatenate([
            [user_vector[0], user_vector[1], user_vector[2], user_vector[3]], 
            [school.get('min_score', 0), school.get('avg_score', 0), 
             school.get('admission_rate', 0), school.get('rank', 999)]
        ])
        lgbm_score = self.lgbm_model.predict([lgbm_features])[0]
        
        # 深度模型预测
        with torch.no_grad():
            user_tensor = torch.tensor(user_vector, dtype=torch.float32).unsqueeze(0).to(self.device)
            school_tensor = torch.tensor(school_vector, dtype=torch.float32).unsqueeze(0).to(self.device)
            deep_score = self.deep_model(user_tensor, school_tensor).item()
        
        # 加权融合
        final_score = self.lgbm_model_weight * lgbm_score + self.deep_model_weight * deep_score
        
        return final_score
    
    def _adjust_weights_by_strategy(self, strategy: str):
        """根据策略调整模型权重"""
        if strategy == "conservative":
            # 更偏重历史数据和录取概率
            self.lgbm_model_weight = 0.7
            self.deep_model_weight = 0.3
        elif strategy == "aggressive":
            # 更偏重兴趣匹配
            self.lgbm_model_weight = 0.3
            self.deep_model_weight = 0.7
        else:  # balanced
            self.lgbm_model_weight = 0.5
            self.deep_model_weight = 0.5
    
    def _assess_risk_level(self, score: float) -> str:
        """评估风险等级"""
        if score >= 0.8:
            return "保底"
        elif score >= 0.6:
            return "稳妥"
        elif score >= 0.4:
            return "适中"
        elif score >= 0.2:
            return "冲刺"
        else:
            return "高难度"
    
    def _group_recommendations_by_risk(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按风险级别分组推荐结果"""
        # 按风险级别排序
        risk_order = {
            "高难度": 0,
            "冲刺": 1, 
            "适中": 2, 
            "稳妥": 3, 
            "保底": 4
        }
        
        # 分组
        grouped = {}
        for rec in recommendations:
            risk = rec['risk_level']
            if risk not in grouped:
                grouped[risk] = []
            grouped[risk].append(rec)
        
        # 格式化输出
        result = []
        for risk in sorted(grouped.keys(), key=lambda x: risk_order.get(x, 999)):
            for rec in grouped[risk]:
                result.append({
                    'school': rec['school'],
                    'score': rec['score'],
                    'risk_level': risk
                })
                
        return result