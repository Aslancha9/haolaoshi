import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Any, Optional, Tuple
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

class MatrixFactorization(nn.Module):
    """基于PyTorch实现的矩阵分解模型，支持GPU加速"""
    
    def __init__(self, n_users: int, n_items: int, n_factors: int = 50, use_gpu: bool = True):
        super(MatrixFactorization, self).__init__()
        self.user_factors = nn.Embedding(n_users, n_factors)
        self.item_factors = nn.Embedding(n_items, n_factors)
        self.user_biases = nn.Embedding(n_users, 1)
        self.item_biases = nn.Embedding(n_items, 1)
        
        # 初始化权重
        self.user_factors.weight.data.uniform_(0, 0.05)
        self.item_factors.weight.data.uniform_(0, 0.05)
        self.user_biases.weight.data.uniform_(-0.01, 0.01)
        self.item_biases.weight.data.uniform_(-0.01, 0.01)
        
        # 全局偏置
        self.global_bias = nn.Parameter(torch.zeros(1))
        
        # 设备
        self.device = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")
        self.to(self.device)
    
    def forward(self, user_idx: torch.Tensor, item_idx: torch.Tensor) -> torch.Tensor:
        """前向传播计算预测评分"""
        # 用户和项目嵌入
        user_embedding = self.user_factors(user_idx)
        item_embedding = self.item_factors(item_idx)
        
        # 用户和项目偏置
        user_bias = self.user_biases(user_idx).squeeze()
        item_bias = self.item_biases(item_idx).squeeze()
        
        # 计算预测评分: 全局偏置 + 用户偏置 + 项目偏置 + 用户和项目嵌入的点积
        prediction = self.global_bias + user_bias + item_bias + (user_embedding * item_embedding).sum(dim=1)
        
        return prediction


