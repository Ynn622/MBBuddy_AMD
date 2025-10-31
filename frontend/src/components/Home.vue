<template>
  <div>
    <!-- 導覽列 -->
    <nav class="navbar">
      <div class="nav-container">
        <div class="nav-brand" @click="router.push('/')" aria-label="返回主頁">
          <img src="/icon.png" alt="MBBuddy" class="brand-icon" />
          <!-- <h1>MBBuddy</h1> -->
          <!-- <span>互動問答平台</span> -->
        </div>
        <div class="nav-actions">
          <button class="btn btn-icon" @click="showAIConfigPanel = true" title="AI 設定">
            <span>⚙️</span>
          </button>
          <button class="btn btn-outline" @click="showJoinModal = true">加入討論</button>
          <button class="btn btn-primary" @click="showCreateModal = true">建立討論室</button>
        </div>
      </div>
    </nav>

    <!-- 主內容 -->
    <main class="main-content">
      <section class="hero">
        <div class="hero-content">
          <h2>讓每個聲音都被聽見</h2>
          <p>建立互動討論室，讓參與者匿名提問、投票，讓討論更有參與感</p>
          <div class="hero-actions">
            <button class="btn btn-primary btn-large" @click="showCreateModal = true">
              <span>➕</span>
              建立新討論室
            </button>
          </div>
        </div>
      </section>
      <section class="features">
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">❓</div>
            <h3>匿名提問</h3>
            <p>參與者可以匿名提出問題，消除發言障礙</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">👍</div>
            <h3>即時投票</h3>
            <p>對問題進行投票，熱門問題自動排序</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3>AI即時統整</h3>
            <p>本地AI及時統整大家意見並給出建議</p>
          </div>
        </div>
      </section>
    </main>

    <!-- 建立討論室 Modal -->
    <CreateRoomModal 
      :visible="showCreateModal" 
      @close="showCreateModal = false"
      @create-success="handleCreateSuccess"
      @show-notification="handleShowNotification"
    />

    <!-- 加入討論室 Modal -->
    <JoinRoomModal
      :visible="showJoinModal"
      @close="showJoinModal = false"
      @join-success="handleJoinSuccess"
      @show-notification="handleShowNotification"
    />

    <!-- AI 配置面板 Overlay -->
    <Transition name="overlay">
      <div v-if="showAIConfigPanel" class="overlay" @click.self="showAIConfigPanel = false">
        <div class="overlay-content">
          <button class="overlay-close" @click="showAIConfigPanel = false">&times;</button>
          <AIConfigPanel />
        </div>
      </div>
    </Transition>

    <!-- 通知訊息 -->
    <TransitionGroup name="fade">
      <div
        v-for="(msg, i) in notifications"
        :key="i"
        :class="['notification', `notification-${msg.type}`]"
        style="position: fixed; top: 20px; right: 20px; z-index: 2000; margin-bottom: 12px;"
      >
        <span>{{ msg.text }}</span>
        <button @click="removeNotification(i)">&times;</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import CreateRoomModal from './CreateRoomModal.vue';
import JoinRoomModal from './JoinRoomModal.vue';
import AIConfigPanel from './AIConfigPanel.vue';

const router = useRouter();

// --- Modal 狀態 ---
const showCreateModal = ref(false);
const showJoinModal = ref(false);
const showAIConfigPanel = ref(false);

// --- 通知 ---
const notifications = ref([]);

function handleShowNotification({ text, type }) {
  showNotification(text, type);
}

function handleCreateSuccess(roomData) {
  showNotification(`討論室建立成功！代碼：${roomData.code}`, 'success');
  // 立刻跳轉到主持人頁面
  router.push(`/host?room=${roomData.code}&new=true`);
}

function handleJoinSuccess(roomCode) {
  showNotification('正在加入討論室...', 'success');
  setTimeout(() => {
    router.push(`/participant?room=${roomCode}`);
  }, 1000);
}

// --- 通知管理 ---
function showNotification(text, type = 'info') {
  notifications.value.push({ text, type });
  setTimeout(() => notifications.value.shift(), 4000);
}
function removeNotification(i) {
  notifications.value.splice(i, 1);
}
</script>

<style scoped>
@import url('../assets/styles.css');

.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* AI 配置面板 Overlay */
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.overlay-content {
  position: relative;
  background: white;
  border-radius: 12px;
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.overlay-close {
  position: absolute;
  top: 15px;
  right: 15px;
  background: transparent;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
  z-index: 10;
}

.overlay-close:hover {
  background: #f0f0f0;
  color: #333;
}

/* Overlay 動畫 */
.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.3s ease;
}

.overlay-enter-active .overlay-content,
.overlay-leave-active .overlay-content {
  transition: transform 0.3s ease;
}

.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}

.overlay-enter-from .overlay-content,
.overlay-leave-to .overlay-content {
  transform: scale(0.9);
}

/* 設定按鈕樣式 */
.btn-icon {
  padding: 5px 12px;
  background: transparent;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 20px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.btn-icon:hover {
  background: #f5f5f5;
  border-color: #007bff;
  transform: rotate(45deg);
}

.btn-icon span {
  display: block;
}

/* 響應式設計 - 只保留 Home.vue 頁面本身需要的 */
@media (max-width: 480px) {
  .nav-actions {
    flex-direction: row;
    gap: 8px;
  }
  
  .nav-actions .btn {
    font-size: 12px;
    padding: 8px 12px;
  }

  .btn-icon {
    padding: 6px 10px;
    font-size: 18px;
  }

  .overlay-content {
    max-width: 95%;
  }
}
</style>
