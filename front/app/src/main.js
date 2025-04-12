import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

// Import route components
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import MainView from './views/MainView.vue'

// Create router instance
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', component: Login },
    { path: '/register', component: Register },
    { 
      path: '/main', 
      component: MainView,
      meta: { requiresAuth: true } 
    }
  ]
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !localStorage.getItem('user')) {
    next('/login')
  } else {
    next()
  }
})

// Create Pinia store
const pinia = createPinia()

// Create and mount app
const app = createApp(App)
app.use(pinia)
app.use(router)
app.mount('#app')
