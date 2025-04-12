<script setup>
import { ref } from 'vue';
import { useMapStore } from '../stores/map';
import { useUserStore } from '../stores/user';
import * as shapefile from 'shapefile';
import * as turf from '@turf/turf';

const mapStore = useMapStore();
const userStore = useUserStore();

const uid = userStore.getUid;

const mapName = ref('');
const mapType = ref('');
const mediaType = ref('');
const description = ref('');
const publicTime = ref('');
const selectedFile = ref(null);
const selectedJsonFile = ref(null);
const preview = ref(null);
const isUploading = ref(false);
const error = ref(null);
const success = ref(false);

const processShapefile = async (file) => {
  try {
    // 读取 .shp 文件内容
    const arrayBuffer = await file.arrayBuffer();
    const source = await shapefile.open(arrayBuffer);
    
    // 获取所有要素
    const features = [];
    let feature;
    while ((feature = await source.read()) && feature.done === false) {
      features.push(feature.value);
    }
    
    // 创建 GeoJSON 特征集合
    const featureCollection = {
      type: 'FeatureCollection',
      features: features
    };
    
    // 计算边界框
    const bbox = turf.bbox(featureCollection);
    
    // 创建画布
    const canvas = document.createElement('canvas');
    const width = 800;
    const height = 600;
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    
    // 设置白色背景
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, width, height);
    
    // 计算缩放比例
    const xScale = width / (bbox[2] - bbox[0]);
    const yScale = height / (bbox[3] - bbox[1]);
    const scale = Math.min(xScale, yScale) * 0.9; // 留出10%边距
    
    // 绘制要素
    ctx.strokeStyle = 'black';
    ctx.lineWidth = 1;
    
    features.forEach(feature => {
      ctx.beginPath();
      const coordinates = feature.geometry.coordinates;
      
      if (feature.geometry.type === 'Polygon') {
        coordinates.forEach(ring => {
          ring.forEach((coord, i) => {
            const x = (coord[0] - bbox[0]) * scale + (width - (bbox[2] - bbox[0]) * scale) / 2;
            const y = height - ((coord[1] - bbox[1]) * scale + (height - (bbox[3] - bbox[1]) * scale) / 2);
            if (i === 0) {
              ctx.moveTo(x, y);
            } else {
              ctx.lineTo(x, y);
            }
          });
          ctx.closePath();
        });
      } else if (feature.geometry.type === 'LineString') {
        coordinates.forEach((coord, i) => {
          const x = (coord[0] - bbox[0]) * scale + (width - (bbox[2] - bbox[0]) * scale) / 2;
          const y = height - ((coord[1] - bbox[1]) * scale + (height - (bbox[3] - bbox[1]) * scale) / 2);
          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        });
      }
      
      ctx.stroke();
    });
    
    // 转换为base64
    return canvas.toDataURL('image/png');
  } catch (err) {
    console.error('Error processing shapefile:', err);
    throw new Error('无法处理矢量地图文件');
  }
};

const selectFile = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  selectedFile.value = file;
  
  try {
    if (file.name.toLowerCase().endsWith('.shp')) {
      // 处理矢量地图
      preview.value = await processShapefile(file);
      mapType.value = '矢量地图';
      mediaType.value = '矢量文件';
    } else {
      // 处理图片文件
      const reader = new FileReader();
      reader.onload = (e) => {
        preview.value = e.target.result;
        mapType.value = '栅格地图';
        mediaType.value = '图片文件';
      };
      reader.readAsDataURL(file);
    }
  } catch (err) {
    error.value = err.message;
    selectedFile.value = null;
    preview.value = null;
  }
};

const selectJsonFile = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  selectedJsonFile.value = file;
  
  try {
    const text = await file.text();
    const json = JSON.parse(text);
    
    // 填充表单数据
    mapName.value = json.map_name || '';
    mapType.value = json.map_type || '';
    mediaType.value = json.mediatype || '';
    description.value = json.description || '';
    publicTime.value = json.public_time ? json.public_time.split('T')[0] : '';
  } catch (err) {
    error.value = 'JSON 文件格式错误';
    console.error('Error parsing JSON:', err);
  }
};

const uploadMap = async () => {
  if (!uid || !selectedFile.value || !mapName.value.trim()) {
    error.value = '请输入地图名称并选择图片文件';
    return;
  }
  
  isUploading.value = true;
  error.value = null;
  success.value = false;
  
  try {
    let base64String;
    
    if (selectedFile.value.name.toLowerCase().endsWith('.shp')) {
      // 对于矢量地图，使用预览图像的base64
      base64String = preview.value.split(',')[1];
    } else {
      // 对于图片文件，直接读取
      const fileReader = new FileReader();
      base64String = await new Promise((resolve, reject) => {
        fileReader.onload = () => {
          resolve(fileReader.result.split(',')[1]);
        };
        fileReader.onerror = reject;
        fileReader.readAsDataURL(selectedFile.value);
      });
    }
    
    // Upload map
    const result = await mapStore.uploadMap(mapName.value, base64String);
    
    if (result.success) {
      // 如果上传成功，更新地图信息
      const mapDetails = {
        map_type: mapType.value,
        media_type: mediaType.value,
        description: description.value,
        public_time: publicTime.value ? `${publicTime.value}T00:00:00` : undefined
      };
      
      await mapStore.updateMapDetails(mapDetails);
      
      success.value = true;
      resetForm();
    } else {
      error.value = result.error || '上传失败';
    }
  } catch (err) {
    error.value = '上传过程中发生错误';
    console.error('Upload error:', err);
  } finally {
    isUploading.value = false;
  }
};

