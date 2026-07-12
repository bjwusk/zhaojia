# 软件造价自动生成器

基于软件造价联盟（BSCEA）标准的软件造价自动生成器，实现需求录入→自动算量→自动计价→一键输出造价成果文件。

## 在线使用（不需本地运行）

一键部署到 Railway（免费，24小时在线）：

[![Deploy to Railway](https://railway.app/button.svg)](https://railway.app/new/github/bjwusk/zhaojia)

点上面按钮 → 用 GitHub 登录 → 点 Deploy → 3分钟部署完成

## 本地开发

`ash
# 后端
cd backend
pip install -r requirements.txt
python run.py

# 前端
cd frontend
npm install
npm run dev
`

## 技术栈

- 后端: Python Flask + SQLAlchemy + SQLite
- 前端: Vue 3 + Element Plus + Vite
- AI: DeepSeek API
- 标准库: BSCEA 软件造价联盟规范