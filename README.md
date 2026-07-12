# 软件造价自动生成器

基于软件造价联盟（BSCEA）标准工具的软件造价自动生成器。实现需求录入→自动算量→自动计价→一键输出造价成果文件。

## 功能

- 文档上传（PDF/DOCX/TXT）
- AI 自动识别功能点（ILF/EIF/EI/EO/EQ）
- 开发费/运维费全链路测算
- 一键导出 Word 造价报告 + Excel 测算底稿

## 本地启动

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

## 部署（Render）

一键部署到 Render：

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## 技术栈

- **后端**: Python Flask + SQLAlchemy + SQLite
- **前端**: Vue 3 + Element Plus + Vite
- **AI**: DeepSeek API
- **标准库**: BSCEA 软件造价联盟规范