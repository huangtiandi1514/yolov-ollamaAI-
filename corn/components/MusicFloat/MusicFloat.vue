<template>
  <view 
    class="music-float" 
    :class="{ rotate: musicPlaying }"
    @click="toggleMusic"
  >
    <text>{{ musicPlaying ? '🔊' : '🔇' }}</text>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const musicPlaying = ref(true)

// 同步全局音乐状态
const syncState = () => {
  const app = getApp()
  if(app.globalData.musicPlaying !== undefined){
    musicPlaying.value = app.globalData.musicPlaying
  }
}

// 组件挂载时同步一次状态
onMounted(syncState)

// 切换播放/暂停核心逻辑
const toggleMusic = () => {
  const app = getApp()
  const bgm = app.globalData.bgm
  if (!bgm) {
    uni.showToast({ title: "音频初始化失败", icon: "none" })
    return
  }
  if (musicPlaying.value) {
    bgm.pause()
    musicPlaying.value = false
    app.globalData.musicPlaying = false
    uni.showToast({ title: "背景音乐已暂停", icon: "none" })
  } else {
    bgm.play()
    musicPlaying.value = true
    app.globalData.musicPlaying = true
    uni.showToast({ title: "背景音乐已播放", icon: "none" })
  }
}
</script>

<style scoped>
.music-float {
  position: fixed;
  top: 140rpx;
  right: 30rpx;
  width: 90rpx;
  height: 90rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 40rpx;
  z-index: 9999;
  box-shadow: 0 4rpx 16rpx rgba(124, 58, 237, 0.4);
}
@keyframes rotateMusic {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.rotate {
  animation: rotateMusic 4s linear infinite;
}
</style>