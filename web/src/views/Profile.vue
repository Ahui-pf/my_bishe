<template>
  <div class="page-stack">
    <section class="profile-hero glass-panel">
      <div class="hero-copy">
        <p class="eyebrow">Profile Center</p>
        <h1 class="section-title">个人中心与报告管理</h1>
        <p class="section-copy">
          这里集中管理用户资料、密码、检测统计和报告导出入口，是演示系统完整性时很适合展示的一页。
        </p>
        <div class="chip-row">
          <span class="soft-chip">欢迎，{{ displayName }}</span>
          <span class="soft-chip">累计检测 {{ userStats.totalDetections }} 次</span>
          <span class="soft-chip">最近登录：{{ userStats.lastLogin }}</span>
        </div>
      </div>

      <div class="hero-summary">
        <span>报告状态</span>
        <strong>{{ reportSummary.hasData ? '可导出' : '待生成' }}</strong>
        <p>{{ reportSummaryText }}</p>
      </div>
    </section>

    <section class="profile-grid">
      <article class="section-panel profile-card">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Account Info</p>
            <h2>基础资料</h2>
          </div>
          <p>用于展示账号信息维护能力，也适合说明系统支持个性化设置。</p>
        </div>

        <div class="avatar-section">
          <el-upload
            class="avatar-uploader"
            :show-file-list="false"
            :auto-upload="false"
            :before-upload="beforeAvatarUpload"
            :on-change="handleAvatarChange"
          >
            <img v-if="profileForm.avatar" :src="profileForm.avatar" class="avatar" alt="头像" />
            <div v-else class="avatar-placeholder">
              <el-icon><Plus /></el-icon>
            </div>
          </el-upload>

          <div class="avatar-copy">
            <h3>{{ displayName }}</h3>
            <p>{{ profileForm.email || '暂无邮箱信息' }}</p>
            <span>支持 JPG / PNG，文件大小不超过 2MB。</span>
          </div>
        </div>

        <el-form ref="profileFormRef" :model="profileForm" :rules="rules" label-width="0">
          <div class="form-grid">
            <el-form-item prop="username">
              <label>用户名</label>
              <el-input v-model="profileForm.username" placeholder="请输入用户名" clearable :prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="email">
              <label>邮箱</label>
              <el-input v-model="profileForm.email" placeholder="请输入邮箱地址" clearable :prefix-icon="Message" />
            </el-form-item>
            <el-form-item prop="phone">
              <label>手机号</label>
              <el-input v-model="profileForm.phone" placeholder="请输入手机号" clearable :prefix-icon="Phone" />
            </el-form-item>
            <el-form-item prop="nickname">
              <label>昵称</label>
              <el-input v-model="profileForm.nickname" placeholder="请输入昵称" clearable :prefix-icon="UserFilled" />
            </el-form-item>
          </div>

          <el-button type="primary" class="block-button" :loading="submitting" @click="submitProfile">
            保存资料
          </el-button>
        </el-form>
      </article>

      <article class="section-panel password-card">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Security</p>
            <h2>密码修改</h2>
          </div>
          <p>用于展示系统基本的账号安全管理能力。</p>
        </div>

        <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="0">
          <div class="form-grid">
            <el-form-item prop="oldPassword">
              <label>原密码</label>
              <el-input v-model="passwordForm.oldPassword" type="password" show-password placeholder="请输入原密码" :prefix-icon="Lock" />
            </el-form-item>
            <el-form-item prop="newPassword">
              <label>新密码</label>
              <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="请输入新密码" :prefix-icon="Lock" />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <label>确认新密码</label>
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码" :prefix-icon="Lock" />
            </el-form-item>
          </div>

          <el-button type="warning" class="block-button" :loading="passwordSubmitting" @click="submitPassword">
            更新密码
          </el-button>
        </el-form>
      </article>

      <article class="section-panel stats-card">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Statistics</p>
            <h2>个人统计</h2>
          </div>
          <p>老师如果问到“数据都保存在哪里”，这一块很适合配合讲解。</p>
        </div>

        <div class="stats-grid">
          <div class="stat-box">
            <span>总检测次数</span>
            <strong>{{ userStats.totalDetections }}</strong>
          </div>
          <div class="stat-box">
            <span>图片检测次数</span>
            <strong>{{ userStats.totalImages }}</strong>
          </div>
          <div class="stat-box">
            <span>加入天数</span>
            <strong>{{ userStats.joinDays }}</strong>
          </div>
          <div class="stat-box">
            <span>最近登录</span>
            <strong class="small">{{ userStats.lastLogin }}</strong>
          </div>
        </div>
      </article>

      <article class="section-panel actions-card">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Actions</p>
            <h2>常用入口</h2>
          </div>
          <p>帮助文档、报告导出和退出登录都可以从这里快速进入。</p>
        </div>

        <div class="action-grid">
          <button type="button" class="action-item" @click="viewHistory">
            <span class="action-tag">Dashboard</span>
            <h3>查看最近记录</h3>
            <p>跳转到仪表板查看最近活动与检测统计。</p>
          </button>

          <button type="button" class="action-item accent" @click="downloadReport">
            <span class="action-tag">Report</span>
            <h3>导出检测报告</h3>
            <p>{{ reportSummary.hasData ? `当前可汇总 ${reportSummary.totalDetections} 条检测记录。` : '完成检测后可在这里导出 PDF 或 JSON 报告。' }}</p>
          </button>

          <button type="button" class="action-item" @click="showHelp">
            <span class="action-tag">Guide</span>
            <h3>打开帮助文档</h3>
            <p>查看系统说明、参数解释与答辩推荐演示顺序。</p>
          </button>

          <button type="button" class="action-item danger" @click="logout">
            <span class="action-tag">Logout</span>
            <h3>退出登录</h3>
            <p>清除当前登录状态并返回登录页面。</p>
          </button>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import { User, Message, Lock, Phone, UserFilled, Plus } from '@element-plus/icons-vue'
