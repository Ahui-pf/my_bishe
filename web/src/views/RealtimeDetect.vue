<template>
  <div class="page-stack">
    <section class="realtime-hero glass-panel">
      <div class="hero-copy">
        <p class="eyebrow">Realtime Workspace</p>
        <h1 class="section-title">实时检测控制台</h1>
        <p class="section-copy">
          这一页适合展示系统的实时交互能力。打开摄像头后，前端会直接叠加检测框，并同步显示连接状态、帧率和检测日志。
        </p>
        <div class="chip-row">
          <span class="soft-chip">当前连接：{{ connectionStatusText }}</span>
          <span class="soft-chip">目标帧率：{{ targetFPS }} FPS</span>
          <span class="soft-chip">已处理帧数：{{ stats.totalFrames }}</span>
        </div>
      </div>

      <div class="status-card">
        <span>实时状态</span>
        <strong>{{ isDetecting ? '检测中' : '待启动' }}</strong>
        <p>{{ isDetecting ? '摄像头画面与检测结果正在同步刷新。' : '点击开始检测后将尝试连接摄像头和 WebSocket 服务。' }}</p>
      </div>
    </section>

    <section class="section-panel control-panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">Live Controls</p>
          <h2>实时参数与控制</h2>
        </div>
        <p>建议答辩时把帧率控制在 3 到 5 FPS，演示会更流畅稳定。</p>
      </div>

      <div class="controls-grid">
        <label class="field-card">
          <span>置信度阈值</span>
          <input v-model.number="conf" type="number" min="0" max="1" step="0.01" />
        </label>

        <label class="field-card">
          <span>IOU 阈值</span>
          <input v-model.number="iou" type="number" min="0" max="1" step="0.01" />
        </label>

        <label class="field-card">
          <span>目标帧率</span>
          <input v-model.number="targetFPS" type="number" min="1" max="30" step="1" />
        </label>

        <div class="field-card action-field">
          <span>连接状态</span>
          <div class="status-value" :class="connectionStatus">{{ connectionStatusText }}</div>
        </div>
      </div>

      <button
        type="button"
        class="toggle-button"
        :class="{ active: isDetecting }"
        :disabled="!canToggle"
        @click="toggleDetection"
      >
        {{ isDetecting ? '停止实时检测' : '开始实时检测' }}
      </button>
    </section>

    <section class="realtime-grid">
      <article class="section-panel live-panel">
        <div class="panel-heading slim">
          <div>
            <p class="eyebrow">Camera Feed</p>
            <h2>摄像头输入</h2>
          </div>
        </div>

        <div class="media-shell">
          <video
            ref="videoElement"
            :class="{ hidden: !hasVideo }"
            autoplay
            playsinline
            muted
          ></video>

          <div v-if="!hasVideo" class="placeholder">
            <strong>等待摄像头启动</strong>
            <span>点击“开始实时检测”后，浏览器会请求摄像头权限。</span>
          </div>
        </div>
      </article>

      <article class="section-panel live-panel">
        <div class="panel-heading slim">
          <div>
            <p class="eyebrow">Detection View</p>
            <h2>检测结果画面</h2>
          </div>
        </div>

        <div class="media-shell">
          <canvas
            ref="canvasElement"
            :class="{ hidden: !isDetecting }"
          ></canvas>

          <div v-if="!isDetecting" class="placeholder">
            <strong>等待检测开始</strong>
            <span>检测结果会叠加在本地画面上，以降低传输和渲染压力。</span>
          </div>
        </div>
      </article>
    </section>

    <section class="stats-grid">
      <article class="metric-card">
        <p class="metric-label">已处理帧数</p>
        <p class="metric-value">{{ stats.totalFrames }}</p>
        <p class="metric-note">持续统计当前会话中已处理的视频帧。</p>
      </article>
      <article class="metric-card">
        <p class="metric-label">识别目标数量</p>
        <p class="metric-value">{{ stats.totalDetections }}</p>
        <p class="metric-note">累计记录本次会话中识别出的目标总数。</p>
      </article>
      <article class="metric-card">
        <p class="metric-label">平均帧率</p>
        <p class="metric-value">{{ stats.avgFPS.toFixed(1) }}</p>
        <p class="metric-note">用于展示实时检测的整体流畅度。</p>
      </article>
      <article class="metric-card">
        <p class="metric-label">连接状态</p>
        <p class="metric-value small" :class="connectionStatus">{{ connectionStatusText }}</p>
        <p class="metric-note">WebSocket 正常时会显示“已连接”。</p>
      </article>
    </section>

    <section v-if="error" class="error-box">
      {{ error }}
    </section>

    <section class="section-panel log-panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">Recent Logs</p>
          <h2>最近检测日志</h2>
        </div>
        <p>默认显示最近 10 条包含目标的实时识别记录。</p>
      </div>

      <div v-if="recentDetections.length" class="log-list">
        <div
          v-for="(detection, index) in recentDetections.slice(-10)"
          :key="index"
          class="log-item"
        >
          <span class="log-time">{{ detection.time }}</span>
          <span class="log-count">检测到 {{ detection.count }} 个目标</span>
          <span class="log-detail">{{ detection.details }}</span>
        </div>
      </div>

      <div v-else class="empty-state">
        <strong>还没有实时检测日志</strong>
        <span>启动摄像头后识别到目标时，这里会自动记录最新结果。</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

