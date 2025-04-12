<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../stores/user';

const router = useRouter();
const userStore = useUserStore();

const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const isLoading = ref(false);
const errorMessage = ref('');

const register = async () => {
  if (!email.value.trim()) {
    errorMessage.value = '邮箱不能为空';
    return;
  }
  
  if (!password.value) {
    errorMessage.value = '密码不能为空';
    return;
  }
  
  if (password.value !== confirmPassword.value) {
    errorMessage.value = '两次密码输入不一致';
    return;
  }
  
  isLoading.value = true;
  errorMessage.value = '';
  
  try {
    const result = await userStore.register(email.value, password.value);
    if (result.success) {
      // 注册成功，跳转到登录页面
      router.push({
        path: '/login',
        query: { email: email.value, registered: 'true' }
      });
    } else {
      errorMessage.value = result.error || '注册失败';
    }
  } catch (error) {
    errorMessage.value = '系统错误，请稍后再试';
    console.error('Registration error:', error);
  } finally {
    isLoading.value = false;
  }
};

const goToLogin = () => {
  router.push('/login');
};
</script>

<template>
  <div class="register-container">
    <div class="register-card">
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
            placeholder="请输入邮箱地址"
          />
        </div>
        <div class="form-group">
          <label for="password">密码:</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码"
          />
        </div>
        <div class="form-group">
          <label for="confirmPassword">确认密码:</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            @keyup.enter="register"
          />
        </div>
        
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
        
        <div class="buttons">
          <button 
            @click="register" 
            class="btn-primary"
            :disabled="isLoading"
          >
            {{ isLoading ? '注册中...' : '注 册' }}
          </button>
          <button 
            @click="goToLogin" 
            class="btn-secondary"
            :disabled="isLoading"
          >
            返回登录
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
.register-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: #f0f2f5;
}

.register-card {
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