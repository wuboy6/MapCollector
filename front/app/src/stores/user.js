import { defineStore } from 'pinia';
import { authService } from '../api';

export const useUserStore = defineStore('user', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    userName: null,
    loading: false,
    error: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.user,
    getUid: (state) => state.user?.uid || null,
    getUserName: (state) => state.userName || 'Unknown User',
  },
  
  actions: {
    async login(email, password) {
      this.loading = true;
      this.error = null;
      try {
        const response = await authService.login(email, password);
        this.user = response.data;
        localStorage.setItem('user', JSON.stringify(this.user));
        await this.fetchUserName();
        return true;
      } catch (error) {
        this.error = error.response?.data?.detail || 'Login failed';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    async register(email, password) {
      this.loading = true;
      this.error = null;
      try {
        const response = await authService.register(email, password);
        return { success: true, uid: response.data.uid };
      } catch (error) {
        this.error = error.response?.data?.detail || 'Registration failed';
        return { success: false, error: this.error };
      } finally {
        this.loading = false;
      }
    },
    
    async fetchUserName() {
      if (!this.user?.uid) return;
      
      try {
        const response = await authService.getUserName(this.user.uid);
        this.userName = response.data.name;
      } catch (error) {
        console.error('Failed to fetch user name:', error);
        this.userName = 'Unknown User';
      }
    },
    
    async updateUserName(newName) {
      if (!this.user?.uid) return false;
      
      try {
        await authService.resetUserName(this.user.uid, newName);
        this.userName = newName;
        return true;
      } catch (error) {
        console.error('Failed to update user name:', error);
        return false;
      }
    },
    
    async updateUserEmail(newEmail) {
      if (!this.user?.uid) return false;
      
      try {
        await authService.resetUserEmail(this.user.uid, newEmail);
        return true;
      } catch (error) {
        console.error('Failed to update user email:', error);
        return false;
      }
    },
    
    logout() {
      this.user = null;
      this.userName = null;
      localStorage.removeItem('user');
    }
  }
}); 