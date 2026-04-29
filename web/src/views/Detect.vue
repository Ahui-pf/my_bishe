<template>
  <div class="page-stack">
    <section class="detect-hero glass-panel">
      <div class="hero-copy">
        <p class="eyebrow">Inference Studio</p>
        <h1 class="section-title">{{ modeTitle }}</h1>
        <p class="section-copy">
          上传文件、调整阈值、查看原始内容与检测结果都集中在这一页完成，方便答辩时流畅展示完整检测流程。
        </p>
        <div class="mode-switch">
          <button type="button" :class="{ active: mode === 'image' }" @click="switchMode('image')">图片检测</button>
          <button type="button" :class="{ active: mode === 'video' }" @click="switchMode('video')">视频检测</button>
        </div>
      </div>

      <div class="hero-brief">
        <article class="brief-card">
          <span>当前模式</span>
          <strong>{{ mode === 'image' ? '单图识别' : '视频分析' }}</strong>
          <p>{{ mode === 'image' ? '适合快速演示推理效果与标注结果。' : '适合展示采样优化和长流程处理能力。' }}</p>
        </article>
        <article class="brief-card accent">
          <span>推荐讲解点</span>
          <strong>{{ mode === 'image' ? '上传即识别' : '自动采样提速' }}</strong>
          <p>{{ mode === 'image' ? '突出检测结果回显和目标数量统计。' : '突出视频检测返回速度与结果预览。' }}</p>
        </article>
      </div>
    </section>

    <section class="detect-grid">
      <article class="section-panel studio-panel">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Upload & Settings</p>
            <h2>检测输入区</h2>
          </div>
          <p>{{ uploadHint }}</p>
        </div>

        <input
          ref="fileInput"
          :accept="mode === 'image' ? 'image/*' : 'video/*'"
          type="file"
          class="hidden-input"
          @change="onFileChange"
        />

        <div
          class="upload-zone"
          :class="{ dragover: isDragOver }"
          @dragover.prevent="onDragOver"
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onDrop"
          @click="openFileDialog"
        >
          <div class="upload-icon">{{ mode === 'image' ? '图' : '视' }}</div>
          <div class="upload-copy">
            <strong>{{ mode === 'image' ? '拖拽图片到这里，或点击上传' : '拖拽视频到这里，或点击上传' }}</strong>
            <span>{{ mode === 'image' ? '支持 jpg / png / jpeg 等常见图片格式。' : '支持常见视频格式，0 为自动采样模式。' }}</span>
            <small>{{ fileName ? `当前文件：${fileName}` : '单个文件大小建议控制在 10MB 左右，演示更顺畅。' }}</small>
          </div>
        </div>

        <form class="form-shell" @submit.prevent="onSubmit">
          <div class="controls-grid">
            <label class="field-card">
              <span>置信度阈值</span>
              <input v-model.number="conf" type="number" min="0" max="1" step="0.01" />
            </label>

            <label class="field-card">
              <span>IOU 阈值</span>
              <input v-model.number="iou" type="number" min="0" max="1" step="0.01" />
            </label>

            <label v-if="mode === 'image'" class="field-card toggle-card">
              <span>返回标注图</span>
              <input v-model="returnImage" type="checkbox" />
            </label>

            <label v-else class="field-card">
              <span>采样步长</span>
              <input v-model.number="frameStride" type="number" min="1" step="1" />
            </label>

            <label v-if="mode === 'video'" class="field-card">
              <span>处理帧数上限</span>
              <input v-model.number="maxFrames" type="number" min="0" step="1" />
            </label>
          </div>

          <div class="submit-row">
            <p>
              {{ mode === 'image'
                ? '图片模式会直接返回标注结果，适合展示目标识别效果。'
                : '视频模式会自动按设定采样并返回预览结果，兼顾速度与演示效果。' }}
            </p>
            <button type="submit" :disabled="!file || loading">
              {{ loading ? '正在推理，请稍候...' : submitLabel }}
            </button>
          </div>
        </form>

        <div v-if="error" class="error-box">{{ error }}</div>
      </article>

      <article class="section-panel tips-panel">
        <div class="panel-heading slim">
          <div>
            <p class="eyebrow">Presentation Tips</p>
            <h2>演示提示</h2>
          </div>
        </div>

        <div class="tips-list">
          <div class="tip-card">
            <strong>先选素材再讲参数</strong>
            <p>答辩时先拖入文件，再讲 conf 和 iou 的含义，老师更容易理解页面流程。</p>
          </div>
          <div class="tip-card">
            <strong>视频模式建议短素材</strong>
            <p>控制在较短时长内，可以更稳定地展示采样优化后的返回速度。</p>
          </div>
          <div class="tip-card">
            <strong>结果区适合做前后对比</strong>
            <p>左边原始内容，右边检测结果，适合边演示边说明模型识别效果。</p>
          </div>
        </div>

        <div v-if="result" class="result-summary">
          <p class="summary-label">本次检测摘要</p>
          <div class="chip-row">
            <span v-if="typeof result.target_count === 'number'" class="soft-chip">目标数量：{{ result.target_count }}</span>
            <span v-if="typeof result.frames_processed === 'number'" class="soft-chip">分析帧数：{{ result.frames_processed }}</span>
            <span class="soft-chip">状态：{{ result.msg || '检测完成' }}</span>
          </div>
        </div>
      </article>
    </section>

    <section class="section-panel result-panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">Result Compare</p>
          <h2>输入与结果对比</h2>
        </div>
        <p>{{ mode === 'image' ? '左侧为原图，右侧为检测结果。' : '左侧为原视频预览，右侧为检测结果预览。' }}</p>
      </div>

      <div class="result-grid">
        <div class="pane">
          <div class="pane-header">
            <span>原始{{ mode === 'image' ? '图片' : '视频' }}</span>
          </div>
          <div v-if="file && mode === 'image'" class="preview">
            <img :src="fileUrl" alt="原始图片预览" />
          </div>
          <div v-else-if="file && mode === 'video'" class="preview">
            <video :src="fileUrl" controls muted></video>
          </div>
          <div v-else class="placeholder">等待上传{{ mode === 'image' ? '图片' : '视频' }}</div>
        </div>

        <div class="pane">
          <div class="pane-header">
            <span>检测输出</span>
          </div>
          <div v-if="result && (result.image_base64 || result.image)" class="preview">
            <img :src="result.image_base64 || result.image" alt="检测结果" />
          </div>
          <div v-else-if="result && result.video_base64 && isVideoResult" class="preview">
            <video :key="result.video_base64" :src="result.video_base64" controls playsinline></video>
          </div>
          <div v-else-if="result && result.video_base64 && !isVideoResult" class="preview">
            <img :src="result.video_base64" alt="检测结果预览" />
          </div>
          <div v-else class="placeholder">等待生成检测结果</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted } from 'vue'