const videoElement = ref(null)
const canvasElement = ref(null)
const conf = ref(0.25)
const iou = ref(0.45)
const targetFPS = ref(5)
const isDetecting = ref(false)
const hasVideo = ref(false)
const error = ref('')
const connectionStatus = ref('disconnected')

const stats = reactive({
  totalFrames: 0,
  totalDetections: 0,
  avgFPS: 0,
  startTime: null
})

const recentDetections = ref([])
const canToggle = ref(true)

let mediaStream = null
let websocket = null
let detectionInterval = null
let ctx = null
let captureCanvas = null
let captureCtx = null
let frameInFlight = false

const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return '已连接'
    case 'connecting':
      return '连接中'
    case 'disconnected':
      return '已断开'
    case 'error':
      return '连接异常'
    default:
      return '未知状态'
  }
})

const connectWebSocket = () => {
  return new Promise((resolve, reject) => {
    try {
      websocket = new WebSocket('ws://127.0.0.1:8000/ws/realtime_detect')
      connectionStatus.value = 'connecting'

      websocket.onopen = () => {
        const token = localStorage.getItem('token')
        if (!token) {
          websocket.close()
          reject(new Error('未找到登录令牌，请重新登录'))
          return
        }

        websocket.send(JSON.stringify({
          type: 'auth',
          token
        }))
      }

      websocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          if (message.type === 'connected') {
            connectionStatus.value = 'connected'
            resolve()
            return
          }

          if (message.type === 'error' && message.message.includes('认证')) {
            connectionStatus.value = 'error'
            frameInFlight = false
            reject(new Error(message.message))
            return
          }

          handleWebSocketMessage(message)
        } catch (parseError) {
          console.error('解析 WebSocket 消息失败:', parseError)
        }
      }

      websocket.onclose = () => {
        connectionStatus.value = 'disconnected'
        frameInFlight = false
      }

      websocket.onerror = (wsError) => {
        console.error('WebSocket 连接异常:', wsError)
        connectionStatus.value = 'error'
        frameInFlight = false
        reject(wsError)
      }
    } catch (connectError) {
      connectionStatus.value = 'error'
      reject(connectError)
    }
  })
}

const handleWebSocketMessage = (message) => {
  switch (message.type) {
    case 'detection_result':
      frameInFlight = false
      handleDetectionResult(message.data)
      break
    case 'error':
      frameInFlight = false
      console.error('服务端返回错误:', message.message)
      error.value = message.message
      break
    case 'pong':
      break
    default:
      break
  }
}

const handleDetectionResult = (data) => {
  if (!data || !canvasElement.value) return

  stats.totalFrames += 1
  stats.totalDetections += data.detection_count

  if (stats.startTime) {
    const elapsed = (Date.now() - stats.startTime) / 1000
    stats.avgFPS = stats.totalFrames / elapsed
  }

  drawDetectionResult(data)

  if (data.detection_count > 0) {
    const detection = {
      time: new Date().toLocaleTimeString(),
      count: data.detection_count,
      details: data.detections.map((item) => item.label).join('、')
    }

    recentDetections.value.push(detection)
    if (recentDetections.value.length > 50) {
      recentDetections.value = recentDetections.value.slice(-50)
    }
  }
}

