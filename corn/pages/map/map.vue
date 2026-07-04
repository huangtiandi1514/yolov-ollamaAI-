<template>
  <view class="map-page">
    <map
      id="hospitalMap"
      class="map"
      :latitude="currentLat"
      :longitude="currentLng"
      :scale="mapScale"
      :markers="markers"
      :polyline="polyline"
      :show-location="false"
      :enable-traffic="false"
      :enable-building="false"
      :enable-rotate="false"
      :enable-overlooking="false"
      :enable-satellite="false"
      :show-compass="false"
      :skeleton="true"
      @markertap="onMarkerTap"
      @regionchange="onMapRegionChange"
    />

    <!-- 顶部标题栏 -->
    <view class="top-bar">
      <view class="top-bar-left">
        <text class="back-btn" @click="goBack">‹</text>
        <text class="title">附近植物医院</text>
      </view>
      <view class="top-bar-right">
        <text class="refresh-btn" @click="refreshLocation">⟳</text>
      </view>
    </view>

    <!-- ========== 顶部医院卡片列表 ========== -->
    <scroll-view
      v-if="hospitalList.length && !isNavigating"
      scroll-x
      class="hospital-scroll-top"
      :show-scrollbar="false"
    >
      <view
        v-for="(item,index) in hospitalList"
        :key="index"
        class="hospital-card"
        :class="{active:index===activeIndex}"
        @click="selectHospital(item,index)"
      >
        <!-- 排名标签 -->
        <view class="card-rank" :class="getRankClass(index)">
          <text class="rank-number">{{index + 1}}</text>
        </view>
        
        <view class="card-content">
          <view class="card-header">
            <view class="hospital-name-wrapper">
              <text class="hospital-name">{{item.name}}</text>
              <view class="hospital-tag" v-if="index === 0">推荐</view>
              <view class="hospital-tag distance-tag" v-if="item.distance && item.distance < 500">最近</view>
            </view>
            <view class="hospital-distance">
              <text class="distance-icon">📍</text>
              <text class="distance-text">{{formatDistance(item.distance)}}</text>
            </view>
          </view>
          
          <view class="card-body">
            <view class="hospital-address-wrapper">
              <text class="address-icon">🏠</text>
              <text class="hospital-address">{{item.address}}</text>
            </view>
            <button class="nav-mini-btn" @click.stop="startNavigate(item)">导航</button>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 导航顶部提示 -->
    <view class="nav-top-tip" v-if="isNavigating && routeInfo">
      <view class="nav-tip-content">
        <text class="nav-tip-icon">🚗</text>
        <text class="nav-tip-text">前往 {{routeInfo.end_name}}</text>
      </view>
      <view class="nav-tip-right">
        <text class="nav-tip-distance">{{routeInfo.distance}}</text>
        <button class="exit-nav-btn" @click="exitNavigate">退出</button>
      </view>
    </view>

    <!-- 导航步骤提示 -->
    <view class="step-tip" v-if="isNavigating && currentNavStep">
      <view class="step-tip-content">
        <text class="step-icon">➡️</text>
        <view class="step-desc">
          <view class="step-instruct">{{currentNavStep.instruction}}</view>
          <view class="step-dis">剩余 {{formatDistance(currentNavStep.distance)}}</view>
        </view>
      </view>
    </view>

    <!-- AI导航按钮 -->
    <view class="ai-btn" @click="showPanel=true" v-if="!showPanel && !isNavigating">
      <text class="ai-btn-icon">🤖</text>
      <text class="ai-btn-text">AI导航</text>
    </view>

    <!-- 遮罩 -->
    <view class="mask" v-if="showPanel && !isNavigating" @click="showPanel=false"></view>

    <!-- 导航面板 -->
    <view class="nav-panel" v-if="showPanel && !isNavigating">
      <view class="panel-header">
        <text class="panel-title">AI智能导航</text>
        <text class="close-btn" @click="showPanel=false">✕</text>
      </view>

      <view class="input-box">
        <input
          v-model="destination"
          class="input"
          placeholder="请输入目的地"
          confirm-type="search"
          @confirm="sendNavigate"
        />
        <button class="send-btn" @click="sendNavigate" :loading="loadingNav">导航</button>
      </view>

      <view class="way-list">
        <view class="way-item" :class="{active:navWay==='driving'}" @click="navWay='driving'">
          <text class="way-icon">🚗</text>
          <text>驾车</text>
        </view>
        <view class="way-item" :class="{active:navWay==='walking'}" @click="navWay='walking'">
          <text class="way-icon">🚶</text>
          <text>步行</text>
        </view>
        <view class="way-item" :class="{active:navWay==='riding'}" @click="navWay='riding'">
          <text class="way-icon">🚴</text>
          <text>骑行</text>
        </view>
      </view>

      <scroll-view scroll-y class="route-box" v-if="routeInfo">
        <view class="summary">
          <view class="summary-item">
            <text class="summary-label">全程</text>
            <text class="summary-value">{{routeInfo.distance}}</text>
          </view>
          <view class="summary-item">
            <text class="summary-label">预计</text>
            <text class="summary-value">{{routeInfo.duration}}</text>
          </view>
        </view>
        <view class="step" v-for="(step,index) in routeInfo.steps" :key="index">
          <view class="step-index">{{index+1}}</view>
          <view class="step-content">
            <view class="step-text">{{step.instruction}}</view>
            <view class="step-distance">{{formatDistance(step.distance)}}</view>
          </view>
        </view>
        <view class="native-box">
          <button class="native-btn amap" @click="openNativeMap('amap')">
            <text class="native-icon">🗺️</text>
            高德导航
          </button>
          <button class="native-btn bmap" @click="openNativeMap('bmap')">
            <text class="native-icon">🗺️</text>
            百度导航
          </button>
        </view>
      </scroll-view>
    </view>

    <!-- 加载遮罩 -->
    <view class="loading-mask" v-if="loading">
      <view class="loading-box">
        <view class="loading-spinner"></view>
        <text class="loading-text">正在加载附近植物医院...</text>
      </view>
    </view>

    <!-- 空状态 -->
    <view class="empty" v-if="!loading && hospitalList.length===0">
      <text class="empty-icon">🏥</text>
      <text class="empty-text">暂未找到附近植物医院</text>
      <button class="empty-btn" @click="refreshLocation">重新加载</button>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { getNearbyHospital } from '@/utils/api.js'