import { authHttp, modelHttp } from '@/api/http'
import { clearStoredToken } from '@/utils/auth'

const router = useRouter()

const submitting = ref(false)
const passwordSubmitting = ref(false)
const profileFormRef = ref()
const passwordFormRef = ref()

const profileForm = ref({
  username: '',
  email: '',
  phone: '',
  nickname: '',
  avatar: ''
})

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const userStats = ref({
  totalDetections: 0,
  totalImages: 0,
  joinDays: 0,
  lastLogin: '暂无'
})

const reportSummary = ref({
  hasData: false,
  lastReportTime: null,
  totalTargets: 0,
  successRate: 0,
  totalDetections: 0,
  apiStatus: 'disconnected'
})

const displayName = computed(() => {
  return profileForm.value.nickname || profileForm.value.username || '未命名用户'
})

const reportSummaryText = computed(() => {
  if (!reportSummary.value.hasData) {
    return '当前还没有足够的检测数据，完成几次检测后即可导出完整报告。'
  }

  return `近一段时间共记录 ${reportSummary.value.totalTargets} 个目标，报告成功率 ${reportSummary.value.successRate}%。`
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入新密码'))
  } else if (value !== passwordForm.value.newPassword) {
    callback(new Error('两次输入的新密码不一致'))
  } else {
    callback()
  }
}

const validateEmail = (rule, value, callback) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (value === '') {
    callback(new Error('请输入邮箱地址'))
  } else if (!emailRegex.test(value)) {
    callback(new Error('请输入正确的邮箱格式'))
  } else {
    callback()
  }
}

const validatePhone = (rule, value, callback) => {
  const phoneRegex = /^1[3-9]\d{9}$/
  if (value === '') {
    callback()
  } else if (!phoneRegex.test(value)) {
    callback(new Error('请输入正确的手机号'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度需在 3 到 20 个字符之间', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [{ validator: validateEmail, trigger: 'blur' }],
  phone: [{ validator: validatePhone, trigger: 'blur' }],
  nickname: [{ max: 20, message: '昵称长度不能超过 20 个字符', trigger: 'blur' }]
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度需在 6 到 20 个字符之间', trigger: 'blur' },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '密码必须包含字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }]
}

const handleAvatarChange = (uploadFile) => {
  if (!uploadFile?.raw) return
  profileForm.value.avatar = URL.createObjectURL(uploadFile.raw)
  ElMessage.success('头像已更新，请记得保存资料')
}

const beforeAvatarUpload = (file) => {
  const isImage = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('头像仅支持 JPG 或 PNG 格式')
  }

  if (!isLt2M) {
    ElMessage.error('头像大小不能超过 2MB')
  }

  return isImage && isLt2M
}

