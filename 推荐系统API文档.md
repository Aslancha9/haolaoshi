# 推荐系统API文档

## 基本信息
- 基础URL: `http://服务器地址:8000`
- 所有API返回JSON格式数据
- 身份验证: 暂无（根据实际情况补充）

## 核心API端点

### 1. 学校推荐API

**请求**:
```
POST /api/students/{student_id}/recommend_schools
```

**路径参数**:
- `student_id`: 学生ID (整数)

**请求体**:
```json
{
  "strategy": "balanced",  // 可选值: "balanced"(平衡), "aggressive"(冲刺), "conservative"(保守)
  "num_recommendations": 9, // 推荐学校总数
  "include_majors": true,   // 是否包含专业推荐
  "prefer_provinces": ["北京", "上海"], // 可选，优先推荐的省份
  "prefer_school_types": ["985", "211"] // 可选，优先推荐的学校类型
}
```

**响应**:
```json
{
  "challenge_schools": [  // 冲刺院校
    {
      "school_id": 1,
      "name": "清华大学",
      "match": 0.85,
      "score": 680,
      "admission_probability": "25%",
      "recommended_majors": [
        {"id": 101, "name": "计算机科学与技术", "match": 0.9}
      ]
    }
    // 更多学校...
  ],
  "match_schools": [  // 匹配院校
    // 结构同上
  ],
  "safety_schools": [  // 保底院校
    // 结构同上
  ],
  "analysis": "根据学生成绩和兴趣分析..."
}
```

### 2. 学习计划生成API

**请求**:
```
POST /api/study_plans/generate
```

**查询参数**:
- `student_id`: 学生ID (整数)

**请求体**:
```json
{
  "plan_type": "exam_prep",  // 计划类型
  "duration": 90,            // 计划持续天数
  "focus_subjects": ["数学", "物理"],  // 重点学科
  "target_score": 680,       // 目标分数
  "target_schools": [1, 2],  // 目标学校ID列表
  "target_majors": [101, 102]  // 目标专业ID列表
}
```

**响应**:
```json
{
  // 学习计划详细信息
}
```

## 错误处理

所有API在遇到错误时返回标准HTTP错误代码，并包含详细错误信息：

```json
{
  "detail": "错误详情"
}
```

常见错误代码:
- 400: 请求参数错误
- 404: 资源不存在(如学生ID不存在)
- 500: 服务器内部错误

## 示例代码

### JavaScript (Fetch API)
```javascript
// 获取学校推荐
async function getSchoolRecommendations(studentId) {
  const response = await fetch(`http://服务器地址:8000/api/students/${studentId}/recommend_schools`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      strategy: 'balanced',
      num_recommendations: 9,
      include_majors: true
    })
  });
  
  const data = await response.json();
  return data;
}
```

## 注意事项
- API响应时间可能因数据量和推荐算法复杂度而有所不同
- 建议前端实现加载状态提示
- 推荐结果已按匹配度排序，无需前端再次排序