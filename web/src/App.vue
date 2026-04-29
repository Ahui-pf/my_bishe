<template>
	<div class="page">
		<div class="container">
			<!-- 左侧介绍 -->
			<div class="intro">
				<h1>YOLO 前端演示</h1>
				<div class="mode-switch">
					<button type="button" :class="{ active: mode==='image' }" @click="switchMode('image')">图片检测</button>
					<button type="button" :class="{ active: mode==='video' }" @click="switchMode('video')">视频检测</button>
				</div>

				<div class="upload-zone" :class="{ 'dragover': isDragOver }" 
					@dragover.prevent="onDragOver" @dragleave.prevent="onDragLeave" @drop.prevent="onDrop" @click="openFileDialog">
					<div class="upload-icon" aria-hidden="true">☁</div>
					<div class="upload-text">
						<span class="primary">拖拽文件到此处</span>
						<span class="secondary">或 <b>点击上传</b>（{{ mode==='image' ? '支持图片' : '支持视频' }}）</span>
						<div class="tips">支持 jpg/png/jpeg 等格式，单个文件≤10MB</div>
						<div class="filename" v-if="fileName">已选择：{{ fileName }}</div>
					</div>
				</div>

				<div class="controls">
					<label>
						阈值(conf):
						<input type="number" step="0.01" min="0" max="1" v-model.number="conf" />
					</label>
					<label>
						IOU:
						<input type="number" step="0.01" min="0" max="1" v-model.number="iou" />
					</label>
					<label v-if="mode==='image'">
						返回标注图:
						<input type="checkbox" v-model="returnImage" />
					</label>
					<label v-else>
						采样步长(帧):
						<input type="number" min="1" step="1" v-model.number="frameStride" />
					</label>
					<label v-if="mode==='video'">
						处理帧数上限(0为全部):
						<input type="number" min="0" step="1" v-model.number="maxFrames" />
					</label>
					<button type="submit" :disabled="!file || loading">{{ loading ? '推理中...' : (mode==='image' ? '开始推理(图片)' : '开始推理(视频)') }}</button>
				</div>
			</div>

			<!-- 右侧登录表单 -->
			<div class="login-card">
				<!-- 表单与控件 -->
				<form @submit.prevent="onSubmit" class="form">
					<div v-if="error" class="error">{{ error }}</div>

					<div class="result" v-if="file || result">
						<!-- 左：输入预览 -->
						<div class="pane left">
							<div class="preview" v-if="file && mode==='image'">
								<img :src="fileUrl" alt="preview" />
							</div>
							<div class="preview" v-else-if="file && mode==='video'">
								<video :src="fileUrl" controls muted></video>
							</div>
							<div class="placeholder" v-else>等待上传...</div>
						</div>

						<!-- 右：推理结果 -->
						<div class="pane right">
							<div class="image" v-if="result && result.image_base64">
								<img :src="result.image_base64" alt="result" />
							</div>
							<div class="video" v-else-if="result && result.video_base64 && isVideoResult">
								<video :key="result.video_base64" :src="result.video_base64" controls playsinline></video>
							</div>
							<div class="image" v-else-if="result && result.video_base64 && !isVideoResult">
								<img :src="result.video_base64" alt="result" />
							</div>
							<div class="placeholder" v-else>等待结果...</div>
						</div>
					</div>
				</form>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { modelHttp } from './api/http.js'

const file = ref(null)
const fileUrl = ref('')
const fileName = ref('')
const conf = ref(0.25)
const iou = ref(0.45)
const returnImage = ref(true)
const result = ref(null)
const loading = ref(false)
const error = ref('')
const mode = ref('image') // 'image' | 'video'
const frameStride = ref(1)
const maxFrames = ref(0)
const fileInput = ref(null)
const isDragOver = ref(false)

const isVideoResult = computed(() => {
    if (!result.value || !result.value.video_base64) return false
    return result.value.video_base64.startsWith('data:video/')
})

function revokeUrl() {
	if (fileUrl.value) {
		URL.revokeObjectURL(fileUrl.value)
		fileUrl.value = ''
	}
}

function switchMode(m) {
	if (mode.value === m) return
	mode.value = m
	// 清理状态
	revokeUrl()
	file.value = null
	result.value = null
	error.value = ''
}

function onFileChange(e) {
	error.value = ''
	result.value = null
	file.value = e.target.files && e.target.files[0] ? e.target.files[0] : null
	revokeUrl()
	if (file.value) {
		fileUrl.value = URL.createObjectURL(file.value)
		fileName.value = file.value.name
	}
}

function openFileDialog() {
	if (fileInput.value) {
		fileInput.value.click()
	}
}

function onDragOver() { isDragOver.value = true }
function onDragLeave() { isDragOver.value = false }
function onDrop(ev) {
	isDragOver.value = false
	const dropped = ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files[0]
	if (!dropped) return
	// 按模式限制类型
	if (mode.value === 'image' && !dropped.type.startsWith('image/')) return
	if (mode.value === 'video' && !dropped.type.startsWith('video/')) return
	const dt = new DataTransfer()
	dt.items.add(dropped)
	if (fileInput.value) fileInput.value.files = dt.files
	onFileChange({ target: { files: dt.files } })
}

