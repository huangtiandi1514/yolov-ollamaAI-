<template>
  <view class="record-page">
    <view class="refresh-bar" @click="loadData">
      <text>🔄 点击刷新记录</text>
    </view>

    <view v-if="recordList.length === 0" class="empty">
      <text>暂无检测记录</text>
    </view>

    <view v-else class="record-list">
      <view 
        v-for="(item, idx) in recordList" 
        :key="idx"
        class="record-card"
      >
        <view class="card-header">
          <text class="time">{{ item.time }}</text>
          <text class="name">{{ item.img_name }}</text>
        </view>
        <view class="summary">
          <text class="label">检测结果：</text>
          <text>{{ item.summary }}</text>
        </view>
        <view class="report-preview">
          <text class="label">诊断报告：</text>
          <text class="report-text">{{ item.report }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRecords } from '@/utils/api.js'

const recordList = ref([])

const loadData = async () => {
  try {
    const res = await getRecords()
    recordList.value = res
  } catch (e) {}
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.record-page {
  padding: 20rpx;
  min-height: 100vh;
  background: #f5f5f5;
  box-sizing: border-box;
}

.refresh-bar {
  background: #fff;
  padding: 24rpx;
  border-radius: 12rpx;
  text-align: center;
  color: #7c3aed;
  font-size: 28rpx;
  margin-bottom: 20rpx;
}

.empty {
  text-align: center;
  padding: 120rpx 0;
  color: #999;
  font-size: 28rpx;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.record-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}

.card-header {
  display: flex;
  justify-content: space-between;
  padding-bottom: 16rpx;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16rpx;
}

.time {
  font-size: 24rpx;
  color: #999;
}

.name {
  font-size: 26rpx;
  color: #333;
  font-weight: bold;
}

.summary {
  font-size: 26rpx;
  color: #555;
  line-height: 1.6;
  margin-bottom: 16rpx;
  white-space: pre-wrap;
}

.label {
  color: #7c3aed;
  font-weight: bold;
}

.report-preview {
  background: #f9f9f9;
  padding: 16rpx;
  border-radius: 8rpx;
}

.report-text {
  font-size: 24rpx;
  color: #666;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>