const drawDetectionResult = (data) => {
  if (!ctx || !canvasElement.value || !captureCanvas) return

  const canvas = canvasElement.value
  const sourceWidth = data.frame_width || captureCanvas.width
  const sourceHeight = data.frame_height || captureCanvas.height
  const scaleX = canvas.width / sourceWidth
  const scaleY = canvas.height / sourceHeight

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(captureCanvas, 0, 0, canvas.width, canvas.height)

  ctx.lineWidth = 2
  ctx.font = '14px "Segoe UI"'
  ctx.textBaseline = 'top'

  for (const detection of data.detections || []) {
    const [x1, y1, x2, y2] = detection.box
    const drawX = x1 * scaleX
    const drawY = y1 * scaleY
    const drawW = Math.max(1, (x2 - x1) * scaleX)
    const drawH = Math.max(1, (y2 - y1) * scaleY)
    const label = `${detection.label} ${Number(detection.confidence || 0).toFixed(2)}`

    ctx.strokeStyle = '#f97316'
    ctx.strokeRect(drawX, drawY, drawW, drawH)

    const textWidth = ctx.measureText(label).width
    const textHeight = 20
    const textY = Math.max(0, drawY - textHeight)

    ctx.fillStyle = '#f97316'
    ctx.fillRect(drawX, textY, textWidth + 10, textHeight)
    ctx.fillStyle = '#ffffff'
    ctx.fillText(label, drawX + 5, textY + 3)
  }
}

const startCamera = async () => {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: 'environment'
      },
      audio: false
    })

    if (videoElement.value) {
      videoElement.value.srcObject = mediaStream
      hasVideo.value = true

      await new Promise((resolve) => {
        videoElement.value.onloadedmetadata = resolve
      })

      await nextTick()
      setupCanvas()
    }
  } catch (cameraError) {
    console.error('启动摄像头失败:', cameraError)
    error.value = `无法访问摄像头：${cameraError.message}`
    throw cameraError
  }
}

const setupCanvas = () => {
  if (!canvasElement.value || !videoElement.value) return

  const sourceWidth = videoElement.value.videoWidth || 640
  const sourceHeight = videoElement.value.videoHeight || 480
  const maxCaptureWidth = 480
  const scale = Math.min(1, maxCaptureWidth / sourceWidth)
  const renderWidth = Math.max(1, Math.round(sourceWidth * scale))
  const renderHeight = Math.max(1, Math.round(sourceHeight * scale))

  canvasElement.value.width = renderWidth
  canvasElement.value.height = renderHeight
  ctx = canvasElement.value.getContext('2d')

  if (!captureCanvas) {
    captureCanvas = document.createElement('canvas')
  }

  captureCanvas.width = renderWidth
  captureCanvas.height = renderHeight
  captureCtx = captureCanvas.getContext('2d')
}

const captureFrame = () => {
  if (!videoElement.value || !ctx || !captureCanvas || !captureCtx) return null

  captureCtx.drawImage(videoElement.value, 0, 0, captureCanvas.width, captureCanvas.height)
  ctx.clearRect(0, 0, canvasElement.value.width, canvasElement.value.height)
  ctx.drawImage(captureCanvas, 0, 0, canvasElement.value.width, canvasElement.value.height)

  return captureCanvas.toDataURL('image/jpeg', 0.6)
}

const sendFrame = () => {
  if (!websocket || websocket.readyState !== WebSocket.OPEN || frameInFlight) return

  const frameData = captureFrame()
  if (!frameData) return

  websocket.send(JSON.stringify({
    type: 'frame',
    frame_data: frameData,
    conf_thres: conf.value,
    iou_thres: iou.value
  }))

  frameInFlight = true
}

const startDetection = async () => {
  try {
    canToggle.value = false
    error.value = ''

    if (!localStorage.getItem('token')) {
      throw new Error('请先登录后再使用实时检测功能')
    }

    await startCamera()
    await connectWebSocket()

    websocket.send(JSON.stringify({ type: 'start_session' }))

    stats.totalFrames = 0
    stats.totalDetections = 0
    stats.avgFPS = 0
    stats.startTime = Date.now()

    detectionInterval = setInterval(sendFrame, 1000 / targetFPS.value)
    isDetecting.value = true
    ElMessage.success('实时检测已启动')
  } catch (startError) {
    console.error('启动实时检测失败:', startError)

    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop())
      mediaStream = null
      hasVideo.value = false
    }

    if (websocket) {
      websocket.close()
      websocket = null
    }

    frameInFlight = false

    let message = startError.message
    if (message.includes('getUserMedia')) {
      message = '无法访问摄像头，请检查浏览器权限设置'
    } else if (message.includes('认证') || message.includes('令牌')) {
      message = '认证失败，请重新登录后再试'
    } else if (message.includes('WebSocket')) {
      message = '无法连接实时检测服务，请确认后端已启动'
    }

    error.value = message
    ElMessage.error(message)
  } finally {
    canToggle.value = true
  }
}

