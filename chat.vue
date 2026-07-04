<template>
  <view class="chat-page">
    <!-- 消息列表 -->
    <scroll-view 
      class="message-list" 
      scroll-y 
      :scroll-into-view="scrollToId"
      scroll-with-animation
    >
      <view 
        v-for="(item, index) in messageList" 
        :key="index"
        :id="'msg-' + index"
        :class="['message-item', item.role === 'user' ? 'user-msg' : 'ai-msg']"
      >
        <view class="avatar">{{ item.role === 'user' ? '我' : 'AI' }}</view>
        <view class="message-content">
          <!-- 强制转字符串，彻底规避类型错误 -->
          <text v-if="formatContent(item.content)">{{ formatContent(item.content) }}</text>
          <text v-else class="empty-tip">内容为空</text>
        </view>
      </view>

      <!-- 加载中状态 -->
      <view v-if="loading" class="message-item ai-msg">
        <view class="avatar">AI</view>
        <view class="message-content loading-content">
          <text>正在思考中</text>
          <view class="loading-dots">
            <view class="dot"></view>
            <view class="dot"></view>
            <view class="dot"></view>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 底部输入栏 -->
    <view class="input-bar">
      <button class="voice-btn" @touchstart="startRecord" @touchend="stopRecord">
        🎤
      </button>
      <input 
        v-model="inputText" 
        class="input-box" 
        placeholder="请输入病害相关问题"
        confirm-type="send"
        @confirm="sendMessage"
      />
      <button 
        class="send-btn" 
        :disabled="!inputText?.trim() || loading"
        @click="sendMessage"
      >
        发送
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { aiChat, speechToText } from '@/utils/api.js'

// 消息列表
const messageList = ref([
  {
    role: 'assistant',
    content: '您好，我是玉米病害专家助手，有什么种植或病害问题都可以问我~'
  }
])
const inputText = ref('')
const loading = ref(false)
const scrollToId = ref('')

// 语音相关实例（延迟初始化）
let audioContext = null
let recorderManager = null

// ==================== 核心修复：内容格式化方法 ====================
// 强制把任意类型转成纯文本字符串，彻底解决trim报错
const formatContent = (content) => {
  if (content === null || content === undefined) return ''
  if (typeof content === 'string') return content.trim()
  // 对象/数组/数字等其他类型，统一转成字符串
  if (typeof content === 'object') {
    try {
      return JSON.stringify(content)
    } catch (e) {
      return String(content)
    }
  }
  return String(content)
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    const lastIndex = messageList.value.length - 1
    scrollToId.value = 'msg-' + lastIndex
  })
}

