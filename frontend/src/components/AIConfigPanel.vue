<!-- 
  AI 配置設定面板 Vue 組件範例
  可以整合到您的前端應用中
-->

<template>
  <div class="ai-config-panel">
    <h2>AI 服務配置</h2>
    
    <!-- 當前配置顯示 -->
    <div class="current-config" v-if="currentConfig">
      <h3>當前配置</h3>
      <div class="config-item">
        <span class="label">Base URL:</span>
        <span class="value">{{ currentConfig.base_url }}</span>
      </div>
      <div class="config-item">
        <span class="label">API Key:</span>
        <span class="value">{{ currentConfig.api_key_masked || '未設定' }}</span>
      </div>
      <div class="config-item">
        <span class="label">當前模型:</span>
        <span class="value">{{ currentConfig.current_model || '未載入' }}</span>
      </div>
      <!-- <div class="config-item">
        <span class="label">模型狀態:</span>
        <span class="value" :class="currentConfig.model_loaded ? 'loaded' : 'unloaded'">
          {{ currentConfig.model_loaded ? '已載入' : '未載入' }}
        </span>
      </div> -->
    </div>

    <!-- 配置表單 -->
    <div class="config-form">
      <h3>更新配置</h3>
      
      <!-- <div class="form-group">
        <label for="baseUrl">Base URL:</label>
        <input 
          id="baseUrl"
          v-model="form.base_url" 
          type="text" 
          placeholder="http://localhost:8000/api"
          :disabled="isOpenAIKey"
        />
        <small v-if="isOpenAIKey" class="auto-note">
          ⚡ 使用 OpenAI key 時會自動設定為 https://api.openai.com/v1
        </small>
      </div> -->

      <div class="form-group">
        <label for="apiKey">API Key:</label>
        <input 
          id="apiKey"
          v-model="form.api_key" 
          type="password" 
          placeholder="輸入 API Key (sk-... 為 OpenAI key)"
          @input="checkApiKeyType"
        />
        <small v-if="isOpenAIKey" class="openai-detected">
          ✓ 檢測到 OpenAI API Key
        </small>
      </div>

      <div class="form-group" v-if="isOpenAIKey">
        <label for="model">預設模型:</label>
        <select 
          id="model"
          v-model="form.default_model"
          @change="checkModelType"
        >
          <!-- <optgroup label="GPT-5 系列 (新端點)">
            <option value="gpt-5-mini">gpt-5-mini</option>
            <option value="gpt-5">gpt-5</option>
            <option value="gpt-5-turbo">gpt-5-turbo</option>
          </optgroup> -->
          <optgroup label="GPT-4 系列">
            <option value="gpt-4o-mini">gpt-4o-mini</option>
            <option value="gpt-4o">gpt-4o</option>
            <option value="gpt-4-turbo">gpt-4-turbo</option>
            <option value="gpt-4">gpt-4</option>
          </optgroup>
          <optgroup label="GPT-3.5 系列">
            <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
            <option value="gpt-3.5-turbo-16k">gpt-3.5-turbo-16k</option>
          </optgroup>
          <optgroup label="其他">
            <option value="">自訂模型...</option>
          </optgroup>
        </select>
        <small class="model-note" v-if="isGPT5Model">
          ⚡ GPT-5 系列使用新端點: /v1/response
        </small>
        <small class="model-note" v-else>
          使用標準端點: /v1
        </small>
      </div>

      <!-- 自訂模型名稱輸入框 (當選擇 "其他" 時顯示) -->
      <div class="form-group" v-if="isOpenAIKey && form.default_model === 'other'">
        <label for="customModel">自訂模型名稱:</label>
        <input 
          id="customModel"
          v-model="customModelName"
          type="text" 
          placeholder="輸入自訂模型名稱 (例如: gpt-4-turbo)"
        />
      </div>

      <div class="form-group" v-if="!isOpenAIKey">
        <label for="model">預設模型:</label>
        <input 
          id="model"
          v-model="form.default_model" 
          type="text" 
          :placeholder="'Qwen-2.5-3B-Instruct-NPU'"
          readonly
          disabled
          class="readonly-input"
        />
        <small class="model-note">
          ⚠️ 請先輸入 OpenAI API Key 才能選擇模型
        </small>
      </div>

      <div class="button-group">
        <button @click="updateConfig" class="btn-primary">
          更新配置
        </button>
        <button @click="useLemonadePreset" class="btn-secondary">
          使用 Lemonade Server (本地)
        </button>
        <button @click="loadConfig" class="btn-secondary">
          重新載入
        </button>
      </div>
    </div>

    <!-- 訊息提示 -->
    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>

    <!-- 預設配置快捷按鈕 -->
    <!-- <div class="presets">
      <h3>快速配置</h3>
      <button @click="useLemonadePreset" class="preset-btn lemonade">
        🏠 使用 Lemonade Server (本地)
      </button>
      <button @click="useOpenAIPreset" class="preset-btn openai">
        🤖 使用 OpenAI API
      </button>
    </div> -->

    <!-- 提示訊息 -->
    <!-- <div class="info-box">
      <h4>💡 提示</h4>
      <ul>
        <li>使用 <strong>OpenAI API key</strong> 時（以 <code>sk-</code> 開頭），端點會自動設定</li>
        <li><strong>GPT-5 系列</strong>使用新端點：<code>https://api.openai.com/v1/response</code></li>
        <li><strong>其他模型</strong>使用標準端點：<code>https://api.openai.com/v1</code></li>
        <li>本地模型請使用 Lemonade Server 配置</li>
      </ul>
    </div> -->
  </div>
