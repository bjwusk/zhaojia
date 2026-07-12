# 软件造价自动生成器

基于软件造价联盟（BSCEA）标准的软件造价自动生成器。

## 在线使用（推荐）

**推荐 → Zeabur（国内访问快，免费）**  
1. 打开 https://zeabur.com  
2. 用 GitHub 登录  
3. 新建项目 → 从 GitHub 导入  
4. 选择 bjwusk/zhaojia  
5. 启动命令：cd backend && python run.py  
6. 部署完成即可通过 https://xxx.zeabur.app 访问  

备用 → Railway（香港节点，免费）  
https://railway.app/new/github/bjwusk/zhaojia  
部署时 Region 选择 Hong Kong  

备用 → Koyeb（新加坡节点，免费）  
https://app.koyeb.com/deploy?type=git&repository=bjwusk/zhaojia&branch=main&name=zhaojia  

## 本地运行

`ash
cd backend
pip install -r requirements.txt
python run.py
`

浏览器打开 http://localhost:5000

## 技术栈

- 后端：Python Flask + SQLite
- 前端：Vue 3 + Element Plus
- 标准：BSCEA 软件造价联盟