<template>
  <div class="evaluation-config">
    <el-card shadow="hover" class="page-card">
      <template #header>
        <div class="card-header">
          <div>
            <h2>评估体系配置</h2>
            <p>配置评估体系的权重和参数</p>
          </div>
          <el-button type="primary" @click="handleSaveConfig" :loading="savingConfig" :icon="Check">
            保存配置
          </el-button>
        </div>
      </template>

      <el-form
        :model="evaluationConfig"
        label-width="200px"
        v-loading="configLoading"
        class="config-form"
      >
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>基础权重配置</span>
            </div>
          </template>
          <el-form-item label="基础指标权重">
            <el-input-number
              v-model="evaluationConfig.base_weight"
              :min="0"
              :max="1"
              :precision="2"
              :step="0.1"
              style="width: 200px"
            />
            <div class="form-help">基础指标在总体得分中的权重（0-1）</div>
          </el-form-item>
          <el-form-item label="通用化指标权重">
            <el-input-number
              v-model="evaluationConfig.generalization_weight"
              :min="0"
              :max="1"
              :precision="2"
              :step="0.1"
              style="width: 200px"
            />
            <div class="form-help">通用化指标在总体得分中的权重（0-1）</div>
          </el-form-item>
        </el-card>

        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <el-icon><Grid /></el-icon>
              <span>通用化指标内部权重</span>
            </div>
          </template>
          <el-form-item label="适应性权重">
            <el-input-number
              v-model="evaluationConfig.adaptivity_weight"
              :min="0"
              :max="1"
              :precision="2"
              :step="0.1"
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="鲁棒性权重">
            <el-input-number
              v-model="evaluationConfig.robustness_weight"
              :min="0"
              :max="1"
              :precision="2"
              :step="0.1"
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="可移植性权重">
            <el-input-number
              v-model="evaluationConfig.portability_weight"
              :min="0"
              :max="1"
              :precision="2"
              :step="0.1"
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="协作效率权重">
            <el-input-number
              v-model="evaluationConfig.collaboration_weight"
              :min="0"
              :max="1"
              :precision="2"
              :step="0.1"
              style="width: 200px"
            />
          </el-form-item>
        </el-card>

        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <el-icon><PieChart /></el-icon>
              <span>评估类型权重</span>
            </div>
          </template>
          <el-form-item label="功能评估权重">
            <el-input-number
              v-model="evaluationConfig.func_weight"
              :min="0"
              :max="1"
              :precision="2"
              :step="0.1"
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="安全评估权重">
            <el-input-number
              v-model="evaluationConfig.safety_weight"
              :min="0"
              :max="1"
              :precision="2"
              :step="0.1"
              style="width: 200px"
            />
          </el-form-item>
        </el-card>

        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <el-icon><Setting /></el-icon>
              <span>其他系数配置</span>
            </div>
          </template>
          <el-form-item label="真实正例总数">
            <el-input-number
              v-model="evaluationConfig.ground_truth_total"
              :min="0"
              style="width: 200px"
            />
            <div class="form-help">用于计算召回率，不填则按用例数量计算</div>
          </el-form-item>
          <el-form-item label="场景类型总数">
            <el-input-number
              v-model="evaluationConfig.total_scene_types"
              :min="0"
              style="width: 200px"
            />
            <div class="form-help">用于计算场景覆盖度</div>
          </el-form-item>
          <el-form-item label="单主体基准耗时（秒）">
            <el-input-number
              v-model="evaluationConfig.baseline_single_task_time"
              :min="0"
              :precision="3"
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="基准适配成本">
            <el-input-number
              v-model="evaluationConfig.baseline_adaptation_cost"
              :min="0"
              :precision="2"
              style="width: 200px"
            />
            <div class="form-help">用于计算适配成本系数</div>
          </el-form-item>
        </el-card>

        <el-form-item>
          <el-button type="primary" @click="handleSaveConfig" :loading="savingConfig" :icon="Check">
            保存配置
          </el-button>
          <el-button @click="loadConfig" :icon="Refresh">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '../../stores/user'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { Check, Refresh, DataAnalysis, Grid, PieChart, Setting } from '@element-plus/icons-vue'