async function submitProfile() {
  try {
    const valid = await profileFormRef.value.validate()
    if (!valid) return

    submitting.value = true

    const response = await authHttp.put('/user/profile', {
      username: profileForm.value.username,
      email: profileForm.value.email,
      phone: profileForm.value.phone,
      nickname: profileForm.value.nickname,
      avatar: profileForm.value.avatar
    })

    if (!response?.message) {
      throw new Error(response?.error || '资料保存失败')
    }

    ElMessage.success('个人资料保存成功')
  } catch (err) {
    console.error('保存个人资料失败:', err)
    ElMessage.error(err?.error || err?.message || '资料保存失败')
  } finally {
    submitting.value = false
  }
}

async function submitPassword() {
  try {
    const valid = await passwordFormRef.value.validate()
    if (!valid) return

    passwordSubmitting.value = true

    const response = await authHttp.put('/user/password', {
      oldPassword: passwordForm.value.oldPassword,
      newPassword: passwordForm.value.newPassword
    })

    if (!response?.message) {
      throw new Error(response?.error || '密码更新失败')
    }

    ElMessage.success('密码更新成功')
    passwordForm.value = {
      oldPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
    passwordFormRef.value.resetFields()
  } catch (err) {
    console.error('更新密码失败:', err)
    ElMessage.error(err?.error || err?.message || '密码更新失败')
  } finally {
    passwordSubmitting.value = false
  }
}

function showHelp() {
  router.push('/help')
}

function viewHistory() {
  router.push('/dashboard')
  ElMessage.info('最近记录可在仪表板的“最近活动”区域查看')
}

const downloadReport = async () => {
  let loadingInstance = null

  try {
    ElMessage.info('正在生成检测报告，请稍候')

    loadingInstance = ElLoading.service({
      lock: true,
      text: '正在整理检测记录并生成报告...',
      background: 'rgba(15, 23, 42, 0.35)'
    })

    const formData = new FormData()
    formData.append('format', 'pdf')
    formData.append('limit', '100')

    const response = await modelHttp.post('/report/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 30000
    })

    if (response?.success && response.pdf_content) {
      const link = document.createElement('a')
      link.href = response.pdf_content
      link.download = response.download_filename || `detection_report_${new Date().toISOString().slice(0, 10)}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      ElMessage.success('PDF 报告下载成功')
      return
    }

    if (response?.success && (response.format === 'json' || response.records)) {
      const jsonContent = JSON.stringify(response, null, 2)
      const blob = new Blob([jsonContent], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `detection_report_${new Date().toISOString().slice(0, 10)}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      ElMessage.success(response.error ? `${response.error}，已导出 JSON 报告` : 'JSON 报告下载成功')
      return
    }

    ElMessage.error(response?.message || '报告生成失败')
  } catch (err) {
    console.error('下载报告失败:', err)

    if (err?.status === 401) {
      ElMessage.error('登录状态失效，请重新登录后再试')
      return
    }

    if (err?.status === 500) {
      ElMessage.error('报告服务异常，请稍后重试')
      return
    }

    ElMessage.error(err?.detail || err?.message || '下载报告失败')
  } finally {
    loadingInstance?.close()
  }
}

function logout() {
  clearStoredToken()
  ElMessage.success('已退出登录')
  setTimeout(() => {
    router.replace('/login')
  }, 500)
}

async function loadUserProfile() {
  try {
    const response = await authHttp.get('/user/profile')
    const data = response?.data || response
    if (!data) return

    profileForm.value = {
      username: data.username || '',
      email: data.email || '',
      phone: data.phone || '',
      nickname: data.nickname || '',
      avatar: data.avatar || ''
    }
  } catch (err) {
    console.error('加载用户资料失败:', err)
    ElMessage.error('加载用户资料失败')
  }
}

async function loadUserStats() {
  try {
    const response = await authHttp.get('/user/stats')
    if (!response) return

    userStats.value = {
      totalDetections: response.totalDetections || 0,
      totalImages: response.totalImages || 0,
      joinDays: response.joinDays || 0,
      lastLogin: response.lastLogin || '暂无'
    }
  } catch (err) {
    console.error('加载用户统计失败:', err)
    userStats.value = {
      totalDetections: 0,
      totalImages: 0,
      joinDays: 0,
      lastLogin: '暂无'
    }
  }
}

