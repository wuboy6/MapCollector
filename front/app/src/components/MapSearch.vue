<script setup>
import { ref } from 'vue';
import { useMapStore } from '../stores/map';
import { useUserStore } from '../stores/user';

const emit = defineEmits(['searchComplete']);

const mapStore = useMapStore();
const userStore = useUserStore();

const uid = userStore.getUid;
const isSearching = ref(false);
const searchComplete = ref(false);
const error = ref(null);

const searchParams = ref({
  query_name: '',
  query_type: '',
  query_media: '',
  query_desc: '',
  top_n: 10
});

const search = async () => {
  if (!uid) return;
  
  // Check if at least one search parameter is provided
  const hasSearchParam = Object.entries(searchParams.value)
    .filter(([key]) => key !== 'top_n')  // Exclude top_n from check
    .some(([_, value]) => value.trim() !== '');
    
  if (!hasSearchParam) {
    error.value = '请至少输入一个搜索条件';
    return;
  }
  
  isSearching.value = true;
  error.value = null;
  searchComplete.value = false;
  
  try {
    const success = await mapStore.searchMaps(uid, searchParams.value);
    if (success) {
      searchComplete.value = true;
      emit('searchComplete'); // 发出搜索完成事件
    }
  } catch (err) {
    error.value = '搜索失败';
    console.error('Search error:', err);
  } finally {
    isSearching.value = false;
  }
};

const resetSearch = () => {
  searchParams.value = {
    query_name: '',
    query_type: '',
    query_media: '',
    query_desc: '',
    top_n: 10
  };
  searchComplete.value = false;
  error.value = null;
};
</script>

<template>
  <div class="search-container">
    <h3>地图检索</h3>
    
    <div class="search-form">
      <div class="form-group">
        <label for="query_name">地图名称</label>
        <input 
          id="query_name" 
          v-model="searchParams.query_name" 
          type="text" 
          placeholder="输入地图名称关键词"
        />
      </div>
      
      <div class="form-group">
        <label for="query_type">地图类型</label>
        <input 
          id="query_type" 
          v-model="searchParams.query_type" 
          type="text" 
          placeholder="输入地图类型"
        />
      </div>
      
      <div class="form-group">
        <label for="query_media">媒体类型</label>
        <input 
          id="query_media" 
          v-model="searchParams.query_media" 
          type="text" 
          placeholder="输入媒体类型"
        />
      </div>
      
      <div class="form-group">
        <label for="query_desc">描述关键词</label>
        <input 
          id="query_desc" 
          v-model="searchParams.query_desc" 
          type="text" 
          placeholder="输入描述关键词"
        />
      </div>
      
      <div class="form-group">
        <label for="top_n">结果数量</label>
        <input 
          id="top_n" 
          v-model.number="searchParams.top_n" 
          type="number" 
          min="1" 
          max="100"
        />
      </div>
      
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
      
      <div v-if="searchComplete" class="success-message">
        搜索完成，请查看当前显示的地图
      </div>
      
      <div class="button-group">
        <button 
          @click="search" 
          class="search-btn" 
          :disabled="isSearching"
        >
          {{ isSearching ? '搜索中...' : '搜 索' }}
        </button>
        
        <button 
          @click="resetSearch" 
          class="reset-btn" 
          :disabled="isSearching"
        >
          重置
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-container {
  padding: 20px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #343a40;
  font-size: 18px;
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 10px;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-size: 14px;
  color: #495057;
}

.form-group input {
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.search-btn, .reset-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.search-btn {
  background-color: #3498db;
  color: white;
}

.search-btn:hover {
  background-color: #2980b9;
}

.reset-btn {
  background-color: #e9ecef;
  color: #495057;
}

.reset-btn:hover {
  background-color: #dee2e6;
}

.search-btn:disabled, .reset-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-message {
  padding: 10px;
  background-color: rgba(231, 76, 60, 0.1);
  border-radius: 4px;
  color: #e74c3c;
  font-size: 14px;
}

.success-message {
  padding: 10px;
  background-color: rgba(46, 204, 113, 0.1);
  border-radius: 4px;
  color: #27ae60;
  font-size: 14px;
}
</style> 