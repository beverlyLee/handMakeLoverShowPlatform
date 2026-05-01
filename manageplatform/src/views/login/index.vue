<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="login-icon">
          <el-icon :size="40"><Handbag /></el-icon>
        </div>
        <h2>手作爱好者平台</h2>
        <p>管理后台登录</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item class="checkbox-item">
          <el-checkbox v-model="loginForm.rememberMe">7天免登</el-checkbox>
        </el-form-item>
        
        <el-form-item class="button-item">
          <el-button
            type="primary"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>默认账号: admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { adminLogin } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  rememberMe: false
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const loginData = {
          username: loginForm.username,
          password: loginForm.password,
          remember_me: loginForm.rememberMe
        }
        const res = await adminLogin(loginData)
        if (res.code === 0) {
          userStore.setToken(res.data.token)
          userStore.userInfo = res.data.user_info
          ElMessage.success('登录成功')
          router.push('/dashboard')
        }
      } catch (error) {
        console.error('登录失败:', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.login-header {
  text-align: center;
  padding: 30px 30px 10px;
}

.login-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 15px;
  background: linear-gradient(135deg, #ff9a56 0%, #ffcc00 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.login-header h2 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #303133;
  font-weight: 600;
}

.login-header p {
  margin: 0;
  font-size: 16px;
  color: #909399;
}

.login-form {
  padding: 0 30px 20px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

.checkbox-item {
  margin-bottom: 15px !important;
}

.button-item {
  margin-bottom: 10px !important;
}

.login-btn {
  width: 100%;
  height: 50px;
  font-size: 18px;
  font-weight: 500;
  border-radius: 8px;
  display: block;
}

:deep(.el-checkbox) {
  font-size: 16px;
  color: #409eff;
}

.login-footer {
  text-align: center;
  padding: 0 30px 30px;
}

.login-footer p {
  margin: 0;
  color: #999;
  font-size: 14px;
}
</style>