async function loadReportSummary() {
  try {
    const response = await modelHttp.get('/report/summary?days=30')
    if (response?.success) {
      const summary = response.summary || {}
      reportSummary.value = {
        hasData: (summary.total_detections || 0) > 0,
        lastReportTime: response.last_updated,
        totalTargets: summary.total_targets || 0,
        successRate: parseFloat(summary.success_rate) || 0,
        totalDetections: summary.total_detections || 0,
        apiStatus: summary.api_status || 'connected'
      }
      return
    }

    reportSummary.value = {
      hasData: false,
      lastReportTime: null,
      totalTargets: 0,
      successRate: 0,
      totalDetections: 0,
      apiStatus: 'disconnected'
    }
  } catch (err) {
    console.error('加载报告摘要失败:', err)
    reportSummary.value = {
      hasData: false,
      lastReportTime: null,
      totalTargets: 0,
      successRate: 0,
      totalDetections: 0,
      apiStatus: 'error'
    }
  }
}

onMounted(() => {
  loadUserProfile()
  loadUserStats()
  loadReportSummary()
})
</script>

<style scoped>
.profile-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.48fr) minmax(280px, 0.84fr);
  gap: 20px;
  padding: 28px;
  border-radius: 30px;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-summary {
  padding: 22px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 247, 237, 0.95) 100%);
  border: 1px solid rgba(249, 115, 22, 0.12);
  box-shadow: 0 14px 28px rgba(249, 115, 22, 0.08);
}

.hero-summary span {
  display: block;
  font-size: 13px;
  color: var(--text-soft);
}

.hero-summary strong {
  display: block;
  margin-top: 10px;
  font-size: 30px;
}

.hero-summary p {
  margin: 10px 0 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.profile-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.92fr);
  gap: 18px;
}

.profile-card,
.password-card,
.stats-card,
.actions-card {
  padding: 24px;
}

.profile-card,
.password-card {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
}

.panel-heading h2 {
  margin: 0;
  font-size: 24px;
}

.panel-heading p:last-child {
  margin: 0;
  max-width: 280px;
  color: var(--text-muted);
  line-height: 1.6;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 250, 251, 0.94) 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.avatar-uploader :deep(.el-upload) {
  display: inline-flex;
}

.avatar,
.avatar-placeholder {
  width: 78px;
  height: 78px;
  border-radius: 24px;
}

.avatar {
  display: block;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.72);
  box-shadow: 0 14px 26px rgba(15, 23, 42, 0.12);
}

.avatar-placeholder {
  display: grid;
  place-items: center;
  color: var(--brand-primary-strong);
  font-size: 24px;
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.12) 0%, rgba(14, 116, 144, 0.14) 100%);
  border: 1px dashed rgba(15, 118, 110, 0.26);
}

.avatar-copy h3 {
  margin: 0;
  font-size: 20px;
}

.avatar-copy p {
  margin: 6px 0 0;
  color: var(--text-muted);
}

.avatar-copy span {
  display: block;
  margin-top: 8px;
  color: var(--text-soft);
  font-size: 13px;
}

.form-grid {
  display: grid;
  gap: 16px;
  margin-bottom: 18px;
}

.form-grid label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
}

.block-button {
  width: 100%;
  height: 46px;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 700;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.stat-box {
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 251, 252, 0.95) 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.stat-box span {
  display: block;
  color: var(--text-soft);
  font-size: 13px;
}

.stat-box strong {
  display: block;
  margin-top: 10px;
  font-size: 30px;
  color: var(--text-main);
}

.stat-box strong.small {
  font-size: 20px;
}

.action-grid {
  display: grid;
  gap: 14px;
}

.action-item {
  padding: 18px;
  text-align: left;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 251, 252, 0.95) 100%);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.action-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-card);
}

.action-item h3 {
  margin: 12px 0 8px;
  font-size: 19px;
  color: var(--text-main);
}

.action-item p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.action-tag {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.1);
  color: var(--brand-primary);
  font-size: 12px;
  font-weight: 700;
}

.action-item.accent .action-tag {
  background: rgba(249, 115, 22, 0.12);
  color: var(--brand-accent);
}

.action-item.danger .action-tag {
  background: rgba(220, 38, 38, 0.12);
  color: var(--danger);
}

@media (max-width: 1200px) {
  .profile-hero,
  .profile-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .profile-hero,
  .profile-card,
  .password-card,
  .stats-card,
  .actions-card {
    padding: 20px;
  }

  .panel-heading,
  .avatar-section {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
