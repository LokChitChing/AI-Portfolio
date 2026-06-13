"""
大模型自动分段器 (LLMBasedSplitter)
使用大模型对文档进行语义分段，支持PDF/Word/TXT/Markdown
"""

import json
from typing import List, Dict, Optional
from openai import OpenAI

class LLMBasedSplitter:
    """
    基于大模型的智能文档分段器
    通过调用LLM理解文档结构，按语义切分为独立段落
    """
    
    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        """
        初始化分段器
        
        Args:
            api_key: 大模型API密钥（可从环境变量读取）
            model: 使用的模型名称
        """
        self.client = OpenAI(
            api_key=api_key or "your-api-key-here",
            base_url="https://api.deepseek.com"  # 可切换其他兼容接口
        )
        self.model = model
    
    def split(self, text: str, max_chars_per_chunk: int = 1500) -> List[Dict]:
        """
        将文档分割为语义段落
        
        Args:
            text: 原始文档文本
            max_chars_per_chunk: 每个段落的最大字符数
            
        Returns:
            段落列表，每个元素包含title和content字段
        """
        # 预处理：去除多余空白
        text = self._preprocess(text)
        
        # 如果文本很短，直接返回一个段落
        if len(text) <= max_chars_per_chunk:
            return [{"title": "全文", "content": text}]
        
        # 调用大模型进行分段
        prompt = self._build_prompt(text, max_chars_per_chunk)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的文档分段助手。请根据语义将文档分成逻辑清晰的段落，每个段落应有独立的标题和内容。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            result = json.loads(response.choices[0].message.content)
            paragraphs = result.get("paragraphs", [])
            
            # 确保返回的是列表
            if not isinstance(paragraphs, list):
                paragraphs = [{"title": "段落", "content": text}]
            
            return paragraphs
            
        except Exception as e:
            # 如果大模型调用失败，回退到简单分段
            print(f"LLM分段失败，使用回退策略: {e}")
            return self._fallback_split(text, max_chars_per_chunk)
    
    def _preprocess(self, text: str) -> str:
        """预处理：去除多余空白和特殊字符"""
        # 去除连续的换行符（保留最多两个）
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 去除首尾空白
        text = text.strip()
        return text
    
    def _build_prompt(self, text: str, max_chars: int) -> str:
        """构造分段提示词"""
        return f"""请将以下文档按照语义逻辑分成若干段落，每个段落应是一个完整独立的主题。
要求：
- 每个段落字数不超过{max_chars}字
- 输出JSON格式：{{"paragraphs": [{{"title": "段落标题", "content": "段落内容"}}]}}
- 标题要简洁概括该段核心内容
- 段落之间不要重叠，也不要遗漏重要内容

文档内容：
{text[:10000]}  # 限制输入长度防止token溢出
"""
    
    def _fallback_split(self, text: str, max_chars: int) -> List[Dict]:
        """回退策略：按段落标记或固定长度分割"""
        import re
        
        # 尝试按双换行分割
        paragraphs = re.split(r'\n\s*\n', text)
        result = []
        
        current_chunk = ""
        current_title = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前块加上新段落会超长，先保存当前块
            if len(current_chunk) + len(para) > max_chars and current_chunk:
                result.append({
                    "title": f"段落 {chunk_index + 1}",
                    "content": current_chunk.strip()
                })
                current_chunk = ""
                chunk_index += 1
            
            # 尝试从段落中提取标题（假设第一行为标题）
            lines = para.split('\n', 1)
            if len(lines) == 2 and len(lines[0]) < 50:
                # 第一行可能是标题
                if not current_chunk:
                    current_title = lines[0].strip()
                current_chunk += lines[1] + "\n"
            else:
                if not current_chunk:
                    current_title = f"段落 {chunk_index + 1}"
                current_chunk += para + "\n"
        
        # 保存最后一个块
        if current_chunk:
            result.append({
                "title": f"段落 {chunk_index + 1}",
                "content": current_chunk.strip()
            })
        
        return result if result else [{"title": "全文", "content": text}]