<template>
  <div class="auth-page">
    <div class="auth-shell register-shell">
      <section class="auth-showcase register-showcase">
        <p class="eyebrow">Create Account</p>
        <h1>加入检测平台，开始你的演示准备</h1>
        <p>
          注册后可以使用系统中的图片检测、视频检测、实时检测、历史记录与报告导出等完整功能模块。
        </p>

        <div class="showcase-list">
          <div class="showcase-line">
            <strong>完整体验</strong>
            <span>登录、检测、记录、报告一条链路全部可跑通。</span>
          </div>
          <div class="showcase-line">
            <strong>交互展示</strong>
            <span>适合毕业答辩时演示系统完成度与前后端联动能力。</span>
          </div>
          <div class="showcase-line">
            <strong>视觉统一</strong>
            <span>注册后进入系统，可直接看到统一风格的工作台界面。</span>
          </div>
        </div>
      </section>

      <section class="auth-panel">
        <div class="panel-top">
          <span class="panel-tag">注册入口</span>
          <h2>创建账号</h2>
          <p>填写基本信息后即可完成注册，并进入系统登录页面。</p>
        </div>

        <el-form ref="registerFormRef" :model="registerForm" :rules="rules" label-width="0">
          <el-form-item prop="username">
            <el-input v-model="registerForm.username" placeholder="请输入用户名" clearable :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="registerForm.email" placeholder="请输入邮箱地址" clearable :prefix-icon="Message" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="registerForm.password" type="password" show-password placeholder="请输入密码" :prefix-icon="Lock" />
          </el-form-item>
          <el-form-item prop="confirmPassword">
            <el-input v-model="registerForm.confirmPassword" type="password" show-password placeholder="请再次输入密码" :prefix-icon="Lock" />
          </el-form-item>

          <div class="terms-row">
            <el-checkbox v-model="agreeTerms">我已阅读并同意相关使用说明</el-checkbox>
          </div>

          <el-button type="primary" class="submit-button" :loading="submitting" @click="submitRegister">
            立即注册
          </el-button>

          <div class="switch-row">
            已有账号？
            <router-link to="/login">去登录</router-link>
          </div>
        </el-form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { User, Message, Lock } from '@element-plus/icons-vue'
import { authHttp } from '@/api/http'

const router = useRouter()
const submitting = ref(false)
const agreeTerms = ref(false)

const registerFormRef = ref()
const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.value.password) {
    callback(new Error('两次输入的密码不一致'))
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

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度需在 3 到 20 个字符之间', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [{ validator: validateEmail, trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度需在 6 到 20 个字符之间', trigger: 'blur' },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '密码必须包含字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }]
}

async function submitRegister() {
  try {
    const valid = await registerFormRef.value.validate()
    if (!valid) return

    if (!agreeTerms.value) {
      ElMessage.warning('请先勾选使用说明')
      return
    }

    submitting.value = true

    const response = await authHttp.post('/auth/register', {
      username: registerForm.value.username,
      email: registerForm.value.email,
      password: registerForm.value.password
    })

    if (!response.message) {
      throw new Error(response.error || '注册失败')
    }

    ElMessage.success('注册成功，请登录')
    setTimeout(() => {
      router.push('/login')
    }, 900)
  } catch (err) {
    console.error('注册失败:', err)
    ElMessage.error(err?.response?.data?.error || err.message || '注册失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  padding: 28px;
  display: grid;
  place-items: center;
}

.register-shell {
  width: min(1180px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.16fr) minmax(360px, 430px);
  gap: 22px;
}

.auth-showcase,
.auth-panel {
  border-radius: 30px;
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(18px) saturate(140%);
}

.register-showcase {
  padding: 36px;
  color: #ffffff;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.16), transparent 28%),
    linear-gradient(135deg, #0f4c5c 0%, #0e7490 54%, #1d4ed8 100%);
}

.register-showcase .eyebrow {
  color: rgba(239, 246, 255, 0.85);
}

.register-showcase h1 {
  margin: 0;
  font-size: 40px;
  line-height: 1.08;
}

.register-showcase p {
  max-width: 560px;
  margin: 18px 0 0;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.82);
}

.showcase-list {
  display: grid;
  gap: 14px;
  margin-top: 30px;
}

.showcase-line {
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.showcase-line strong {
  display: block;
  margin-bottom: 8px;
  font-size: 18px;
}

.showcase-line span {
  color: rgba(255, 255, 255, 0.82);
  line-height: 1.7;
}

.auth-panel {
  padding: 30px 28px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.7);
}

.panel-top {
  margin-bottom: 22px;
}

.panel-tag {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(14, 116, 144, 0.1);
  color: var(--brand-primary-strong);
  font-size: 12px;
  font-weight: 700;
}

.panel-top h2 {
  margin: 14px 0 8px;
  font-size: 30px;
  color: var(--text-main);
}

.panel-top p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.terms-row {
  margin: 8px 0 18px;
}

.submit-button {
  width: 100%;
  height: 46px;
  border: none;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--brand-primary-strong) 0%, #1d4ed8 100%);
}

.switch-row {
  margin-top: 18px;
  text-align: center;
  color: var(--text-muted);
}

.switch-row a {
  margin-left: 6px;
  color: var(--brand-primary-strong);
  text-decoration: none;
  font-weight: 700;
}

@media (max-width: 980px) {
  .register-shell {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .auth-page {
    padding: 16px;
  }

  .register-showcase,
  .auth-panel {
    padding: 22px;
    border-radius: 24px;
  }

  .register-showcase h1 {
    font-size: 34px;
  }
}
</style>