async function onSubmit() {
	if (!file.value) return
	
	// 检查是否已登录
	const token = localStorage.getItem('token')
	if (!token) {
		error.value = '请先登录后再使用检测功能'
		return
	}
	
	loading.value = true
	error.value = ''
	result.value = null
	try {
		const form = new FormData()
		form.append('file', file.value)
		form.append('conf_thres', String(conf.value))
		form.append('iou_thres', String(iou.value))
		let url = ''
		if (mode.value === 'image') {
			form.append('return_image', String(returnImage.value))
			url = '/infer'
		} else {
			form.append('max_frames', String(maxFrames.value))
			form.append('frame_stride', String(frameStride.value))
			url = '/infer_video'
		}

		const data = await modelHttp.post(url, form, {
			headers: { 'Content-Type': 'multipart/form-data' }
		})
		
		if (data?.error) {
			throw new Error(typeof data.error === 'string' ? data.error : JSON.stringify(data.error))
		}
		result.value = data
	} catch (err) {
		error.value = err?.message || String(err)
	} finally {
		loading.value = false
	}
}

onBeforeUnmount(() => {
	revokeUrl()
})
</script>

<style>
/* 页面与背景 */
.page {
  min-height: 100vh;
  display: flex;
  align-items: center;   /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  background: linear-gradient(135deg, #6a88f7 0%, #8b5cf6 40%, #ec4899 100%);
}

/* 容器 */
.container {
  display: flex;
  width: 100%;
  max-width: 1200px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

/* 左侧介绍 */
.intro {
  padding: 24px 28px;
  width: 50%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.intro h1 {
	margin: 0 0 16px;
	font-size: 22px;
	font-weight: 700;
	color: #1f2937;
}

/* 右侧登录表单 */
.login-card {
  padding: 24px 28px;
  width: 50%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #ffffff;
  border-left: 1px solid #e5e7eb;
}

/* 表单与控件 */
.form { display: flex; flex-direction: column; gap: 16px; margin-bottom: 16px; }
.controls { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

/* 上传区域 */
.upload-zone { 
	border: 2px dashed #c7cbe3; 
	background: linear-gradient(0deg, rgba(255,255,255,0.95), rgba(255,255,255,0.95));
	border-radius: 14px; 
	padding: 26px; 
	display: grid; 
	grid-template-columns: 64px 1fr; 
	gap: 16px; 
	align-items: center; 
	cursor: pointer; 
	transition: border-color .2s ease, background .2s ease, box-shadow .2s ease; 
	box-shadow: inset 0 0 0 0 rgba(99,102,241,0);
}
.upload-zone:hover { border-color: #818cf8; box-shadow: inset 0 0 0 1px rgba(99,102,241,.15); }
.upload-zone.dragover { border-color: #22c55e; background: rgba(34,197,94,0.06); box-shadow: inset 0 0 0 1px rgba(34,197,94,.3); }
.upload-icon { width: 64px; height: 64px; border-radius: 12px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg,#eef2ff,#e0e7ff); color: #6366f1; font-size: 28px; }
.upload-text { display: flex; flex-direction: column; gap: 4px; }
.upload-text .primary { color: #1f2937; font-weight: 600; }
.upload-text .secondary { color: #6b7280; }
.upload-text .tips { color: #9ca3af; font-size: 12px; }
.upload-text .filename { margin-top: 4px; color: #4b5563; font-size: 13px; }

.controls label { 
	display: flex; 
	align-items: center; 
	gap: 8px; 
	color: #374151; 
	background: #fafafa; 
	border: 1px solid #eee; 
	border-radius: 10px; 
	padding: 8px 10px;
}

.controls input[type="number"], .controls input[type="checkbox"] { 
	border: 1px solid #e5e7eb; 
	border-radius: 8px; 
	padding: 6px 8px; 
	outline: none; 
	background: #fff;
}

.controls button, .mode-switch button { 
	height: 36px; 
	padding: 0 14px; 
	border-radius: 10px; 
	border: 1px solid transparent; 
	background: linear-gradient(90deg, #6366f1, #06b6d4);
	color: #fff; 
	font-weight: 600; 
	cursor: pointer; 
	box-shadow: 0 4px 12px rgba(99,102,241,.35);
	transition: transform .08s ease, box-shadow .2s ease, filter .2s ease;
}
.controls button:hover, .mode-switch button:hover { filter: brightness(1.05); box-shadow: 0 6px 16px rgba(99,102,241,.45); }
.controls button:disabled { filter: grayscale(.2) brightness(.9); cursor: not-allowed; box-shadow: none; }

/* 模式切换 */
.mode-switch { display: flex; gap: 8px; margin-bottom: 8px; }
.mode-switch button { background: #ffffff; color: #374151; border: 1px solid #e5e7eb; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
.mode-switch button.active { background: linear-gradient(90deg, #22c55e, #10b981); color: #fff; border-color: transparent; box-shadow: 0 4px 12px rgba(16,185,129,.35); }

/* 结果区域 */
.result { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }
.pane { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.04); }
.result img, .preview img, .result video, .preview video { width: 100%; max-height: 520px; object-fit: contain; border: 1px solid #eef2f7; border-radius: 10px; box-shadow: 0 4px 16px rgba(0,0,0,0.06); }
.preview { margin: 6px 0; }
.placeholder { height: 380px; display: flex; align-items: center; justify-content: center; color: #9ca3af; background: #fafafa; border: 1px dashed #e5e7eb; border-radius: 10px; }

/* 错误提示 */
.error { color: #b00020; background: #fdecec; border: 1px solid #f5c2c7; padding: 10px 12px; border-radius: 10px; margin: 12px 0; }

/* 响应式 */
@media (max-width: 1200px) {
	.result { grid-template-columns: 1fr; }
	.result img, .result video, .preview img, .preview video { max-width: 100%; }
}
</style>