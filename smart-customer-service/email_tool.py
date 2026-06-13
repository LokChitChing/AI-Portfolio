"""
邮件通知工具 (ContactNotifier)
通过正则预检联系方式，并通过 SMTP 发送通知给销售
"""

import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict

class ContactNotifier:
    """
    捕获客户联系方式并发送邮件通知
    """
    
    def __init__(self, smtp_server: str = "smtp.qq.com",
                 smtp_port: int = 587,
                 sender_email: str = "your-email@qq.com",
                 sender_password: str = "your-password"):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def extract_contact(self, message: str) -> Optional[Dict[str, str]]:
        """
        从用户消息中提取手机号或微信号
        
        Args:
            message: 用户输入的消息
            
        Returns:
            包含手机号或微信号的字典，若无则返回None
        """
        # 手机号正则（简单版）
        phone_pattern = r'(1[3-9]\d{9})'
        # 微信号正则（通常6-20位字母数字下划线）
        wechat_pattern = r'(?:微信号?[：:]?\s*([a-zA-Z][a-zA-Z0-9_-]{5,19}))'
        
        phone_match = re.search(phone_pattern, message)
        wechat_match = re.search(wechat_pattern, message)
        
        result = {}
        if phone_match:
            result['phone'] = phone_match.group(1)
        if wechat_match:
            result['wechat'] = wechat_match.group(1)
        
        return result if result else None
    
    def send_notification(self, contact_info: Dict[str, str], customer_message: str):
        """
        发送邮件通知销售
        
        Args:
            contact_info: 联系方式字典（含phone/wechat）
            customer_message: 用户原始消息
        """
        subject = "【新客户线索】智能客服捕获"
        body = f"""
        客户联系方式：
        {contact_info.get('phone', '无')}
        {contact_info.get('wechat', '无')}
        
        客户消息：
        {customer_message}
        """
        
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = self.sender_email  # 发送给自己或销售邮箱
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            print("邮件发送成功")
        except Exception as e:
            print(f"邮件发送失败: {e}")