const resetForm = () => {
  mapName.value = '';
  mapType.value = '';
  mediaType.value = '';
  description.value = '';
  publicTime.value = '';
  selectedFile.value = null;
  selectedJsonFile.value = null;
  preview.value = null;
  error.value = null;
  success.value = false;
  
  // 重置文件输入
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => input.value = '');
};
</script>

<template>
  <div class="upload-container">
    <h3>添加新地图</h3>
    
    <div class="upload-content">
      <div class="upload-left">
        <div class="form-section">
          <h4>地图文件</h4>
          <div class="file-input-wrapper">
            <input 
              ref="fileInput"
              type="file"
              accept="image/*,.shp"
              @change="selectFile"
              :disabled="isUploading"
              class="file-input"
            />
            <button 
              class="file-select-btn" 
              @click="$refs.fileInput?.click()"
              :disabled="isUploading"
            >
              选择地图文件
            </button>
            <span class="file-name">{{ selectedFile?.name || '未选择文件' }}</span>
          </div>
        </div>

        <div class="form-section">
          <h4>描述文件（可选）</h4>
          <div class="file-input-wrapper">
            <input 
              ref="jsonInput"
              type="file"
              accept=".json"
              @change="selectJsonFile"
              :disabled="isUploading"
              class="file-input"
            />
            <button 
              class="file-select-btn" 
              @click="$refs.jsonInput?.click()"
              :disabled="isUploading"
            >
              选择 JSON 文件
            </button>
            <span class="file-name">{{ selectedJsonFile?.name || '未选择文件' }}</span>
          </div>
        </div>

        <div class="form-section">
          <h4>地图信息</h4>
          <div class="form-group">
            <label for="map-name">地图名称 <span class="required">*</span></label>
            <input 
              id="map-name" 
              v-model="mapName" 
              type="text" 
              placeholder="请输入地图名称"
              :disabled="isUploading"
            />
          </div>
          
          <div class="form-group">
            <label for="map-type">地图类型</label>
            <input 
              id="map-type" 
              v-model="mapType" 
              type="text" 
              placeholder="例如：矢量地图、栅格地图"
              :disabled="isUploading"
            />
          </div>
          
          <div class="form-group">
            <label for="media-type">媒介类型</label>
            <input 
              id="media-type" 
              v-model="mediaType" 
              type="text" 
              placeholder="例如：矢量文件、图片文件"
              :disabled="isUploading"
            />
          </div>
          
          <div class="form-group">
            <label for="public-time">发行时间</label>
            <input 
              id="public-time" 
              v-model="publicTime" 
              type="date" 
              :disabled="isUploading"
            />
          </div>
          
          <div class="form-group">
            <label for="description">地图描述</label>
            <textarea 
              id="description" 
              v-model="description" 
              placeholder="请输入地图描述"
              :disabled="isUploading"
              rows="4"
            ></textarea>
          </div>
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div v-if="success" class="success-message">
          地图上传成功！
        </div>
        
        <div class="button-group">
          <button 
            @click="uploadMap" 
            class="upload-btn" 
            :disabled="isUploading || !selectedFile || !mapName.trim()"
          >
            {{ isUploading ? '上传中...' : '上 传' }}
          </button>
          
          <button 
            @click="resetForm" 
            class="reset-btn" 
            :disabled="isUploading"
          >
            重置
          </button>
        </div>
      </div>
      
      <div class="upload-right">
        <div class="preview-container">
          <h4>预览</h4>
          <div class="preview-area" :class="{ 'has-preview': preview }">
            <img v-if="preview" :src="preview" alt="地图预览" class="preview-image" />
            <div v-else class="preview-placeholder">
              <span>选择地图文件后在此处显示预览</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-container {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

h3 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 24px;
}

h4 {
  margin: 0 0 15px 0;
  color: #34495e;
  font-size: 18px;
}

.upload-content {
  display: flex;
  gap: 30px;
  height: calc(100% - 60px);
}

.upload-left {
  flex: 1;
  min-width: 400px;
}

.upload-right {
  flex: 1;
  min-width: 400px;
}

.form-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.file-input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.file-input {
  display: none;
}

.file-select-btn {
  padding: 8px 16px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.file-select-btn:hover {
  background-color: #2980b9;
}

.file-name {
  color: #666;
  font-size: 14px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  color: #34495e;
  font-size: 14px;
}

.required {
  color: #e74c3c;
}

input[type="text"],
input[type="date"],
textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

textarea {
  resize: vertical;
  min-height: 100px;
}

.preview-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  height: 100%;
}

.preview-area {
  height: calc(100% - 40px);
  border: 2px dashed #ddd;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.preview-area.has-preview {
  border: none;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-placeholder {
  color: #999;
  text-align: center;
  padding: 20px;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.upload-btn, .reset-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  min-width: 100px;
}

.upload-btn {
  background-color: #2ecc71;
  color: white;
}

.upload-btn:hover {
  background-color: #27ae60;
}

.reset-btn {
  background-color: #e9ecef;
  color: #495057;
}

.reset-btn:hover {
  background-color: #dee2e6;
}

.upload-btn:disabled, .reset-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-message {
  padding: 10px;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 4px;
  color: #dc2626;
  margin-bottom: 15px;
}

.success-message {
  padding: 10px;
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 4px;
  color: #15803d;
  margin-bottom: 15px;
}
</style> 