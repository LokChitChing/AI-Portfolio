# 智能在线客服系统

> **⚠️ 脱敏声明**  
> 本项目为商业交付项目的**脱敏重构版本**。所有客户名称、IP 地址、API 密钥、内部域名及敏感数据均已移除或替换为占位符。代码仅用于展示技术架构与工程能力，不可直接用于生产环境。

---

## 项目信息

- **开发时间**：2025.04 - 2025.06  
- **项目角色**：独立完成（全栈开发：后端 + 前端 + AI 模块）  
- **应用场景**：某连锁服务机构/某培训机构原有官网客服只能回复固定 FAQ，无法理解复杂问题，也无法自动获取用户联系方式。

---

## 项目背景

原有官网客服只能回复固定 FAQ，无法理解复杂问题，也无法自动获取用户联系方式。需要一套支持以下功能的智能客服系统：

- 多租户隔离（不同机构独立使用）
- 文档上传与管理（PDF / Word / TXT / Markdown）
- 多轮对话（理解上下文，连续问答）
- 联系方式自动通知（捕获手机号 / 微信号后自动通知销售）
- 联网搜索增强（知识库无答案时自动搜索网络）

---

## 技术栈

| 类别 | 技术 |
|---|---|
| 后端框架 | FastAPI |
| 向量数据库 | Qdrant |
| RAG 框架 | LlamaIndex |
| 大模型 | DeepSeek / 智谱 AI |
| 文档分段 | 自定义 LLMBasedSplitter（基于大模型语义分段） |
| 检索增强 | 混合检索（向量 + BM25）+ Rerank |
| 工具调用 | Function Calling（正则预检 + LLM 确认） |
| 通知方式 | SMTP 邮件（QQ邮箱） |
| 鉴权方案 | AES-GCM 加密 Token |
| 联网搜索 | 阿里云 OpenSearch API（后备） |
| 前端 | 原生 HTML / CSS / JS（Jinja2 模板） |

---

## 核心功能

1. **文档管理**：上传、删除、分段查看，支持多种格式
2. **智能分段**：调用大模型按语义自动切分文档，保留元数据（标题、来源）
3. **RAG 问答**：向量检索 + 关键词检索 + Rerank 重排序，引用溯源
4. **多轮对话**：基于对话历史的上下文理解
5. **线索捕获**：正则预检联系方式 → Function Calling 确认 → 邮件通知销售
6. **多租户隔离**：每个客户独立 Qdrant Collection
7. **联网搜索**：知识库无答案时自动搜索阿里云 OpenSearch

---

## 目录结构

smart-customer-service/

├── main.py                 # FastAPI 应用入口 + 路由

├── module.py               # RAG 检索 / 对话 /Embedding 核心逻辑

├── custom_splitter.py      # 大模型自动分段器

├── email_tool.py           # Function Calling 邮件通知

├── users.py                # 登录鉴权（AES 加解密）

├── static/                 # 前端页面

│   ├── index.html          # 对话页面

│   ├── admin.html          # 管理页面

│   ├── section.html        # 分段查看页面

│   ├── script.js           # 前端交互逻辑

│   └── style.css           # 样式

└── documents-info.json     # 文档元数据存储（模拟数据库）


## 快速开始

### 环境要求
- Python 3.10+
- FastAPI
- Qdrant（本地或 Docker）
- 大模型 API Key（DeepSeek / 智谱 AI）

### 安装依赖

bash

pip install fastapi uvicorn qdrant-client llama-index openai

### 运行

bash

cd smart-customer-service

uvicorn main:app --reload

### 访问
- 对话页面：http://localhost:8000
- 管理页面：http://localhost:8000/admin
- 分段查看：http://localhost:8000/section

## 注意事项
- 本仓库代码为**脱敏重构版本**，不可直接运行（依赖外部 API Key 与基础设施）
- 代码中的 API Key 和密钥均为占位符，实际使用时请从环境变量读取
- 前端为简化版演示，生产环境建议使用 Vue / React 重构