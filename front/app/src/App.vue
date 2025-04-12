<script setup>
// Main app component that serves as a container for router views
</script>

<template>
  <div class="app-container">
    <router-view />
  </div>
</template>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
  background-color: #f5f5f5;
}

.app-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
