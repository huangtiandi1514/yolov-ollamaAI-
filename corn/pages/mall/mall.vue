<template>
  <view class="mall-page">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <input 
        class="search-input" 
        v-model="keyword" 
        placeholder="搜索玉米病害·农药·农资"
        confirm-type="search"
        @confirm="handleSearch"
      />
      <view class="search-btn" @click="handleSearch">搜索</view>
    </view>

    <!-- 京东农资专区快捷入口 -->
    <view class="jd-channel-tip" @click="goToJDAgricultural">
      <text class="tip-icon">🏪</text>
      <text class="tip-text">京东农资 · 正品保障</text>
      <text class="tip-arrow">›</text>
    </view>

    <!-- 病害药品分类区 -->
    <view class="section">
      <view class="section-title">玉米病害 · 对症购药</view>
      <view class="drug-grid">
        <view 
          class="drug-card"
          v-for="(item, index) in drugCategory"
          :key="index"
          @click="goToJD(item.keyword)"
        >
          <view class="drug-icon">{{ item.icon }}</view>
          <view class="drug-name">{{ item.name }}</view>
          <view class="drug-effect">{{ item.effect }}</view>
          <view class="go-buy">去京东购买 ›</view>
        </view>
      </view>
    </view>

    <!-- 常用农资专区 -->
    <view class="section">
      <view class="section-title">常用农资推荐</view>
      <view class="tool-list">
        <view class="tool-item" v-for="(item, index) in toolList" :key="index" @click="goToJD(item.keyword)">
          <view class="tool-icon">{{ item.icon }}</view>
          <view class="tool-info">
            <view class="tool-name">{{ item.name }}</view>
            <view class="tool-desc">{{ item.desc }}</view>
          </view>
          <view class="tool-arrow">›</view>
        </view>
      </view>
    </view>

    <!-- 底部提示 -->
    <view class="footer-tip">
      <text>点击商品将跳转京东官方平台选购</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'

const keyword = ref('')

// 病害药品分类
const drugCategory = ref([
  {
    name: '玉米大斑病',
    icon: '🍂',
    effect: '叶部长梭形大病斑',
    keyword: '玉米大斑病 戊唑醇 苯醚甲环唑 杀菌剂'
  },
  {
    name: '玉米小斑病',
    icon: '🍃',
    effect: '叶片小圆斑坏死',
    keyword: '玉米小斑病 百菌清 代森锰锌 农药'
  },
  {
    name: '玉米锈病',
    icon: '🌾',
    effect: '叶片黄褐色锈粉',
    keyword: '玉米锈病 三唑酮 戊唑醇 三唑类杀菌剂'
  },
  {
    name: '玉米茎腐病',
    icon: '🌱',
    effect: '茎基腐烂倒伏',
    keyword: '玉米茎腐病 恶霉灵 噻呋酰胺 灌根药剂'
  },
  {
    name: '玉米纹枯病',
    icon: '🌿',
    effect: '茎秆云纹状病斑',
    keyword: '玉米纹枯病 井冈霉素 噻呋酰胺 农药'
  },
  {
    name: '玉米黑粉病',
    icon: '🖤',
    effect: '瘤状黑粉孢子',
    keyword: '玉米黑粉病 三唑酮 福美双 拌种杀菌剂'
  },
  {
    name: '玉米蚜虫',
    icon: '🐛',
    effect: '吸汁叶片卷曲',
    keyword: '玉米蚜虫 吡虫啉 噻虫嗪 杀虫剂'
  },
  {
    name: '玉米螟虫',
    icon: '🐞',
    effect: '钻心蛀茎危害',
    keyword: '玉米螟 氯虫苯甲酰胺 甲维盐 杀虫剂'
  }
])

// 常用农资
const toolList = ref([
  {
    icon: '🌱',
    name: '玉米专用复合肥',
    desc: '缓释高产型氮磷钾肥料',
    keyword: '玉米专用复合肥 缓释肥 高产'
  },
  {
    icon: '💧',
    name: '叶面肥 芸苔素',
    desc: '增产抗逆 调节生长',
    keyword: '玉米叶面肥 芸苔素内酯 增产'
  },
  {
    icon: '🌾',
    name: '玉米除草剂',
    desc: '苗后安全型 禾阔双除',
    keyword: '玉米苗后除草剂 烟嘧磺隆 莠去津'
  },
  {
    icon: '🧪',
    name: '拌种剂 种衣剂',
    desc: '防虫防病 出苗整齐',
    keyword: '玉米拌种剂 噻虫嗪 咯菌腈 种衣剂'
  }
])