import { modelHttp, authHttp } from '@/api/http'
import { ElMessage } from 'element-plus'

const file = ref(null)
const fileUrl = ref('')
const fileName = ref('')
const conf = ref(0.25)
const iou = ref(0.45)
const returnImage = ref(true)
const result = ref(null)
const loading = ref(false)
const error = ref('')
const mode = ref('image')
const frameStride = ref(1)
const maxFrames = ref(0)
const fileInput = ref(null)
const isDragOver = ref(false)

const userSettings = ref({
  defaultConf: 0.25,
  defaultIou: 0.45,
  defaultReturnImage: true,
  defaultFrameStride: 1,
  defaultMaxFrames: 0
})

const isVideoResult = computed(() => {
  if (!result.value?.video_base64) return false
  return result.value.video_base64.startsWith('data:video/')
})

const modeTitle = computed(() => {
  return mode.value === 'image' ? '图片智能检测工作台' : '视频智能检测工作台'
})

const uploadHint = computed(() => {
  return mode.value === 'image'
    ? '上传后即可展示原图与标注图的对比效果。'
    : '支持采样步长与处理帧数上限设置，便于兼顾速度和效果。'
})

const submitLabel = computed(() => {
  return mode.value === 'image' ? '开始图片检测' : '开始视频检测'
})

function revokeUrl() {
  if (fileUrl.value) {
    URL.revokeObjectURL(fileUrl.value)
    fileUrl.value = ''
  }
}