</template>

<script>
export default {
  name: 'AIConfigPanel',
  
  data() {
    return {
      currentConfig: null,
      form: {
        base_url: '',
        api_key: '',
        default_model: ''
      },
      message: '',
      messageType: 'info', // 'success', 'error', 'info'
      isOpenAIKey: false, // 追蹤是否為 OpenAI key
      customModelName: '' // 自訂模型名稱
    }
  },

  computed: {
    isGPT5Model() {
      const model = this.form.default_model.toLowerCase();
      return model.includes('gpt-5') || model.includes('gpt5');
    },
    
    endpointType() {
      return this.isGPT5Model ? 'response' : 'standard';
    }
  },

  mounted() {
    this.loadConfig()
  },

  methods: {
    checkApiKeyType() {
      // 檢查是否為 OpenAI API key (以 sk- 開頭)
      this.isOpenAIKey = this.form.api_key.startsWith('sk-')
      
      if (this.isOpenAIKey) {
        // 自動清空 base_url（讓後端自動設定）
        this.form.base_url = ''
      }
    },

    async loadConfig() {
      try {
        const response = await fetch('http://localhost:8001/ai/config')
        if (!response.ok) throw new Error('無法載入配置')
        
        this.currentConfig = await response.json()
        this.showMessage('配置已載入', 'success')
      } catch (error) {
        this.showMessage(`載入配置失敗: ${error.message}`, 'error')
      }
    },

    async updateConfig() {
      try {
        // 處理自訂模型名稱
        if (this.form.default_model === 'other' && this.customModelName) {
          this.form.default_model = this.customModelName;
        }
        
        // 只發送有值的欄位
        const config = {}
        
        // 如果是 OpenAI key，不需要發送 base_url（後端會自動設定）
        if (!this.isOpenAIKey && this.form.base_url) {
          config.base_url = this.form.base_url
        }
        
        if (this.form.api_key) config.api_key = this.form.api_key
        if (this.form.default_model) config.default_model = this.form.default_model
        
        // 加入端點類型 (GPT-5 使用 response，其他使用 standard)
        config.endpoint_type = this.endpointType

        if (Object.keys(config).length === 0) {
          this.showMessage('請至少填寫一個欄位', 'error')
          return
        }

        const response = await fetch('http://localhost:8001/ai/config', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(config)
        })

        if (!response.ok) throw new Error('更新失敗')
        
        const result = await response.json()
        this.showMessage(result.message, 'success')
        
        // 清空表單
        this.form = { base_url: '', api_key: '', default_model: '' }
        this.customModelName = ''
        this.isOpenAIKey = false
        
        // 重新載入配置
        await this.loadConfig()
      } catch (error) {
        this.showMessage(`更新配置失敗: ${error.message}`, 'error')
      }
    },

    // async resetConfig() {
    //   if (!confirm('確定要重置配置到預設值嗎？')) return

    //   try {
    //     const response = await fetch('http://localhost:8001/ai/config/reset', {
    //       method: 'POST'
    //     })

    //     if (!response.ok) throw new Error('重置失敗')
        
    //     const result = await response.json()
    //     this.showMessage(result.message, 'success')
        
    //     // 重新載入配置
    //     await this.loadConfig()
    //   } catch (error) {
    //     this.showMessage(`重置配置失敗: ${error.message}`, 'error')
    //   }
    // },

    async useLemonadePreset() {
      // 填入表單資料
      this.form.base_url = 'http://localhost:8000/api'
      this.form.api_key = 'lemonade'
      this.form.default_model = 'Qwen-2.5-3B-Instruct-NPU'
      this.isOpenAIKey = false
      
      // 直接調用更新配置
      await this.updateConfig()
    },

    // useOpenAIPreset() {
    //   this.form.base_url = '' // 不需要填寫，會自動設定
    //   this.form.api_key = '' // 使用者需要填入自己的 key
    //   this.form.default_model = 'gpt-4o-mini'
    //   this.isOpenAIKey = false // 還沒輸入 key
    //   this.showMessage('請填入您的 OpenAI API Key（以 sk- 開頭），URL 會自動設定', 'info')
    // },

    showMessage(text, type = 'info') {
      this.message = text
      this.messageType = type
      
      // 3 秒後自動清除訊息
      setTimeout(() => {
        this.message = ''
      }, 3000)
    }
  }
}
</script>

