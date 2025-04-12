<script setup>
import { ref, watch, computed } from 'vue';

const props = defineProps({
  mapImage: {
    type: String,
    default: null
  },
  mapDetails: {
    type: Object,
    default: () => ({})
  }
});

const imageUrl = computed(() => {
  if (!props.mapImage) {
    console.debug('No map image data provided');
    return null;
  }
  
  try {
    return `data:image/png;base64,${props.mapImage}`;
  } catch (err) {
    console.error('Error creating image URL:', err);
    return null;
  }
});

const loading = ref(false);
const loaded = ref(false);
const error = ref(null);
const imageOpacity = ref(0);

const handleImageError = (e) => {
  console.error('Image loading error:', e);
  error.value = '无法加载地图图像';
  loading.value = false;
  loaded.value = false;
  imageOpacity.value = 0;
};

const handleImageLoad = () => {
  loading.value = false;
  loaded.value = true;
  imageOpacity.value = 1;
};

watch(() => props.mapImage, (newValue) => {
  if (newValue) {
    loading.value = true;
    loaded.value = false;
    imageOpacity.value = 0;
    error.value = null;
    
    // 预加载图片
    if (typeof window !== 'undefined') {
      const img = new Image();
      img.onload = handleImageLoad;
      img.onerror = handleImageError;
      img.src = `data:image/png;base64,${newValue}`;
    }
  } else {
    loading.value = false;
    loaded.value = false;
    imageOpacity.value = 0;
  }
});
</script>

<template>
  <div class="map-display-container">
    <div v-if="loading && !loaded" class="map-loading">
      <div class="loading-spinner"></div>
      <div>正在加载地图...</div>
    </div>
    
    <div v-else-if="error" class="map-error">
      {{ error }}
    </div>
    
    <div v-else-if="!imageUrl" class="no-map">
      暂无地图显示
    </div>
    
    <div v-else class="map-image-container">
      <img 
        :src="imageUrl" 
        class="map-image" 
        alt="地图"
        @load="handleImageLoad"
        @error="handleImageError"
        :style="{ opacity: imageOpacity, transition: 'opacity 0.3s ease-in-out' }"
      />
      
      <div v-if="Object.keys(mapDetails).length > 0" class="map-info-overlay">
        <h3>{{ mapDetails.map_name || '未命名地图' }}</h3>
        <p v-if="mapDetails.map_type">类型: {{ mapDetails.map_type }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-display-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  overflow: hidden;
}

.map-loading, .map-error, .no-map {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #6c757d;
  font-size: 16px;
  padding: 20px;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #3498db;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.map-image-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
}

.map-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  opacity: 0;
}

.map-info-overlay {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 10px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.map-info-overlay h3 {
  margin: 0 0 5px 0;
  font-size: 16px;
  color: #343a40;
}

.map-info-overlay p {
  margin: 0;
  font-size: 14px;
  color: #495057;
}
</style> 