// ====================== 图标路径配置 ======================
const MARKER_ICON = {
  user: '/static/marker.png',
  hospital: '/static/marker.png',
  dest: '/static/marker.png'
}
// =========================================================

// 接口配置
const NAV_API = 'http://192.168.6.127:5000/api/ai/navigate'
const TTS_API = 'http://192.168.6.127:5000/api/text-to-speech'

// 核心状态
const currentLat = ref(23.2056)
const currentLng = ref(113.2781)
const mapScale = ref(15)
const markers = ref([])
const polyline = ref([])
const hospitalList = ref([])
const loading = ref(true)
const activeIndex = ref(-1)
const showPanel = ref(false)
const destination = ref('')
const loadingNav = ref(false)
const navWay = ref('driving')
const routeInfo = ref(null)
const isNavigating = ref(false)
const currentStepIdx = ref(0)

let mapContext = null
let audioCtx = null
let isSearching = false
let lastSearchPos = { lat: 0, lng: 0 }
const SEARCH_THRESHOLD = 500

// ====================== 用户定位标记 ======================
const userMarker = {
  id: 0,
  latitude: 23.2056,
  longitude: 113.2781,
  iconPath: MARKER_ICON.user,
  width: 44,
  height: 44,
  anchor: { x: 0.5, y: 1 },
  callout: { content: '我的位置', color: '#7c3aed', fontSize: 12, borderRadius: 6, bgColor: '#fff', padding: 6, display: 'ALWAYS' }
}
let poiMarkers = []

