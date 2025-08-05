# 智能升学择校辅助系统

基于Django的轻量级智能升学择校辅助系统，帮助学生选择适合的院校和专业。

## 功能特点

- 学生信息管理：输入和管理学生基本信息、成绩和兴趣爱好
- 院校推荐：基于学生情况推荐匹配度最高的院校和专业
- 多种推荐策略：支持平衡、激进和保守三种推荐策略
- 历史数据分析：分析目标院校历年录取分数线和趋势
- 个性化备考建议：根据学生与目标院校的差距提供备考指导

## 技术栈

- Python 3.8+
- Django 4.2+
- SQLite 数据库
- Bootstrap 5 前端框架

## 安装步骤

1. 克隆项目到本地：

```bash
git clone https://github.com/yourusername/haolaoshi.git
cd haolaoshi
```

2. 创建并激活虚拟环境：

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 运行数据库迁移：

```bash
python manage.py makemigrations
python manage.py migrate
```

5. 生成示例数据（可选）：

```bash
python manage.py generate_sample_data
```

6. 创建超级用户（可选，用于访问管理后台）：

```bash
python manage.py createsuperuser
```

7. 运行开发服务器：

```bash
python manage.py runserver
```

8. 在浏览器中访问：http://127.0.0.1:8000/

## 使用指南

1. 添加学生信息：
   - 点击"添加新学生"按钮
   - 填写学生基本信息和成绩
   - 提交表单

2. 生成院校推荐：
   - 在学生详情页点击"推荐院校"按钮
   - 选择推荐策略（平衡、激进或保守）
   - 设置推荐院校数量
   - 点击"开始推荐"按钮

3. 查看推荐结果：
   - 查看保底院校、匹配院校和冲刺院校列表
   - 了解每所推荐院校的匹配度和录取概率
   - 查看推荐理由和专业建议

## 项目结构

```
haolaoshi/
├── haolaoshi_django/       # 项目配置目录
├── recommendation/         # 核心应用目录
│   ├── management/        # 管理命令
│   ├── migrations/        # 数据库迁移文件
│   ├── admin.py           # 管理后台配置
│   ├── forms.py           # 表单定义
│   ├── models.py          # 数据模型
│   ├── recommender.py     # 推荐算法
│   ├── urls.py            # URL配置
│   └── views.py           # 视图定义
├── static/                 # 静态文件目录
│   ├── css/               # CSS样式文件
│   ├── js/                # JavaScript文件
│   └── images/            # 图片文件
├── templates/              # 模板目录
│   ├── base.html          # 基础模板
│   └── recommendation/    # 应用模板
├── manage.py               # Django管理脚本
└── README.md               # 项目说明文档
```