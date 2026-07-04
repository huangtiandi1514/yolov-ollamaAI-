<template>
  <view class="favorites-page">
    <view class="top-bar">
      <button class="refresh-btn" @click="loadFavorites">🔄 刷新列表</button>
    </view>

    <view v-if="favoritesList.length === 0 && !loading" class="empty">
      <text class="empty-icon">📭</text>
      <text class="empty-text">暂无收藏的防治方案</text>
      <text class="empty-desc">检测病害后可点击收藏保存方案</text>
    </view>

    <view v-else class="favorites-list">
      <view 
        v-for="(item, index) in favoritesList" 
        :key="index" 
        class="favorite-card"
      >
        <view class="card-header">
          <text class="card-title">{{ item.title }}</text>
          <text class="card-time">{{ item.add_time }}</text>
        </view>
        
        <view class="card-content">
          <text class="content-text">{{ item.content }}</text>
        </view>

        <view class="card-footer">
          <button class="delete-btn" @click="handleDelete(index)">
            🗑️ 删除
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getFavorites, deleteFavorite } from '@/utils/api.js'

const favoritesList = ref([])
const loading = ref(false)

const loadFavorites = async () => {
  loading.value = true
  try {
    const res = await getFavorites()
    favoritesList.value = res
  } catch (e) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const handleDelete = (index) => {
  uni.showModal({
    title: '提示',
    content: '确定要删除这条收藏方案吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteFavorite(index)
          uni.showToast({ title: '删除成功', icon: 'success' })
          loadFavorites()
        } catch (e) {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

onMounted(() => {
  loadFavorites()
})
</script>

<style scoped>
.favorites-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
  box-sizing: border-box;
}

.top-bar {
  margin-bottom: 20rpx;
}

.refresh-btn {
  width: 100%;
  height: 80rpx;
  line-height: 80rpx;
  background: #fff;
  border-radius: 12rpx;
  font-size: 28rpx;
  color: #7c3aed;
  border: none;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
  gap: 20rpx;
}

.empty-icon {
  font-size: 100rpx;
}

.empty-text {
  font-size: 30rpx;
  color: #666;
}

.empty-desc {
  font-size: 24rpx;
  color: #999;
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.favorite-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16rpx;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16rpx;
}

.card-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
}

.card-time {
  font-size: 22rpx;
  color: #999;
}

.card-content {
  margin-bottom: 20rpx;
}

.content-text {
  font-size: 26rpx;
  line-height: 1.8;
  color: #555;
  white-space: pre-wrap;
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
}

.delete-btn {
  width: 160rpx;
  height: 60rpx;
  line-height: 60rpx;
  font-size: 24rpx;
  background: #ffebee;
  color: #c62828;
  border-radius: 30rpx;
  border: none;
}
</style>