const stopDetection = () => {
  try {
    if (detectionInterval) {
      clearInterval(detectionInterval)
      detectionInterval = null
    }

    if (websocket) {
      websocket.close(1000, 'client stop')
      websocket = null
    }

    frameInFlight = false

    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop())
      mediaStream = null
    }

    isDetecting.value = false
    hasVideo.value = false
    connectionStatus.value = 'disconnected'

    if (ctx && canvasElement.value) {
      ctx.clearRect(0, 0, canvasElement.value.width, canvasElement.value.height)
    }

    ElMessage.info('实时检测已停止')
  } catch (stopError) {
    console.error('停止实时检测失败:', stopError)
  }
}

const toggleDetection = async () => {
  if (isDetecting.value) {
    stopDetection()
  } else {
    await startDetection()
  }
}

onBeforeUnmount(() => {
  stopDetection()
})
</script>

<style scoped>
.realtime-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(260px, 0.8fr);
  gap: 20px;
  padding: 28px;
  border-radius: 30px;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.status-card {
  padding: 22px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 247, 237, 0.95) 100%);
  border: 1px solid rgba(249, 115, 22, 0.12);
  box-shadow: 0 14px 28px rgba(249, 115, 22, 0.08);
}

.status-card span {
  display: block;
  font-size: 13px;
  color: var(--text-soft);
}

.status-card strong {
  display: block;
  margin-top: 10px;
  font-size: 30px;
}

.status-card p {
  margin: 10px 0 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.control-panel,
.live-panel,
.log-panel {
  padding: 24px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 20px;
}

.panel-heading.slim {
  margin-bottom: 14px;
}

.panel-heading h2 {
  margin: 0;
  font-size: 24px;
}

.panel-heading p:last-child {
  margin: 0;
  max-width: 320px;
  color: var(--text-muted);
  line-height: 1.6;
}

.controls-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.field-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.field-card span {
  font-size: 14px;
  font-weight: 700;
}

.field-card input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 14px;
  background: #ffffff;
  color: var(--text-main);
}

.action-field {
  justify-content: space-between;
}

.status-value {
  font-size: 15px;
  font-weight: 700;
}

.status-value.connected,
.metric-value.connected {
  color: var(--success);
}

.status-value.connecting,
.metric-value.connecting {
  color: var(--warning);
}

.status-value.disconnected,
.metric-value.disconnected,
.status-value.error,
.metric-value.error {
  color: var(--danger);
}

.toggle-button {
  margin-top: 18px;
  padding: 14px 18px;
  border: none;
  border-radius: 16px;
  color: #ffffff;
  font-weight: 700;
  background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-primary-strong) 100%);
  box-shadow: 0 14px 26px rgba(15, 118, 110, 0.22);
  cursor: pointer;
}

.toggle-button.active {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 14px 26px rgba(220, 38, 38, 0.22);
}

.toggle-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
  box-shadow: none;
}

.realtime-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.media-shell {
  position: relative;
  overflow: hidden;
  border-radius: 22px;
  background: rgba(250, 252, 253, 0.96);
  border: 1px solid rgba(15, 23, 42, 0.06);
  aspect-ratio: 4 / 3;
}

.media-shell video,
.media-shell canvas {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  text-align: center;
  padding: 24px;
  color: var(--text-soft);
}

.placeholder strong {
  display: block;
  margin-bottom: 8px;
  font-size: 18px;
  color: var(--text-main);
}

.hidden {
  display: none;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.metric-value.small {
  font-size: 28px;
}

.error-box {
  padding: 14px 16px;
  border-radius: 16px;
  color: var(--danger);
  background: rgba(254, 242, 242, 0.9);
  border: 1px solid rgba(220, 38, 38, 0.14);
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  display: grid;
  grid-template-columns: 112px 160px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 251, 252, 0.95) 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.log-time {
  color: var(--text-soft);
  font-size: 13px;
}

.log-count {
  font-weight: 700;
  color: var(--text-main);
}

.log-detail {
  min-width: 0;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 1200px) {
  .realtime-hero,
  .realtime-grid,
  .controls-grid,
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .realtime-hero,
  .control-panel,
  .live-panel,
  .log-panel {
    padding: 20px;
  }

  .panel-heading,
  .log-item {
    grid-template-columns: 1fr;
  }

  .panel-heading {
    flex-direction: column;
    align-items: flex-start;
  }

  .toggle-button {
    width: 100%;
  }

  .log-item {
    gap: 8px;
  }

  .log-detail {
    white-space: normal;
  }
}
</style>
