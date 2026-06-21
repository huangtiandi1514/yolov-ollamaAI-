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
          <text>正在思考中...</text>
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
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.message-list {
  flex: 1;
  padding: 20rpx;
  box-sizing: border-box;
}

.message-item {
  display: flex;
  margin-bottom: 30rpx;
  gap: 16rpx;
}

.user-msg {
  flex-direction: row-reverse;
}

.avatar {
  width: 70rpx;
  height: 70rpx;
  border-radius: 50%;
  background: #7c3aed;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  flex-shrink: 0;
}

.user-msg .avatar {
  background: #10b981;
}

.message-content {
  max-width: 70%;
  padding: 20rpx 24rpx;
  border-radius: 16rpx;
  background: #fff;
  font-size: 28rpx;
  line-height: 1.6;
  color: #333;
  word-break: break-all;
}

.user-msg .message-content {
  background: #7c3aed;
  color: #fff;
}

.loading-content {
  color: #999;
}

.empty-tip {
  color: #ccc;
  font-size: 24rpx;
}

.input-bar {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 20rpx;
  background: #fff;
  border-top: 1px solid #eee;
  box-sizing: border-box;
}

.voice-btn {
  width: 70rpx;
  height: 70rpx;
  border-radius: 50%;
  background: #f3e8ff;
  color: #7c3aed;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  border: none;
  padding: 0;
  flex-shrink: 0;
}

.input-box {
  flex: 1;
  height: 70rpx;
  padding: 0 20rpx;
  background: #f5f5f5;
  border-radius: 35rpx;
  font-size: 28rpx;
}

.send-btn {
  width: 120rpx;
  height: 70rpx;
  line-height: 70rpx;
  background: #7c3aed;
  color: #fff;
  border-radius: 35rpx;
  font-size: 28rpx;
  border: none;
  padding: 0;
  flex-shrink: 0;
}

.send-btn[disabled] {
  opacity: 0.5;
}
</style>