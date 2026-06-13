let sessionId = null;

async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    if (!message) return;

    // 显示用户消息
    appendMessage('user', message);
    input.value = '';

    // 显示加载状态
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot-message loading';
    loadingDiv.innerText = '思考中...';
    document.getElementById('chat-box').appendChild(loadingDiv);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, session_id: sessionId })
        });

        const data = await response.json();
        sessionId = data.session_id;

        // 移除加载状态
        loadingDiv.remove();

        // 显示机器人回复
        appendMessage('bot', data.response);
    } catch (error) {
        loadingDiv.remove();
        appendMessage('system', '网络错误，请稍后重试');
    }
}

function appendMessage(sender, text) {
    const chatBox = document.getElementById('chat-box');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-message`;
    msgDiv.innerText = text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // 滚动到底部
}

// 支持回车发送
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('message-input');
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});