class CollaborativeFiltering:
    """协同过滤推荐模型，结合基于邻域的方法和矩阵分解"""
    
    def __init__(self, use_gpu: bool = True):
        self.user_item_matrix = None
        self.user_id_map = {}  # 用户ID到矩阵索引的映射
        self.item_id_map = {}  # 项目ID到矩阵索引的映射
        self.item_similarity_matrix = None
        self.knn_model = None
        self.mf_model = None
        self.use_gpu = use_gpu
        self.device = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")
    
    def fit(self, 
            interactions: List[Dict[str, Any]], 
            n_factors: int = 50, 
            k_neighbors: int = 20, 
            epochs: int = 20, 
            batch_size: int = 64, 
            learning_rate: float = 0.01) -> None:
        """训练协同过滤模型
        
        Args:
            interactions: 用户交互数据，格式为[{user_id: 1, item_id: 101, rating: 5.0}, ...]
            n_factors: 潜在因子数量
            k_neighbors: KNN算法中的邻居数量
            epochs: 训练轮数
            batch_size: 批次大小
            learning_rate: 学习率
        """
        print("开始训练协同过滤模型...")
        
        # 创建用户和项目的ID映射
        unique_users = set([interaction['user_id'] for interaction in interactions])
        unique_items = set([interaction['item_id'] for interaction in interactions])
        
        self.user_id_map = {user_id: i for i, user_id in enumerate(unique_users)}
        self.item_id_map = {item_id: i for i, item_id in enumerate(unique_items)}
        
        n_users = len(unique_users)
        n_items = len(unique_items)
        
        print(f"用户数: {n_users}, 项目数: {n_items}")
        
        # 构建用户-项目交互矩阵
        ratings = []
        user_indices = []
        item_indices = []
        
        for interaction in interactions:
            user_idx = self.user_id_map[interaction['user_id']]
            item_idx = self.item_id_map[interaction['item_id']]
            rating = interaction.get('rating', 1.0)  # 如果没有评分，默认为1.0
            
            user_indices.append(user_idx)
            item_indices.append(item_idx)
            ratings.append(rating)
        
        # 创建稀疏矩阵
        self.user_item_matrix = csr_matrix((ratings, (user_indices, item_indices)), shape=(n_users, n_items))
        
        # 计算物品相似度矩阵
        item_similarity = cosine_similarity(self.user_item_matrix.T)
        self.item_similarity_matrix = item_similarity
        
        # 训练KNN模型
        self.knn_model = NearestNeighbors(n_neighbors=k_neighbors + 1, metric='cosine')
        self.knn_model.fit(self.user_item_matrix.T)
        
        # 训练矩阵分解模型
        self.mf_model = MatrixFactorization(n_users, n_items, n_factors, use_gpu=self.use_gpu)
        self._train_mf_model(interactions, epochs, batch_size, learning_rate)
    
    def _train_mf_model(self, 
                       interactions: List[Dict[str, Any]], 
                       epochs: int, 
                       batch_size: int, 
                       learning_rate: float) -> None:
        """训练矩阵分解模型"""
        # 准备训练数据
        user_indices = [self.user_id_map[interaction['user_id']] for interaction in interactions]
        item_indices = [self.item_id_map[interaction['item_id']] for interaction in interactions]
        ratings = [interaction.get('rating', 1.0) for interaction in interactions]
        
        # 转换为PyTorch张量
        user_tensor = torch.LongTensor(user_indices).to(self.device)
        item_tensor = torch.LongTensor(item_indices).to(self.device)
        rating_tensor = torch.FloatTensor(ratings).to(self.device)
        
        # 优化器和损失函数
        optimizer = optim.Adam(self.mf_model.parameters(), lr=learning_rate, weight_decay=0.01)
        criterion = nn.MSELoss()
        
        # 创建数据集和数据加载器
        dataset = torch.utils.data.TensorDataset(user_tensor, item_tensor, rating_tensor)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # 训练模型
        self.mf_model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch_user, batch_item, batch_rating in dataloader:
                # 前向传播
                prediction = self.mf_model(batch_user, batch_item)
                loss = criterion(prediction, batch_rating)
                
                # 反向传播和优化
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.4f}")
        
        # 训练结束后切换到评估模式
        self.mf_model.eval()
    
    def recommend_items_for_user(self, 
                                user_id: int, 
                                n_recommendations: int = 10, 
                                item_pool: Optional[List[int]] = None, 
                                blend_ratio: float = 0.5) -> List[Tuple[int, float]]:
        """为用户推荐项目
        
        Args:
            user_id: 用户ID
            n_recommendations: 推荐的项目数量
            item_pool: 候选项目池
            blend_ratio: 混合比例，0表示纯KNN，1表示纯矩阵分解
            
        Returns:
            推荐的项目列表，每个元素为(项目ID, 推荐分数)的元组
        """
        # 检查用户是否在训练集中
        if user_id not in self.user_id_map:
            # 冷启动问题，返回空列表或者最受欢迎的项目
            return []
        
        user_idx = self.user_id_map[user_id]
        
        # 获取用户交互的项目
        user_interactions = self.user_item_matrix[user_idx].toarray().flatten()
        interacted_items = set(np.where(user_interactions > 0)[0])
        
        # 设置候选项目池
        if item_pool is None:
            candidate_items = set(range(self.user_item_matrix.shape[1])) - interacted_items
        else:
            candidate_items = set([self.item_id_map.get(item_id) for item_id in item_pool 
                                  if item_id in self.item_id_map]) - interacted_items
        
        if not candidate_items:
            return []
        
        # 计算KNN推荐分数
        knn_scores = self._knn_prediction(user_idx, list(candidate_items))
        
        # 计算矩阵分解推荐分数
        mf_scores = self._mf_prediction(user_idx, list(candidate_items))
        
        # 混合推荐分数
        final_scores = [(item_idx, (1 - blend_ratio) * knn_score + blend_ratio * mf_score) 
                        for item_idx, knn_score, mf_score in zip(candidate_items, knn_scores, mf_scores)]
        
        # 排序并选择前N个
        final_scores.sort(key=lambda x: x[1], reverse=True)
        top_n = final_scores[:n_recommendations]
        
        # 将项目索引映射回项目ID
        reverse_item_map = {idx: item_id for item_id, idx in self.item_id_map.items()}
        recommendations = [(reverse_item_map[item_idx], score) for item_idx, score in top_n]
        
        return recommendations
    
    def _knn_prediction(self, user_idx: int, candidate_items: List[int]) -> List[float]:
        """使用基于KNN的方法计算推荐分数"""
        user_vector = self.user_item_matrix[user_idx].toarray().flatten()
        interacted_items = np.where(user_vector > 0)[0]
        
        if len(interacted_items) == 0:
            # 用户没有交互记录，返回零分
            return [0.0] * len(candidate_items)
        
        # 计算候选项目的分数
        scores = []
        for item_idx in candidate_items:
            # 获取相似项目
            item_similarities = self.item_similarity_matrix[item_idx, interacted_items]
            # 加权平均
            weights = user_vector[interacted_items]
            score = np.sum(item_similarities * weights) / np.sum(weights)
            scores.append(score)
        
        return scores
    
    def _mf_prediction(self, user_idx: int, candidate_items: List[int]) -> List[float]:
        """使用矩阵分解模型计算推荐分数"""
        # 转换为PyTorch张量
        user_tensor = torch.LongTensor([user_idx] * len(candidate_items)).to(self.device)
        item_tensor = torch.LongTensor(candidate_items).to(self.device)
        
        # 使用模型预测
        with torch.no_grad():
            predictions = self.mf_model(user_tensor, item_tensor)
        
        return predictions.cpu().numpy().tolist()
    
    def update_with_new_interaction(self, user_id: int, item_id: int, rating: float = 1.0) -> None:
        """更新模型，加入新的交互记录"""
        # 检查用户和项目是否存在
        if user_id not in self.user_id_map:
            print(f"用户 {user_id} 不在训练集中，需要重新训练模型")
            return
        
        if item_id not in self.item_id_map:
            print(f"项目 {item_id} 不在训练集中，需要重新训练模型")
            return
        
        user_idx = self.user_id_map[user_id]
        item_idx = self.item_id_map[item_id]
        
        # 更新用户-项目矩阵
        self.user_item_matrix[user_idx, item_idx] = rating
        
        # 重新计算物品相似度矩阵（只更新受影响的项目）
        # 注意：在生产环境中，应该使用增量更新或定期重新计算
        item_vector = self.user_item_matrix[:, item_idx].toarray().T
        for i in range(self.user_item_matrix.shape[1]):
            if i != item_idx:
                other_vector = self.user_item_matrix[:, i].toarray().T
                sim = cosine_similarity(item_vector, other_vector)[0][0]
                self.item_similarity_matrix[item_idx, i] = sim
                self.item_similarity_matrix[i, item_idx] = sim
        
        # 矩阵分解模型的在线更新需要更复杂的实现，此处省略
        # 实际应用中可以定期重新训练或使用在线学习方法