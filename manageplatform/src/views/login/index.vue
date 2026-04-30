<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-title">
        <div class="login-icon">
          <el-icon :size="36"><Handbag /></el-icon>
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
        
        <el-form-item>
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
      
      <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
        <p>默认账号: admin / admin123</p>
        <p>开发模式: 任意用户名密码均可登录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
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
        const res = await userStore.login(loginForm)
        if (res.code === 0) {
          ElMessage.success('登录成功')
          router.push('/dashboard')
        }
      } catch (error) {
        console.error('登录失败:', error)
        localStorage.setItem('token', 'valid_token_1')
        userStore.userInfo = {
          id: 1,
          username: 'admin',
          nickname: '管理员',
          roles: ['admin']
        }
        ElMessage.success('登录成功（开发模式）')
        router.push('/dashboard')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>
