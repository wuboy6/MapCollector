<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useMapStore } from '../stores/map';
import { useUserStore } from '../stores/user';

const mapStore = useMapStore();
const userStore = useUserStore();

const notes = computed(() => {
  const notesList = mapStore.notes || [];
  console.log('Current notes:', notesList);
  return notesList;
});
const newNote = ref('');
const loading = ref(false);
const isSending = ref(false);
const error = ref(null);

const uid = userStore.getUid;

// Format timestamp (YYYY-MM-DD HH:MM:SS)
const formatTime = (timeStr) => {
  if (!timeStr) return '';
  try {
    const date = new Date(timeStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    console.error('Error formatting time:', e);
    return timeStr;
  }
};

const fetchNotes = async () => {
  if (!uid) {
    console.log('No user ID available');
    return;
  }
  
  if (!mapStore.currentMap) {
    console.log('No current map selected');
    return;
  }
  
  loading.value = true;
  error.value = null;
  
  try {
    console.log('Fetching notes for map:', mapStore.currentMap.mapid);
    await mapStore.fetchMapNotes(uid);
  } catch (err) {
    error.value = '无法加载评论';
    console.error('Failed to fetch notes:', err);
  } finally {
    loading.value = false;
  }
};

const submitNote = async () => {
  if (!uid || !newNote.value.trim()) return;
  
  isSending.value = true;
  error.value = null;
  
  try {
    const success = await mapStore.addNote(uid, newNote.value.trim());
    if (success) {
      newNote.value = '';
    } else {
      error.value = '评论发送失败';
    }
  } catch (err) {
    error.value = '评论发送失败';
    console.error('Failed to submit note:', err);
  } finally {
    isSending.value = false;
  }
};

// Watch for current map changes to refresh notes
watch(() => mapStore.currentMap, () => {
  if (mapStore.currentMap) {
    fetchNotes();
  }
});

// Initial fetch
onMounted(() => {
  if (mapStore.currentMap) {
    fetchNotes();
  }
});
</script>

<template>
  <div class="notes-container">
    <div class="notes-header">
      <h3>地图评论</h3>
      <button class="refresh-btn" @click="fetchNotes" :disabled="loading">
        {{ loading ? '加载中...' : '刷新' }}
      </button>
    </div>
    
    <div class="notes-content">
      <div v-if="loading" class="notes-loading">
        加载评论中...
      </div>
      
      <div v-else-if="error" class="notes-error">
        {{ error }}
      </div>
      
      <div v-else-if="notes.length === 0" class="notes-empty">
        暂无评论，添加第一条评论吧
      </div>
      
      <div v-else class="notes-list">
        <div v-for="note in notes" :key="note.noteid" class="note-item">
          <div class="note-header">
            <span class="note-user">{{ note.userName || '未知用户' }}</span>
            <span class="note-time">{{ formatTime(note.time) }}</span>
          </div>
          <div class="note-content">{{ note.content }}</div>
          <div v-if="!note.content && !note.time" class="note-error">
            评论数据格式错误
          </div>
        </div>
      </div>
    </div>
    
    <div class="note-input-container">
      <textarea 
        v-model="newNote" 
        placeholder="添加评论..." 
        rows="3"
        :disabled="isSending"
      ></textarea>
      <button 
        @click="submitNote" 
        :disabled="!newNote.trim() || isSending"
        class="submit-btn"
      >
        {{ isSending ? '发送中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.notes-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background-color: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
}

.notes-header {
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e9ecef;
}

.notes-header h3 {
  margin: 0;
  font-size: 16px;
  color: #343a40;
}

.refresh-btn {
  padding: 4px 8px;
  font-size: 12px;
  background-color: #e9ecef;
  border: 1px solid #ced4da;
  border-radius: 4px;
  cursor: pointer;
}

.refresh-btn:hover {
  background-color: #dee2e6;
}

.notes-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.notes-loading, .notes-error, .notes-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #6c757d;
  text-align: center;
  font-size: 14px;
}

.notes-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.note-item {
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #3498db;
}

.note-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.note-user {
  font-weight: 500;
  color: #495057;
  font-size: 14px;
}

.note-time {
  color: #6c757d;
  font-size: 12px;
}

.note-content {
  color: #343a40;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.note-input-container {
  padding: 12px;
  border-top: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.note-input-container textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  resize: none;
  font-size: 14px;
  font-family: inherit;
}

.note-input-container textarea:focus {
  outline: none;
  border-color: #3498db;
}

.submit-btn {
  align-self: flex-end;
  padding: 6px 12px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.submit-btn:hover {
  background-color: #2980b9;
}

.submit-btn:disabled {
  background-color: #a0d0f0;
  cursor: not-allowed;
}

.note-error {
  color: #dc3545;
  font-size: 12px;
  margin-top: 4px;
}
</style> 