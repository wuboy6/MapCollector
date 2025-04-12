import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

// Create axios instance with base URL
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth services
export const authService = {
  login: (email, password) => {
    return apiClient.post('/login', { email, password });
  },
  register: (email, password) => {
    return apiClient.post('/register', { email, password });
  },
  getUserName: (uid) => {
    return apiClient.get(`/user/${uid}/name`);
  },
  resetUserName: (uid, newName) => {
    return apiClient.put(`/user/${uid}/name`, { new_name: newName });
  },
  resetUserEmail: (uid, newEmail) => {
    return apiClient.put(`/user/${uid}/email`, { new_email: newEmail });
  }
};

// Map services
export const mapService = {
  getMapList: () => {
    return apiClient.get('/maps');
  },
  getMapDetails: (mapId) => {
    return apiClient.get(`/maps/${mapId}`);
  },
  addMap: (mapName, fileBase64) => {
    return apiClient.post('/maps', { map_name: mapName, file: fileBase64 });
  },
  setCurrentMap: (uid, mapId) => {
    return apiClient.put(`/user/${uid}/current_map/${mapId}`, {});
  },
  getCurrentMapDetails: (uid) => {
    return apiClient.get(`/user/${uid}/current_map/details`);
  },
  updateMapDetails: (uid, mapId, details) => {
    return apiClient.put(`/user/${uid}/maps/${mapId}`, { arcs: details });
  },
  getMapChanges: (mapId) => {
    return axios.get(`${API_URL}/maps/${mapId}/changes`);
  }
};

// User map interaction services
export const userMapService = {
  getChangeDetails: (uid) => {
    return apiClient.get(`/user/${uid}/changes/selfall`);
  },
  getCurrentMapChanges: (uid) => {
    return apiClient.get(`/user/${uid}/changes/selfcurr`);
  },
  getAllCurrentMapChanges: (uid) => {
    return apiClient.get(`/user/${uid}/changes/curr`);
  },
  searchMaps: (uid, params) => {
    return apiClient.post(`/user/${uid}/search`, params);
  },
  goToNextMap: (uid) => {
    return apiClient.post(`/user/${uid}/next`);
  },
  goToPreviousMap: (uid) => {
    return apiClient.post(`/user/${uid}/before`);
  },
  changeMap: (uid, mapId, arcs) => {
    return apiClient.put(`/user/${uid}/maps/${mapId}`, { arcs });
  }
};

// Note services
export const noteService = {
  getCurrentMapNotes: (uid) => {
    return apiClient.get(`/user/${uid}/current_map/notes`);
  },
  addNote: (uid, note) => {
    return apiClient.post(`/user/${uid}/current_map/notes`, { note });
  }
};

export default {
  auth: authService,
  maps: mapService,
  userMap: userMapService,
  notes: noteService
}; 