// 发送消息
const sendMessage = async () => {
  // 空值校验
  const text = inputText.value?.trim()
  if (!text) {
    uni.showToast({ title: '请输入内容', icon: 'none' })
    return
  }

  // 添加用户消息
  messageList.value.push({
    role: 'user',
    content: text
  })
  inputText.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const reply = await aiChat(text)
    // 兜底：强制格式化返回内容，保证一定是字符串
    const safeReply = formatContent(reply)
    messageList.value.push({
      role: 'assistant',
      content: safeReply || '抱歉，我暂时无法回答这个问题。'
    })
  } catch (err) {
    messageList.value.push({
      role: 'assistant',
      content: '网络连接失败，请稍后重试。'
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 开始录音
const startRecord = () => {
  if (!recorderManager) return
  recorderManager.start({
    duration: 60000,
    format: 'mp3'
  })
  uni.showToast({ title: '正在录音...', icon: 'none' })
}

// 结束录音并识别
const stopRecord = async () => {
  if (!recorderManager) return
  recorderManager.stop()
}

// 初始化语音实例
const initVoice = () => {
  // #ifndef H5
  // 初始化录音管理器
  recorderManager = uni.getRecorderManager()
  
  // 录音结束回调
  recorderManager.onStop(async (res) => {
    try {
      uni.showLoading({ title: '识别中...' })
      const text = await speechToText(res.tempFilePath)
      inputText.value = formatContent(text)
    } catch (err) {
      uni.showToast({ title: '识别失败', icon: 'none' })
    } finally {
      uni.hideLoading()
    }
  })

  // 初始化音频播放器
  audioContext = uni.createInnerAudioContext()
  
  // 播放结束回调，加判空保护
  audioContext.onStop(() => {
    console.log('语音播放结束')
  })

  audioContext.onError((err) => {
    console.error('播放失败', err)
    uni.showToast({ title: '语音播放失败', icon: 'none' })
  })
  // #endif
}

onMounted(() => {
  initVoice()
})

onUnmounted(() => {
  // 销毁实例前先判空，避免重复销毁报错
  if (audioContext) {
    audioContext.stop()
    audioContext.destroy()
    audioContext = null
  }
  if (recorderManager) {
    recorderManager.stop()
    recorderManager = null
  }
})
</script>

<style scoped>
/* ==================== 全局优化 ==================== */
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #f0f7f2 0%, #e8f0ea 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

/* ==================== 消息列表优化 ==================== */
.message-list {
  flex: 1;
  padding: 24rpx 20rpx 10rpx 20rpx;
  box-sizing: border-box;
  /* 美化滚动条 */
  scrollbar-width: thin;
  scrollbar-color: #b8d0be #e8f0ea;
}

.message-list::-webkit-scrollbar {
  width: 4px;
}

.message-list::-webkit-scrollbar-track {
  background: #e8f0ea;
  border-radius: 10px;
}

.message-list::-webkit-scrollbar-thumb {
  background: #b8d0be;
  border-radius: 10px;
}

.message-item {
  display: flex;
  margin-bottom: 32rpx;
  gap: 16rpx;
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-msg {
  flex-direction: row-reverse;
}

/* ==================== 头像优化 ==================== */
.avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 600;
  flex-shrink: 0;
  box-shadow: 0 4rpx 16rpx rgba(124, 58, 237, 0.25);
  transition: transform 0.2s;
}

.user-msg .avatar {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 4rpx 16rpx rgba(16, 185, 129, 0.25);
}

.message-item:hover .avatar {
  transform: scale(1.05);
}

/* ==================== 消息内容优化 ==================== */
.message-content {
  max-width: 72%;
  padding: 22rpx 28rpx;
  border-radius: 20rpx;
  background: #ffffff;
  font-size: 28rpx;
  line-height: 1.7;
  color: #1a2332;
  word-break: break-all;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(200, 215, 205, 0.15);
  transition: box-shadow 0.2s;
}

.user-msg .message-content {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  color: #ffffff;
  box-shadow: 0 6rpx 24rpx rgba(124, 58, 237, 0.25);
  border: none;
}

.user-msg .message-content:active {
  transform: scale(0.98);
}

.loading-content {
  background: #f0f6f2 !important;
  color: #5a7a6a !important;
  border: 1px solid #d4e2d8 !important;
  display: flex;
  align-items: center;
  gap: 12rpx;
  box-shadow: none !important;
}

/* ==================== 加载动画优化 ==================== */
.loading-dots {
  display: inline-flex;
  gap: 8rpx;
  margin-left: 4rpx;
}

.dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #5a7a6a;
  animation: dotBounce 1.4s ease-in-out infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dotBounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-12rpx);
    opacity: 1;
  }
}

.empty-tip {
  color: #b8c8be;
  font-size: 24rpx;
  font-style: italic;
}

/* ==================== 底部输入栏优化 ==================== */
.input-bar {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 18rpx 24rpx 24rpx 24rpx;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(200, 215, 205, 0.25);
  box-sizing: border-box;
  box-shadow: 0 -4rpx 24rpx rgba(0, 0, 0, 0.03);
}

/* ==================== 语音按钮优化 ==================== */
.voice-btn {
  width: 76rpx;
  height: 76rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #f3e8ff, #ede0ff);
  color: #7c3aed;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  border: none;
  padding: 0;
  flex-shrink: 0;
  transition: all 0.25s ease;
  box-shadow: 0 4rpx 12rpx rgba(124, 58, 237, 0.12);
  cursor: pointer;
  position: relative;
}