// ========== 工具函数 ==========
const throttle = (fn, delay = 1000) => {
  let last = 0
  return (...args) => {
    const now = Date.now()
    if (now - last >= delay) {
      last = now
      fn(...args)
    }
  }
}

const calcDistance = (lat1, lng1, lat2, lng2) => {
  const rad = d => d * Math.PI / 180
  const a = rad(lat1) - rad(lat2)
  const b = rad(lng1) - rad(lng2)
  const s = 2 * Math.asin(Math.sqrt(Math.sin(a/2)**2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(b/2)**2))
  return Math.round(s * 6378137)
}

const formatDistance = num => !num && num !== 0 ? '未知' : num < 1000 ? `${num}米` : `${(num/1000).toFixed(1)}公里`

const currentNavStep = computed(() => routeInfo.value?.steps?.[currentStepIdx.value] || null)

// ========== 排名样式 ==========
const getRankClass = (index) => {
  if (index === 0) return 'rank-gold'
  if (index === 1) return 'rank-silver'
  if (index === 2) return 'rank-bronze'
  return 'rank-default'
}

let locationHandler = throttle(onLocationChange, 1000)

// ========== 生命周期 ==========
onMounted(() => {
  const systemInfo = uni.getSystemInfoSync()
  document.documentElement.style.setProperty('--status-bar-height', systemInfo.statusBarHeight + 'px')
  
  mapContext = uni.createMapContext('hospitalMap')
  markers.value = [userMarker]
  audioCtx = uni.createInnerAudioContext()
  initLocation()
})

onUnmounted(() => {
  uni.offLocationChange(locationHandler)
  uni.stopLocationUpdate()
  audioCtx?.destroy()
})

watch(isNavigating, isNav => {
  if (isNav) {
    locationHandler = throttle(onLocationChange, 2000)
    poiMarkers = []
    markers.value = [{ ...userMarker, latitude: currentLat.value, longitude: currentLng.value }]
    mapScale.value = 17
  } else {
    locationHandler = throttle(onLocationChange, 1000)
    polyline.value = []
    routeInfo.value = destination.value = ''
    mapScale.value = 15
    getHospitalList()
  }
})

// ========== 定位与站点 ==========
const initLocation = () => {
  uni.getLocation({
    type: 'gcj02',
    success: res => {
      updateUserPos(res.latitude, res.longitude)
      getHospitalList()
    },
    fail: getHospitalList
  })
  uni.startLocationUpdate({
    success: () => uni.onLocationChange(locationHandler),
    fail: () => uni.showToast({ title: '定位未开启，使用默认坐标', icon: 'none' })
  })
}

function onLocationChange(res) {
  const { latitude, longitude } = res
  updateUserPos(latitude, longitude)
  if (!isNavigating.value) {
    const dis = calcDistance(lastSearchPos.lat, lastSearchPos.lng, latitude, longitude)
    if (dis >= SEARCH_THRESHOLD && !isSearching) getHospitalList()
  } else {
    checkNavStep(latitude, longitude)
  }
}

const updateUserPos = (lat, lng) => {
  currentLat.value = lat
  currentLng.value = lng
  userMarker.latitude = lat
  userMarker.longitude = lng
  markers.value = isNavigating.value ? [userMarker] : [userMarker, ...poiMarkers]
  if (isNavigating.value) mapContext.moveToLocation({ latitude: lat, longitude: lng, animation: false })
}

const refreshLocation = () => {
  uni.showLoading({ title: '定位中...' })
  uni.getLocation({
    type: 'gcj02',
    success: res => {
      updateUserPos(res.latitude, res.longitude)
      getHospitalList()
      uni.hideLoading()
      uni.showToast({ title: '定位成功', icon: 'success' })
    },
    fail: () => {
      uni.hideLoading()
      uni.showToast({ title: '定位失败', icon: 'none' })
    }
  })
}

