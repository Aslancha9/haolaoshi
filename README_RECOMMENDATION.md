# 考研推荐系统

基于混合推荐策略的考研院校与专业推荐系统，融合机器学习、深度学习和语义匹配技术。

## 系统架构

系统采用"混合推荐策略"，主要由以下几个核心模块组成：

1. **用户画像建模**：将用户基本背景信息、目标意向、能力评估及风险偏好转化为数值化输入向量
2. **混合推荐引擎**：
   - LightGBM/CatBoost树模型：预测录取概率
   - BERT语义匹配：对专业介绍文本、招生简章等进行语义匹配
   - 协同过滤：基于用户行为数据的推荐增强
3. **推荐API服务**：提供学校推荐、专业推荐、学习计划生成等API

## 技术栈

- **深度学习框架**：PyTorch + Transformers (BERT)
- **机器学习框架**：scikit-learn, LightGBM
- **特征工程**：pandas, numpy
- **API服务**：FastAPI
- **实验管理**：MLflow, Optuna
- **GPU加速**：CUDA (通过PyTorch)

## 安装指南

### 1. 安装依赖

```bash
# 安装基础依赖
pip install -r requirements_ml.txt
```

### 2. GPU设置检查

```bash
# 检查GPU是否可用
python -c "import torch; print(f'GPU可用: {torch.cuda.is_available()}')"

# 如果可用，显示GPU信息
python -c "import torch; print(f'GPU设备: {torch.cuda.get_device_name(0)}') if torch.cuda.is_available() else print('无可用GPU')"
```

## 使用方法

### 1. 运行推荐服务

```bash
# 启动推荐系统API服务
python -m app.main_recommendation
```

服务将在 `http://localhost:8000` 启动，API文档可通过 `http://localhost:8000/docs` 访问。

### 2. 测试模型性能

```bash
# 运行测试脚本，检查模型性能和GPU加速效果
python test_recommendation_model.py
```

### 3. 主要API端点

- **用户画像创建**: `/api/recommendation/profile`
- **学校推荐**: `/api/recommendation/recommend/schools`
- **专业推荐**: `/api/recommendation/recommend/majors`
- **学习计划生成**: `/api/recommendation/generate/study_plan`
- **用户反馈记录**: `/api/recommendation/feedback`
- **模型信息**: `/api/recommendation/model/info`

## 模块说明

### 1. 用户画像模块 (`app/models/user_profile.py`)

负责特征工程和向量化，将用户的基本信息、学业成绩、兴趣偏好等转化为模型输入向量。使用BERT进行文本特征提取。

### 2. 核心推荐模型 (`app/models/recommender_model.py`)

混合推荐引擎，集成了机器学习模型和深度学习模型，预测用户对学校的匹配度，并根据风险等级进行分组推荐。

### 3. 语义匹配模块 (`app/models/semantic_matcher.py`)

基于BERT的语义匹配引擎，计算用户兴趣和专业描述之间的相似度，用于专业推荐。

### 4. 协同过滤模块 (`app/models/collaborative_filtering.py`)

基于用户行为的推荐增强，使用矩阵分解和KNN算法实现，能够捕捉用户之间的相似性模式。

### 5. 模型训练管理 (`app/models/model_trainer.py`)

负责模型的训练、评估、保存和加载，集成了MLflow和Optuna进行实验追踪和超参数优化。

### 6. API服务 (`app/api/endpoints/recommendation_api.py`)

提供RESTful API接口，用于外部系统调用推荐服务。

## 性能优化

1. **GPU加速**：所有深度学习相关代码都使用GPU加速，在BERT编码、矩阵分解等计算密集型任务上有显著提速。

2. **缓存优化**：语义匹配模块实现了嵌入向量缓存，避免重复计算。

3. **批处理**：在推理和训练中使用批处理，提高GPU利用率。

4. **异步API**：FastAPI提供异步处理能力，提高并发性能。

## 待优化方向

1. 增加用户反馈和行为数据收集机制，优化协同过滤模型
2. 实现增量训练和模型更新机制
3. 添加更复杂的特征工程和更多数据源
4. 实现A/B测试框架，持续优化推荐效果
5. 增强模型可解释性，提供更详细的推荐理由