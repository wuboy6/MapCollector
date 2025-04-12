<script setup>
import { ref, onMounted } from 'vue';
import { useMapStore } from '../stores/map';

const mapStore = useMapStore();
const changes = ref([]);

onMounted(async () => {
  try {
    const response = await mapStore.fetchMapChanges();
    changes.value = response?.details || [];
  } catch (error) {
    console.error('Failed to fetch map changes:', error);
    changes.value = [];
  }
});

// 格式化日期时间
const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return '';
  try {
    const date = new Date(dateTimeStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return dateTimeStr;
  }
};
</script>

<template>
  <div class="map-changes">
    <h4>地图修改历史记录</h4>
    <table class="changes-table">
      <thead>
        <tr>
          <th>用户名</th>
          <th>地图名称</th>
          <th>修改时间</th>
          <th>新地图名称</th>
          <th>新地图类型</th>
          <th>新地图媒介</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(change, index) in changes" :key="index">
          <td>{{ change.user_name }}</td>
          <td>{{ change.map_name }}</td>
          <td>{{ formatDateTime(change.change_time) }}</td>
          <td>{{ change.new_map_name || '-' }}</td>
          <td>{{ change.new_map_type || '-' }}</td>
          <td>{{ change.new_media_type || '-' }}</td>
        </tr>
        <tr v-if="changes.length === 0">
          <td colspan="6" class="no-data">暂无修改记录</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.map-changes {
  margin-top: 20px;
  padding: 15px;
}

h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.changes-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background-color: white;
}

.changes-table th,
.changes-table td {
  padding: 8px;
  text-align: left;
  border: 1px solid #ddd;
}

.changes-table th {
  background-color: #f5f5f5;
  font-weight: normal;
}

.changes-table tr:nth-child(even) {
  background-color: #fafafa;
}

.no-data {
  text-align: center;
  color: #666;
  padding: 20px !important;
}
</style> 