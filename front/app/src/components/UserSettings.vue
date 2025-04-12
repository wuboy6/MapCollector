<script setup>
import { ref, onMounted } from 'vue';
import { useUserStore } from '../stores/user';

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  onClose: {
    type: Function,
    required: true
  }
});

const userStore = useUserStore();
const newName = ref('');
const newEmail = ref('');
const isUpdating = ref(false);
const success = ref(false);
const error = ref(null);

// Initialize with current values
onMounted(() => {
  newName.value = userStore.getUserName || '';
});

const updateProfile = async () => {
  isUpdating.value = true;
  error.value = null;
  success.value = false;
  
  try {
    if (newName.value && newName.value !== userStore.getUserName) {
      const nameResult = await userStore.updateUserName(newName.value);
      if (!nameResult) {
        error.value = '更新用户名失败';
        return;
      }
    }
    
    if (newEmail.value) {
      const emailResult = await userStore.updateUserEmail(newEmail.value);
      if (!emailResult) {
        error.value = '更新邮箱失败';
        return;
      }
      newEmail.value = '';
    }
    
    success.value = true;
  } catch (err) {
    error.value = '更新信息时发生错误';
    console.error('Update profile error:', err);
  } finally {
    isUpdating.value = false;
  }
};

const handleClose = () => {
  success.value = false;
  error.value = null;
  newEmail.value = '';
  props.onClose();
};
</script>

<template>
  <div v-if="isOpen" class="modal-backdrop" @click="handleClose">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>用户设置</h3>
        <button class="close-btn" @click="handleClose">✕</button>
      </div>
      
      <div class="modal-body">
        <div class="form-group">
          <label for="username">用户名称</label>
          <input 
            id="username" 
            v-model="newName" 
            type="text" 
            placeholder="输入新的用户名"
            :disabled="isUpdating"
          />
        </div>
        
        <div class="form-group">
          <label for="email">电子邮箱</label>
          <input 
            id="email" 
            v-model="newEmail" 
            type="email" 
            placeholder="输入新的邮箱地址"
            :disabled="isUpdating"
          />
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div v-if="success" class="success-message">
          个人信息已成功更新
        </div>
      </div>
      
      <div class="modal-footer">
        <button 
          @click="updateProfile" 
          class="update-btn"
          :disabled="isUpdating || (!newName && !newEmail)"
        >
          {{ isUpdating ? '更新中...' : '更新信息' }}
        </button>
        <button @click="handleClose" class="cancel-btn">取消</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #343a40;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  color: #6c757d;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #495057;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.error-message {
  padding: 10px;
  background-color: rgba(231, 76, 60, 0.1);
  border-radius: 4px;
  color: #e74c3c;
  font-size: 14px;
  margin-top: 15px;
}

.success-message {
  padding: 10px;
  background-color: rgba(46, 204, 113, 0.1);
  border-radius: 4px;
  color: #27ae60;
  font-size: 14px;
  margin-top: 15px;
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.update-btn, .cancel-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.update-btn {
  background-color: #3498db;
  color: white;
}

.update-btn:hover {
  background-color: #2980b9;
}

.update-btn:disabled {
  background-color: #a0d0f0;
  cursor: not-allowed;
}

.cancel-btn {
  background-color: #e9ecef;
  color: #495057;
}

.cancel-btn:hover {
  background-color: #dee2e6;
}
</style> 