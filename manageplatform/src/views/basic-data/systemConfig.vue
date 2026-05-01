<template>
  <div class="system-config-container">
    <el-card v-for="(configs, group) in groupedConfigs" :key="group" class="config-card">
      <template #header>
        <span>{{ getGroupName(group) }}</span>
      </template>
      
      <el-form
        :model="configForm"
        label-width="120px"
        class="config-form"
      >
        <el-form-item
          v-for="config in configs"
          :key="config.id"
          :label="config.description || config.key"
        >
          <el-input
            v-model="configForm[config.key]"
            :placeholder="`请输入${config.description || config.key}`"
            style="width: 400px;"
          />
        </el-form-item>
      </el-form>
    </el-card>
    
    <div class="toolbar">
      <el-button type="primary" @click="handleSave" :loading="loading">
        保存配置
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSystemConfigs, saveSystemConfigs } from '@/api/systemConfig'

const loading = ref(false)
const configs = ref([])
const configForm = reactive({})

const groupNames = {
  general: '通用设置',
  contact: '联系方式',
  miniprogram: '小程序配置',
  order: '订单配置'
}

const groupedConfigs = computed(() => {
  const groups = {}
  configs.value.forEach(config => {
    if (!groups[config.group]) {
      groups[config.group] = []
    }
    groups[config.group].push(config)
  })
  return groups
})

const getGroupName = (group) => {
  return groupNames[group] || group
}

const loadConfigs = async () => {
  loading.value = true
  try {
    const res = await getSystemConfigs()
    if (res.code === 0) {
      const allConfigs = []
      Object.keys(res.data).forEach(group => {
        allConfigs.push(...res.data[group])
      })
      configs.value = allConfigs
      
      allConfigs.forEach(config => {
        configForm[config.key] = config.value
      })
    }
  } catch (error) {
    console.error('加载配置失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  loading.value = true
  try {
    const res = await saveSystemConfigs(configForm)
    if (res.code === 0) {
      ElMessage.success('配置已同步')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.system-config-container {
  padding: 20px;
  max-width: 800px;
}

.config-card {
  margin-bottom: 20px;
}

.config-form {
  margin-bottom: 0;
}

.toolbar {
  margin-top: 20px;
}
</style>
