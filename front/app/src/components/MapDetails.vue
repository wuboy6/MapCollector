<script setup>
import { ref, computed } from 'vue';
import { useMapStore } from '../stores/map';
import MapChangeHistory from './MapChangeHistory.vue';

const mapStore = useMapStore();
const isEditing = ref(false);
const isSaving = ref(false);
const errorMessage = ref('');
const showChanges = ref(false);

// 编辑表单数据
const editForm = ref({
  map_name: '',
  map_type: '',
  media_type: '',
  description: ''
});

// 地图详情
const mapDetails = computed(() => mapStore.mapDetails || {});

// 开始编辑
const startEditing = () => {
  if (mapDetails.value) {
    editForm.value = {
      map_name: mapDetails.value.map_name || '',
      map_type: mapDetails.value.map_type || '',
      media_type: mapDetails.value.media_type || '',
      description: mapDetails.value.description || ''
    };
    isEditing.value = true;
  }
};

// 保存编辑
const saveEdit = async () => {
  try {
    isSaving.value = true;
    errorMessage.value = '';
    await mapStore.updateMapDetails(editForm.value);
    isEditing.value = false;
  } catch (error) {
    console.error('Failed to update map details:', error);
    errorMessage.value = '保存失败，请重试';
  } finally {
    isSaving.value = false;
  }
};

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false;
};

// 格式化日期
const formatDate = (isoString) => {
  if (!isoString) return '未设置';
  try {
    const date = new Date(isoString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return '日期格式错误';
  }
};

// 切换修改记录显示状态
const toggleChanges = () => {
  showChanges.value = !showChanges.value;
};
</script>

<template>
  <div class="map-details">
    <div class="details-header">
      <h3>地图详情</h3>
      <div class="header-actions">
        <button v-if="!isEditing" class="edit-btn" @click="startEditing">
          修改信息
        </button>
        <button class="changes-btn" @click="toggleChanges">
          {{ showChanges ? '隐藏修改记录' : '显示修改记录' }}
        </button>
      </div>
    </div>

    <div v-if="!isEditing" class="details-content">
      <div class="detail-item">
        <span class="label">地图名称：</span>
        <span class="value">{{ mapDetails?.map_name || '未设置' }}</span>
      </div>
      <div class="detail-item">
        <span class="label">地图类型：</span>
        <span class="value">{{ mapDetails?.map_type || '未设置' }}</span>
      </div>
      <div class="detail-item">
        <span class="label">媒体类型：</span>
        <span class="value">{{ mapDetails?.media_type || '未设置' }}</span>
      </div>
      <div class="detail-item">
        <span class="label">出版时间：</span>
        <span class="value">{{ formatDate(mapDetails?.public_time) }}</span>
      </div>
      <div class="detail-item">
        <span class="label">收藏时间：</span>
        <span class="value">{{ formatDate(mapDetails?.collect_time) }}</span>
      </div>
      <div class="detail-item description">
        <span class="label">描述：</span>
        <span class="value">{{ mapDetails?.description || '未设置' }}</span>
      </div>
    </div>

    <div v-else class="edit-form">
      <div class="form-group">
        <label>地图名称</label>
        <input type="text" v-model="editForm.map_name" placeholder="输入地图名称">
      </div>
      <div class="form-group">
        <label>地图类型</label>
        <input type="text" v-model="editForm.map_type" placeholder="输入地图类型">
      </div>
      <div class="form-group">
        <label>媒体类型</label>
        <input type="text" v-model="editForm.media_type" placeholder="输入媒体类型">
      </div>
      <div class="form-group">
        <label>出版时间</label>
        <input type="text" :value="formatDate(mapDetails?.public_time)" disabled>
      </div>
      <div class="form-group">
        <label>收藏时间</label>
        <input type="text" :value="formatDate(mapDetails?.collect_time)" disabled>
      </div>
      <div class="form-group">
        <label>描述</label>
        <textarea v-model="editForm.description" placeholder="输入地图描述"></textarea>
      </div>
      <div class="form-actions">
        <button class="save-btn" @click="saveEdit" :disabled="isSaving">
          {{ isSaving ? '保存中...' : '保存' }}
        </button>
        <button class="cancel-btn" @click="cancelEdit" :disabled="isSaving">取消</button>
      </div>
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </div>
    
    <!-- 修改记录组件，只在 showChanges 为 true 时显示 -->
    <MapChangeHistory v-if="showChanges" />
  </div>
</template>

<style scoped>
.map-details {
  padding: 20px;
  background-color: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.details-header h3 {
  margin: 0;
  color: #343a40;
}

.edit-btn {
  padding: 6px 12px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.edit-btn:hover {
  background-color: #2980b9;
}

.details-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-item {
  display: flex;
  gap: 10px;
}

.detail-item.description {
  flex-direction: column;
}

.label {
  font-weight: 500;
  color: #495057;
  min-width: 80px;
}

.value {
  color: #212529;
}

.edit-form {
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
  font-weight: 500;
  color: #495057;
}

.form-group input,
.form-group textarea {
  padding: 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.form-group textarea {
  min-height: 100px;
  resize: vertical;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.save-btn,
.cancel-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.save-btn {
  background-color: #28a745;
  color: white;
}

.save-btn:hover {
  background-color: #218838;
}

.cancel-btn {
  background-color: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background-color: #5a6268;
}

.form-group input:disabled {
  background-color: #e9ecef;
  cursor: not-allowed;
  color: #6c757d;
}

.error-message {
  color: #dc3545;
  margin-top: 10px;
  font-size: 14px;
}

.save-btn:disabled,
.cancel-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.changes-btn {
  padding: 6px 12px;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.changes-btn:hover {
  background-color: #5a6268;
}
</style> 