const goBack = () => {
  uni.navigateBack()
}

const getHospitalList = async () => {
  if (isSearching) return
  isSearching = true
  lastSearchPos = { lat: currentLat.value, lng: currentLng.value }
  try {
    const res = await getNearbyHospital(currentLng.value, currentLat.value)
    if (Array.isArray(res.list)) {
      hospitalList.value = res.list
      poiMarkers = res.list.map((item, idx) => ({
        id: idx + 1,
        latitude: item.latitude,
        longitude: item.longitude,
        iconPath: MARKER_ICON.hospital,
        width: 40,
        height: 40,
        anchor: { x: 0.5, y: 1 },
        callout: { content: item.name, display: 'BYCLICK', fontSize: 12 }
      }))
      markers.value = [userMarker, ...poiMarkers]
    }
  } catch {
    uni.showToast({ title: '站点加载失败', icon: 'none' })
  } finally {
    loading.value = false
    isSearching = false
  }
}

// ========== 交互逻辑 ==========
const onMarkerTap = e => {
  const mid = e.detail.markerId
  if (mid === 0) return
  const idx = mid - 1
  activeIndex.value = idx
  const item = hospitalList.value[idx]
  uni.showActionSheet({
    itemList: ['查看详情', '导航前往'],
    success: tap => tap.tapIndex === 0
      ? uni.showModal({ title: item.name, content: `地址：${item.address}\n距离：${formatDistance(item.distance)}`, showCancel: false })
      : startNavigate(item)
  })
}

const selectHospital = (item, index) => {
  activeIndex.value = index
  mapContext.moveToLocation({ latitude: item.latitude, longitude: item.longitude })
}

const startNavigate = item => {
  destination.value = item.name
  showPanel.value = false
  sendNavigate(() => enterNavMode())
}

// ========== 导航核心 ==========
const sendNavigate = async (callback) => {
  const target = destination.value.trim()
  if (!target) return uni.showToast({ title: '请输入目的地', icon: 'none' })
  if (loadingNav.value) return
  loadingNav.value = true
  try {
    const res = await uni.request({
      url: NAV_API,
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      data: { start_lng: currentLng.value, start_lat: currentLat.value, end_name: target, way: navWay.value }
    })
    if (res.data.code === 200) {
      const data = res.data.data
      routeInfo.value = data
      const points = data.route.map(p => ({ longitude: p[0], latitude: p[1] }))
      polyline.value = [{ points, color: '#7c3aed', width: 8, borderWidth: 2, arrowLine: true }]

      const destMarker = {
        id: 9999,
        latitude: data.end_lat,
        longitude: data.end_lng,
        iconPath: MARKER_ICON.dest,
        width: 48,
        height: 48,
        anchor: { x: 0.5, y: 1 },
        callout: { content: data.end_name, display: 'ALWAYS', fontSize: 13, bgColor: '#7c3aed', color: '#fff', padding: 8, borderRadius: 8 }
      }
      markers.value = [
        { ...userMarker, latitude: currentLat.value, longitude: currentLng.value },
        destMarker
      ]

      setTimeout(() => mapContext.includePoints({ points, padding: [120, 40, 240, 40], animation: true }), 300)
      callback?.()
    } else {
      uni.showToast({ title: res.data.msg || '路线规划失败', icon: 'none' })
    }
  } catch {
    uni.showToast({ title: '连接导航服务失败', icon: 'none' })
  } finally {
    loadingNav.value = false
  }
}

const enterNavMode = () => {
  isNavigating.value = true
  currentStepIdx.value = 0
  speakTTS(currentNavStep.value.instruction)
}

const exitNavigate = () => {
  isNavigating.value = false
  currentStepIdx.value = 0
  uni.showToast({ title: '已退出导航', icon: 'none' })
}

