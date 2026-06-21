<template>
  <view class="container">
    <!-- 图片上传区域 -->
    <view class="upload-box" @click="chooseImage">
      <image v-if="selectedImg" :src="selectedImg" class="preview-img" mode="aspectFit"></image>
      <view v-else class="upload-placeholder">
        <text class="upload-icon">📷</text>
        <text class="upload-text">点击上传或拍摄玉米叶片图片</text>
      </view>
    </view>

    <!-- 置信度滑块 -->
    <view class="conf-box">
      <view class="conf-header">
        <text>置信度阈值</text>
        <text class="conf-value">{{ confValue }}</text>
      </view>
      <slider 
        :value="confValue * 100" 
        :min="10" 
        :max="90" 
        :step="5" 
        @change="onConfChange"
        activeColor="#7c3aed"
        backgroundColor="#e0e0e0"
        block-size="20"
      />
    </view>

    <!-- 检测按钮 -->
    <button 
      class="detect-btn" 
      :disabled="!selectedImg || loading"
      @click="startDetect"
    >
      {{ loading ? "检测中..." : "🔍 一键病害检测 + AI诊断" }}
    </button>

    <!-- 检测结果区域 -->
    <view v-if="detectResult" class="result-box">
      <!-- 风险等级卡片 -->
      <view :class="['risk-card', riskClass]">
        <text class="risk-level">病害等级：{{ detectResult.level }}</text>
        <text class="risk-score">风险指数：{{ detectResult.risk }} / 100</text>
      </view>

      <!-- 检测详情 -->
      <view class="detect-detail">
        <view class="section-title">📊 检测结果</view>
        <text class="detail-text">{{ detectResult.detect_text }}</text>
      </view>

      <!-- AI 诊断报告 -->
      <view class="report-box">
        <view class="section-title">🧑‍⚕️ AI 专业诊断报告</view>
        <text class="report-text">{{ detectResult.report }}</text>
      </view>

      <!-- 操作按钮 -->
      <view class="action-btns">
        <button class="action-btn" @click="saveReport">⭐ 收藏方案</button>
        <button class="action-btn" @click="readReport">🔊 语音播报</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { detectDisease, addFavorite, textToSpeech } from '@/utils/api.js'
import request from '@/utils/request.js'

const selectedImg = ref("")
const confValue = ref(0.25)
const loading = ref(false)
const detectResult = ref(null)

// 风险等级样式
const riskClass = computed(() => {
  if (!detectResult.value) return ""
  const level = detectResult.value.level
  const map = {
    "正常": "risk-normal",
    "轻度": "risk-light",
    "中度": "risk-medium",
    "重度": "risk-heavy"
  }
  return map[level] || ""
})

// 选择图片
const chooseImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ["compressed"],
    sourceType: ["album", "camera"],
    success: (res) => {
      selectedImg.value = res.tempFilePaths[0]
      detectResult.value = null
    }
  })
}

// 调节置信度
const onConfChange = (e) => {
  confValue.value = e.detail.value / 100
}

// 开始检测
const startDetect = async () => {
  if (!selectedImg.value) return
  loading.value = true
  try {
    const res = await detectDisease(selectedImg.value, confValue.value)
    detectResult.value = res
  } catch (e) {
    console.error("检测失败", e)
  } finally {
    loading.value = false
  }
}

// 收藏报告
const saveReport = async () => {
  if (!detectResult.value) return
  try {
    await addFavorite("玉米病害防治方案", detectResult.value.report)
    uni.showToast({ title: "收藏成功", icon: "success" })
  } catch (e) {}
}

// 语音播报
const readReport = async () => {
  if (!detectResult.value || !detectResult.value.report) {
    uni.showToast({ title: "暂无诊断内容可朗读", icon: "none" })
    return
  }
  try {
    uni.showLoading({ title: "生成语音中..." })
    const res = await textToSpeech(detectResult.value.report)
    const fullAudioUrl = request.BASE_URL + res.url
    
    const innerAudio = uni.createInnerAudioContext()
    innerAudio.src = fullAudioUrl
    innerAudio.onError((err) => {
      console.error("音频播放失败：", err)
      uni.showToast({ title: "语音播放失败", icon: "none" })
    })
    innerAudio.play()
  } catch (e) {
    console.error("语音生成失败：", e)
    uni.showToast({ title: "语音生成失败", icon: "none" })
  } finally {
    uni.hideLoading()
  }
}
</script>

<style scoped>
.container {
  padding: 20rpx;
  background: #f5f5f5;
  min-height: 100vh;
  box-sizing: border-box;
}

.upload-box {
  background: #fff;
  border-radius: 16rpx;
  height: 400rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  margin-bottom: 20rpx;
  border: 2rpx dashed #d0d0d0;
}

.preview-img {
  width: 100%;
  height: 100%;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #999;
  gap: 16rpx;
}

.upload-icon {
  font-size: 80rpx;
}

.upload-text {
  font-size: 28rpx;
}

.conf-box {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.conf-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16rpx;
  font-size: 28rpx;
  color: #333;
}

.conf-value {
  color: #7c3aed;
  font-weight: bold;
}

.detect-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  color: #fff;
  border-radius: 44rpx;
  font-size: 30rpx;
  font-weight: bold;
  border: none;
  margin-bottom: 30rpx;
}

.detect-btn[disabled] {
  opacity: 0.5;
}

.result-box {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 12rpx;
}

.risk-card {
  padding: 30rpx;
  border-radius: 12rpx;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.risk-normal, .risk-light { background: #e8f5e9; color: #2e7d32; }
.risk-medium { background: #fff8e1; color: #f57f17; }
.risk-heavy { background: #ffebee; color: #c62828; }

.risk-level {
  font-size: 32rpx;
  font-weight: bold;
}

.risk-score {
  font-size: 26rpx;
}

.detect-detail {
  padding: 20rpx;
  background: #f9f9f9;
  border-radius: 8rpx;
}

.detail-text {
  font-size: 28rpx;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
}

.report-box {
  border-top: 1px solid #eee;
  padding-top: 24rpx;
}

.report-text {
  font-size: 26rpx;
  line-height: 1.8;
  color: #555;
  white-space: pre-wrap;
}

.action-btns {
  display: flex;
  gap: 20rpx;
  margin-top: 10rpx;
}

.action-btn {
  flex: 1;
  height: 72rpx;
  line-height: 72rpx;
  font-size: 26rpx;
  border-radius: 36rpx;
  background: #f3e8ff;
  color: #7c3aed;
  border: none;
}
</style>