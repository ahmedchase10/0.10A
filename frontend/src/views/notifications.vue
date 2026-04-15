<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-grey-900">Notifications</h1>
        <p class="text-grey-600 mt-1">System alerts and important updates</p>
      </div>
      <button
        v-if="unreadCount > 0"
        @click="markAllAsRead"
        class="flex items-center gap-2 px-4 py-2 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
      >
        <CheckIcon class="w-5 h-5" />
        Mark All Read
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-16">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="notifications.length === 0" class="text-center py-16 bg-white rounded-xl shadow-sm border border-grey-200">
      <BellIcon class="w-16 h-16 mx-auto text-grey-300 mb-4" />
      <h3 class="text-lg font-medium text-grey-900 mb-2">No notifications</h3>
      <p class="text-grey-600">You're all caught up!</p>
    </div>

    <!-- Notifications List -->
    <div v-else class="space-y-4">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="[
          'bg-white rounded-xl shadow-sm border p-6 transition hover:shadow-md',
          notification.read ? 'border-grey-200' : 'border-l-4 border-l-primary-500'
        ]"
      >
        <div class="flex items-start gap-4">
          <!-- Icon -->
          <div
            :class="[
              'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0',
              getNotificationBg(notification.type)
            ]"
          >
            <component :is="getNotificationIcon(notification.type)" class="w-6 h-6" />
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between mb-2">
              <div>
                <span :class="[
                  'inline-block px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider mb-2',
                  getNotificationTypeClass(notification.type)
                ]">
                  {{ notification.type }}
                </span>
                <p class="text-grey-900 font-medium">{{ notification.message }}</p>
              </div>
              <span class="text-sm text-grey-500 ml-4 flex-shrink-0">{{ formatTime(notification.sent_at) }}</span>
            </div>

            <p v-if="notification.student_name" class="text-sm text-grey-600 mb-3">
              Student: <span class="font-medium">{{ notification.student_name }}</span>
            </p>

            <!-- Actions -->
            <div class="flex items-center gap-2">
              <button
                v-if="!notification.read"
                @click="markAsRead(notification.id)"
                class="text-sm text-primary-600 hover:text-primary-700 font-medium transition"
              >
                Mark as read
              </button>
              <button
                @click="deleteNotification(notification.id)"
                class="text-sm text-red-600 hover:text-red-700 font-medium transition"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import {
  BellIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  AcademicCapIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline';
import api from '@/services/api';

const loading = ref(true);
const notifications = ref([]);

const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.read).length;
});

function getNotificationIcon(type) {
  const icons = {
    'behavior': ExclamationTriangleIcon,
    'absence': ClockIcon,
    'grade': AcademicCapIcon,
    'system': InformationCircleIcon
  };
  return icons[type] || InformationCircleIcon;
}

function getNotificationBg(type) {
  const classes = {
    'behavior': 'bg-red-50 text-red-600',
    'absence': 'bg-yellow-50 text-yellow-600',
    'grade': 'bg-success-50 text-success-600',
    'system': 'bg-primary-50 text-primary-600'
  };
  return classes[type] || classes['system'];
}

function getNotificationTypeClass(type) {
  const classes = {
    'behavior': 'bg-red-100 text-red-700',
    'absence': 'bg-yellow-100 text-yellow-700',
    'grade': 'bg-success-100 text-success-700',
    'system': 'bg-primary-100 text-primary-700'
  };
  return classes[type] || classes['system'];
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}min ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString();
}

async function loadNotifications() {
  try {
    const response = await api.getNotifications();
    if (response.success) {
      notifications.value = response.notifications || [];
    }
  } catch (err) {
    // Mock data for demo
    notifications.value = [
      {
        id: 1,
        type: 'absence',
        message: 'Ahmed Ben Ali has been absent for 3 consecutive days',
        student_name: 'Ahmed Ben Ali',
        read: false,
        sent_at: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: 2,
        type: 'behavior',
        message: 'Mohamed disrupted class for the 3rd time this week',
        student_name: 'Mohamed',
        read: false,
        sent_at: new Date(Date.now() - 7200000).toISOString()
      },
      {
        id: 3,
        type: 'system',
        message: 'Your weekly report card generation is ready',
        read: true,
        sent_at: new Date(Date.now() - 86400000).toISOString()
      }
    ];
  } finally {
    loading.value = false;
  }
}

async function markAsRead(id) {
  try {
    await api.markNotificationRead(id);
    const notification = notifications.value.find(n => n.id === id);
    if (notification) {
      notification.read = true;
    }
  } catch (err) {
    console.error('Failed to mark as read:', err);
    // Fallback for demo
    const notification = notifications.value.find(n => n.id === id);
    if (notification) {
      notification.read = true;
    }
  }
}

async function deleteNotification(id) {
  try {
    await api.deleteNotification(id);
    notifications.value = notifications.value.filter(n => n.id !== id);
  } catch (err) {
    console.error('Failed to delete:', err);
    // Fallback for demo
    notifications.value = notifications.value.filter(n => n.id !== id);
  }
}

async function markAllAsRead() {
  const unread = notifications.value.filter(n => !n.read);
  for (const notification of unread) {
    await markAsRead(notification.id);
  }
}

onMounted(() => {
  loadNotifications();
});
</script>