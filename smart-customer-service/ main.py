"""
智能在线客服系统 - 主入口
FastAPI 应用启动、路由注册、中间件配置
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 导入自定义模块
from module import RAGChatEngine
from custom_splitter import LLMBasedSplitter
from email_tool import ContactNotifier
from users import AuthHandler

# ============================================================
# 应用初始化
# ============================================================

app = FastAPI(title="智能在线客服系统", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================================
# 全局实例
# ============================================================

# 认证处理器
auth_handler = AuthHandler()

# RAG 对话引擎
rag_engine = RAGChatEngine()

# 文档分段器
splitter = LLMBasedSplitter()

# 邮件通知器
notifier = ContactNotifier()

# ============================================================
# 数据模型
# ============================================================

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    doc_id: Optional[str] = None

# ============================================================
# 中间件：鉴权校验
# ============================================================

async def verify_token(authorization: Optional[str] = Header(None)):
    """验证 Bearer Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    
    payload = auth_handler.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload

# ============================================================
# 路由：页面
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def chat_page():
    """对话页面"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    """管理页面"""
    with open("static/admin.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/section", response_class=HTMLResponse)
async def section_page():
    """分段查看页面"""
    with open("static/section.html", "r", encoding="utf-8") as f:
        return f.read()

# ============================================================
# 路由：认证
# ============================================================

@app.post("/api/login")
async def login(request: LoginRequest):
    """用户登录"""
    token = auth_handler.login(request.username, request.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": token, "token_type": "bearer"}

# ============================================================
# 路由：文档管理
# ============================================================

@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    payload: dict = Depends(verify_token)
):
    """上传文档"""
    try:
        # 读取文件内容
        content = await file.read()
        text = content.decode("utf-8")
        
        # 使用大模型分段
        chunks = splitter.split(text)
        
        # 保存到知识库
        doc_id = rag_engine.add_document(
            title=title or file.filename,
            content=text,
            chunks=chunks
        )
        
        return DocumentUploadResponse(
            success=True,
            message=f"Document '{title or file.filename}' uploaded successfully",
            doc_id=doc_id
        )
    except Exception as e:
        return DocumentUploadResponse(
            success=False,
            message=f"Upload failed: {str(e)}"
        )

@app.get("/api/documents")
async def list_documents(payload: dict = Depends(verify_token)):
    """获取文档列表"""
    documents = rag_engine.list_documents()
    return {"documents": documents}

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str, payload: dict = Depends(verify_token)):
    """删除文档"""
    success = rag_engine.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True, "message": "Document deleted"}

# ============================================================
# 路由：对话
# ============================================================

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """对话接口（无需登录）"""
    response = rag_engine.chat(
        message=request.message,
        session_id=request.session_id
    )
    
    # 检查是否包含联系方式
    contact_info = notifier.extract_contact(request.message)
    if contact_info:
        notifier.send_notification(contact_info, request.message)
    
    return response

# ============================================================
# 路由：分段查看
# ============================================================

@app.get("/api/documents/{doc_id}/sections")
async def get_document_sections(doc_id: str, payload: dict = Depends(verify_token)):
    """获取文档的分段列表"""
    sections = rag_engine.get_document_sections(doc_id)
    return {"doc_id": doc_id, "sections": sections}

# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)