<template>
  <view class="batch-page">
    <view class="upload-section">
      <view class="section-title">选择检测图片</view>
      <view class="image-grid">
        <view v-for="(img, idx) in imageList" :key="idx" class="image-item">
          <image :src="img" mode="aspectFill" class="img-preview"></image>
          <view class="delete-icon" @click="removeImage(idx)">×</view>
          <view v-if="resultList[idx]" class="result-tag" :class="getLevelClass(resultList[idx].level)">
            {{ resultList[idx].level }}
          </view>
        </view>
        <view v-if="imageList.length < maxCount" class="add-btn" @click="chooseImage">
          <text class="add-icon">+</text>
          <text class="add-text">添加图片</text>
        </view>
      </view>
      <view class="tip-text">最多可选择 {{ maxCount }} 张图片</view>
    </view>

    <view class="conf-section">
      <view class="conf-header">
        <text>置信度阈值</text>
        <text class="conf-value">{{ confThreshold }}</text>
      </view>
      <slider 
        :value="confThreshold * 100" 
        :min="10" 
        :max="90" 
        :step="5" 
        @change="onConfChange"
        activeColor="#7c3aed"
        backgroundColor="#e0e0e0"
        block-size="20"
      />
    </view>

    <button 
      class="detect-btn" 
      :disabled="imageList.length === 0 || detecting"
      @click="startBatchDetect"
    >
      {{ detecting ? '检测中...' : '开始批量检测' }}
    </button>

    <view v-if="resultList.length > 0" class="result-section">
      <view class="section-title">检测结果汇总</view>
      
      <view class="summary-card">
        <view class="summary-item">
          <text class="summary-num">{{ totalCount }}</text>
          <text class="summary-label">总检测数</text>
        </view>
        <view class="summary-item">
          <text class="summary-num success">{{ successCount }}</text>
          <text class="summary-label">成功</text>
        </view>
        <view class="summary-item">
          <text class="summary-num error">{{ failCount }}</text>
          <text class="summary-label">失败</text>
        </view>
      </view>

      <view class="result-list">
        <view 
          v-for="(item, index) in resultList" 
          :key="index" 
          class="result-card"
        >
          <view class="result-header">
            <text class="result-name">图片 {{ index + 1 }}</text>
            <view v-if="item.success" class="level-tag" :class="getLevelClass(item.level)">
              {{ item.level }}
            </view>
            <view v-else class="level-tag error">检测失败</view>
          </view>

          <view v-if="item.success" class="result-content">
            <text class="detect-text">{{ item.detect_text }}</text>
            <view class="action-row">
              <button class="action-btn" @click="viewReport(index)">查看完整报告</button>
              <button class="action-btn primary" @click="saveToFavorites(index)">收藏方案</button>
            </view>
          </view>
          <view v-else class="result-content">
            <text class="error-text">{{ item.error }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { batchDetect, addFavorite } from '@/utils/api.js'

const maxCount = 9
const imageList = ref([])
const confThreshold = ref(0.25)
const detecting = ref(false)
const resultList = ref([])

const totalCount = computed(() => resultList.value.length)
const successCount = computed(() => resultList.value.filter(item => item.success).length)
const failCount = computed(() => resultList.value.filter(item => !item.success).length)

const getLevelClass = (level) => {
  const map = {
    '正常': 'normal',
    '轻度': 'light',
    '中度': 'medium',
    '重度': 'heavy'
  }
  return map[level] || 'normal'
}

const chooseImage = () => {
  const remainCount = maxCount - imageList.value.length
  uni.chooseImage({
    count: remainCount,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      imageList.value = [...imageList.value, ...res.tempFilePaths]
    }
  })
}

const removeImage = (index) => {
  imageList.value.splice(index, 1)
  if (resultList.value.length > 0) {
    resultList.value.splice(index, 1)
  }
}

const onConfChange = (e) => {
  confThreshold.value = e.detail.value / 100
}

