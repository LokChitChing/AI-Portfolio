# 智能在线客服系统（脱敏展示）

> 本仓库为一个**多租户智能客服系统**的商业交付项目脱敏重构版本，展示 RAG 知识库问答、Function Calling 通知、文档智能分段等核心能力。  
> 所有客户名称、IP 地址、密钥均已移除，仅保留技术框架与设计思路。

---

## 项目概述

- **场景**：培训机构官网智能问答与线索捕获
- 开发时间：2025.04 - 2025.06  
- 项目背景：某培训机构原有官网客服只能回复固定FAQ，无法理解复杂问题，也无法自动获取用户联系方式。需要一套支持多租户、文档管理、多轮对话、联系方式自动通知的智能客服系统。
- **技术栈**：FastAPI + Qdrant + LlamaIndex + DeepSeek + 智谱 AI Embedding
- **核心功能**：
  - 文档上传与管理（支持 PDF / Word / TXT / Markdown）
  - 大模型自动分段（自定义 LlamaIndex NodeParser）
  - 向量检索 + 关键词混合检索 + Rerank
  - Function Calling 捕获客户联系方式 → SMTP 邮件通知销售
  - 联网搜索增强（阿里云 OpenSearch API）
  - 登录鉴权（AES 加解密 Token）
  - 前端管理页面（文档列表、分段查看、上传 / 删除）

---

## 目录结构

├── README.md
├── main.py # FastAPI 应用入口 + 路由
├── module.py # RAG 检索 / 对话 / Embedding 核心逻辑
├── custom_splitter.py # 大模型自动分段器
├── email_tool.py # Function Calling 邮件通知
├── users.py # 登录鉴权（AES 加解密）
├── static/ # 前端页面（对话 / 管理 / 分段查看）
│ ├── index.html
│ ├── admin.html
│ ├── section.html
│ ├── script.js
│ └── style.css
└── documents-info.json # 文档元数据存储

## 说明

- 本仓库代码为**脱敏重构版本**，不可直接运行（依赖外部 API Key 与基础设施）
- 如需了解具体实现细节，欢迎通过 GitHub Issues 联系
