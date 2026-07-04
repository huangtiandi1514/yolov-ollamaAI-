<template>
  <view class="container">
    <!-- 音乐悬浮按钮 -->
    <MusicFloat />
	
    <!-- 图片上传区域 -->
    <view class="upload-box" @click="chooseImage">
      <image v-if="selectedImg" :src="selectedImg" class="preview-img" mode="aspectFit"></image>
      <view v-else class="upload-placeholder">
        <text class="upload-icon">📷</text>
        <text class="upload-text">点击上传或拍摄玉米叶片图片</text>
        <text class="upload-tip">支持相册选取 / 现场拍照</text>
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
      <view class="slider-tips">数值越高，AI判定病害标准越严格</view>
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
// 相对路径导入，解决找不到模块报错
import MusicFloat from '../../components/MusicFloat/MusicFloat.vue'

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
/* 全局基础美化 */
page {
  background: linear-gradient(180deg, #f8f6ff 0%, #f5f5f5 100%);
}
.container {
  padding: 24rpx;
  background: transparent;
  min-height: 100vh;
  box-sizing: border-box;
}

/* 上传区域优化：渐变虚线边框、阴影、点击动效 */
.upload-box {
  background: #fff;
  border-radius: 24rpx;
  height: 420rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  margin-bottom: 24rpx;
  border: 2rpx dashed #c4b5fd;
  box-shadow: 0 6rpx 20rpx rgba(124, 58, 237, 0.08);
  transition: all 0.25s ease;
}
.upload-box:active {
  transform: scale(0.98);
  box-shadow: 0 2rpx 8rpx rgba(124, 58, 237, 0.12);
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
  gap: 20rpx;
}
.upload-icon {
  font-size: 90rpx;
  color: #7c3aed;
  opacity: 0.75;
}
.upload-text {
  font-size: 30rpx;
  color: #444;
}
.upload-tip {
  font-size: 24rpx;
  color: #b1a2d8;
}

/* 置信度卡片美化 */
.conf-box {
  background: #fff;
  border-radius: 24rpx;
  padding: 36rpx 30rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 6rpx 20rpx rgba(124, 58, 237, 0.06);
}
.conf-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20rpx;
  font-size: 30rpx;
  color: #222;
  font-weight: 500;
}
.conf-value {
  color: #7c3aed;
  font-weight: bold;
  font-size: 32rpx;
}
.slider-tips {
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #999;
}

/* 检测按钮增强立体渐变、按压动画 */
.detect-btn {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  color: #fff;
  border-radius: 48rpx;
  font-size: 32rpx;
  font-weight: bold;
  border: none;
  margin-bottom: 36rpx;
  box-shadow: 0 8rpx 24rpx rgba(124, 58, 237, 0.3);
  transition: all 0.2s ease;
}
.detect-btn:active {
  transform: translateY(2rpx);
  box-shadow: 0 4rpx 12rpx rgba(124, 58, 237, 0.22);
}
.detect-btn[disabled] {
  opacity: 0.55;
  transform: none;
  box-shadow: none;
}

/* 结果卡片容器分层阴影 */
.result-box {
  background: #fff;
  border-radius: 24rpx;
  padding: 36rpx 30rpx;
  display: flex;
  flex-direction: column;
  gap: 28rpx;
  box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.05);
}
.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #222;
  margin-bottom: 16rpx;
  display: flex;
  align-items: center;
}

/* 风险等级卡片美化渐变背景 */
.risk-card {
  padding: 36rpx 20rpx;
  border-radius: 20rpx;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}
.risk-normal { 
  background: linear-gradient(135deg, #e8f5e9, #f1f8e9); 
  color: #2e7d32;
}
.risk-light { 
  background: linear-gradient(135deg, #e8f5e9, #dcedc8); 
  color: #2e7d32;
}
.risk-medium { 
  background: linear-gradient(135deg, #fff8e1, #ffecb3); 
  color: #f57f17;
}
.risk-heavy { 
  background: linear-gradient(135deg, #ffebee, #ffcdd2); 
  color: #c62828;
}
.risk-level {
  font-size: 36rpx;
  font-weight: bold;
}
.risk-score {
  font-size: 28rpx;
  opacity: 0.85;
}

/* 检测详情面板 */
.detect-detail {
  padding: 24rpx;
  background: #f9f7ff;
  border-radius: 16rpx;
}
.detail-text {
  font-size: 28rpx;
  line-height: 1.7;
  color: #333;
  white-space: pre-wrap;
}

/* AI诊断报告区域分割线美化 */
.report-box {
  border-top: 1rpx solid #eee;
  padding-top: 28rpx;
}
.report-text {
  font-size: 27rpx;
  line-height: 1.9;
  color: #444;
  white-space: pre-wrap;
}

/* 底部操作按钮 */
.action-btns {
  display: flex;
  gap: 24rpx;
  margin-top: 16rpx;
}
.action-btn {
  flex: 1;
  height: 76rpx;
  line-height: 76rpx;
  font-size: 28rpx;
  border-radius: 40rpx;
  background: linear-gradient(135deg, #f3e8ff, #ede2fe);
  color: #7c3aed;
  border: none;
  transition: all 0.2s ease;
}
.action-btn:active {
  transform: scale(0.97);
  background: linear-gradient(135deg, #e9dfff, #e1d4fd);
}
</style>