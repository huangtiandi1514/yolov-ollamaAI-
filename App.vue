<script>
export default {
  onLaunch() {},
  globalData: {
    pageActive: "index" // 当前激活导航页面
  }
}
</script>

<style>
page {
  background: linear-gradient(120deg, #f0f4ff, #f9f6ff);
  font-size: 14px;
}
/* 卡片通用 */
.panel-box {
  background: #fff;
  border-radius: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(120,80,220,0.08);
  padding: 32rpx;
  margin-bottom: 24rpx;
}
/* 按钮配色 */
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
/* 分割线 */
.divider {
  height: 2rpx;
  background: linear-gradient(90deg, transparent,#ddd6fe,transparent);
  margin: 40rpx 0;
}
</style>