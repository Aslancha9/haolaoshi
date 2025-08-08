import torch
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from transformers import BertModel, BertTokenizer
from sklearn.metrics.pairwise import cosine_similarity

class SemanticMatcher:
    """基于BERT的语义匹配模型，用于计算用户兴趣和专业描述的相似度"""
    
    def __init__(self, use_gpu: bool = True):
        self.device = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
        self.model = BertModel.from_pretrained('bert-base-chinese').to(self.device)
        self.model.eval()
        
        # 缓存已计算的嵌入向量
        self.embedding_cache = {}
        
    def match_interests_to_majors(self, 
                                  user_interests: List[str], 
                                  majors_data: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        """匹配用户兴趣与专业的契合度"""
        # 获取用户兴趣的嵌入向量
        interest_text = ' '.join(user_interests)
        interest_embedding = self._get_text_embedding(interest_text)
        
        # 计算与每个专业的相似度
        similarities = []
        for major in majors_data:
            major_name = major.get('name', '')
            major_desc = major.get('description', '')
            
            # 专业描述文本
            major_text = f"{major_name} {major_desc}"
            
            # 获取专业的嵌入向量
            major_embedding = self._get_text_embedding(major_text)
            
            # 计算相似度
            similarity = self._calculate_similarity(interest_embedding, major_embedding)
            
            similarities.append({
                'major': major,
                'similarity': float(similarity),
            })
        
        # 排序
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities
    
    def match_career_goals_to_majors(self, 
                                    career_goals: str, 
                                    majors_data: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        """匹配用户职业目标与专业的契合度"""
        if not career_goals:
            # 如果没有职业目标，返回空列表
            return []
            
        # 获取职业目标的嵌入向量
        career_embedding = self._get_text_embedding(career_goals)
        
        # 计算与每个专业的相似度
        similarities = []
        for major in majors_data:
            major_name = major.get('name', '')
            career_prospects = major.get('career_prospects', '')
            
            # 专业就业前景文本
            major_text = f"{major_name} {career_prospects}"
            
            # 获取专业的嵌入向量
            major_embedding = self._get_text_embedding(major_text)
            
            # 计算相似度
            similarity = self._calculate_similarity(career_embedding, major_embedding)
            
            similarities.append({
                'major': major,
                'similarity': float(similarity),
            })
        
        # 排序
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities
    
    def _get_text_embedding(self, text: str) -> np.ndarray:
        """获取文本的BERT嵌入向量，支持缓存"""
        # 检查缓存
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        # 如果文本为空，返回零向量
        if not text:
            embedding = np.zeros(768)  # BERT base的隐藏层维度
            self.embedding_cache[text] = embedding
            return embedding
        
        # 对文本进行编码
        with torch.no_grad():
            inputs = self.tokenizer(text, return_tensors="pt", 
                                    padding=True, truncation=True, 
                                    max_length=512).to(self.device)
            outputs = self.model(**inputs)
            
            # 使用[CLS]标记的表示作为整个文本的嵌入
            embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()[0]
        
        # 缓存结果
        self.embedding_cache[text] = embedding
        return embedding
    
    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """计算两个嵌入向量的余弦相似度"""
        # 将向量重塑为二维
        vec1 = embedding1.reshape(1, -1)
        vec2 = embedding2.reshape(1, -1)
        
        # 计算余弦相似度
        similarity = cosine_similarity(vec1, vec2)[0][0]
        return similarity
    
    def get_major_recommendations(self, 
                                 user_data: Dict[str, Any], 
                                 majors_data: List[Dict[str, Any]], 
                                 top_n: int = 5) -> List[Dict[str, Any]]:
        """根据用户兴趣和职业目标推荐专业"""
        # 获取用户兴趣和职业目标
        interests = user_data.get('interests', [])
        career_goals = user_data.get('career_goals', '')
        
        # 匹配兴趣和职业目标
        interest_matches = self.match_interests_to_majors(interests, majors_data)
        career_matches = self.match_career_goals_to_majors(career_goals, majors_data)
        
        # 综合评分
        major_scores = {}
        
        # 处理兴趣匹配结果
        for match in interest_matches:
            major_id = match['major']['id']
            if major_id not in major_scores:
                major_scores[major_id] = {
                    'major': match['major'],
                    'interest_score': match['similarity'],
                    'career_score': 0.0
                }
            else:
                major_scores[major_id]['interest_score'] = match['similarity']
        
        # 处理职业目标匹配结果
        for match in career_matches:
            major_id = match['major']['id']
            if major_id not in major_scores:
                major_scores[major_id] = {
                    'major': match['major'],
                    'interest_score': 0.0,
                    'career_score': match['similarity']
                }
            else:
                major_scores[major_id]['career_score'] = match['similarity']
        
        # 计算综合得分（兴趣占60%，职业目标占40%）
        recommendations = []
        for major_id, data in major_scores.items():
            total_score = 0.6 * data['interest_score'] + 0.4 * data['career_score']
            recommendations.append({
                'major': data['major'],
                'score': float(total_score),
                'interest_score': float(data['interest_score']),
                'career_score': float(data['career_score'])
            })
        
        # 排序并返回前N个
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:top_n]