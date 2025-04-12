<script setup>
import { ref, onMounted, watch } from 'vue';
import { useMapStore } from '../stores/map';
import { useUserStore } from '../stores/user';

const props = defineProps({
  onMapSelected: {
    type: Function,
    required: true
  }
});

const mapStore = useMapStore();
const userStore = useUserStore();
const uid = userStore.getUid;

const mapsByType = ref({});
const expandedTypes = ref({});
const loading = ref(false);
const selectedMapId = ref(null);

const fetchMaps = async () => {
  loading.value = true;
  await mapStore.fetchMapList();
  mapsByType.value = mapStore.getMapByType;
  
  // Expand all map types by default
  Object.keys(mapsByType.value).forEach(type => {
    expandedTypes.value[type] = true;
  });
  
  loading.value = false;
};

const toggleMapType = (type) => {
  expandedTypes.value[type] = !expandedTypes.value[type];
};

const selectMap = async (mapId) => {
  if (!uid) {
    console.error('No user ID available, cannot select map');
    return;
  }
  
  if (!mapId) {
    console.error('Invalid map ID');
    return;
  }
  
  // 如果已经选择了这个地图并且加载中，则不进行操作
  if (selectedMapId.value === mapId && loading.value) {
    console.log('Map already being loaded, ignoring duplicate request');
    return;
  }
  
  // 立即标记选中状态，提高UI响应性
  selectedMapId.value = mapId;
  loading.value = true;
  
  try {
    console.log(`Selecting map: ${mapId}`);
    let success = await mapStore.setCurrentMap(uid, mapId);
    
    if (success) {
      console.log(`Successfully loaded map: ${mapId}`);
      props.onMapSelected(mapId);
    } else {
      console.error(`Failed to load map: ${mapId}`, mapStore.error);
      // 使用更友好的错误提示
      if (mapStore.error) {
        // 显示轻量级提示，不使用弹窗阻止用户操作
        const errorText = document.createElement('div');
        errorText.className = 'map-error-toast';
        errorText.innerText = `加载失败: ${mapStore.error}`;
        document.body.appendChild(errorText);
        
        // 3秒后自动消失
        setTimeout(() => {
          document.body.removeChild(errorText);
        }, 3000);
      }
    }
  } catch (error) {
    console.error('Error selecting map:', error);
  } finally {
    loading.value = false;
  }
};

// Watch for map list changes
watch(() => mapStore.mapList, () => {
  mapsByType.value = mapStore.getMapByType;
});

// Initial fetch
onMounted(fetchMaps);
</script>

<template>
  <div class="map-list-container">
    <div class="map-list-header">
      <h3>地图列表</h3>
      <button class="refresh-btn" @click="fetchMaps" :disabled="loading">
        {{ loading ? '加载中...' : '刷新' }}
      </button>
    </div>
    
    <div v-if="loading && !Object.keys(mapsByType).length" class="loading">
      <div class="loading-dot"></div>
      <div class="loading-dot"></div>
      <div class="loading-dot"></div>
      加载地图列表中...
    </div>
    
    <div v-else-if="Object.keys(mapsByType).length === 0" class="empty-state">
      暂无可用地图
    </div>
    
    <div v-else class="map-tree">
      <div v-for="(maps, type) in mapsByType" :key="type" class="map-type">
        <div class="type-header" @click="toggleMapType(type)">
          <span class="expand-icon">{{ expandedTypes[type] ? '▼' : '►' }}</span>
          <span class="type-name">{{ type }}</span>
          <span class="count">({{ maps.length }})</span>
        </div>
        
        <div v-if="expandedTypes[type]" class="map-items">
          <div 
            v-for="map in maps" 
            :key="map.mapid" 
            class="map-item"
            :class="{ 'selected': selectedMapId === map.mapid, 'loading': selectedMapId === map.mapid && loading }"
            @click="selectMap(map.mapid)"
          >
            {{ map.map_name || '未命名' }}
            <span v-if="selectedMapId === map.mapid && loading" class="mini-loader"></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #f8f9fa;
  border-left: 1px solid #e9ecef;
}

.map-list-header {
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e9ecef;
}

.map-list-header h3 {
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

.refresh-btn:hover:not(:disabled) {
  background-color: #dee2e6;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading, .empty-state {
  padding: 16px;
  color: #6c757d;
  text-align: center;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.loading-dot {
  width: 8px;
  height: 8px;
  background-color: #3498db;
  border-radius: 50%;
  display: inline-block;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}

.map-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.map-type {
  margin-bottom: 12px;
}

.type-header {
  display: flex;
  align-items: center;
  padding: 8px;
  background-color: #e9ecef;
  border-radius: 4px;
  cursor: pointer;
  user-select: none;
}

.type-header:hover {
  background-color: #dee2e6;
}

.expand-icon {
  margin-right: 8px;
  font-size: 10px;
  color: #495057;
}

.type-name {
  font-weight: 500;
  color: #495057;
}

.count {
  margin-left: 8px;
  font-size: 12px;
  color: #6c757d;
}

.map-items {
  margin-top: 4px;
  margin-left: 16px;
}

.map-item {
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 4px;
  cursor: pointer;
  color: #495057;
  transition: background-color 0.2s, color 0.2s;
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.map-item:hover {
  background-color: #e9ecef;
}

.map-item.selected {
  background-color: #cce5ff;
  color: #004085;
  font-weight: 500;
}

.map-item.loading {
  background-color: #e2f0ff;
}

.mini-loader {
  width: 10px;
  height: 10px;
  border: 2px solid #3498db;
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 轻量级错误提示样式 */
:global(.map-error-toast) {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background-color: rgba(231, 76, 60, 0.9);
  color: white;
  padding: 10px 15px;
  border-radius: 4px;
  z-index: 1000;
  font-size: 14px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  animation: slide-in-out 3s forwards;
}

@keyframes slide-in-out {
  0% { transform: translateX(100%); opacity: 0; }
  10% { transform: translateX(0); opacity: 1; }
  90% { transform: translateX(0); opacity: 1; }
  100% { transform: translateX(100%); opacity: 0; }
}
</style>