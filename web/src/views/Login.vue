<template>
  <div class="auth-page">
    <div class="auth-shell">
      <section class="auth-showcase">
        <p class="eyebrow">Welcome Back</p>
        <h1>YOLO 路面病害检测系统</h1>
        <p>
          一个面向毕业答辩展示的智能检测平台，集成图片检测、视频检测、实时检测、记录管理与报告导出等核心能力。
        </p>

        <div class="showcase-grid">
          <article class="showcase-card">
            <strong>图片检测</strong>
            <span>快速上传并展示目标识别结果</span>
          </article>
          <article class="showcase-card">
            <strong>视频检测</strong>
            <span>支持采样处理与预览回传</span>
          </article>
          <article class="showcase-card">
            <strong>实时检测</strong>
            <span>基于 WebSocket 实现低延迟推理</span>
          </article>
          <article class="showcase-card">
            <strong>记录管理</strong>
            <span>自动同步检测记录与统计数据</span>
          </article>
        </div>
      </section>

      <section class="auth-panel">
        <div class="panel-top">
          <span class="panel-tag">登录入口</span>
          <h2>欢迎回来</h2>
          <p>登录后即可进入仪表板并开始演示完整检测流程。</p>
        </div>

        <el-form ref="loginFormRef" :model="loginForm" :rules="rules" label-width="0">
          <el-form-item prop="username">
            <el-input v-model="loginForm.username" placeholder="请输入用户名" clearable />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="loginForm.password" type="password" show-password placeholder="请输入密码" />
          </el-form-item>

          <div class="form-row">
            <el-checkbox v-model="remember">记住我</el-checkbox>
            <span class="link-text">演示账号请提前准备好</span>
          </div>

          <el-button type="primary" class="submit-button" :loading="submitting" @click="submitLogin">
            立即登录
          </el-button>

          <div class="switch-row">
            还没有账号？
            <router-link to="/register">去注册</router-link>
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
import { authHttp } from '@/api/http'

const router = useRouter()
const submitting = ref(false)
const remember = ref(false)

const loginFormRef = ref()
const loginForm = ref({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为 6 位', trigger: 'blur' }
  ]
}

async function submitLogin() {
  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    submitting.value = true

    const response = await authHttp.post('/auth/login', {
      username: loginForm.value.username,
      password: loginForm.value.password
    })

    if (!response.token) {
      throw new Error(response.error || '登录失败')
    }

    localStorage.setItem('token', response.token)
    ElMessage.success('登录成功')
    setTimeout(() => {
      router.push('/dashboard')
    }, 800)
  } catch (err) {
    console.error('登录失败:', err)
    ElMessage.error(err?.response?.data?.msg || err.message || '登录失败')
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

.auth-shell {
  width: min(1180px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(360px, 420px);
  gap: 22px;
}

.auth-showcase,
.auth-panel {
  border-radius: 30px;
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(18px) saturate(140%);
}

.auth-showcase {
  padding: 36px;
  color: #ffffff;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.18), transparent 28%),
    linear-gradient(135deg, #0f766e 0%, #0e7490 58%, #155e75 100%);
}

.auth-showcase .eyebrow {
  color: rgba(240, 253, 250, 0.85);
}

.auth-showcase h1 {
  margin: 0;
  font-size: 42px;
  line-height: 1.08;
}

.auth-showcase p {
  max-width: 560px;
  margin: 18px 0 0;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.82);
}

.showcase-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 32px;
}

.showcase-card {
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.showcase-card strong {
  display: block;
  margin-bottom: 8px;
  font-size: 18px;
}

.showcase-card span {
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.82);
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
  background: rgba(15, 118, 110, 0.1);
  color: var(--brand-primary);
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

.form-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin: 8px 0 18px;
}

.link-text {
  font-size: 13px;
  color: var(--text-soft);
}

.submit-button {
  width: 100%;
  height: 46px;
  border: none;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-primary-strong) 100%);
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
  .auth-shell {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .auth-page {
    padding: 16px;
  }

  .auth-showcase,
  .auth-panel {
    padding: 22px;
    border-radius: 24px;
  }

  .auth-showcase h1 {
    font-size: 34px;
  }

  .showcase-grid {
    grid-template-columns: 1fr;
  }

  .form-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
