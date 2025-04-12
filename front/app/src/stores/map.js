import { defineStore } from 'pinia';
import { mapService, userMapService, noteService, authService } from '../api';
import { useUserStore } from './user';

export const useMapStore = defineStore('map', {
  state: () => ({
    mapList: [],
    currentMap: null,
    mapDetails: null,
    mapImage: null,
    notes: [],
    loading: false,
    error: null,
    imageCache: new Map(),
    detailsCache: new Map(),
    userNamesCache: new Map()
  }),
  
  getters: {
    getMapByType: (state) => {
      const mapsByType = {};
      state.mapList.forEach(map => {
        const type = map.map_type || 'Uncategorized';
        if (!mapsByType[type]) {
          mapsByType[type] = [];
        }
        mapsByType[type].push(map);
      });
      return mapsByType;
    },
    
    getCurrentMapId: (state) => state.currentMap?.mapid,
    
    getMapImage: (state) => state.mapImage
  },
  
  actions: {
    async fetchMapList() {
      this.loading = true;
      this.error = null;
      try {
        const response = await mapService.getMapList();
        this.mapList = response.data.maps;
      } catch (error) {
        console.error('Failed to fetch map list:', error);
        this.error = error.response?.data?.detail || 'Failed to load maps';
        this.mapList = [];
      } finally {
        this.loading = false;
      }
    },
    
    async fetchMapDetails(mapId) {
      if (this.detailsCache.has(mapId)) {
        return this.detailsCache.get(mapId);
      }
      
      this.loading = true;
      this.error = null;
      try {
        const response = await mapService.getMapDetails(mapId);
        this.detailsCache.set(mapId, response.data);
        return response.data;
      } catch (error) {
        console.error('Failed to fetch map details:', error);
        this.error = error.response?.data?.detail || 'Failed to load map details';
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    async setCurrentMap(uid, mapId) {
      this.loading = true;
      this.error = null;
      
      try {
        console.log(`Setting current map to ${mapId} for user ${uid}`);
        
        // 1. 首先检查缓存
        if (this.detailsCache.has(mapId)) {
          const cachedData = this.detailsCache.get(mapId);
          console.log('Using cached map data');
          this.currentMap = cachedData;
          this.mapDetails = cachedData.details;
          this.mapImage = cachedData.image;
          this.loading = false; // 使用缓存数据时立即关闭loading状态
        }
        
        // 2. 异步更新当前地图
        const updatePromise = (async () => {
          try {
            await mapService.setCurrentMap(uid, mapId);
            console.log('Getting current map details');
            const response = await mapService.getCurrentMapDetails(uid);
            
            if (!response.data || !response.data.image) {
              console.error('Map data missing or incomplete:', response.data);
              this.error = 'Map data missing or incomplete';
              return false;
            }
            
            this.currentMap = response.data;
            this.mapDetails = response.data.details;
            this.mapImage = response.data.image;
            
            if (response.data.mapid) {
              this.detailsCache.set(response.data.mapid, response.data);
            }

            this.fetchMapNotes(uid).catch(error => 
              console.error('Failed to fetch map notes:', error)
            );
            
            return true;
          } catch (error) {
            console.error('Failed to update map data:', error);
            this.error = error.response?.data?.detail || 'Failed to update map data';
            return false;
          }
        })();
        
        // 3. 如果缓存中没有数据，等待更新完成
        if (!this.detailsCache.has(mapId)) {
          await updatePromise;
        }
        
        return true;
      } catch (error) {
        console.error('Failed to set current map:', error);
        this.error = error.response?.data?.detail || 'Failed to set current map';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    async fetchCurrentMap(uid) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await mapService.getCurrentMapDetails(uid);
        console.log('Fetched current map:', response.data);
        
        if (!response.data || !response.data.image) {
          console.error('No image data in response:', response.data);
          this.error = 'Map data is incomplete or missing';
          return false;
        }
        
        this.currentMap = response.data;
        this.mapDetails = response.data.details;
        this.mapImage = response.data.image;
        
        if (response.data.mapid) {
          this.detailsCache.set(response.data.mapid, response.data);
        }
        
        this.fetchMapNotes(uid).catch(error => 
          console.error('Failed to fetch map notes:', error)
        );
        
        return true;
      } catch (error) {
        console.error('Failed to fetch current map:', error);
        this.error = error.response?.data?.detail || 'Failed to load current map';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    async nextMap(uid) {
      this.loading = true;
      this.error = null;
      try {
        const response = await userMapService.goToNextMap(uid);
        if (response.data?.map_id) {
          await this.fetchCurrentMap(uid);
          return true;
        }
        return false;
      } catch (error) {
        console.error('Failed to navigate to next map:', error);
        this.error = error.response?.data?.detail || 'Failed to navigate to next map';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    async prevMap(uid) {
      this.loading = true;
      this.error = null;
      try {
        const response = await userMapService.goToPreviousMap(uid);
        if (response.data?.map_id) {
          await this.fetchCurrentMap(uid);
          return true;
        }
        return false;
      } catch (error) {
        console.error('Failed to navigate to previous map:', error);
        this.error = error.response?.data?.detail || 'Failed to navigate to previous map';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    async getUserName(uid) {
      if (this.userNamesCache.has(uid)) {
        return this.userNamesCache.get(uid);
      }
      
      try {
        const response = await authService.getUserName(uid);
        const userName = response.data.name;
        this.userNamesCache.set(uid, userName);
        return userName;
      } catch (error) {
        console.error('Failed to fetch user name:', error);
        return 'Unknown User';
      }
    },
    
    async fetchMapNotes(uid) {
      if (!this.currentMap) return;
      
      this.loading = true;
      this.error = null;
      try {
        const response = await noteService.getCurrentMapNotes(uid);
        console.log('Fetched notes:', response.data);
        
        if (!Array.isArray(response.data)) {
          console.error('Notes data is not an array:', response.data);
          this.notes = [];
          return [];
        }
        
        const notesWithNames = await Promise.all(
          response.data.map(async (note) => {
            const userName = await this.getUserName(note.uid);
            return {
              ...note,
              userName,
              content: note.content || note.context,
              time: note.time,
              noteid: note.noteid || note.id
            };
          })
        );
        
        console.log('Processed notes:', notesWithNames);
        this.notes = notesWithNames;
        return this.notes;
      } catch (error) {
        console.error('Failed to fetch map notes:', error);
        this.error = error.message;
        this.notes = [];
        return [];
      } finally {
        this.loading = false;
      }
    },
    
    async addNote(uid, noteText) {
      this.loading = true;
      this.error = null;
      try {
        await noteService.addNote(uid, noteText);
        await this.fetchMapNotes(uid);
        return true;
      } catch (error) {
        console.error('Failed to add note:', error);
        this.error = error.message;
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    async uploadMap(mapName, fileBase64) {
      this.loading = true;
      this.error = null;
      try {
        const response = await mapService.addMap(mapName, fileBase64);
        await this.fetchMapList();
        return { success: true, mapId: response.data.mapid };
      } catch (error) {
        console.error('Failed to upload map:', error);
        this.error = error.response?.data?.detail || 'Failed to upload map';
        return { success: false, error: this.error };
      } finally {
        this.loading = false;
      }
    },
    
    async searchMaps(uid, searchParams) {
      this.loading = true;
      this.error = null;
      try {
        await userMapService.searchMaps(uid, searchParams);
        await this.fetchCurrentMap(uid);
        return true;
      } catch (error) {
        console.error('Failed to search maps:', error);
        this.error = error.response?.data?.detail || 'Failed to search maps';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    clearCache() {
      this.imageCache.clear();
      this.detailsCache.clear();
      this.userNamesCache.clear();
    },

    async updateMapDetails(details) {
      if (!this.currentMap) return;
      try {
        this.loading = true;
        const uid = useUserStore().getUid;
        await mapService.updateMapDetails(uid, this.currentMap.mapid, details);
        
        this.mapDetails = { ...this.mapDetails, ...details };
        
        const index = this.mapList.findIndex(map => map.mapid === this.currentMap.mapid);
        if (index !== -1) {
          this.mapList[index] = { ...this.mapList[index], ...details };
        }
        
        this.detailsCache.delete(this.currentMap.mapid);
        
        return true;
      } catch (error) {
        console.error('Failed to update map details:', error);
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchMapChanges() {
      if (!this.currentMap) {
        console.warn('No current map selected');
        return [];
      }

      try {
        this.loading = true;
        const uid = useUserStore().getUid;
        const response = await userMapService.getAllCurrentMapChanges(uid);
        return response.data;
      } catch (error) {
        console.error('Error fetching map changes:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    }
  }
});