const checkNavStep = (lat, lng) => {
  if (!routeInfo.value?.steps || currentStepIdx.value >= routeInfo.value.steps.length - 1) return
  const idx = Math.min(currentStepIdx.value + 1, routeInfo.value.route.length - 1)
  const [pLng, pLat] = routeInfo.value.route[idx]
  if (calcDistance(lat, lng, pLat, pLng) < 50) {
    currentStepIdx.value++
    speakTTS(currentNavStep.value.instruction)
  }
}

const speakTTS = async text => {
  try {
    const res = await uni.request({ url: TTS_API, method: 'POST', header: { 'Content-Type': 'application/json' }, data: { text } })
    if (res.data.code === 200 && audioCtx) {
      audioCtx.stop()
      audioCtx.src = `http://192.168.6.127:5000${res.data.data.url}`
      audioCtx.play()
    }
  } catch (e) {
    console.log('语音播报失败', e)
  }
}

const openNativeMap = type => {
  if (!routeInfo.value) return
  const { end_lat, end_lng, end_name } = routeInfo.value
  if (type === 'amap') {
    uni.openLocation({
      latitude: Number(end_lat),
      longitude: Number(end_lng),
      name: end_name,
      scale: 18,
      fail: () => uni.showToast({ title: '未安装高德地图', icon: 'none' })
    })
  } else {
    plus.runtime.openURL(
      `baidumap://map/direction?destination=latlng:${end_lat},${end_lng}|name:${encodeURIComponent(end_name)}&mode=${navWay}`,
      () => uni.showToast({ title: '未安装百度地图', icon: 'none' })
    )
  }
}

const onMapRegionChange = () => isNavigating.value && (void 0)
</script>

<style scoped>
/* ========== CSS变量 ========== */
:root {
  --status-bar-height: 44px;
  --safe-bottom: env(safe-area-inset-bottom, 20px);
}

/* ========== 页面容器 ========== */
.map-page {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: #f5f5f5;
}

.map {
  width: 100%;
  height: 100%;
  position: absolute;
  left: 0;
  top: 0;
  z-index: 0;
}

/* ========== 顶部标题栏 ========== */
.top-bar {
  position: absolute;
  top: calc(var(--status-bar-height) + 12px);
  left: 16px;
  right: 16px;
  height: 48px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 99;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  font-size: 32px;
  font-weight: 300;
  color: #333;
  line-height: 1;
  padding: 0 4px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.top-bar-right {
  display: flex;
  align-items: center;
}

.refresh-btn {
  font-size: 22px;
  color: #666;
  padding: 4px 8px;
}

/* ========== 顶部医院卡片列表 ========== */
.hospital-scroll-top {
  position: absolute;
  top: calc(var(--status-bar-height) + 72px);
  left: 0;
  width: 100%;
  padding: 0 16px;
  z-index: 99;
  height: 145px;
  white-space: nowrap;
}

.hospital-card {
  display: inline-block;
  width: 320px;
  padding: 14px 16px;
  margin-right: 12px;
  background: #ffffff;
  border-radius: 14px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  vertical-align: top;
  border: 2px solid transparent;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 100%;
  position: relative;
  overflow: hidden;
}

.hospital-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #7c3aed, #9d65f0);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.hospital-card.active {
  border-color: #7c3aed;
  box-shadow: 0 8px 32px rgba(124, 58, 237, 0.2);
  transform: translateY(2px);
}

.hospital-card.active::before {
  opacity: 1;
}

/* 排名标签 - 顶部卡片使用小尺寸 */
.card-rank {
  position: absolute;
  top: 8px;
  right: 10px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: #fff;
}

.rank-gold {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.4);
}

