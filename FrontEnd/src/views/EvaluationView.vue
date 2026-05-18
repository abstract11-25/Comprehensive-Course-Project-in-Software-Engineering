<template>
  <div class="evaluation-container">
    <!-- 页面标题 -->
    <el-card class="welcome-card" shadow="hover">
      <div class="welcome-content">
        <div class="welcome-text">
          <h1>智能体评估工作台</h1>
          <p>配置评估参数、实时观察执行状态并查看多维度特征指标</p>
        </div>
        <div class="welcome-icon">
          <el-icon :size="60" color="#409eff"><DataBoard /></el-icon>
        </div>
      </div>
    </el-card>

    <!-- 主内容区 -->
    <el-row :gutter="24" style="margin-top: 24px;">
      <!-- 左侧：评估配置 -->
      <el-col :span="8">
        <el-card class="panel-card config-card glass">
          <template #header>
            <div class="config-header">
              <div class="config-title">
                <h2>评估配置</h2>
                <p>填写模型信息与评估参数即可开始测试</p>
              </div>
            </div>
          </template>

          <el-scrollbar max-height="calc(100vh - 220px)" class="config-scrollbar">
          <el-form :model="form" label-width="110px" class="config-form">
            <el-collapse v-model="activeConfigSections" class="config-collapse">
              <el-collapse-item title="基础配置" name="basic">
                <el-form-item label="服务商" required>
                  <el-select v-model="form.provider" placeholder="请选择服务商">
                    <el-option
                      v-for="item in providerOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </el-form-item>
            <el-form-item label="API密钥" required>
              <div style="display: flex; gap: 8px;">
                <el-select
                  v-model="apiKeyMode"
                  style="width: 140px; flex-shrink: 0;"
                  @change="handleApiKeyModeChange"
                >
                  <el-option label="已保存" value="saved" />
                  <el-option label="手动输入" value="manual" />
                </el-select>
                <el-select
                  v-if="apiKeyMode === 'saved'"
                  v-model="selectedApiKeyId"
                  placeholder="选择已保存的密钥"
                  style="flex: 1;"
                  @change="handleSavedKeyChange"
                >
                  <el-option
                    v-for="key in currentProviderApiKeys"
                    :key="key.id"
                    :label="key.name + (key.is_default ? ' (默认)' : '')"
                    :value="key.id"
                  />
                </el-select>
                <el-input
                  v-else
                  v-model="apiKeyInput"
                  type="password"
                  :placeholder="apiKeyPlaceholder"
                  clearable
                  style="flex: 1;"
                />
                <el-button
                  v-if="userStore.user?.role === 'admin'"
                  type="primary"
                  plain
                  @click="showApiKeyDialog = true"
                >
                  管理密钥
                </el-button>
                <el-button
                  v-else
                  type="primary"
                  plain
                  @click="showApiKeyDialog = true"
                >
                  查看密钥
                </el-button>
              </div>
            </el-form-item>
                <el-form-item label="模型名称">
                  <el-input
                    v-model="form.model"
                    placeholder="例如：gpt-4o-mini / glm-4.5-flash"
                    clearable
                  />
                </el-form-item>
                <el-form-item label="Base URL">
                  <el-input
                    v-model="form.baseUrl"
                    placeholder="请输入接口地址"
                    clearable
                  />
                </el-form-item>
            <el-form-item label="测试用例来源">
              <el-radio-group v-model="form.testCaseSource">
                <el-radio label="default">默认测试集</el-radio>
                <el-radio label="custom">自定义测试集</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item
              label="自定义测试集"
              v-if="form.testCaseSource === 'custom'"
            >
              <el-upload
                accept=".json"
                :auto-upload="false"
                :on-change="handleTestCasesUpload"
                :show-file-list="true"
              >
                <el-button type="primary">选择JSON文件</el-button>
              </el-upload>
              <div class="text-help">格式：[{"type":"functional","input":"问题","expected":"答案","category":"分类"}]</div>
            </el-form-item>
            <el-form-item label="评估类型">
              <el-checkbox-group v-model="form.evaluationTypes">
                <el-checkbox label="functional">功能评估</el-checkbox>
                <el-checkbox label="safety">安全评估</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
              </el-collapse-item>

              <el-collapse-item title="高级配置" name="advanced">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="温度">
                      <el-input-number
                        v-model="form.temperature"
                        :step="0.1"
                        :min="0"
                        :max="2"
                        :precision="2"
                        controls-position="right"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Max Tokens">
                      <el-input-number
                        v-model="form.maxTokens"
                        :min="1"
                        :max="4096"
                        :step="64"
                        controls-position="right"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="请求超时(s)">
                      <el-input-number
                        v-model="form.timeout"
                        :min="5"
                        :max="300"
                        controls-position="right"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="重试次数">
                      <el-input-number
                        v-model="form.maxRetries"
                        :min="0"
                        :max="5"
                        controls-position="right"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="并发数">
                      <el-input-number
                        v-model="form.concurrency"
                        :min="1"
                        :max="20"
                        controls-position="right"
                      />
                      <div class="text-help">同时执行的测试用例数量，建议1-10</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="额外请求头">
                  <el-input
                    v-model="form.extraHeaders"
                    type="textarea"
                    placeholder='示例：{"Authorization":"Bearer xxx"}'
                    autosize
                  />
                  <div class="text-help">可选，JSON 对象格式，会与默认请求头合并。</div>
                </el-form-item>

                <el-form-item label="额外请求体">
                  <el-input
                    v-model="form.extraBody"
                    type="textarea"
                    placeholder='示例：{"stream":false}'
                    autosize
                  />
                  <div class="text-help">可选，JSON 对象格式，会合并进请求 body。</div>
                </el-form-item>
              </el-collapse-item>

              <el-collapse-item title="特征评估配置" name="feature" class="feature-config-section">
                <div class="feature-switch-wrapper">
                  <el-form-item label="启用特征评估" class="feature-switch-item">
                    <el-switch 
                      v-model="form.featureMetricsEnabled" 
                      size="large"
                      active-text="已启用"
                      inactive-text="已禁用"
                    />
                  </el-form-item>
                </div>
                <template v-if="form.featureMetricsEnabled">
                  <div class="feature-params-section">
                    <div class="section-title">
                      <span>参数配置</span>
                    </div>
                    <el-row :gutter="16">
                      <el-col :span="12">
                        <div class="param-card">
                          <el-form-item label="真实正例总数">
                            <el-input-number
                              v-model="form.groundTruthTotal"
                              :min="0"
                              :controls="false"
                              placeholder="可选"
                              class="feature-input"
                            />
                            <div class="text-help-small">不填则按用例数量计算</div>
                          </el-form-item>
                        </div>
                      </el-col>
                      <el-col :span="12">
                        <div class="param-card">
                          <el-form-item label="场景类型总数">
                            <el-input-number
                              v-model="form.totalSceneTypes"
                              :min="0"
                              :controls="false"
                              placeholder="例如：5"
                              class="feature-input"
                            />
                            <div class="text-help-small">用于计算场景覆盖度</div>
                          </el-form-item>
                        </div>
                      </el-col>
                      <el-col :span="12">
                        <div class="param-card">
                          <el-form-item label="单主体基准耗时">
                            <el-input-number
                              v-model="form.baselineSingleTaskTime"
                              :min="0"
                              :precision="3"
                              :controls="false"
                              placeholder="可选"
                              class="feature-input"
                            />
                            <div class="text-help-small">单主体完成任务的基准时间（单位：秒）</div>
                          </el-form-item>
                        </div>
                      </el-col>
                      <el-col :span="12">
                        <div class="param-card">
                          <el-form-item label="基准适配成本">
                            <el-input-number
                              v-model="form.baselineAdaptationCost"
                              :min="0"
                              :precision="2"
                              :controls="false"
                              placeholder="例如：1.0"
                              class="feature-input"
                            />
                            <div class="text-help-small">用于计算适配成本系数</div>
                          </el-form-item>
                        </div>
                      </el-col>
                    </el-row>
                  </div>
                  <div class="feature-selection-section">
                    <div class="section-title">
                      <span>评估特性</span>
                    </div>
                    <el-checkbox-group v-model="form.selectedFeatures">
                      <el-checkbox
                        v-for="item in featureOptions"
                        :key="item.value"
                        :label="item.value"
                      >
                        {{ item.label }}
                      </el-checkbox>
                    </el-checkbox-group>
                    <el-alert
                      type="info"
                      :closable="false"
                      show-icon
                      class="feature-alert"
                    >
                      <template #title>
                        <div class="alert-content">
                          <div class="alert-title">提示</div>
                          <div class="alert-text">未选中的特性不会计算，对应的结果面板也会隐藏。</div>
                        </div>
                      </template>
                    </el-alert>
                  </div>
                </template>
              </el-collapse-item>
            </el-collapse>

            <el-form-item class="button-group">
              <!-- 新增：取消按钮，与开始按钮并排 -->
              <el-button
                type="primary"
                @click="startEvaluation"
                :loading="isEvaluating"
                :disabled="isStartButtonDisabled"
              >
                开始评估
              </el-button>
              <el-button
                type="warning"
                @click="cancelEvaluation"
                :disabled="!isEvaluating"
              >
                取消评估
              </el-button>
            </el-form-item>
          </el-form>
          </el-scrollbar>
        </el-card>
      </el-col>

      <!-- 右侧：评估结果（不变，新增对“取消”状态的处理） -->
      <el-col :span="16">
        <el-card v-if="agentInfo" class="panel-card glass">
          <template #header>当前智能体</template>
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="服务商">
              {{ providerLabel(agentInfo?.provider) }}
            </el-descriptions-item>
            <el-descriptions-item label="模型名称">
              {{ agentInfo?.model || '未指定' }}
            </el-descriptions-item>
            <el-descriptions-item label="Base URL">
              {{ agentInfo?.base_url || '未指定' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="panel-card glass">
          <el-tabs v-model="activeTab" class="result-tabs">
          <el-tab-pane label="执行状态" name="progress">
        <el-card v-if="isEvaluating">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>评估进度</span>
              <span style="font-size: 18px; font-weight: bold; color: #409EFF;">
                {{ progress }}%
              </span>
            </div>
          </template>
          <div class="progress-container">
            <el-progress
              :percentage="progress"
              :status="progress < 100 ? 'progress' : 'success'"
              :format="() => `${progress}%`"
            />
            <div class="progress-info">
              <div class="progress-text">
                <strong>当前进度：</strong>
                <span v-if="totalCases > 0">
                  第 {{ currentIndex }} / {{ totalCases }} 个测试用例
                </span>
                <span v-else>准备中...</span>
              </div>
              <div class="progress-text" style="margin-top: 8px;">
                <strong>当前测试用例：</strong>{{ currentTestCase }}
              </div>
              <div v-if="currentInput" class="progress-detail">
                <div class="detail-item">
                  <span class="detail-label">测试输入：</span>
                  <span class="detail-content">{{ currentInput }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">智能体回答：</span>
                  <div class="response-content" v-if="currentResponse">
                    <span v-if="currentResponse === '正在调用API...' || currentResponse.includes('正在调用')" class="api-calling">
                      <el-icon class="is-loading" style="margin-right: 8px;"><Loading /></el-icon>
                      {{ currentResponse }}
                    </span>
                    <span v-else>{{ currentResponse }}</span>
                  </div>
                  <div class="response-content api-calling" v-else>
                    <el-icon class="is-loading" style="margin-right: 8px;"><Loading /></el-icon>
                    等待响应...
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
            <el-empty v-else description="暂无执行任务，请开始评估" />

            <el-card v-if="isEvaluating && realtimeResults.length > 0" class="history-card subtle-card">
              <template #header>实时回答记录</template>
              <div class="history-list">
                <div
                  v-for="(item, index) in realtimeResults"
                  :key="item.input + index"
                  class="history-item"
                >
                  <div class="history-title">
                    <el-tag :type="item.type === 'functional' ? 'success' : 'warning'" size="small">
                      {{ item.type === 'functional' ? '功能' : '安全' }}
                    </el-tag>
                    <span class="history-category">{{ item.category || '未分类' }}</span>
                  </div>
                  <div class="history-body">
                    <div class="history-label">测试输入：</div>
                    <div class="history-content">{{ item.input }}</div>
                  </div>
                  <div class="history-body">
                    <div class="history-label">智能体回答：</div>
                    <div class="history-content response">{{ item.actual || '无响应' }}</div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="评估结果" name="results">
            <template v-if="evaluationSummary || evaluationResults.length">
              <el-card v-if="evaluationSummary">
          <template #header>评估结果概览</template>
          <el-row :gutter="20">
            <el-col :span="6" v-if="evaluationSummary.functional">
              <div class="stat-card">
                <div class="stat-label">功能评估准确率</div>
                <div class="stat-value">{{ (evaluationSummary.functional.accuracy * 100).toFixed(1) }}%</div>
                      <div class="stat-subvalue">
                  通过 {{ evaluationSummary.functional.passed_count ?? Math.round(evaluationSummary.functional.accuracy * evaluationSummary.functional.count) }} / {{ evaluationSummary.functional.count }} 项
                </div>
              </div>
            </el-col>
            <el-col :span="6" v-if="evaluationSummary.safety">
              <div class="stat-card">
                <div class="stat-label">安全评估通过率</div>
                <div class="stat-value">{{ (evaluationSummary.safety.safety_rate * 100).toFixed(1) }}%</div>
                      <div class="stat-subvalue">
                  通过 {{ evaluationSummary.safety.passed_count ?? Math.round(evaluationSummary.safety.safety_rate * evaluationSummary.safety.count) }} / {{ evaluationSummary.safety.count }} 项
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">总体得分</div>
                <div class="stat-value">{{ (evaluationSummary.summary.overall_score * 100).toFixed(2) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">总耗时</div>
                <div class="stat-value">{{ evaluationSummary.total_time }}s</div>
                      <div class="stat-subvalue">
                        平均单次：{{ evaluationSummary.average_case_time ? `${formatNumber(evaluationSummary.average_case_time)}s` : 'N/A' }}
                      </div>
              </div>
            </el-col>
          </el-row>
        </el-card>

              <el-card v-if="evaluationResults.length > 0" style="margin-top: 20px;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>详细评估结果</span>
              <el-radio-group v-model="resultFilter" size="small">
                <el-radio-button label="">全部</el-radio-button>
                <el-radio-button label="functional">功能评估</el-radio-button>
                <el-radio-button label="safety">安全评估</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <el-table :data="filteredResults" stripe style="width: 100%">
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="row.type === 'functional' ? 'success' : 'warning'">
                  {{ row.type === 'functional' ? '功能' : '安全' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120" />
            <el-table-column prop="input" label="输入" min-width="200" show-overflow-tooltip />
            <el-table-column prop="expected" label="期望结果" min-width="150" show-overflow-tooltip />
            <el-table-column prop="actual" label="实际结果" min-width="200" show-overflow-tooltip />
            <el-table-column prop="passed" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.passed ? 'success' : 'danger'">
                  {{ row.passed ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
            </template>
            <el-empty v-else description="暂无评估结果，请先完成评估任务" />
          </el-tab-pane>

          <el-tab-pane
            label="特征指标"
            name="features"
            :disabled="!basicFeatureMetrics && !(generalizationMetrics && ((hasValues(generalizationMetrics?.adaptivity) && isFeatureSelected('adaptivity')) || (hasValues(generalizationMetrics?.robustness) && isFeatureSelected('robustness')) || (hasValues(generalizationMetrics?.portability) && isFeatureSelected('portability')) || (hasValues(generalizationMetrics?.collaboration) && isFeatureSelected('collaboration'))))"
          >
            <template v-if="basicFeatureMetrics || (generalizationMetrics && ((hasValues(generalizationMetrics?.adaptivity) && isFeatureSelected('adaptivity')) || (hasValues(generalizationMetrics?.robustness) && isFeatureSelected('robustness')) || (hasValues(generalizationMetrics?.portability) && isFeatureSelected('portability')) || (hasValues(generalizationMetrics?.collaboration) && isFeatureSelected('collaboration'))))">
              <el-card v-if="basicFeatureMetrics" class="subtle-card">
                <template #header>基础特征指标</template>
                <el-descriptions :column="3" size="small" border>
                  <el-descriptions-item label="准确率">
                    {{ formatPercent(basicFeatureMetrics?.accuracy ?? null) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="召回率">
                    {{ formatPercent(basicFeatureMetrics?.recall ?? null) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="F1 值">
                    {{ formatPercent(basicFeatureMetrics?.f1_score ?? null) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="任务完成率">
                    {{ formatPercent(basicFeatureMetrics?.task_completion_rate ?? null) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="平均响应耗时">
                    {{ basicFeatureMetrics?.average_response_time !== null && basicFeatureMetrics?.average_response_time !== undefined ? `${formatNumber(basicFeatureMetrics?.average_response_time)}s` : 'N/A' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="通过/总用例">
                    {{ basicFeatureMetrics?.passed_cases ?? 0 }} / {{ basicFeatureMetrics?.total_cases ?? 0 }}
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>

              <el-card
                v-if="generalizationMetrics && ((hasValues(generalizationMetrics?.adaptivity) && isFeatureSelected('adaptivity')) || (hasValues(generalizationMetrics?.robustness) && isFeatureSelected('robustness')) || (hasValues(generalizationMetrics?.portability) && isFeatureSelected('portability')) || (hasValues(generalizationMetrics?.collaboration) && isFeatureSelected('collaboration')))"
                style="margin-top: 20px;"
                class="subtle-card"
              >
                <template #header>通用化指标</template>
                <div class="metric-section" v-if="hasValues(generalizationMetrics?.adaptivity) && isFeatureSelected('adaptivity')">
                  <h4>适应性</h4>
                  <el-descriptions :column="2" size="small" border>
                    <el-descriptions-item label="训练场景完成率">
                      {{ formatPercent(generalizationMetrics?.adaptivity?.train_completion_rate ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="非训练场景完成率">
                      {{ formatPercent(generalizationMetrics?.adaptivity?.non_train_completion_rate ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="跨场景完成率偏差">
                      {{ generalizationMetrics?.adaptivity?.cross_scene_completion_deviation !== null && generalizationMetrics?.adaptivity?.cross_scene_completion_deviation !== undefined ? formatNumber(generalizationMetrics?.adaptivity?.cross_scene_completion_deviation, 4) : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="场景覆盖度">
                      {{ formatPercent(generalizationMetrics?.adaptivity?.scene_coverage ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="未知场景适配耗时">
                      {{ generalizationMetrics?.adaptivity?.unknown_scene_adaptation_time ? `${formatNumber(generalizationMetrics?.adaptivity?.unknown_scene_adaptation_time)}s` : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="覆盖场景类型">
                      <template v-if="generalizationMetrics?.adaptivity?.covered_scene_types?.length">
                        <el-tag
                          v-for="scene in generalizationMetrics?.adaptivity?.covered_scene_types"
                          :key="scene"
                          size="small"
                          style="margin-right: 4px; margin-bottom: 4px;"
                        >
                          {{ scene }}
                        </el-tag>
                      </template>
                      <span v-else>N/A</span>
                    </el-descriptions-item>
                  </el-descriptions>
                </div>

                <div class="metric-section" v-if="hasValues(generalizationMetrics?.robustness) && isFeatureSelected('robustness')">
                  <h4>鲁棒性</h4>
                  <el-descriptions :column="2" size="small" border>
                    <el-descriptions-item label="异常输入错误率">
                      {{ formatPercent(generalizationMetrics?.robustness?.abnormal_input_error_rate ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="高并发稳定性">
                      {{ generalizationMetrics?.robustness?.high_concurrency_stability !== null && generalizationMetrics?.robustness?.high_concurrency_stability !== undefined ? formatNumber(generalizationMetrics?.robustness?.high_concurrency_stability, 4) : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="环境波动容错率">
                      {{ formatPercent(generalizationMetrics?.robustness?.environment_fault_tolerance ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="异常输入样本数">
                      {{ generalizationMetrics?.robustness?.abnormal_case_count ?? 0 }}
                    </el-descriptions-item>
                    <el-descriptions-item label="高并发样本数">
                      {{ generalizationMetrics?.robustness?.high_concurrency_case_count ?? 0 }}
                    </el-descriptions-item>
                    <el-descriptions-item label="环境波动样本数">
                      {{ generalizationMetrics?.robustness?.environment_unstable_case_count ?? 0 }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>

                <div class="metric-section" v-if="hasValues(generalizationMetrics?.portability) && isFeatureSelected('portability')">
                  <h4>可移植性</h4>
                  <el-descriptions :column="2" size="small" border>
                    <el-descriptions-item label="跨环境部署成功率">
                      {{ formatPercent(generalizationMetrics?.portability?.cross_environment_success_rate ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="兼容性问题数">
                      {{ generalizationMetrics?.portability?.compatibility_issue_count ?? 0 }}
                    </el-descriptions-item>
                    <el-descriptions-item label="适配成本系数">
                      {{ generalizationMetrics?.portability?.adaptation_cost_ratio !== null && generalizationMetrics?.portability?.adaptation_cost_ratio !== undefined ? formatNumber(generalizationMetrics?.portability?.adaptation_cost_ratio, 4) : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="兼容性清单覆盖率">
                      {{ formatPercent(generalizationMetrics?.portability?.compatibility_coverage ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="部署尝试次数">
                      {{ generalizationMetrics?.portability?.deployment_attempts ?? 0 }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>

                <div class="metric-section" v-if="hasValues(generalizationMetrics?.collaboration) && isFeatureSelected('collaboration')">
                  <h4>协作效率</h4>
                  <el-descriptions :column="2" size="small" border>
                    <el-descriptions-item label="信息交互准确率">
                      {{ formatPercent(generalizationMetrics?.collaboration?.information_accuracy ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="协同耗时差值">
                      {{ generalizationMetrics?.collaboration?.collaboration_time_delta !== null && generalizationMetrics?.collaboration?.collaboration_time_delta !== undefined ? `${formatNumber(generalizationMetrics?.collaboration?.collaboration_time_delta)}s` : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="协同贡献度">
                      {{ generalizationMetrics?.collaboration?.collaboration_contribution !== null && generalizationMetrics?.collaboration?.collaboration_contribution !== undefined ? formatNumber(generalizationMetrics?.collaboration?.collaboration_contribution, 4) : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="协作样本数">
                      {{ generalizationMetrics?.collaboration?.collaboration_case_count ?? 0 }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-card>
            </template>
            <el-empty v-else description="未启用或暂无特征评估结果" />
          </el-tab-pane>
        </el-tabs>
        </el-card>
      </el-col>
    </el-row>

    <!-- API密钥管理对话框 -->
    <el-dialog
      v-model="showApiKeyDialog"
      title="API密钥管理"
      width="800px"
      @open="loadAllApiKeys"
      @close="handleDialogClose"
    >
      <el-tabs v-model="apiKeyDialogTab">
        <el-tab-pane label="密钥列表" name="list">
          <div v-if="userStore.user?.role !== 'admin'" style="margin-bottom: 16px; padding: 12px; background: #f0f9ff; border-radius: 8px; color: #606266; font-size: 13px;">
            <el-icon style="margin-right: 4px;"><InfoFilled /></el-icon>
            您只能查看和使用管理员添加的API密钥，无法保存自己的密钥。
          </div>
          <el-table :data="savedApiKeys" style="width: 100%" stripe>
            <el-table-column prop="name" label="名称" width="200" />
            <el-table-column prop="provider" label="服务商" width="120">
              <template #default="{ row }">
                {{ providerLabel(row.provider) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
                <span v-else style="color: #909399;">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="!row.is_default"
                  type="primary"
                  link
                  size="small"
                  @click="setDefaultKey(row.id)"
                >
                  设为默认
                </el-button>
                <el-button
                  v-if="userStore.user?.role === 'admin'"
                  type="danger"
                  link
                  size="small"
                  @click="deleteKey(row.id)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty
            v-if="savedApiKeys.length === 0"
            description="暂无已保存的密钥"
            :image-size="100"
          />
        </el-tab-pane>
        <el-tab-pane v-if="userStore.user?.role === 'admin'" label="添加密钥" name="add">
          <el-form
            :model="newApiKeyForm"
            label-width="120px"
            style="max-width: 600px; margin-top: 20px;"
          >
            <el-form-item label="服务商" required>
              <el-select v-model="newApiKeyForm.provider" placeholder="选择服务商">
                <el-option
                  v-for="item in providerOptions.filter(p => p.value !== 'custom')"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="密钥名称" required>
              <el-input
                v-model="newApiKeyForm.name"
                placeholder="例如：我的OpenAI密钥"
                clearable
              />
            </el-form-item>
            <el-form-item label="API密钥" required>
              <el-input
                v-model="newApiKeyForm.api_key"
                type="password"
                placeholder="请输入API密钥"
                show-password
                clearable
              />
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="newApiKeyForm.is_default">
                设为该服务商的默认密钥
              </el-checkbox>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="addApiKey">添加</el-button>
              <el-button @click="resetNewApiKeyForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { InfoFilled, DataBoard, Loading } from '@element-plus/icons-vue'
import request from '../utils/request'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

// 1. 类型定义（新增任务ID和取消状态的适配）
interface FormData {
  provider: string
  apiKey: string
  model: string
  baseUrl: string
  temperature: number
  maxTokens: number
  timeout: number
  maxRetries: number
  concurrency: number
  extraHeaders: string
  extraBody: string
  featureMetricsEnabled: boolean
  selectedFeatures: string[]
  groundTruthTotal: number | null
  totalSceneTypes: number | null
  baselineSingleTaskTime: number | null
  baselineAdaptationCost: number | null
  testCaseSource: 'default' | 'custom'
  evaluationTypes: ('functional' | 'safety')[]
  customTestCases: Array<{
    type: 'functional' | 'safety'
    input: string
    expected: string
    category: string
  }> | null
}

interface ProviderOption {
  value: string
  label: string
  baseUrl?: string
  model?: string
  placeholder?: string
}

interface EvaluationResult {
  type: 'functional' | 'safety'
  category: string
  input: string
  expected: string
  actual: string
  passed: boolean
  duration?: number
  metadata?: Record<string, any>
}

interface EvaluationSummary {
  total_time: number
  functional?: {
    accuracy: number
    count: number
    passed_count?: number
  }
  safety?: {
    safety_rate: number
    count: number
    passed_count?: number
  }
  summary: {
    overall_score: number
  }
  average_case_time?: number | null
  feature_metrics?: FeatureMetrics
}

interface FeatureMetrics {
  basic?: {
    accuracy?: number | null
    recall?: number | null
    f1_score?: number | null
    task_completion_rate?: number | null
    average_response_time?: number | null
    total_cases?: number
    passed_cases?: number
    total_duration?: number | null
  }
  generalization?: {
    adaptivity?: AdaptivityMetrics
    robustness?: RobustnessMetrics
    portability?: PortabilityMetrics
    collaboration?: CollaborationMetrics
  }
}

interface AdaptivityMetrics {
  train_completion_rate?: number | null
  non_train_completion_rate?: number | null
  cross_scene_completion_deviation?: number | null
  scene_coverage?: number | null
  covered_scene_types?: string[]
  unknown_scene_adaptation_time?: number | null
  scene_distribution?: Record<string, number>
}

interface RobustnessMetrics {
  abnormal_input_error_rate?: number | null
  high_concurrency_stability?: number | null
  environment_fault_tolerance?: number | null
  abnormal_case_count?: number
  high_concurrency_case_count?: number
  environment_unstable_case_count?: number
}

interface PortabilityMetrics {
  cross_environment_success_rate?: number | null
  compatibility_issue_count?: number | null
  adaptation_cost_ratio?: number | null
  compatibility_coverage?: number | null
  deployment_attempts?: number
}

interface CollaborationMetrics {
  information_accuracy?: number | null
  collaboration_time_delta?: number | null
  collaboration_contribution?: number | null
  collaboration_case_count?: number
}

interface ApiKeyInfo {
  id: number
  provider: string
  name: string
  is_default: boolean
  created_at: string
  updated_at: string
}

// 2. 状态管理（新增任务ID存储）
const featureOptions = [
  { value: 'basic', label: '基础指标' },
  { value: 'adaptivity', label: '适应性' },
  { value: 'robustness', label: '鲁棒性' },
  { value: 'portability', label: '可移植性' },
  { value: 'collaboration', label: '协作效率' }
]
const defaultFeatures = featureOptions.map(option => option.value)
const providerOptions: ProviderOption[] = [
  {
    value: 'zhipu',
    label: '智谱 GLM',
    baseUrl: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    model: 'glm-4.5-flash',
    placeholder: '请输入智谱 AI API Key'
  },
  {
    value: 'openai',
    label: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1/chat/completions',
    model: 'gpt-4o-mini',
    placeholder: '请输入 OpenAI API Key'
  },
  {
    value: 'deepseek',
    label: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com/v1/chat/completions',
    model: 'deepseek-chat',
    placeholder: '请输入 DeepSeek API Key'
  },
  {
    value: 'moonshot',
    label: 'Moonshot',
    baseUrl: 'https://api.moonshot.cn/v1/chat/completions',
    model: 'moonshot-v1-8k',
    placeholder: '请输入 Moonshot API Key'
  },
  {
    value: 'qwen',
    label: '通义千问 (DashScope)',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    model: 'qwen-plus',
    placeholder: '请输入 DashScope API Key'
  },
  {
    value: 'baichuan',
    label: '百川',
    baseUrl: 'https://api.baichuan-ai.com/v1/chat/completions',
    model: 'Baichuan2-Turbo',
    placeholder: '请输入百川 API Key'
  },
  {
    value: 'custom',
    label: '自定义兼容接口',
    baseUrl: '',
    model: '',
    placeholder: '请输入 API Key（若需要）'
  }
]

const form: FormData = reactive({
  provider: 'zhipu',
  apiKey: '',
  model: 'glm-4.5-flash',
  baseUrl: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
  temperature: 0.3,
  maxTokens: 512,
  timeout: 60,
  maxRetries: 2,
  concurrency: 1,
  extraHeaders: '',
  extraBody: '',
  featureMetricsEnabled: true,
  selectedFeatures: [...defaultFeatures],
  groundTruthTotal: null,
  totalSceneTypes: null,
  baselineSingleTaskTime: null,
  baselineAdaptationCost: null,
  testCaseSource: 'default',
  evaluationTypes: ['functional', 'safety'],
  customTestCases: null
})

// API密钥管理相关状态
const apiKeyMode = ref<'saved' | 'manual'>('saved')
const selectedApiKeyId = ref<number | null>(null)
const apiKeyInput = ref('')
const savedApiKeys = ref<ApiKeyInfo[]>([])
const showApiKeyDialog = ref(false)
const apiKeyDialogTab = ref<'list' | 'add'>('list')
const newApiKeyForm = reactive({
  provider: 'zhipu',
  name: '',
  api_key: '',
  is_default: false
})

const providerPresetMap = providerOptions.reduce<Record<string, ProviderOption>>((acc, option) => {
  acc[option.value] = option
  return acc
}, {})

const providerLabel = (value?: string) => {
  if (!value) return '-'
  return providerPresetMap[value]?.label ?? value
}

const currentProviderOption = computed<ProviderOption | undefined>(() =>
  providerOptions.find(option => option.value === form.provider)
)

const apiKeyPlaceholder = computed(() => {
  const option = currentProviderOption.value
  if (!option) return '请输入 API Key'
  return option.placeholder || `请输入 ${option.label} API Key`
})

// 当前服务商的已保存密钥
const currentProviderApiKeys = computed(() => {
  return savedApiKeys.value.filter(k => k.provider === form.provider)
})

// 检查是否有有效的API密钥
const hasValidApiKey = computed(() => {
  if (apiKeyMode.value === 'saved') {
    return selectedApiKeyId.value !== null || currentProviderApiKeys.value.length > 0
  } else {
    return !!apiKeyInput.value
  }
})

// 开始评估按钮是否禁用
const isStartButtonDisabled = computed(() => {
  return !hasValidApiKey.value || form.evaluationTypes.length === 0 || isEvaluating.value
})

watch(
  () => form.provider,
  async (newProvider) => {
    const newPreset = providerPresetMap[newProvider]
    if (newPreset) {
      form.baseUrl = newPreset.baseUrl ?? ''
      form.model = newPreset.model ?? ''
    }
    // 加载该服务商的密钥列表
    await loadApiKeys(newProvider)
    // 自动选择默认密钥（只考虑当前服务商的密钥）
    const providerKeys = savedApiKeys.value.filter(k => k.provider === newProvider)
    const defaultKey = providerKeys.find(k => k.is_default)
    if (defaultKey) {
      selectedApiKeyId.value = defaultKey.id
      apiKeyMode.value = 'saved'
    } else if (providerKeys.length > 0) {
      // 如果没有默认密钥，选择第一个
      selectedApiKeyId.value = providerKeys[0].id
      apiKeyMode.value = 'saved'
    } else {
      // 如果没有已保存的密钥，切换到手动输入
      apiKeyMode.value = 'manual'
      selectedApiKeyId.value = null
      apiKeyInput.value = ''
    }
  },
  { immediate: true }
)

const isEvaluating = ref(false)
const progress = ref(0)
const currentTestCase = ref('')
const currentInput = ref('')
const currentResponse = ref('')
const currentIndex = ref(0)
const totalCases = ref(0)
const evaluationResults = ref<EvaluationResult[]>([])
const evaluationSummary = ref<EvaluationSummary | null>(null)
const resultFilter = ref('')
let pollInterval: NodeJS.Timeout | null = null
const taskId = ref('')  // 新增：存储当前任务ID
const taskFeatureConfig = ref<{ features?: string[] } | null>(null)  // 新增：存储任务的特征配置
interface AgentRuntimeInfo {
  provider?: string
  model?: string
  base_url?: string
}
const agentInfo = ref<AgentRuntimeInfo | null>(null)
const activeTab = ref<'progress' | 'results'>('progress')
const activeConfigSections = ref<string[]>(['basic'])

// 3. 处理自定义测试用例上传（不变）
const handleTestCasesUpload = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const content = JSON.parse((e.target as FileReader).result as string)
      form.customTestCases = content
      ElMessage.success(`已加载 ${content.length} 条测试用例`)
    } catch (error) {
      ElMessage.error('JSON格式错误，请检查文件')
      console.error(error)
    }
  }
  reader.readAsText(file.raw)
}

// 4. 筛选结果（不变）
const filteredResults = computed(() => {
  if (!resultFilter.value) return evaluationResults.value
  return evaluationResults.value.filter(item => item.type === resultFilter.value)
})

const realtimeResults = computed(() => evaluationResults.value.slice().reverse())

const featureMetrics = computed(() => evaluationSummary.value?.feature_metrics ?? null)
const basicFeatureMetrics = computed(() => featureMetrics.value?.basic ?? null)
const generalizationMetrics = computed(() => featureMetrics.value?.generalization ?? null)

// 获取评估时选择的特性（从任务配置或当前表单）
const selectedFeaturesForDisplay = computed(() => {
  // 优先使用任务配置中的特性（评估时的选择）
  if (taskFeatureConfig.value?.features && taskFeatureConfig.value.features.length > 0) {
    return taskFeatureConfig.value.features.map(f => f.toLowerCase())
  }
  // 如果没有任务配置，使用当前表单的选择
  return form.selectedFeatures.map(f => f.toLowerCase())
})

// 检查特性是否被选择
const isFeatureSelected = (featureName: string) => {
  return selectedFeaturesForDisplay.value.includes(featureName.toLowerCase())
}

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined) return 'N/A'
  return `${value.toFixed(2)}%`
}

const formatNumber = (value?: number | null, digits = 3) => {
  if (value === null || value === undefined) return 'N/A'
  return value.toFixed(digits)
}

const hasValues = (group?: Record<string, any> | null): boolean => {
  if (!group) return false
  return Object.values(group).some((value) => {
    if (value === null || value === undefined) return false
    if (Array.isArray(value)) return value.length > 0
    if (typeof value === 'object') return Object.keys(value as Record<string, any>).length > 0
    return true
  })
}

watch(
  () => form.featureMetricsEnabled,
  (enabled) => {
    if (enabled && form.selectedFeatures.length === 0) {
      form.selectedFeatures = [...defaultFeatures]
    }
  }
)

// 5. 开始评估（修改：记录任务ID）
const startEvaluation = async () => {
  isEvaluating.value = true
  progress.value = 0
  evaluationResults.value = []
  evaluationSummary.value = null
  taskId.value = ''  // 重置任务ID
  taskFeatureConfig.value = null  // 重置特征配置
  agentInfo.value = null
  activeTab.value = 'progress'

  const parseOptionalObject = (source: string, label: string) => {
    if (!source || !source.trim()) return undefined
    try {
      const parsed = JSON.parse(source)
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed
      }
      throw new Error('需要是 JSON 对象')
    } catch (error: any) {
      ElMessage.error(`${label} 格式错误：${error?.message || error}`)
      throw error
    }
  }

  let extraHeaders: Record<string, any> | undefined
  let extraBody: Record<string, any> | undefined

  try {
    extraHeaders = parseOptionalObject(form.extraHeaders, '额外请求头')
    extraBody = parseOptionalObject(form.extraBody, '额外请求体')
  } catch {
    isEvaluating.value = false
    return
  }

  // 确定使用的API密钥
  let apiKeyToUse: string | undefined = undefined
  let apiKeyIdToUse: number | undefined = undefined

  if (apiKeyMode.value === 'saved' && selectedApiKeyId.value) {
    // 使用已保存的密钥ID
    apiKeyIdToUse = selectedApiKeyId.value
  } else if (apiKeyMode.value === 'manual' && apiKeyInput.value) {
    // 使用手动输入的密钥
    apiKeyToUse = apiKeyInput.value
  } else {
    // 如果没有选择密钥，检查是否有默认密钥
    const defaultKey = savedApiKeys.value.find(k => k.is_default && k.provider === form.provider)
    if (!defaultKey) {
      ElMessage.error('请选择或输入API密钥')
      isEvaluating.value = false
      return
    }
    apiKeyIdToUse = defaultKey.id
  }

  const payload: Record<string, any> = {
    test_case_source: form.testCaseSource,
    evaluation_types: form.evaluationTypes,
    concurrency: form.concurrency || 1
  }

  // 根据后端逻辑：如果使用api_key_id，不发送agent对象，而是在顶层发送参数
  // 如果使用api_key，发送agent对象
  if (apiKeyIdToUse) {
    // 使用api_key_id时，在顶层发送参数，不发送agent对象
    payload.api_key_id = apiKeyIdToUse
    payload.provider = form.provider
    if (form.model) payload.model = form.model
    if (form.baseUrl) payload.base_url = form.baseUrl
    payload.temperature = form.temperature
    payload.max_tokens = form.maxTokens
    payload.timeout = form.timeout
    payload.max_retries = form.maxRetries
    if (extraHeaders) payload.extra_headers = extraHeaders
    if (extraBody) payload.extra_body = extraBody
  } else if (apiKeyToUse) {
    // 使用api_key时，发送agent对象
    const agentPayload: Record<string, any> = {
      provider: form.provider,
      api_key: apiKeyToUse,
      model: form.model || undefined,
      base_url: form.baseUrl || undefined,
      temperature: form.temperature,
      max_tokens: form.maxTokens,
      timeout: form.timeout,
      max_retries: form.maxRetries
    }
    if (!agentPayload.model) {
      delete agentPayload.model
    }
    if (!agentPayload.base_url) {
      delete agentPayload.base_url
    }
    if (extraHeaders) {
      agentPayload.extra_headers = extraHeaders
    }
    if (extraBody) {
      agentPayload.extra_body = extraBody
    }
    payload.agent = agentPayload
  }

  if (form.testCaseSource === 'custom' && form.customTestCases) {
    payload.custom_test_cases = form.customTestCases
  }

  if (form.featureMetricsEnabled) {
    const featureConfigPayload: Record<string, any> = {
      enabled: true,
      ground_truth_total: form.groundTruthTotal ?? undefined,
      total_scene_types: form.totalSceneTypes ?? undefined,
      baseline_single_task_time: form.baselineSingleTaskTime ?? undefined,
      baseline_adaptation_cost: form.baselineAdaptationCost ?? undefined,
      features: form.selectedFeatures.length ? form.selectedFeatures : undefined
    }
    Object.keys(featureConfigPayload).forEach((key) => {
      if (featureConfigPayload[key] === undefined || featureConfigPayload[key] === null) {
        delete featureConfigPayload[key]
      }
    })
    if (Object.keys(featureConfigPayload).length > 0) {
      payload.feature_config = featureConfigPayload
    }
  }

  try {
    // 调用后端启动评估接口
    const response = await request.post('/api/evaluate', payload)
    taskId.value = response.data.task_id  // 保存任务ID
    // 保存到sessionStorage，以便切换页面后能恢复
    sessionStorage.setItem('current_task_id', taskId.value)
    // 从form中获取agent信息（无论使用哪种方式）
    agentInfo.value = {
      provider: form.provider,
      model: form.model || undefined,
      base_url: form.baseUrl || undefined
    }

    // 定义状态查询函数
    const pollStatus = async () => {
      if (!taskId.value) {
        if (pollInterval) {
          clearInterval(pollInterval)
          pollInterval = null
        }
        return
      }

      try {
        const statusResponse = await request.get(`/api/evaluation/${taskId.value}`)
        const taskStatus = statusResponse.data

        // 更新进度和结果
        progress.value = taskStatus.progress
        currentTestCase.value = taskStatus.current_case || ''
        currentInput.value = taskStatus.current_input || ''
        currentResponse.value = taskStatus.current_response || ''
        currentIndex.value = taskStatus.current_index || 0
        totalCases.value = taskStatus.total_cases || 0
        evaluationResults.value = taskStatus.results || []
        if (taskStatus.agent) {
          agentInfo.value = taskStatus.agent
        }
        // 保存任务的特征配置
        if (taskStatus.feature_config) {
          taskFeatureConfig.value = taskStatus.feature_config
        }

        // 处理所有可能的状态：完成、失败、取消
        if (taskStatus.status === 'completed') {
          if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
          }
          evaluationSummary.value = taskStatus.summary
          isEvaluating.value = false
          ElMessage.success('评估完成！')
          activeTab.value = 'results'
          // 保存评估历史记录
          saveEvaluationHistory(taskStatus)
          // 清除sessionStorage
          sessionStorage.removeItem('current_task_id')
        } else if (taskStatus.status === 'failed') {
          if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
          }
          ElMessage.error(`评估失败：${taskStatus.error}`)
          isEvaluating.value = false
          // 保存失败的评估记录
          saveEvaluationHistory(taskStatus)
          // 清除sessionStorage
          sessionStorage.removeItem('current_task_id')
        } else if (taskStatus.status === 'cancelled') {  // 新增：处理取消状态
          if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
          }
          ElMessage.info('评估已取消')
          isEvaluating.value = false
          // 清除sessionStorage
          sessionStorage.removeItem('current_task_id')
        }
      } catch (error: any) {
        if (pollInterval) {
          clearInterval(pollInterval)
          pollInterval = null
        }
        ElMessage.error('获取评估状态失败：' + error.message)
        isEvaluating.value = false
      }
    }

    // 立即查询一次状态
    await pollStatus()
    
    // 然后每500毫秒轮询一次，确保状态更新更及时
    pollInterval = setInterval(pollStatus, 500)

  } catch (error: any) {
    ElMessage.error('启动评估失败：' + (error.response?.data?.detail || error.message))
    isEvaluating.value = false
    agentInfo.value = null
  }
}

// 新增：取消评估的方法
const cancelEvaluation = async () => {
  if (!taskId.value || !isEvaluating.value) return

  try {
    // 调用后端取消接口
    await request.post(`/api/cancel/${taskId.value}`)
    // 清除轮询并更新状态
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
    isEvaluating.value = false
    currentTestCase.value = '评估已取消'
    // 清除sessionStorage
    sessionStorage.removeItem('current_task_id')
    ElMessage.success('评估已成功取消')
  } catch (error: any) {
    ElMessage.error('取消评估失败：' + (error.response?.data?.detail || error.message))
  }
}

// 保存评估历史记录
function saveEvaluationHistory(taskStatus: any) {
  try {
    const historyItem = {
      task_id: taskId.value,
      provider: agentInfo.value?.provider || form.provider,
      model: agentInfo.value?.model || form.model || '未指定',
      status: taskStatus.status,
      overall_score: taskStatus.summary?.summary?.overall_score || null,
      summary: taskStatus.summary,
      results: taskStatus.results || [],
      created_at: new Date().toLocaleString('zh-CN')
    }

    // 从localStorage读取现有历史
    const stored = localStorage.getItem('evaluation_history')
    let history: any[] = []
    if (stored) {
      try {
        history = JSON.parse(stored)
      } catch (e) {
        history = []
      }
    }

    // 检查是否已存在相同task_id的记录，如果存在则更新，否则添加
    const existingIndex = history.findIndex((item: any) => item.task_id === taskId.value)
    if (existingIndex >= 0) {
      history[existingIndex] = historyItem
    } else {
      history.unshift(historyItem) // 新记录添加到最前面
    }

    // 限制历史记录数量（最多保存100条）
    if (history.length > 100) {
      history = history.slice(0, 100)
    }

    // 保存回localStorage
    localStorage.setItem('evaluation_history', JSON.stringify(history))
  } catch (error) {
    console.error('保存评估历史失败:', error)
  }
}

// API密钥管理相关函数
const loadApiKeys = async (provider?: string) => {
  try {
    const providerParam = provider || form.provider
    const response = await request.get('/api/apikeys', {
      params: { provider: providerParam }
    })
    // 如果指定了provider，合并该provider的密钥；否则替换所有密钥
    if (providerParam && savedApiKeys.value.length > 0) {
      // 移除该provider的旧密钥，添加新密钥
      savedApiKeys.value = savedApiKeys.value.filter(k => k.provider !== providerParam)
      savedApiKeys.value.push(...response.data)
    } else {
      // 加载所有密钥或首次加载
      savedApiKeys.value = response.data
    }
  } catch (error: any) {
    console.error('加载API密钥列表失败:', error)
    // 如果失败，清空列表
    if (!provider) {
      savedApiKeys.value = []
    }
  }
}

// 加载所有密钥（用于对话框）
const loadAllApiKeys = async () => {
  try {
    const response = await request.get('/api/apikeys')
    savedApiKeys.value = response.data
  } catch (error: any) {
    console.error('加载所有API密钥列表失败:', error)
  }
}

const handleApiKeyModeChange = () => {
  if (apiKeyMode.value === 'saved') {
    // 切换到已保存模式时，如果有默认密钥则选择它（只考虑当前服务商）
    const providerKeys = currentProviderApiKeys.value
    const defaultKey = providerKeys.find(k => k.is_default)
    if (defaultKey) {
      selectedApiKeyId.value = defaultKey.id
    } else if (providerKeys.length > 0) {
      selectedApiKeyId.value = providerKeys[0].id
    } else {
      selectedApiKeyId.value = null
    }
  } else {
    // 切换到手动输入模式
    selectedApiKeyId.value = null
  }
}

const handleSavedKeyChange = () => {
  // 选择已保存密钥时，清空手动输入
  apiKeyInput.value = ''
}

const addApiKey = async () => {
  if (!newApiKeyForm.provider || !newApiKeyForm.name || !newApiKeyForm.api_key) {
    ElMessage.warning('请填写完整信息')
    return
  }

  try {
    await request.post('/api/apikeys', {
      provider: newApiKeyForm.provider,
      name: newApiKeyForm.name,
      api_key: newApiKeyForm.api_key,
      is_default: newApiKeyForm.is_default
    })
    ElMessage.success('密钥添加成功')
    resetNewApiKeyForm()
    // 重新加载密钥列表
    await loadApiKeys(newApiKeyForm.provider)
    // 如果添加的是当前服务商的密钥，自动选择它
    if (newApiKeyForm.provider === form.provider) {
      const newKey = savedApiKeys.value.find(k => k.name === newApiKeyForm.name && k.provider === form.provider)
      if (newKey) {
        selectedApiKeyId.value = newKey.id
        apiKeyMode.value = 'saved'
      }
    }
    apiKeyDialogTab.value = 'list'
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '添加密钥失败')
  }
}

const setDefaultKey = async (keyId: number) => {
  try {
    await request.post(`/api/apikeys/${keyId}/set-default`)
    ElMessage.success('已设置为默认密钥')
    // 重新加载密钥列表
    await loadApiKeys(form.provider)
    // 如果设置的是当前服务商的密钥，自动选择它
    const updatedKey = savedApiKeys.value.find(k => k.id === keyId)
    if (updatedKey && updatedKey.provider === form.provider) {
      selectedApiKeyId.value = keyId
      apiKeyMode.value = 'saved'
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '设置默认密钥失败')
  }
}

const deleteKey = async (keyId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个密钥吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await request.delete(`/api/apikeys/${keyId}`)
    ElMessage.success('密钥已删除')
    // 重新加载密钥列表
    await loadApiKeys(form.provider)
    // 如果删除的是当前选中的密钥，切换到手动输入或选择其他密钥
    if (selectedApiKeyId.value === keyId) {
      const remainingKeys = savedApiKeys.value.filter(k => k.provider === form.provider)
      if (remainingKeys.length > 0) {
        const defaultKey = remainingKeys.find(k => k.is_default)
        selectedApiKeyId.value = defaultKey ? defaultKey.id : remainingKeys[0].id
      } else {
        apiKeyMode.value = 'manual'
        selectedApiKeyId.value = null
        apiKeyInput.value = ''
      }
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除密钥失败')
    }
  }
}

const resetNewApiKeyForm = () => {
  newApiKeyForm.provider = form.provider
  newApiKeyForm.name = ''
  newApiKeyForm.api_key = ''
  newApiKeyForm.is_default = false
}

const handleDialogClose = () => {
  apiKeyDialogTab.value = 'list'
  resetNewApiKeyForm()
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

// 恢复进行中的任务
async function restoreRunningTask(savedTaskId: string) {
  try {
    const statusResponse = await request.get(`/api/evaluation/${savedTaskId}`)
    const taskStatus = statusResponse.data
    
    if (taskStatus.status === 'running') {
      // 恢复任务状态
      taskId.value = savedTaskId
      isEvaluating.value = true
      progress.value = taskStatus.progress || 0
      currentTestCase.value = taskStatus.current_case || ''
      currentInput.value = taskStatus.current_input || ''
      currentResponse.value = taskStatus.current_response || ''
      currentIndex.value = taskStatus.current_index || 0
      totalCases.value = taskStatus.total_cases || 0
      evaluationResults.value = taskStatus.results || []
      
      if (taskStatus.agent) {
        agentInfo.value = taskStatus.agent
      }
      
      if (taskStatus.feature_config) {
        taskFeatureConfig.value = taskStatus.feature_config
      }
      
      activeTab.value = 'progress'
      
      // 恢复轮询
      if (pollInterval) {
        clearInterval(pollInterval)
      }
      
      pollInterval = setInterval(async () => {
        if (!taskId.value) {
          if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
          }
          return
        }

        try {
          const statusResponse = await request.get(`/api/evaluation/${taskId.value}`)
          const taskStatus = statusResponse.data

          // 更新进度和结果
          progress.value = taskStatus.progress
          currentTestCase.value = taskStatus.current_case || ''
          currentInput.value = taskStatus.current_input || ''
          currentResponse.value = taskStatus.current_response || ''
          currentIndex.value = taskStatus.current_index || 0
          totalCases.value = taskStatus.total_cases || 0
          evaluationResults.value = taskStatus.results || []
          if (taskStatus.agent) {
            agentInfo.value = taskStatus.agent
          }
          if (taskStatus.feature_config) {
            taskFeatureConfig.value = taskStatus.feature_config
          }

          // 处理所有可能的状态：完成、失败、取消
          if (taskStatus.status === 'completed') {
            if (pollInterval) {
              clearInterval(pollInterval)
              pollInterval = null
            }
            evaluationSummary.value = taskStatus.summary
            isEvaluating.value = false
            ElMessage.success('评估完成！')
            activeTab.value = 'results'
            saveEvaluationHistory(taskStatus)
            sessionStorage.removeItem('current_task_id')
          } else if (taskStatus.status === 'failed') {
            if (pollInterval) {
              clearInterval(pollInterval)
              pollInterval = null
            }
            ElMessage.error(`评估失败：${taskStatus.error}`)
            isEvaluating.value = false
            saveEvaluationHistory(taskStatus)
            sessionStorage.removeItem('current_task_id')
          } else if (taskStatus.status === 'cancelled') {
            if (pollInterval) {
              clearInterval(pollInterval)
              pollInterval = null
            }
            ElMessage.info('评估已取消')
            isEvaluating.value = false
            sessionStorage.removeItem('current_task_id')
          }
        } catch (error: any) {
          if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
          }
          ElMessage.error('获取评估状态失败：' + error.message)
          isEvaluating.value = false
          sessionStorage.removeItem('current_task_id')
        }
      }, 1000)
      
      ElMessage.info('已恢复进行中的评估任务')
    } else {
      // 任务已完成或失败，清除sessionStorage
      sessionStorage.removeItem('current_task_id')
    }
  } catch (error: any) {
    console.warn('恢复任务失败:', error)
    sessionStorage.removeItem('current_task_id')
  }
}

// 组件挂载时获取用户信息和加载密钥列表
onMounted(async () => {
  if (userStore.isLoggedIn && !userStore.user) {
    await userStore.fetchUserInfo()
  }
  // 加载当前服务商的密钥列表
  await loadApiKeys()
  
  // 检查是否有需要恢复的任务
  const savedTaskId = sessionStorage.getItem('current_task_id')
  if (savedTaskId) {
    await restoreRunningTask(savedTaskId)
  }
})
</script>

<style scoped lang="scss">
.evaluation-container {
  max-width: 1600px;
  margin: 0 auto;
}

.welcome-card {
  margin-bottom: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  
  :deep(.el-card__body) {
    padding: 32px;
  }
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;
  
  .welcome-text {
    flex: 1;
    
    h1 {
      font-size: 28px;
      margin: 0 0 12px 0;
      font-weight: 600;
      color: #fff;
    }
    
    p {
      font-size: 16px;
      opacity: 0.9;
      margin: 0;
      color: rgba(255, 255, 255, 0.9);
    }
  }
  
  .welcome-icon {
    opacity: 0.3;
  }
}

.panel-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: all 0.3s;
  
  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  }
}

.panel-card :deep(.el-card__header) {
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  padding: 16px 20px;
  font-weight: 600;
  color: #303133;
}

.config-card {
  position: sticky;
  top: 24px;
  
  :deep(.el-card__header) {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  }
}

/* 配置区域滚动条样式 */
.config-scrollbar :deep(.el-scrollbar__wrap) {
  padding: 20px 20px 20px 20px;
  margin-right: 0;
}

.config-scrollbar :deep(.el-scrollbar__view) {
  padding-right: 8px;
}

.config-scrollbar :deep(.el-scrollbar__bar) {
  right: 8px;
}

.config-scrollbar :deep(.el-scrollbar__thumb) {
  background-color: rgba(64, 158, 255, 0.3);
  border-radius: 4px;
}

.config-scrollbar :deep(.el-scrollbar__thumb:hover) {
  background-color: rgba(64, 158, 255, 0.5);
}

/* 按钮组样式 */
.button-group {
  margin-top: 20px;
  margin-bottom: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(64, 158, 255, 0.1);
}

.button-group :deep(.el-form-item__content) {
  display: flex;
  gap: 12px;
}

.button-group :deep(.el-button) {
  flex: 1;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.button-group :deep(.el-button--primary) {
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.button-group :deep(.el-button--primary:hover:not(:disabled)) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.button-group :deep(.el-button--warning) {
  box-shadow: 0 2px 8px rgba(255, 152, 0, 0.3);
}

.button-group :deep(.el-button--warning:hover:not(:disabled)) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
}

.config-header {
  h2 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #303133;
  }
  
  p {
    margin: 6px 0 0;
    color: #909399;
    font-size: 14px;
  }
}

/* 表单样式 */
.config-form {
  padding: 0;
}

.config-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.config-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #1f2d3d;
  padding-right: 12px;
}

.progress-container {
  padding: 18px 0;
}

.progress-text {
  margin: 10px 0;
  color: #5c6c83;
  font-size: 14px;
}

.progress-info {
  margin-top: 15px;
}

.subtle-card {
  border-radius: 12px;
  border: 1px solid #ebeef5;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  background: #fff;
}

.progress-detail {
  margin-top: 15px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
  border-radius: 12px;
  border-left: 4px solid #409eff;
}

.detail-item {
  margin-bottom: 12px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-weight: 600;
  color: #1f2d3d;
  display: inline-block;
  min-width: 100px;
  margin-right: 10px;
}

.detail-content {
  color: #5c6c83;
  word-break: break-word;
}

.response-content {
  color: #4e5c70;
  background: rgba(255, 255, 255, 0.9);
  padding: 12px;
  border-radius: 12px;
  margin-top: 6px;
  max-height: 200px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.6;
  box-shadow: inset 0 0 0 1px rgba(64, 158, 255, 0.12);
  min-height: 40px;
  display: flex;
  align-items: center;
}

.response-content.api-calling {
  color: #409eff;
  font-weight: 500;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(64, 158, 255, 0.05) 100%);
  border: 1px solid rgba(64, 158, 255, 0.2);
}

.response-content.api-calling .el-icon {
  animation: rotating 1s linear infinite;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.stat-card {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
  border: 1px solid rgba(102, 126, 234, 0.2);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  }
}

.stat-label {
  color: #5c6c83;
  font-size: 14px;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #1890ff;
}

.stat-subvalue {
  color: #909399;
  font-size: 12px;
  margin-top: 6px;
}

.result-tabs {
  padding: 12px 4px 4px;
}

.result-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.result-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  padding: 0 22px;
  height: 42px;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
}

.result-tabs :deep(.el-tabs__item.is-active) {
  font-weight: 600;
  color: #409eff;
}

.result-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 999px;
}

.result-tabs :deep(.el-tab-pane) {
  padding-bottom: 8px;
}

.history-card {
  margin-top: 20px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  border-left: 4px solid #409eff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    transform: translateX(2px);
  }
}

.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.history-category {
  color: #5c6c83;
  font-size: 13px;
}

.history-body {
  display: flex;
  margin-bottom: 8px;
}

.history-body:last-child {
  margin-bottom: 0;
}

.history-label {
  flex: 0 0 80px;
  color: #303133;
  font-weight: 600;
  font-size: 13px;
}

.history-content {
  flex: 1;
  color: #5c6c83;
  font-size: 13px;
  word-break: break-word;
  white-space: pre-wrap;
}

.history-content.response {
  background-color: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
  padding: 8px 12px;
  line-height: 1.6;
  box-shadow: inset 0 0 0 1px rgba(233, 240, 255, 0.9);
}

.metric-section {
  margin-bottom: 20px;
}

.metric-section:last-child {
  margin-bottom: 0;
}

.metric-section h4 {
  margin-bottom: 10px;
  color: #1f2d3d;
  font-size: 15px;
  font-weight: 600;
}

.text-help {
  color: #7a8aa0;
  font-size: 12px;
  margin-top: 5px;
}

.text-help-small {
  color: #909399;
  font-size: 11px;
  margin-top: 4px;
  line-height: 1.4;
  word-wrap: break-word;
  white-space: normal;
}

/* 特征评估配置美化样式 */
.feature-config-section {
  margin-top: 8px;
}

.feature-switch-wrapper {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.08) 0%, rgba(64, 158, 255, 0.03) 100%);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
  border: 1px solid rgba(64, 158, 255, 0.1);
}

.feature-switch-item :deep(.el-form-item__label) {
  font-weight: 600;
  color: #1f2d3d;
  font-size: 14px;
}

.feature-switch-item :deep(.el-switch) {
  --el-switch-on-color: #409EFF;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid rgba(64, 158, 255, 0.15);
}


.feature-params-section {
  margin-bottom: 24px;
}

.param-card {
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(64, 158, 255, 0.12);
  transition: all 0.3s ease;
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

.param-card:hover {
  border-color: rgba(64, 158, 255, 0.3);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.1);
  transform: translateY(-2px);
}

.param-card :deep(.el-form-item) {
  margin-bottom: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.param-card :deep(.el-form-item__content) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.param-card :deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
  font-size: 13px;
  padding-bottom: 8px;
}

.param-card :deep(.el-input-number) {
  width: 100%;
}

.feature-input {
  width: 100%;
}

.param-card :deep(.el-input-number__input) {
  width: 100%;
  min-width: 0;
}

.feature-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.feature-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.3) inset;
}

.feature-selection-section {
  margin-top: 24px;
}


.feature-alert {
  margin-top: 0;
  border-radius: 10px;
  border: 1px solid rgba(64, 158, 255, 0.2);
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.08) 0%, rgba(64, 158, 255, 0.04) 100%);
}

.feature-alert :deep(.el-alert__content) {
  padding: 0;
}

.alert-content {
  font-size: 12px;
  line-height: 1.6;
  word-wrap: break-word;
  white-space: normal;
}

.alert-title {
  font-weight: 600;
  color: #409EFF;
  margin-bottom: 6px;
  font-size: 13px;
}

.alert-text {
  color: #606266;
  line-height: 1.6;
}

@media screen and (max-width: 1400px) {
  .config-card {
    position: static;
  }
}
</style>