const startBatchDetect = async () => {
  if (imageList.value.length === 0) return
  
  detecting.value = true
  resultList.value = []
  
  try {
    const results = await batchDetect(imageList.value, confThreshold.value)
    resultList.value = results
    uni.showToast({ title: '检测完成', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: '批量检测失败', icon: 'none' })
  } finally {
    detecting.value = false
  }
}

const viewReport = (index) => {
  const item = resultList.value[index]
  uni.showModal({
    title: '完整诊断报告',
    content: item.report,
    showCancel: false,
    confirmText: '我知道了'
  })
}

const saveToFavorites = async (index) => {
  const item = resultList.value[index]
  try {
    await addFavorite(`批量检测-${item.level}病害方案`, item.report)
    uni.showToast({ title: '收藏成功', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: '收藏失败', icon: 'none' })
  }
}
</script>

<style scoped>
.batch-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
  box-sizing: border-box;
  padding-bottom: 40rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.upload-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.image-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.image-item {
  width: calc((100% - 32rpx) / 3);
  height: 200rpx;
  border-radius: 12rpx;
  overflow: hidden;
  position: relative;
  background: #f0f0f0;
}

.img-preview {
  width: 100%;
  height: 100%;
}

.delete-icon {
  position: absolute;
  top: 4rpx;
  right: 4rpx;
  width: 40rpx;
  height: 40rpx;
  line-height: 36rpx;
  text-align: center;
  background: rgba(0,0,0,0.6);
  color: #fff;
  border-radius: 50%;
  font-size: 28rpx;
}

.result-tag {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 22rpx;
  padding: 4rpx 0;
  color: #fff;
}

.result-tag.normal { background: rgba(76, 175, 80, 0.9); }
.result-tag.light { background: rgba(76, 175, 80, 0.9); }
.result-tag.medium { background: rgba(255, 152, 0, 0.9); }
.result-tag.heavy { background: rgba(244, 67, 54, 0.9); }

.add-btn {
  width: calc((100% - 32rpx) / 3);
  height: 200rpx;
  border: 2rpx dashed #d0d0d0;
  border-radius: 12rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  background: #fafafa;
}

.add-icon {
  font-size: 48rpx;
  color: #999;
}

.add-text {
  font-size: 24rpx;
  color: #999;
}

.tip-text {
  font-size: 22rpx;
  color: #999;
  margin-top: 16rpx;
  text-align: right;
}

.conf-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
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

.result-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}

.summary-card {
  display: flex;
  background: #fafafa;
  border-radius: 12rpx;
  padding: 24rpx 0;
  margin-bottom: 24rpx;
}

.summary-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.summary-num {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.summary-num.success { color: #4CAF50; }
.summary-num.error { color: #f44336; }

.summary-label {
  font-size: 24rpx;
  color: #666;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.result-card {
  border: 1px solid #f0f0f0;
  border-radius: 12rpx;
  padding: 20rpx;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.result-name {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
}

.level-tag {
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
  color: #fff;
}

.level-tag.normal { background: #4CAF50; }
.level-tag.light { background: #4CAF50; }
.level-tag.medium { background: #FF9800; }
.level-tag.heavy { background: #f44336; }
.level-tag.error { background: #9e9e9e; }

.result-content {
  font-size: 26rpx;
  color: #555;
  line-height: 1.6;
}

.detect-text {
  white-space: pre-wrap;
  margin-bottom: 16rpx;
}

.error-text {
  color: #f44336;
}

.action-row {
  display: flex;
  gap: 16rpx;
  margin-top: 12rpx;
}

.action-btn {
  flex: 1;
  height: 64rpx;
  line-height: 64rpx;
  font-size: 24rpx;
  border-radius: 32rpx;
  background: #f3e8ff;
  color: #7c3aed;
  border: none;
}

.action-btn.primary {
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  color: #fff;
}
</style>