const userStore = useUserStore()

const configLoading = ref(false)
const savingConfig = ref(false)

const evaluationConfig = ref({
  base_weight: 0.8,
  generalization_weight: 0.2,
  adaptivity_weight: 0.3,
  robustness_weight: 0.3,
  portability_weight: 0.2,
  collaboration_weight: 0.2,
  func_weight: 0.7,
  safety_weight: 0.3,
  ground_truth_total: null,
  total_scene_types: null,
  baseline_single_task_time: null,
  baseline_adaptation_cost: null
})

async function loadConfig() {
  configLoading.value = true
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/admin/evaluation-config', {
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    const config = response.data
    evaluationConfig.value = {
      base_weight: parseFloat(config.base_weight) || 0.8,
      generalization_weight: parseFloat(config.generalization_weight) || 0.2,
      adaptivity_weight: parseFloat(config.adaptivity_weight) || 0.3,
      robustness_weight: parseFloat(config.robustness_weight) || 0.3,
      portability_weight: parseFloat(config.portability_weight) || 0.2,
      collaboration_weight: parseFloat(config.collaboration_weight) || 0.2,
      func_weight: parseFloat(config.func_weight) || 0.7,
      safety_weight: parseFloat(config.safety_weight) || 0.3,
      ground_truth_total: config.ground_truth_total,
      total_scene_types: config.total_scene_types,
      baseline_single_task_time: config.baseline_single_task_time
        ? parseFloat(config.baseline_single_task_time)
        : null,
      baseline_adaptation_cost: config.baseline_adaptation_cost
        ? parseFloat(config.baseline_adaptation_cost)
        : null
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载配置失败')
  } finally {
    configLoading.value = false
  }
}

async function handleSaveConfig() {
  savingConfig.value = true
  try {
    const configData: any = {
      base_weight: String(evaluationConfig.value.base_weight),
      generalization_weight: String(evaluationConfig.value.generalization_weight),
      adaptivity_weight: String(evaluationConfig.value.adaptivity_weight),
      robustness_weight: String(evaluationConfig.value.robustness_weight),
      portability_weight: String(evaluationConfig.value.portability_weight),
      collaboration_weight: String(evaluationConfig.value.collaboration_weight),
      func_weight: String(evaluationConfig.value.func_weight),
      safety_weight: String(evaluationConfig.value.safety_weight)
    }

    if (evaluationConfig.value.ground_truth_total !== null) {
      configData.ground_truth_total = evaluationConfig.value.ground_truth_total
    }
    if (evaluationConfig.value.total_scene_types !== null) {
      configData.total_scene_types = evaluationConfig.value.total_scene_types
    }
    if (evaluationConfig.value.baseline_single_task_time !== null) {
      configData.baseline_single_task_time = String(evaluationConfig.value.baseline_single_task_time)
    }
    if (evaluationConfig.value.baseline_adaptation_cost !== null) {
      configData.baseline_adaptation_cost = String(evaluationConfig.value.baseline_adaptation_cost)
    }

    await axios.put('http://127.0.0.1:8000/api/admin/evaluation-config', configData, {
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    ElMessage.success('配置已保存')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存配置失败')
  } finally {
    savingConfig.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped lang="scss">
.evaluation-config {
  max-width: 1200px;
  margin: 0 auto;
}

.page-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  h2 {
    margin: 0 0 4px 0;
    font-size: 20px;
    color: #303133;
  }
  
  p {
    margin: 0;
    font-size: 14px;
    color: #909399;
  }
}

.config-form {
  .section-card {
    margin-bottom: 24px;
    border: 1px solid #ebeef5;
    
    :deep(.el-card__header) {
      background: #f5f7fa;
      padding: 16px 20px;
    }
    
    :deep(.el-card__body) {
      padding: 24px;
    }
  }
  
  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #303133;
    
    .el-icon {
      color: #409eff;
    }
  }
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>

