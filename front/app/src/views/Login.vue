<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../stores/user';

const router = useRouter();
const userStore = useUserStore();

const email = ref('');
const password = ref('');
const isLoading = ref(false);
const errorMessage = ref('');

const login = async () => {
  if (!email.value.trim() || !password.value) {
    errorMessage.value = '邮箱和密码不能为空';
    return;
  }
  
  isLoading.value = true;
  errorMessage.value = '';
  
  try {
    const success = await userStore.login(email.value, password.value);
    if (success) {
      router.push('/main');
    } else {
      errorMessage.value = userStore.error || '登录失败';
    }
  } catch (error) {
    errorMessage.value = '系统错误，请稍后再试';
    console.error('Login error:', error);
  } finally {
    isLoading.value = false;
  }
};

const goToRegister = () => {
  router.push('/register');
};
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <div class="header">
        <div class="logo">
          <img src="/logo.png" alt="Logo" />
        </div>
        <div class="title-wrapper">
          <h1>地图收藏家</h1>
          <p>Geographic Collection System</p>
        </div>
      </div>
      
      <div class="separator"></div>
      
      <div class="form">
        <div class="form-group">
          <label for="email">邮箱:</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="请输入注册邮箱"
            @keyup.enter="login"
          />
        </div>
        <div class="form-group">
          <label for="password">密码:</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码"
            @keyup.enter="login"
          />
        </div>
        
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
        
        <div class="buttons">
          <button 
            @click="login" 
            class="btn-primary"
            :disabled="isLoading"
          >
            {{ isLoading ? '登录中...' : '登 录' }}
          </button>
          <button 
            @click="goToRegister" 
            class="btn-secondary"
            :disabled="isLoading"
          >
            注 册
          </button>
        </div>
      </div>
      
      <div class="footer">
        <p>探索地理之美 · 收藏世界精彩</p>
        <p>developer: wuboy</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: #f0f2f5;
}

.login-card {
  width: 430px;
  padding: 30px;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.logo {
  flex: 0 0 100px;
}

.logo img {
  width: 80px;
  height: 80px;
  object-fit: contain;
}

.title-wrapper {
  flex: 1;
}

.title-wrapper h1 {
  font-size: 28px;
  font-weight: bold;
  color: #2c3e50;
  margin: 0 0 6px 0;
}

.title-wrapper p {
  font-size: 14px;
  color: #7f8c8d;
  margin: 0;
}

.separator {
  height: 1px;
  background-color: #bdc3c7;
  margin: 20px 0;
}

.form {
  margin-bottom: 25px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 2px solid #ecf0f1;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
}

.form-group input:focus {
  border-color: #3498db;
}

.error-message {
  color: #e74c3c;
  font-size: 14px;
  margin: 10px 0;
  padding: 8px;
  background-color: rgba(231, 76, 60, 0.1);
  border-radius: 4px;
}

.buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
}

.btn-primary, .btn-secondary {
  padding: 12px 30px;
  border-radius: 6px;
  font-weight: bold;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
  border: none;
}

.btn-primary {
  background-color: #3498db;
  color: white;
}

.btn-primary:hover {
  background-color: #2980b9;
}

.btn-secondary {
  background-color: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background-color: #7f8c8d;
}

.btn-primary:disabled, .btn-secondary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.footer {
  text-align: center;
  font-size: 12px;
  color: #7f8c8d;
  margin-top: 20px;
}

.footer p {
  margin: 2px 0;
}
</style> 