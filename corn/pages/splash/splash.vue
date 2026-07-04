<template>
  <view class="splash-container">
    <!-- 启动视频：静音自动播放，禁止手势进度，避免误操作 -->
    <video
      id="splashVideo"
      class="splash-video"
      :src="videoSrc"
      :controls="false"
      :show-center-play-btn="false"
      :show-fullscreen-btn="false"
      :show-play-btn="false"
      :muted="true"
      :loop="false"
      :autoplay="true"
      :enable-progress-gesture="false"
      object-fit="cover"
      @ended="onVideoEnd"
      @error="onVideoError"
    ></video>

    <!-- 跳过按钮 -->
    <cover-view class="skip-btn" @click="goHome">
      <cover-view>跳过 {{ countDown }}s</cover-view>
    </cover-view>
  </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const videoSrc = '/static/video/corns.mp4'
const countDown = ref(5)
let timer = null
let videoContext = null

onMounted(() => {
  videoContext = uni.createVideoContext('splashVideo')
  // 兜底：部分平台autoplay属性不生效，手动调用播放
  videoContext.play()
  // 启动倒计时
  startCountDown()
})

// 启动5秒倒计时，时间到自动跳转
const startCountDown = () => {
  timer = setInterval(() => {
    countDown.value--
    if (countDown.value <= 0) {
      clearInterval(timer)
      goHome()
    }
  }, 1000)
}

// 视频播放结束：自动跳首页
const onVideoEnd = () => {
  clearInterval(timer)
  goHome()
}

// 视频加载失败：1秒后自动跳转首页，避免白屏
const onVideoError = () => {
  clearInterval(timer)
  uni.showToast({ title: '视频加载失败', icon: 'none' })
  setTimeout(() => goHome(), 1000)
}

// 跳转首页（reLaunch避免返回回到启动页）
const goHome = () => {
  clearInterval(timer)
  uni.reLaunch({
    url: '/pages/index/index'
  })
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.splash-container {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background-color: #000;
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  user-select: none;
}

.splash-video {
  width: 100%;
  height: 100%;
  display: block;
  vertical-align: middle;
}

/* 跳过按钮：适配刘海屏 */
.skip-btn {
  position: absolute;
  top: calc(var(--status-bar-height, 20px) + 24rpx);
  right: 40rpx;
  padding: 14rpx 32rpx;
  background-color: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: 26rpx;
  border-radius: 40rpx;
  z-index: 999;
  min-height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>