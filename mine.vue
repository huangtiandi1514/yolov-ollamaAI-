<template>
  <view class="mine-page">
    <!-- 用户信息卡片 -->
    <view class="user-card">
      <text class="avatar">👨‍🌾</text>
      <view class="info">
        <text class="name">农业管理员</text>
        <text class="desc">本地离线玉米病害诊断系统</text>
      </view>
    </view>

    <!-- 功能菜单 -->
    <view class="menu-group">
      <view class="menu-item" @click="goFavorites">
        <text class="icon">⭐</text>
        <text class="title">收藏的防治方案</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item" @click="goBatch">
        <text class="icon">📁</text>
        <text class="title">批量图片检测</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item" @click="runEvaluate">
        <text class="icon">📈</text>
        <text class="title">模型精度评估</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item" @click="clearCache">
        <text class="icon">🗑️</text>
        <text class="title">清理缓存</text>
        <text class="arrow">></text>
      </view>
    </view>

    <!-- 系统信息 -->
    <view class="info-card">
      <view class="card-title">系统信息</view>
      <view class="info-row">
        <text class="label">检测模型</text>
        <text class="value">YOLOv11 自定义病害模型</text>
      </view>
      <view class="info-row">
        <text class="label">AI大模型</text>
        <text class="value">Qwen2.5 本地部署</text>
      </view>
      <view class="info-row">
        <text class="label">支持病害种类</text>
        <text class="value">4 类玉米常见病害</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { evaluateModel } from '@/utils/api.js'

// 跳转到收藏方案
const goFavorites = () => {
  uni.navigateTo({
    url: '/pages/favorites/favorites'
  })
}

// 跳转到批量检测
const goBatch = () => {
  uni.navigateTo({
    url: '/pages/batch/batch'
  })
}

// 模型精度评估
const runEvaluate = async () => {
  try {
    const res = await evaluateModel()
    uni.showModal({
      title: '模型精度评估结果',
      content: `mAP@0.5：${res.map50}\nmAP@0.5-0.95：${res['map50_95']}`,
      showCancel: false
    })
  } catch (e) {}
}

// 清理缓存
const clearCache = () => {
  uni.showModal({
    title: '提示',
    content: '确定要清理缓存吗？',
    success: (res) => {
      if (res.confirm) {
        uni.clearStorageSync()
        uni.showToast({ title: '清理成功', icon: 'success' })
      }
    }
  })
}
</script>

<style scoped>
.mine-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 40rpx;
}

.user-card {
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  padding: 60rpx 30rpx;
  display: flex;
  align-items: center;
  gap: 30rpx;
  color: #fff;
}

.avatar {
  font-size: 100rpx;
}

.info {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.name {
  font-size: 36rpx;
  font-weight: bold;
}

.desc {
  font-size: 24rpx;
  opacity: 0.8;
}

.menu-group {
  background: #fff;
  margin: 20rpx;
  border-radius: 16rpx;
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 30rpx 24rpx;
  border-bottom: 1px solid #f0f0f0;
  gap: 20rpx;
}

.menu-item:last-child {
  border-bottom: none;
}

.icon {
  font-size: 36rpx;
}

.title {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.arrow {
  font-size: 28rpx;
  color: #ccc;
}

.info-card {
  background: #fff;
  margin: 0 20rpx;
  border-radius: 16rpx;
  padding: 24rpx;
}

.card-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.info-row {
  display: flex;
  padding: 12rpx 0;
  font-size: 26rpx;
}

.label {
  color: #666;
  width: 200rpx;
}

.value {
  color: #333;
  flex: 1;
}
</style>