// 关键词优化：自动补充农资相关关键词
const enrichKeyword = (originalKey) => {
  if (!originalKey || !originalKey.trim()) return originalKey
  
  const key = originalKey.trim()
  const agriculturalTerms = ['农药', '肥料', '除草剂', '拌种剂', '种衣剂', '叶面肥', '杀菌剂', '杀虫剂']
  const hasAgriTerm = agriculturalTerms.some(term => key.includes(term))
  
  if (hasAgriTerm) {
    return `${key} 农资 正品保障`
  }
  
  if (key.includes('病') || key.includes('虫')) {
    return `${key} 防治 特效药 农资`
  }
  
  return key
}

// 处理搜索
const handleSearch = () => {
  if (!keyword.value.trim()) {
    uni.showToast({ title: '请输入搜索内容', icon: 'none' })
    return
  }
  goToJD(keyword.value)
}

// 跳转京东农资专区
const goToJDAgricultural = () => {
  goToJD('农资 正品保障 京东农资')
}

// 核心跳转方法 - 手机端京东适配
const goToJD = (searchKey) => {
  if (!searchKey || !searchKey.trim()) {
    uni.showToast({ title: '请输入搜索内容', icon: 'none' })
    return
  }

  const enhancedKey = enrichKeyword(searchKey)
  // 京东搜索URL（移动端优先）
  const searchUrl = `https://search.jd.com/Search?keyword=${encodeURIComponent(enhancedKey)}&enc=utf-8`
  
  // 京东APP URL Scheme（通用）
  const jdScheme = `openapp.jdmobile://virtual?params=${encodeURIComponent(JSON.stringify({
    category: 'jump',
    des: 'searchList',
    keyWord: enhancedKey
  }))}`

  // #ifdef APP-PLUS
  // App端：优先唤起京东APP
  plus.runtime.openURL(jdScheme, (err) => {
    console.log('京东APP唤起失败，打开浏览器:', err)
    plus.runtime.openURL(searchUrl)
  })
  // #endif

  // #ifdef H5
  // H5端：手机浏览器适配
  const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)
  
  if (isMobile) {
    // 手机端尝试唤起京东APP
    const startTime = Date.now()
    window.location.href = jdScheme
    
    // 2秒内未唤起成功则跳转H5
    setTimeout(() => {
      if (Date.now() - startTime < 2500) {
        window.open(searchUrl, '_blank')
      }
    }, 2000)
  } else {
    // PC端直接打开网页
    window.open(searchUrl, '_blank')
  }
  // #endif

  // #ifdef MP-WEIXIN
  // 微信小程序：复制链接并引导
  uni.setClipboardData({
    data: searchUrl,
    success: () => {
      uni.showModal({
        title: '购药指引',
        content: '链接已复制！\n\n📱 推荐操作：\n1. 打开京东APP自动识别\n2. 或粘贴到浏览器打开\n\n已为您推荐农资专区商品',
        showCancel: false,
        confirmText: '我知道了'
      })
    }
  })
  // #endif
}
</script>

<style scoped>
.mall-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 40rpx;
  box-sizing: border-box;
}

/* 搜索栏 - 优化视觉层次 */
.search-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 20rpx 30rpx;
  background: linear-gradient(135deg, #7c3aed, #9d65f0);
  display: flex;
  gap: 20rpx;
  align-items: center;
  box-shadow: 0 4rpx 20rpx rgba(124, 58, 237, 0.25);
}
.search-input {
  flex: 1;
  height: 72rpx;
  padding: 0 28rpx;
  background: #ffffff;
  border-radius: 36rpx;
  font-size: 28rpx;
  border: none;
  outline: none;
  color: #1f1f2e;
}
.search-input::placeholder {
  color: #aaa;
}
.search-btn {
  padding: 0 32rpx;
  height: 72rpx;
  line-height: 72rpx;
  background: #ffffff;
  color: #7c3aed;
  font-weight: 600;
  border-radius: 36rpx;
  font-size: 28rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
  transition: all 0.2s;
  cursor: pointer;
}
.search-btn:active {
  transform: scale(0.94);
  background: #f5f0ff;
}