function switchMode(nextMode) {
  if (mode.value === nextMode) return
  mode.value = nextMode
  revokeUrl()
  file.value = null
  fileName.value = ''
  result.value = null
  error.value = ''
}

function onFileChange(event) {
  error.value = ''
  result.value = null
  file.value = event.target.files?.[0] || null
  revokeUrl()

  if (file.value) {
    fileUrl.value = URL.createObjectURL(file.value)
    fileName.value = file.value.name
  } else {
    fileName.value = ''
  }
}

function openFileDialog() {
  fileInput.value?.click()
}

function onDragOver() {
  isDragOver.value = true
}

function onDragLeave() {
  isDragOver.value = false
}

function onDrop(event) {
  isDragOver.value = false
  const dropped = event.dataTransfer?.files?.[0]
  if (!dropped) return

  if (mode.value === 'image' && !dropped.type.startsWith('image/')) {
    error.value = '请拖入图片文件'
    return
  }

  if (mode.value === 'video' && !dropped.type.startsWith('video/')) {
    error.value = '请拖入视频文件'
    return
  }

  const dt = new DataTransfer()
  dt.items.add(dropped)
  if (fileInput.value) {
    fileInput.value.files = dt.files
    onFileChange({ target: { files: dt.files } })
  }
}

async function apiDetectImage(formData) {
  const token = localStorage.getItem('token')
  if (!token) throw new Error('请先登录后再进行检测')

  return modelHttp.post('/infer', formData, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

async function apiDetectVideo(formData) {
  const token = localStorage.getItem('token')
  if (!token) throw new Error('请先登录后再进行检测')

  return modelHttp.post('/infer_video', formData, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

async function onSubmit() {
  if (!file.value) {
    error.value = '请先选择文件'
    return
  }

  if (!localStorage.getItem('token')) {
    error.value = '请先登录后再进行检测'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('conf_thres', String(conf.value))
    formData.append('iou_thres', String(iou.value))

    if (mode.value === 'image') {
      formData.append('return_image', String(returnImage.value))
      result.value = await apiDetectImage(formData)
    } else {
      formData.append('frame_stride', String(frameStride.value))
      formData.append('max_frames', String(maxFrames.value))
      result.value = await apiDetectVideo(formData)
    }

    ElMessage.success(result.value?.msg || '检测完成')
  } catch (err) {
    console.error('检测请求失败:', err)
    error.value = err?.detail || err?.response?.data?.detail || err?.message || String(err)
  } finally {
    loading.value = false
  }
}

async function loadUserSettings() {
  try {
    const response = await authHttp.get('/user/settings')
    const settings = response?.data || response
    if (!settings) return

    userSettings.value = {
      defaultConf: settings.defaultConf || 0.25,
      defaultIou: settings.defaultIou || 0.45,
      defaultReturnImage: settings.defaultReturnImage !== false,
      defaultFrameStride: settings.defaultFrameStride || 1,
      defaultMaxFrames: settings.defaultMaxFrames || 0
    }

    conf.value = userSettings.value.defaultConf
    iou.value = userSettings.value.defaultIou
    returnImage.value = userSettings.value.defaultReturnImage
    frameStride.value = userSettings.value.defaultFrameStride
    maxFrames.value = userSettings.value.defaultMaxFrames
  } catch (err) {
    console.error('加载用户默认参数失败:', err)
  }
}

onMounted(() => {
  loadUserSettings()
})

onBeforeUnmount(() => {
  revokeUrl()
})
</script>

<style scoped>
.detect-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(280px, 0.95fr);
  gap: 20px;
  padding: 28px;
  border-radius: 30px;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-brief {
  display: grid;
  gap: 16px;
}

.brief-card {
  padding: 22px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(236, 254, 255, 0.94) 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: var(--shadow-card);
}

.brief-card.accent {
  background: linear-gradient(180deg, rgba(255, 247, 237, 0.98) 0%, rgba(255, 255, 255, 0.96) 100%);
}

.brief-card span {
  display: block;
  font-size: 13px;
  color: var(--text-soft);
}

.brief-card strong {
  display: block;
  margin-top: 10px;
  font-size: 28px;
  line-height: 1.2;
}

.brief-card p {
  margin: 10px 0 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.mode-switch {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.mode-switch button {
  min-width: 132px;
  padding: 12px 16px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--text-main);
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.mode-switch button.active {
  color: #ffffff;
  background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-primary-strong) 100%);
  box-shadow: 0 14px 26px rgba(15, 118, 110, 0.22);
  border-color: transparent;
}

.mode-switch button:hover {
  transform: translateY(-2px);
}

.detect-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) minmax(260px, 0.82fr);
  gap: 18px;
}

.studio-panel,
.tips-panel,
.result-panel {
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
  margin-bottom: 16px;
}

.panel-heading h2 {
  margin: 0;
  font-size: 24px;
}

.panel-heading p:last-child {
  max-width: 280px;
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.hidden-input {
  display: none;
}

.upload-zone {
  display: grid;
  grid-template-columns: 74px 1fr;
  gap: 18px;
  align-items: center;
  padding: 24px;
  border-radius: 24px;
  border: 1.5px dashed rgba(14, 116, 144, 0.24);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(244, 250, 251, 0.92) 100%);
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.upload-zone:hover,
.upload-zone.dragover {
  transform: translateY(-2px);
  border-color: rgba(15, 118, 110, 0.42);
  box-shadow: 0 18px 30px rgba(15, 118, 110, 0.08);
}

.upload-icon {
  display: grid;
  place-items: center;
  width: 74px;
  height: 74px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.14) 0%, rgba(14, 116, 144, 0.16) 100%);
  color: var(--brand-primary-strong);
  font-size: 22px;
  font-weight: 800;
}

.upload-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.upload-copy strong {
  font-size: 19px;
}

.upload-copy span {
  color: var(--text-muted);
  line-height: 1.6;
}

.upload-copy small {
  color: var(--text-soft);
}

.form-shell {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.controls-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.field-card span {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
}

.field-card input[type="number"] {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 14px;
  background: #ffffff;
  color: var(--text-main);
}

.toggle-card {
  justify-content: space-between;
}

.toggle-card input {
  width: 18px;
  height: 18px;
}

.submit-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.submit-row p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.submit-row button {
  flex: none;
  min-width: 168px;
  padding: 14px 18px;
  border: none;
  border-radius: 16px;
  color: #ffffff;
  font-weight: 700;
  background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-primary-strong) 100%);
  box-shadow: 0 14px 26px rgba(15, 118, 110, 0.22);
  cursor: pointer;
}

