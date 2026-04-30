import { defineStore } from 'pinia'
import { ref } from 'vue'
import { adminLogin, getUserInfo, logout } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref(null)
  const token = ref(localStorage.getItem('token') || '')

  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = ''
    localStorage.removeItem('token')
  }

  const handleLogin = async (loginForm) => {
    const res = await adminLogin(loginForm)
    if (res.code === 0) {
      setToken(res.data.token)
      userInfo.value = res.data.user_info
      return res
    }
    return res
  }

  const getUserInfoAction = async () => {
    const res = await getUserInfo()
    if (res.code === 0) {
      userInfo.value = res.data
      return res
    }
    return res
  }

  const handleLogout = async () => {
    try {
      await logout()
    } catch (e) {
      console.log('登出接口调用失败')
    }
    clearToken()
    userInfo.value = null
  }

  return {
    userInfo,
    token,
    setToken,
    clearToken,
    login: handleLogin,
    getUserInfo: getUserInfoAction,
    logout: handleLogout
  }
})