/* 京东农资专区快捷入口 - 增强视觉 */
.jd-channel-tip {
  margin: 24rpx 24rpx 16rpx;
  padding: 24rpx 28rpx;
  background: linear-gradient(135deg, #fff7ed, #fff1f2);
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
  border: 2rpx solid rgba(245, 158, 11, 0.2);
  box-shadow: 0 4rpx 16rpx rgba(245, 158, 11, 0.08);
  cursor: pointer;
  transition: all 0.2s;
}
.jd-channel-tip:active {
  transform: scale(0.97);
  background: #fef3e8;
}
.tip-icon {
  font-size: 36rpx;
}
.tip-text {
  flex: 1;
  font-size: 28rpx;
  color: #b45309;
  font-weight: 500;
}
.tip-arrow {
  font-size: 32rpx;
  color: #f59e0b;
}

/* 通用区块 */
.section {
  margin: 30rpx 24rpx 0;
}
.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1e1e2a;
  margin-bottom: 20rpx;
  padding-left: 12rpx;
  border-left: 8rpx solid #7c3aed;
}

/* 药品网格 - 优化卡片 */
.drug-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}
.drug-card {
  background: #ffffff;
  border-radius: 20rpx;
  padding: 28rpx 20rpx 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
  cursor: pointer;
  border: 2rpx solid transparent;
}
.drug-card:active {
  transform: scale(0.96);
  box-shadow: 0 8rpx 24rpx rgba(124, 58, 237, 0.12);
  border-color: #d5c3ff;
}
.drug-icon {
  font-size: 64rpx;
  margin-bottom: 8rpx;
}
.drug-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #1f1f2e;
  margin-bottom: 6rpx;
}
.drug-effect {
  font-size: 24rpx;
  color: #888;
  margin-bottom: 14rpx;
  line-height: 1.4;
  flex: 1;
}
.go-buy {
  font-size: 24rpx;
  color: #f59e0b;
  font-weight: 500;
  border-top: 2rpx dashed #f0e6d0;
  padding-top: 14rpx;
  margin-top: 4rpx;
}

/* 农资列表 - 优化样式 */
.tool-list {
  background: #ffffff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}
.tool-item {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 28rpx 24rpx;
  border-bottom: 2rpx solid #f1f3f8;
  cursor: pointer;
  transition: background 0.15s;
}
.tool-item:last-child {
  border-bottom: none;
}
.tool-item:active {
  background: #f8f6ff;
}
.tool-icon {
  width: 88rpx;
  height: 88rpx;
  line-height: 88rpx;
  text-align: center;
  font-size: 44rpx;
  background: #f3efff;
  border-radius: 18rpx;
  flex-shrink: 0;
}
.tool-info {
  flex: 1;
}
.tool-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #1f1f2e;
  margin-bottom: 4rpx;
}
.tool-desc {
  font-size: 24rpx;
  color: #8e8ea0;
}
.tool-arrow {
  font-size: 32rpx;
  color: #c0c0d0;
}

/* 底部提示 */
.footer-tip {
  margin-top: 40rpx;
  text-align: center;
  font-size: 24rpx;
  color: #c0c0cc;
}

/* 移动端触屏优化 */
@media (max-width: 768px) {
  .mall-page {
    -webkit-overflow-scrolling: touch;
  }
  
  .search-bar {
    position: sticky;
    top: 0;
    z-index: 1000;
  }
  
  .drug-card,
  .tool-item,
  .jd-channel-tip {
    cursor: pointer;
    -webkit-tap-highlight-color: rgba(124, 58, 237, 0.08);
    user-select: none;
    -webkit-user-select: none;
  }
}

/* 横屏适配 */
@media (orientation: landscape) {
  .drug-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* 刘海屏适配 */
@supports (padding: max(0px)) {
  .search-bar {
    padding-left: max(30rpx, env(safe-area-inset-left));
    padding-right: max(30rpx, env(safe-area-inset-right));
  }
}

/* 过渡动画 */
.go-buy,
.tool-arrow {
  transition: all 0.3s ease;
}

.go-buy:active {
  color: #7c3aed;
}
</style>