.submit-row button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
  box-shadow: none;
}

.error-box {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 16px;
  color: var(--danger);
  background: rgba(254, 242, 242, 0.9);
  border: 1px solid rgba(220, 38, 38, 0.14);
}

.tips-list {
  display: grid;
  gap: 14px;
}

.tip-card {
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 251, 252, 0.94) 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.tip-card strong {
  display: block;
  margin-bottom: 8px;
  font-size: 16px;
}

.tip-card p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.result-summary {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid rgba(15, 23, 42, 0.08);
}

.summary-label {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--text-soft);
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.pane {
  padding: 16px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 251, 252, 0.94) 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.pane-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.pane-header span {
  font-size: 15px;
  font-weight: 700;
}

.preview img,
.preview video {
  display: block;
  width: 100%;
  max-height: 560px;
  object-fit: contain;
  border-radius: 18px;
  background: rgba(245, 250, 251, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.placeholder {
  display: grid;
  place-items: center;
  min-height: 360px;
  text-align: center;
  color: var(--text-soft);
  border-radius: 18px;
  border: 1.5px dashed rgba(15, 23, 42, 0.12);
  background: rgba(250, 252, 253, 0.9);
}

@media (max-width: 1200px) {
  .detect-grid,
  .detect-hero,
  .result-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .detect-hero,
  .studio-panel,
  .tips-panel,
  .result-panel {
    padding: 20px;
  }

  .panel-heading,
  .submit-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .controls-grid {
    grid-template-columns: 1fr;
  }

  .upload-zone {
    grid-template-columns: 1fr;
    text-align: center;
    justify-items: center;
  }

  .mode-switch {
    width: 100%;
  }

  .mode-switch button {
    flex: 1;
  }

  .submit-row button {
    width: 100%;
  }
}
</style>
