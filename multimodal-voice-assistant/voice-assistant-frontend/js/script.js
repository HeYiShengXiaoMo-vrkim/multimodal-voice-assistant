document.addEventListener('DOMContentLoaded', () => {
    // --- 获取 DOM 元素 ---
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const voiceButton = document.getElementById('voice-button');
    const statusIndicator = document.getElementById('status-indicator');
    const statusDot = statusIndicator.querySelector('.status-dot');
    const statusText = statusIndicator.querySelector('.status-text');
    const assistantResponse = document.getElementById('assistant-response');
    const loadingIndicator = document.getElementById('loading-indicator');
    // const responseImage = document.getElementById('response-image'); // 如果需要显示图片

    // --- 状态管理 ---
    const STATUS = {
        IDLE: 'idle',
        PROCESSING: 'processing',
        ERROR: 'error',
        RECORDING: 'recording' // 用于语音输入状态
    };

    let currentStatus = STATUS.IDLE;
    let isRecording = false; // 跟踪录音状态

    function updateStatus(newStatus, text) {
        statusIndicator.className = `status-indicator status-${newStatus}`;
        statusText.textContent = text;
        currentStatus = newStatus;
    }

    function showLoading(isLoading) {
        loadingIndicator.style.display = isLoading ? 'block' : 'none';
    }

    function displayResponse(message, isError = false) {
        // 清空现有内容
        assistantResponse.innerHTML = '';

        const p = document.createElement('p');
        p.textContent = message;
        if (isError) {
            p.style.color = 'var(--error-color)';
        }
        assistantResponse.appendChild(p);

        // 如果需要显示图片，可以在这里处理
        // responseImage.style.display = 'none'; // 重置图片
        // if (imageUrl) {
        //     responseImage.src = imageUrl;
        //     responseImage.style.display = 'block';
        // }
    }

    // --- API 调用 ---
    async function sendCommandToBackend(command, type = 'text') {
        updateStatus(STATUS.PROCESSING, '处理中...');
        showLoading(true);
        displayResponse(''); // 清空旧响应

        // --- 假设后端 API 端点为 /api/command ---
        const apiUrl = '/api/command'; // 你需要创建这个后端端点

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: command, type: type }), // 发送指令和类型
            });

            if (!response.ok) {
                // 处理 HTTP 错误
                const errorData = await response.json().catch(() => ({ detail: '无法解析错误信息' }));
                throw new Error(errorData.detail || `服务器错误: ${response.status}`);
            }

            const data = await response.json(); // 解析 JSON 响应

            if (data.error) {
                // 处理后端返回的业务错误
                throw new Error(data.error);
            }

            // 显示成功响应
            displayResponse(data.response || '收到空响应');
            // 如果后端返回图片 URL 或 Base64 数据，可以在这里处理并显示图片
            // if (data.image_url) { displayResponse(data.response, false, data.image_url); }

            updateStatus(STATUS.IDLE, '空闲');

        } catch (error) {
            console.error('API 调用失败:', error);
            displayResponse(`错误: ${error.message}`, true);
            updateStatus(STATUS.ERROR, '错误');
        } finally {
            showLoading(false);
        }
    }

    // --- 事件监听器 ---

    // 发送文本指令
    sendButton.addEventListener('click', () => {
        const commandText = userInput.value.trim();
        if (commandText) {
            sendCommandToBackend(commandText, 'text');
            // userInput.value = ''; // 可选：发送后清空输入框
        } else {
            displayResponse('请输入指令。', true);
        }
    });

    // 允许按 Enter 发送 (在 textarea 中按 Shift+Enter 换行)
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // 阻止默认的换行行为
            sendButton.click(); // 触发发送按钮点击
        }
    });

    // 语音输入按钮 (基本逻辑，未实现 Web Speech API)
    voiceButton.addEventListener('click', () => {
        if (!isRecording) {
            // --- 开始录音 (需要 Web Speech API 实现) ---
            isRecording = true;
            voiceButton.classList.add('recording'); // 添加录音样式
            voiceButton.title = '停止语音输入';
            voiceButton.querySelector('i').className = 'fas fa-stop'; // 更改图标
            updateStatus(STATUS.RECORDING, '录音中...');
            userInput.value = ''; // 清空文本框
            userInput.placeholder = '正在聆听...';
            console.log("开始录音 (需要 Web Speech API)");

            // --- 模拟录音结束并获取结果 (需要替换为真实 API) ---
            // setTimeout(() => {
            //     if (isRecording) { // 确保仍然在录音状态
            //         const mockTranscript = "这是模拟的语音识别结果";
            //         userInput.value = mockTranscript;
            //         voiceButton.click(); // 模拟点击停止
            //         // 可以选择自动发送
            //         // sendCommandToBackend(mockTranscript, 'voice');
            //     }
            // }, 5000); // 模拟 5 秒录音

        } else {
            // --- 停止录音 (需要 Web Speech API 实现) ---
            isRecording = false;
            voiceButton.classList.remove('recording');
            voiceButton.title = '开始语音输入';
            voiceButton.querySelector('i').className = 'fas fa-microphone'; // 恢复图标
            updateStatus(STATUS.IDLE, '空闲');
            userInput.placeholder = '输入文本指令或点击麦克风...';
            console.log("停止录音 (需要 Web Speech API)");
            // 在这里，Web Speech API 会返回最终识别结果
            // 你可以将结果填充到 userInput.value 中，或者直接发送
            // const finalTranscript = event.results[0][0].transcript; // 示例
            // sendCommandToBackend(finalTranscript, 'voice');
        }
    });

    // --- 初始化 ---
    updateStatus(STATUS.IDLE, '空闲'); // 设置初始状态

}); // End DOMContentLoaded