"""
RAG 对话引擎 - 核心检索与对话逻辑
包含文档管理、向量检索、对话生成等功能
"""

import json
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime

import chromadb
from chromadb.config import Settings
from openai import OpenAI
import tiktoken

class RAGChatEngine:
    """RAG 检索增强生成对话引擎"""
    
    def __init__(self, collection_name: str = "knowledge_base"):
        # 初始化 Chroma 客户端（持久化存储）
        self.client = chromadb.PersistentClient(path="./chroma_db", settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
        # 初始化 embedding 模型（使用智谱AI）
        self.embedding_client = OpenAI(
        api_key="your-zhipu-api-key-here",
            base_url="https://open.bigmodel.cn/api/paas/v4"
        )
        self.embedding_model = "embedding-2"
        
        # 初始化对话模型（使用 DeepSeek）
        self.chat_client = OpenAI(
            api_key="your-deepseek-api-key-here",
            base_url="https://api.deepseek.com"
        )
        self.chat_model = "deepseek-chat"
        
        # 分词器用于计算 token 数量
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # 对话历史存储（session_id -> messages）
        self.sessions: Dict[str, List[Dict]] = {}
        
        # 文档元数据存储
        self.documents_file = "documents-info.json"
        self.documents = self._load_documents()
    
    def _load_documents(self) -> Dict:
        """从本地文件加载文档元数据"""
        try:
            with open(self.documents_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_documents(self):
        """保存文档元数据到本地文件"""
        with open(self.documents_file, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示"""
        response = self.embedding_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def add_document(self, title: str, content: str, chunks: List[Dict]) -> str:
        """添加文档及其分段到知识库"""
        doc_id = str(uuid.uuid4())
        self.documents[doc_id] = {
            "title": title,
            "content_preview": content[:200],
            "created_at": datetime.now().isoformat(),
            "chunk_count": len(chunks)
        }
        self._save_documents()
        
        # 将每个分段添加到向量库
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            text = chunk.get("content", "")
            metadata = {
                "doc_id": doc_id,
                "title": title,
                "chunk_index": i,
                "source": chunk.get("source", ""),
                "section": chunk.get("title", "")
            }
            
            # 获取向量并添加
            embedding = self._get_embedding(text)
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
        
        return doc_id
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档及其所有分段"""
        if doc_id not in self.documents:
            return False
        
        # 删除向量库中的相关分段
        self.collection.delete(where={"doc_id": doc_id})
        
        # 删除元数据
        del self.documents[doc_id]
        self._save_documents()
        return True
    
    def list_documents(self) -> List[Dict]:
        """获取所有文档列表"""
        return [
            {"id": doc_id, **meta}
            for doc_id, meta in self.documents.items()
        ]
    
    def get_document_sections(self, doc_id: str) -> List[Dict]:
        """获取指定文档的所有分段"""
        results = self.collection.get(
            where={"doc_id": doc_id},
            include=["documents", "metadatas"]
        )
        sections = []
        for i in range(len(results["ids"])):
            sections.append({
                "id": results["ids"][i],
                "content": results["documents"][i],
                "metadata": results["metadatas"][i]
            })
        return sections
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """向量检索，返回最相关的文档分段"""
        query_embedding = self._get_embedding(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        retrieved = []
        for i in range(len(results["ids"][0])):
            retrieved.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i]  # 距离转相似度
            })
        return retrieved
    
    def chat(self, message: str, session_id: Optional[str] = None) -> Dict:
        """对话接口：检索 + 生成"""
        # 如果没有 session_id，创建一个新的
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 初始化会话历史
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        # 检索相关知识
        relevant_chunks = self.search(message, top_k=3)
        context = "\n\n".join([
            f"[来源：{chunk['metadata'].get('title', '未知')} - {chunk['metadata'].get('section', '')}]\n{chunk['content']}"
            for chunk in relevant_chunks
        ])
        
        # 构建 system prompt
        system_prompt = f"""你是一个专业的在线客服助手。请根据以下知识库内容回答用户问题。
如果知识库中没有相关信息，请如实告知用户你不知道，不要编造答案。

知识库内容：
{context}

回答要求：
1. 基于知识库内容回答
2. 如果知识库不足以回答问题，请说明
3. 保持友好、专业的语气
4. 回答末尾可以附上知识来源"""
        
        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.sessions[session_id][-10:])  # 保留最近10轮对话
        messages.append({"role": "user", "content": message})
        
        # 调用大模型生成回答
        response = self.chat_client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        
        reply = response.choices[0].message.content
        
        # 更新对话历史
        self.sessions[session_id].append({"role": "user", "content": message})
        self.sessions[session_id].append({"role": "assistant", "content": reply})
        
        # 如果会话太长，裁剪到最近20轮
        if len(self.sessions[session_id]) > 40:
            self.sessions[session_id] = self.sessions[session_id][-20:]
        
        return {
            "reply": reply,
            "session_id": session_id,
            "sources": [
                {
                    "title": chunk["metadata"].get("title", ""),
                    "section": chunk["metadata"].get("section", ""),
                    "score": round(chunk["score"], 3)
                }
                for chunk in relevant_chunks
            ]
        }