.voice-btn:active {
  transform: scale(0.88);
  background: linear-gradient(135deg, #ede0ff, #dcc8ff);
  box-shadow: 0 2rpx 8rpx rgba(124, 58, 237, 0.2);
}

/* 语音录制激活状态 */
.voice-btn.recording {
  background: linear-gradient(135deg, #f87171, #ef4444);
  color: #ffffff;
  animation: pulse-recording 1.2s ease-in-out infinite;
  box-shadow: 0 4rpx 20rpx rgba(239, 68, 68, 0.3);
}

@keyframes pulse-recording {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
  }
  50% {
    box-shadow: 0 0 0 16rpx rgba(239, 68, 68, 0);
  }
}

/* ==================== 输入框优化 ==================== */
.input-box {
  flex: 1;
  height: 76rpx;
  padding: 0 28rpx;
  background: #f5faf7;
  border-radius: 40rpx;
  font-size: 28rpx;
  border: 1.5px solid transparent;
  transition: all 0.3s ease;
  color: #1a2332;
  outline: none;
}

.input-box:focus {
  background: #ffffff;
  border-color: #7c3aed;
  box-shadow: 0 0 0 6rpx rgba(124, 58, 237, 0.08);
}

.input-box::placeholder {
  color: #9ab0a4;
  font-weight: 300;
}

/* ==================== 发送按钮优化 ==================== */
.send-btn {
  width: 128rpx;
  height: 76rpx;
  line-height: 76rpx;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  color: #fff;
  border-radius: 40rpx;
  font-size: 28rpx;
  font-weight: 500;
  border: none;
  padding: 0;
  flex-shrink: 0;
  transition: all 0.25s ease;
  box-shadow: 0 6rpx 20rpx rgba(124, 58, 237, 0.25);
  cursor: pointer;
  letter-spacing: 2rpx;
}

.send-btn:active {
  transform: scale(0.94);
  box-shadow: 0 3rpx 12rpx rgba(124, 58, 237, 0.15);
}

.send-btn[disabled] {
  opacity: 0.4;
  transform: scale(0.98);
  box-shadow: none;
  pointer-events: none;
}

.send-btn::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 40rpx;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), transparent);
  pointer-events: none;
}

.send-btn {
  position: relative;
  overflow: hidden;
}

/* ==================== 消息时间戳（新增） ==================== */
.message-content .message-time {
  display: block;
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 10rpx;
  text-align: right;
}

.user-msg .message-content .message-time {
  color: rgba(255, 255, 255, 0.5);
}

.ai-msg .message-content .message-time {
  color: #9ab0a4;
}

/* ==================== 消息复制功能（新增） ==================== */
.message-content .copy-btn {
  display: inline-block;
  font-size: 20rpx;
  color: #7c3aed;
  background: rgba(124, 58, 237, 0.08);
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  margin-top: 10rpx;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.message-content .copy-btn:active {
  background: rgba(124, 58, 237, 0.2);
  transform: scale(0.95);
}

.user-msg .message-content .copy-btn {
  color: #d4b0ff;
  background: rgba(255, 255, 255, 0.12);
}

/* ==================== 响应式适配 ==================== */
@media (max-width: 460px) {
  .message-content {
    font-size: 26rpx;
    padding: 18rpx 22rpx;
  }
  
  .avatar {
    width: 64rpx;
    height: 64rpx;
    font-size: 24rpx;
  }
  
  .input-box {
    height: 68rpx;
    font-size: 26rpx;
  }
  
  .send-btn {
    width: 112rpx;
    height: 68rpx;
    line-height: 68rpx;
    font-size: 26rpx;
  }
  
  .voice-btn {
    width: 68rpx;
    height: 68rpx;
    font-size: 30rpx;
  }
  
  .input-bar {
    padding: 14rpx 16rpx 20rpx 16rpx;
    gap: 12rpx;
  }
}

/* 适配 iPhone 安全区域 */
@supports (padding: max(0px)) {
  .chat-page {
    padding-bottom: max(env(safe-area-inset-bottom), 0px);
  }
}
</style>