.rank-silver {
  background: linear-gradient(135deg, #9ca3af, #d1d5db);
  box-shadow: 0 2px 8px rgba(156, 163, 175, 0.4);
}

.rank-bronze {
  background: linear-gradient(135deg, #d97706, #f59e0b);
  box-shadow: 0 2px 8px rgba(217, 119, 6, 0.4);
}

.rank-default {
  background: #e5e7eb;
  color: #6b7280;
}

.rank-number {
  font-size: 10px;
  font-weight: 700;
}

/* 卡片内容 - 顶部卡片紧凑布局 */
.card-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding-right: 28px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
  gap: 8px;
}

.hospital-name-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.hospital-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hospital-tag {
  flex-shrink: 0;
  padding: 0px 8px;
  border-radius: 8px;
  font-size: 9px;
  font-weight: 600;
  background: linear-gradient(135deg, #7c3aed, #9d65f0);
  color: #fff;
  line-height: 16px;
}

.hospital-tag.distance-tag {
  background: linear-gradient(135deg, #10b981, #34d399);
}

.hospital-distance {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.distance-icon {
  font-size: 12px;
}

.distance-text {
  font-size: 13px;
  font-weight: 600;
  color: #7c3aed;
}

.card-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.hospital-address-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.address-icon {
  font-size: 11px;
  flex-shrink: 0;
}

.hospital-address {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-mini-btn {
  flex-shrink: 0;
  padding: 2px 14px;
  height: 24px;
  line-height: 24px;
  background: linear-gradient(135deg, #7c3aed, #9d65f0);
  color: #fff;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  border: none;
  transition: all 0.2s ease;
}

.nav-mini-btn:active {
  transform: scale(0.92);
}

/* ========== 导航顶部提示 ========== */
.nav-top-tip {
  position: absolute;
  top: calc(var(--status-bar-height) + 12px);
  left: 16px;
  right: 16px;
  height: 56px;
  background: rgba(124, 58, 237, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(124, 58, 237, 0.3);
}

.nav-tip-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  overflow: hidden;
}

.nav-tip-icon {
  font-size: 20px;
}

.nav-tip-text {
  font-size: 15px;
  color: #fff;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-tip-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.nav-tip-distance {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

.exit-nav-btn {
  padding: 4px 14px;
  height: 28px;
  line-height: 28px;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border-radius: 14px;
  font-size: 12px;
  border: none;
}

/* ========== 导航步骤提示 ========== */
.step-tip {
  position: absolute;
  bottom: 210px;
  left: 50%;
  transform: translateX(-50%);
  max-width: 90%;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 14px 20px;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12);
  z-index: 99;
}

.step-tip-content {
  display: flex;
  align-items: center;
  gap: 14px;
}

.step-icon {
  font-size: 22px;
}

.step-desc {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.step-instruct {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
}

.step-dis {
  font-size: 13px;
  color: #7c3aed;
}

/* ========== AI导航按钮 ========== */
.ai-btn {
  position: absolute;
  right: 20px;
  bottom: 220px;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #7c3aed, #9d65f0);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 24px rgba(124, 58, 237, 0.4);
  z-index: 98;
  transition: transform 0.2s ease;
}

.ai-btn:active {
  transform: scale(0.92);
}

.ai-btn-icon {
  font-size: 22px;
  line-height: 1;
}

.ai-btn-text {
  font-size: 11px;
  margin-top: 2px;
}

/* ========== 遮罩 ========== */
.mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 101;
  animation: fadeIn 0.3s ease;
}

/* ========== 导航面板 ========== */
.nav-panel {
  position: fixed;
  left: 0;
  bottom: 0;
  width: 100%;
  max-height: 70vh;
  background: #ffffff;
  border-radius: 24px 24px 0 0;
  z-index: 102;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.35s cubic-bezier(0.32, 0.72, 0, 1);
  padding-bottom: var(--safe-bottom);
}

.panel-header {
  padding: 20px 20px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f0f0f0;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.close-btn {
  font-size: 22px;
  color: #999;
  padding: 4px 8px;
}

.input-box {
  padding: 16px 20px;
  display: flex;
  gap: 12px;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
}

.input {
  flex: 1;
  height: 44px;
  padding: 0 16px;
  background: #f5f5f5;
  border-radius: 22px;
  font-size: 15px;
  border: none;
  outline: none;
}

.send-btn {
  flex-shrink: 0;
  height: 44px;
  padding: 0 24px;
  background: linear-gradient(135deg, #7c3aed, #9d65f0);
  color: #fff;
  border-radius: 22px;
  font-size: 15px;
  font-weight: 500;
  border: none;
}

.way-list {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.way-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 0;
  border-radius: 22px;
  font-size: 14px;
  background: #f5f5f5;
  color: #666;
  transition: all 0.2s ease;
}

.way-item.active {
  background: linear-gradient(135deg, #7c3aed, #9d65f0);
  color: #fff;
  box-shadow: 0 2px 12px rgba(124, 58, 237, 0.3);
}

.way-icon {
  font-size: 18px;
}

.route-box {
  flex: 1;
  padding: 0 20px 20px;
  max-height: 300px;
}

.summary {
  display: flex;
  gap: 32px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-label {
  font-size: 12px;
  color: #999;
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
  color: #7c3aed;
}

.step {
  display: flex;
  gap: 14px;
  padding: 14px 0;
  border-bottom: 1px solid #f8f8f8;
}

.step-index {
  width: 28px;
  height: 28px;
  line-height: 28px;
  text-align: center;
  background: #7c3aed;
  color: #fff;
  border-radius: 50%;
  font-size: 13px;
  flex-shrink: 0;
  margin-top: 2px;
}

.step-content {
  flex: 1;
}

.step-text {
  font-size: 14px;
  color: #333;
  line-height: 1.5;
}

.step-distance {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.native-box {
  display: flex;
  gap: 12px;
  padding: 16px 0 8px;
}

.native-btn {
  flex: 1;
  height: 44px;
  border-radius: 22px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.native-btn.amap {
  background: linear-gradient(135deg, #1890ff, #40a9ff);
}

.native-btn.bmap {
  background: linear-gradient(135deg, #29b6f6, #4fc3f7);
}

.native-icon {
  font-size: 16px;
}

/* ========== 加载状态 ========== */
.loading-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e8e8e8;
  border-top-color: #7c3aed;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-text {
  font-size: 15px;
  color: #666;
}

/* ========== 空状态 ========== */
.empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 9;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  font-size: 48px;
}

.empty-text {
  font-size: 16px;
  color: #999;
}

.empty-btn {
  padding: 8px 24px;
  background: #7c3aed;
  color: #fff;
  border-radius: 20px;
  font-size: 14px;
  border: none;
}

/* ========== 动画 ========== */
@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

/* ========== iPhone 刘海屏适配 ========== */
@supports (padding: max(0px)) {
  .nav-panel {
    padding-bottom: max(20px, env(safe-area-inset-bottom));
  }
}

/* ========== 小屏手机适配 ========== */
@media screen and (max-width: 375px) {
  .hospital-scroll-top {
    height: 130px;
    padding: 0 12px;
  }
  
  .hospital-card {
    width: 270px;
    padding: 12px 14px;
  }
  
  .top-bar {
    height: 44px;
    left: 12px;
    right: 12px;
  }
  
  .title {
    font-size: 16px;
  }
  
  .hospital-name {
    font-size: 14px;
  }
  
  .step-tip {
    bottom: 190px;
    padding: 12px 16px;
  }
}

/* ========== 大屏手机适配 ========== */
@media screen and (min-width: 414px) {
  .hospital-scroll-top {
    padding: 0 20px;
  }
  
  .hospital-card {
    width: 360px;
  }
  
  .top-bar {
    left: 20px;
    right: 20px;
  }
}
</style>