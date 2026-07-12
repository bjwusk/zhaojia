# 开发者指南

## 项目结构说明

### 后端 (backend/)
- Flask 3.x + SQLAlchemy + SQLite
- API 遵循 RESTful 规范，返回 `{code, data, message}`
- 核心计算引擎在 `app/core/` 中，为纯算法模块，无 Flask 依赖

### 前端 (frontend/)
- Vue 3 + Vite + Element Plus + Pinia
- 代理配置：`/api` → `localhost:5000`
- 构建产物输出到 `dist/`

## 扩展指南

### 添加新的行业模板
在 `backend/data/industry_templates/` 下创建 JSON 文件，格式参照现有模板。

### 添加新的人月单价
编辑 `backend/data/city_price.json`。

### 添加新的调整因子
1. 在对应标准库 JSON 中添加
2. 在核心计算引擎中添加因子处理方法
3. 在前端 FactorPanel 组件中添加选项

### 添加新的费用项
编辑 `app/core/fee_engine.py` 中的 MEASURE_RATES 字典。

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/project | 项目列表 |
| POST | /api/project | 创建项目 |
| GET | /api/project/:id | 项目详情 |
| PUT | /api/project/:id | 更新项目 |
| DELETE | /api/project/:id | 删除项目 |
| POST | /api/estimate/dev/version | 创建开发费版本 |
| POST | /api/estimate/dev/version/:id/items | 保存功能点 |
| POST | /api/estimate/dev/version/:id/calculate | 运行测算 |
| GET | /api/estimate/dev/version/:id | 查看版本 |
| POST | /api/estimate/ops/... | 运维费类似 |
| GET | /api/template | 列出模板 |
| GET | /api/template/:key/items | 获取模板功能点 |
| GET | /api/export/excel/:versionId | 导出Excel |
| GET | /api/export/word/:versionId | 导出Word |