<style scoped>
.ai-config-panel {
  max-width: 600px;
  margin: 20px auto;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
}

h2 {
  margin-top: 0;
  color: #333;
}

h3 {
  color: #555;
  margin-top: 20px;
  margin-bottom: 10px;
}

.current-config {
  background: white;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.config-item:last-child {
  border-bottom: none;
}

.label {
  font-weight: bold;
  color: #666;
}

.value {
  color: #333;
}

.value.loaded {
  color: #28a745;
}

.value.unloaded {
  color: #dc3545;
}

.config-form {
  background: white;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #555;
}

.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
  background-color: white;
  cursor: pointer;
}

.form-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.form-group optgroup {
  font-weight: bold;
  font-style: normal;
  padding: 5px 0;
}

.form-group option {
  padding: 5px 10px;
}

.form-group input:disabled {
  background-color: #f0f0f0;
  cursor: not-allowed;
  color: #999;
}

.form-group input.readonly-input {
  background-color: #f8f9fa;
  cursor: not-allowed;
  color: #adb5bd;
  border-color: #dee2e6;
  font-style: italic;
}

.form-group small {
  display: block;
  margin-top: 5px;
  font-size: 12px;
  color: #666;
}

.form-group small.auto-note {
  color: #007bff;
  font-weight: 500;
}

.form-group small.openai-detected {
  color: #28a745;
  font-weight: 500;
}

.form-group small.model-note {
  color: #6c757d;
  font-style: italic;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

button {
  flex: 1;
  padding: 10px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.message {
  padding: 12px;
  border-radius: 4px;
  margin-top: 15px;
  text-align: center;
}

.message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.message.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.presets {
  background: white;
  padding: 15px;
  border-radius: 6px;
}

.preset-btn {
  width: 100%;
  margin-bottom: 10px;
  padding: 12px;
  background: #17a2b8;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
  font-weight: 500;
}

.preset-btn:hover {
  background: #117a8b;
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.preset-btn.lemonade {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.preset-btn.lemonade:hover {
  background: linear-gradient(135deg, #5568d3 0%, #63408b 100%);
}

.preset-btn.openai {
  background: linear-gradient(135deg, #10a37f 0%, #1a7f64 100%);
}

.preset-btn.openai:hover {
  background: linear-gradient(135deg, #0d8c6f 0%, #156b54 100%);
}

.info-box {
  background: #e8f4f8;
  border-left: 4px solid #17a2b8;
  padding: 15px;
  border-radius: 4px;
  margin-top: 20px;
}

.info-box h4 {
  margin: 0 0 10px 0;
  color: #17a2b8;
  font-size: 14px;
}

.info-box ul {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  line-height: 1.6;
  color: #555;
}

.info-box li {
  margin-bottom: 5px;
}

.info-box code {
  background: #fff;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  color: #d63384;
  font-size: 12px;
}

.info-box strong {
  color: #333;
}
</style>
