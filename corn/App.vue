<script>
export default {
  globalData: {
    pageActive: "index",
    bgm: null,
    musicPlaying: true
  },
  onLaunch() {
    console.log("玉米病害检测系统启动")
    const bgm = uni.createInnerAudioContext()
    // 根路径斜杠修复加载失败
    bgm.src = "/static/music/butterfly.mp3"
	
    bgm.loop = true
    bgm.volume = 0.5

    bgm.onError((err) => {
      console.error("背景音乐完整错误信息：", err)
      uni.showToast({ title: "背景音乐加载失败", icon: "none" })
    })

    this.globalData.bgm = bgm
  },
  onHide() {
    const bgm = this.globalData.bgm
    if (bgm) bgm.pause()
  },
  onShow() {
    const { bgm, musicPlaying } = this.globalData
    if (bgm && musicPlaying) bgm.play()
  },
  onUnload() {
    const bgm = this.globalData.bgm
    if (bgm) {
      bgm.stop()
      bgm.destroy()
      this.globalData.bgm = null
    }
  }
}
</script>

<style>
page {
  background: linear-gradient(120deg, #f0f4ff, #f9f6ff);
  font-size: 14px;
}
.panel-box {
  background: #fff;
  border-radius: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(120,80,220,0.08);
  padding: 32rpx;
  margin-bottom: 24rpx;
}
.btn-primary {
  background: linear-gradient(135deg,#7c3aed,#8b5cf6);
  color: #fff;
  border-radius: 12rpx;
}
.btn-voice {
  background: #3b82f6;
  color: #fff;
  border-radius: 12rpx;
}
.btn-read {
  background: #ec4899;
  color: #fff;
  border-radius: 12rpx;
}
.music-btn {
  background: linear-gradient(135deg,#10b981,#34d399);
  color: white;
  border-radius: 12rpx;
  padding: 16rpx 32rpx;
  font-size: 28rpx;
}
.divider {
  height: 2rpx;
  background: linear-gradient(90deg, transparent,#ddd6fe,transparent);
  margin: 40rpx 0;
}
</style>