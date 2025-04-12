<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../stores/user';
import { useMapStore } from '../stores/map';
import MapList from '../components/MapList.vue';
import MapDisplay from '../components/MapDisplay.vue';
import MapNotes from '../components/MapNotes.vue';
import MapSearch from '../components/MapSearch.vue';
import MapUpload from '../components/MapUpload.vue';
import UserSettings from '../components/UserSettings.vue';
import MapDetails from '../components/MapDetails.vue';

const router = useRouter();
const userStore = useUserStore();
const mapStore = useMapStore();

// User info
const userName = computed(() => userStore.getUserName);
const uid = computed(() => userStore.getUid);

// Current view state
const activeView = ref('mapView'); // 'mapView', 'searchView', 'uploadView'
const isShowingMenu = ref(false);
const isLoading = ref(false);
const isShowingSettings = ref(false);

// Logout handler
const logout = () => {
  userStore.logout();
  router.push('/login');
};

// Navigation handlers
const goToSearchView = () => {
  activeView.value = 'searchView';
  isShowingMenu.value = false;
};

const goToMapView = () => {
  activeView.value = 'mapView';
  isShowingMenu.value = false;
};

const goToUploadView = () => {
  activeView.value = 'uploadView';
  isShowingMenu.value = false;
};

const openSettings = () => {
  isShowingSettings.value = true;
  isShowingMenu.value = false;
};

const closeSettings = () => {
  isShowingSettings.value = false;
};

// Map navigation
const goToPrevMap = async () => {
  if (!uid.value) return;
  isLoading.value = true;
  await mapStore.prevMap(uid.value);
  isLoading.value = false;
};

const goToNextMap = async () => {
  if (!uid.value) return;
  isLoading.value = true;
  await mapStore.nextMap(uid.value);
  isLoading.value = false;
};

// Map selection
const handleMapSelected = (mapId) => {
  console.log(`Map selected in main view: ${mapId}`);
  // 确保我们是在地图视图中
  if (activeView.value !== 'mapView') {
    console.log('Switching to map view');
    goToMapView();
  }
};

// Toggle menu
const toggleMenu = () => {
  isShowingMenu.value = !isShowingMenu.value;
};

// Initialize component
onMounted(async () => {
  if (!uid.value) {
    router.push('/login');
    return;
  }
  
  await userStore.fetchUserName();
  await mapStore.fetchMapList();
  await mapStore.fetchCurrentMap(uid.value);
});
</script>

<template>
  <div class="main-container">
    <!-- Header -->
    <header class="main-header">
      <div class="header-left">
        <div class="menu-button" @click="toggleMenu">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <h1 class="app-title">地图收藏家</h1>
      </div>
      
      <div class="user-info">
        <span class="user-name">{{ userName }}</span>
        <button class="logout-btn" @click="logout">退出登录</button>
      </div>
    </header>
    
    <!-- Menu Overlay -->
    <div v-if="isShowingMenu" class="menu-overlay" @click="isShowingMenu = false">
      <div class="menu-content" @click.stop>
        <div class="menu-header">
          <h3>系统菜单</h3>
          <button class="close-btn" @click="isShowingMenu = false">✕</button>
        </div>
        
        <div class="menu-items">
          <div class="menu-item" @click="goToMapView">
            地图浏览
          </div>
          <div class="menu-item" @click="goToSearchView">
            地图检索
          </div>
          <div class="menu-item" @click="goToUploadView">
            添加地图
          </div>
          <div class="menu-item" @click="openSettings">
            用户设置
          </div>
        </div>
      </div>
    </div>
    
    <!-- User Settings Dialog -->
    <UserSettings :isOpen="isShowingSettings" :onClose="closeSettings" />
    
    <!-- Main Content -->
    <div class="main-content">
      <!-- Left Panel (Map List) -->
      <div class="left-panel">
        <MapList :onMapSelected="handleMapSelected" />
      </div>
      
      <!-- Center Panel (Map Display or Search/Upload) -->
      <div class="center-panel">
        <div v-if="activeView === 'mapView'" class="map-view">
          <div class="map-navigation">
            <button 
              class="nav-btn prev-btn" 
              @click="goToPrevMap"
              :disabled="isLoading"
            >
              &lt; 上一个
            </button>
            <button 
              class="nav-btn next-btn"
              @click="goToNextMap"
              :disabled="isLoading"
            >
              下一个 &gt;
            </button>
          </div>
          
          <div class="map-display-area">
            <MapDisplay 
              :mapImage="mapStore.mapImage" 
              :mapDetails="mapStore.mapDetails" 
            />
          </div>
          <MapDetails />
        </div>
        
        <div v-else-if="activeView === 'searchView'" class="search-view">
          <MapSearch @search-complete="goToMapView" />
        </div>
        
        <div v-else-if="activeView === 'uploadView'" class="upload-view">
          <MapUpload />
        </div>
      </div>
      
      <!-- Right Panel (Notes) -->
      <div class="right-panel">
        <MapNotes />
      </div>
    </div>
  </div>
</template>

<style scoped>
.main-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

/* Header */
.main-header {
  height: 60px;
  min-height: 60px;
  background-color: #3498db;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
}

.menu-button {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 20px;
  height: 16px;
  cursor: pointer;
  margin-right: 20px;
}

.menu-button span {
  width: 100%;
  height: 2px;
  background-color: white;
  transition: transform 0.3s;
}

.app-title {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-name {
  font-size: 14px;
}

.logout-btn {
  padding: 6px 12px;
  background-color: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  font-size: 14px;
}

.logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.left-panel {
  width: 300px;
  min-width: 300px;
  height: 100%;
  overflow: hidden;
  border-right: 1px solid #e9ecef;
}

.center-panel {
  flex: 1;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.right-panel {
  width: 300px;
  min-width: 300px;
  height: 100%;
  overflow: hidden;
  border-left: 1px solid #e9ecef;
}

/* Map View */
.map-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.map-navigation {
  padding: 10px;
  display: flex;
  justify-content: space-between;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  min-height: 50px;
}

.nav-btn {
  padding: 8px 16px;
  background-color: #e9ecef;
  border: 1px solid #ced4da;
  border-radius: 4px;
  cursor: pointer;
  color: #495057;
}

.nav-btn:hover {
  background-color: #dee2e6;
}

.nav-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.map-display-area {
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* Search & Upload Views */
.search-view, .upload-view {
  height: 100%;
  padding: 20px;
  overflow-y: auto;
}

/* Menu Overlay */
.menu-overlay {
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

.menu-content {
  background-color: white;
  border-radius: 8px;
  width: 300px;
  max-width: 90vw;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #e9ecef;
}

.menu-header h3 {
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

.menu-items {
  padding: 10px 0;
}

.menu-item {
  padding: 12px 20px;
  cursor: pointer;
  transition: background-color 0.2s;
  color: #495057;
}

.menu-item:hover {
  background-color: #f8f9fa;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .left-panel, .right-panel {
    width: 250px;
    min-width: 250px;
  }
}

@media (max-width: 900px) {
  .left-panel, .right-panel {
    width: 200px;
    min-width: 200px;
  }
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  
  .left-panel, .right-panel {
    width: 100%;
    min-width: 100%;
    height: auto;
    max-height: 30vh;
  }
  
  .center-panel {
    height: 40vh;
  }
}
</style> 