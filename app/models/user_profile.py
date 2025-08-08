import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import torch
from transformers import BertModel, BertTokenizer

class UserProfiler:
    """用户画像建模类，负责特征工程和向量化"""
    
    def __init__(self, use_gpu: bool = True):
        self.device = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")
        # 加载BERT模型用于兴趣向量化
        self.bert_tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
        self.bert_model = BertModel.from_pretrained('bert-base-chinese').to(self.device)
        self.bert_model.eval()
        
        # 特征归一化参数
        self.feature_means = {}
        self.feature_stds = {}
        
    def fit_normalizer(self, user_data: List[Dict[str, Any]]):
        """根据用户数据拟合归一化参数"""
        df = pd.DataFrame(user_data)
        numeric_features = ['total_score', 'math_score', 'english_score', 'specialized_score']
        
        for feature in numeric_features:
            if feature in df.columns:
                self.feature_means[feature] = df[feature].mean()
                self.feature_stds[feature] = df[feature].std()
    
    def extract_features(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """从用户数据中提取特征"""
        features = {}
        
        # 基本信息特征
        features['total_score'] = self._normalize(user_data.get('total_score', 0), 'total_score')
        features['math_score'] = self._normalize(user_data.get('math_score', 0), 'math_score')
        features['english_score'] = self._normalize(user_data.get('english_score', 0), 'english_score')
        features['specialized_score'] = self._normalize(user_data.get('specialized_score', 0), 'specialized_score')
        
        # 省份特征（one-hot编码）
        province = user_data.get('province', '')
        province_features = self._one_hot_encode_province(province)
        features.update(province_features)
        
        # 风险偏好
        risk_preference = user_data.get('risk_preference', 'balanced')
        risk_features = self._encode_risk_preference(risk_preference)
        features.update(risk_features)
        
        # 兴趣向量化 - BERT处理
        interests = user_data.get('interests', [])
        interest_embedding = self._get_text_embedding(' '.join(interests))
        for i, val in enumerate(interest_embedding):
            features[f'interest_vec_{i}'] = val
            
        # 职业目标向量化
        career_goals = user_data.get('career_goals', '')
        career_embedding = self._get_text_embedding(career_goals)
        for i, val in enumerate(career_embedding):
            features[f'career_vec_{i}'] = val
        
        return features
    
    def _normalize(self, value: float, feature_name: str) -> float:
        """归一化数值特征"""
        if feature_name not in self.feature_means:
            return value
        
        mean = self.feature_means[feature_name]
        std = self.feature_stds[feature_name]
        
        if std == 0:
            return 0
        
        return (value - mean) / std
    
    def _one_hot_encode_province(self, province: str) -> Dict[str, float]:
        """省份one-hot编码"""
        # 简化版本，实际应从数据库获取所有省份列表
        provinces = ['北京', '上海', '广东', '江苏', '浙江', '山东', '四川', '湖北', '湖南', '河北']
        encoded = {}
        
        for p in provinces:
            encoded[f'province_{p}'] = 1.0 if province == p else 0.0
        
        # 其他省份
        if province not in provinces and province:
            encoded['province_other'] = 1.0
        else:
            encoded['province_other'] = 0.0
            
        return encoded
    
    def _encode_risk_preference(self, risk_preference: str) -> Dict[str, float]:
        """风险偏好编码"""
        preferences = {
            'conservative': {'risk_conservative': 1.0, 'risk_balanced': 0.0, 'risk_aggressive': 0.0},
            'balanced': {'risk_conservative': 0.0, 'risk_balanced': 1.0, 'risk_aggressive': 0.0},
            'aggressive': {'risk_conservative': 0.0, 'risk_balanced': 0.0, 'risk_aggressive': 1.0}
        }
        
        return preferences.get(risk_preference, preferences['balanced'])
    
    def _get_text_embedding(self, text: str, max_length: int = 512) -> List[float]:
        """使用BERT获取文本嵌入"""
        if not text:
            # 返回零向量
            return [0.0] * 768  # BERT base hidden size
        
        with torch.no_grad():
            inputs = self.bert_tokenizer(text, return_tensors="pt", 
                                         padding=True, truncation=True, 
                                         max_length=max_length).to(self.device)
            outputs = self.bert_model(**inputs)
            # 使用[CLS]标记的表示作为整个文本的嵌入
            embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()[0]
        
        return embedding.tolist()
    
    def vectorize_user(self, user_data: Dict[str, Any]) -> np.ndarray:
        """将用户数据向量化为模型输入"""
        features = self.extract_features(user_data)
        # 将特征字典转换为向量
        feature_names = sorted(features.keys())
        feature_vector = np.array([features[name] for name in feature_names])
        
        return feature_vector