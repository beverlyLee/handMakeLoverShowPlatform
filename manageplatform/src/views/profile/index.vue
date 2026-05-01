<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <span>个人信息</span>
      </template>
      
      <el-form
        ref="profileFormRef"
        :model="profileForm"
        :rules="profileRules"
        label-width="100px"
      >
        <el-form-item label="账号">
          <el-input v-model="profileForm.username" disabled />
        </el-form-item>
        
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="profileForm.nickname" placeholder="请输入昵称" />
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        
        <el-form-item label="邮箱">
          <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSaveProfile" :loading="profileLoading">
            保存
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="password-card">
      <template #header>
        <span>修改密码</span>
      </template>
      
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            placeholder="请输入旧密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码（6位以上，包含字母和数字）"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleChangePassword" :loading="passwordLoading">
            修改密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAdminProfile, updateAdminProfile, changePassword } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

const profileFormRef = ref(null)
const passwordFormRef = ref(null)
const profileLoading = ref(false)
const passwordLoading = ref(false)

const profileForm = reactive({
  username: '',
  nickname: '',
  phone: '',
  email: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validatePasswordStrength = (rule, value, callback) => {
  if (value && value.length < 6) {
    callback(new Error('密码长度不能少于6位'))
  } else if (value && !/[a-zA-Z]/.test(value)) {
    callback(new Error('密码必须包含字母'))
  } else if (value && !/[0-9]/.test(value)) {
    callback(new Error('密码必须包含数字'))
  } else {
    callback()
  }
}

const profileRules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }]
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { validator: validatePasswordStrength, trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const loadProfile = async () => {
  try {
    const res = await getAdminProfile()
    if (res.code === 0) {
      profileForm.username = res.data.username || ''
      profileForm.nickname = res.data.nickname || ''
      profileForm.phone = res.data.phone || ''
      profileForm.email = res.data.email || ''
    }
  } catch (error) {
    console.error('加载个人信息失败:', error)
  }
}

const handleSaveProfile = async () => {
  if (!profileFormRef.value) return
  
  await profileFormRef.value.validate(async (valid) => {
    if (valid) {
      profileLoading.value = true
      try {
        const res = await updateAdminProfile({
          nickname: profileForm.nickname,
          phone: profileForm.phone,
          email: profileForm.email
        })
        if (res.code === 0) {
          ElMessage.success('个人信息更新成功')
          if (userStore.userInfo) {
            userStore.userInfo.nickname = profileForm.nickname
          }
        }
      } catch (error) {
        console.error('保存失败:', error)
      } finally {
        profileLoading.value = false
      }
    }
  })
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await ElMessageBox.confirm(
          '密码修改成功后需要重新登录，确定要修改吗？',
          '提示',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        passwordLoading.value = true
        const res = await changePassword({
          old_password: passwordForm.oldPassword,
          new_password: passwordForm.newPassword,
          confirm_password: passwordForm.confirmPassword
        })
        
        if (res.code === 0) {
          ElMessage.success('密码修改成功，请重新登录')
          await userStore.logout()
          router.push('/login')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('修改密码失败:', error)
        }
      } finally {
        passwordLoading.value = false
      }
    }
  })
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-container {
  max-width: 600px;
}

.profile-card,
.password-card {
  margin-bottom: 20px;
}
</style>
