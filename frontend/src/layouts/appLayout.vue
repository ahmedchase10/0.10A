<template>
  <div class="flex h-screen bg-grey-50">
    <!-- Sidebar -->
    <aside :class="[
      'bg-white border-r border-grey-200 transition-all duration-300 flex flex-col',
      sidebarExpanded ? 'w-64' : 'w-20'
    ]">
      <!-- Logo -->
      <div class="h-16 flex items-center justify-between px-4 border-b border-grey-200">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <span v-show="sidebarExpanded" class="text-lg font-bold text-grey-900">Digi-School</span>
        </div>
        <button
          @click="sidebarExpanded = !sidebarExpanded"
          class="p-2 hover:bg-grey-100 rounded-lg transition"
        >
          <ChevronLeftIcon v-if="sidebarExpanded" class="w-5 h-5 text-grey-600" />
          <ChevronRightIcon v-else class="w-5 h-5 text-grey-600" />
        </button>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        <RouterLink
          v-for="item in navigation"
          :key="item.name"
          :to="item.to"
          v-slot="{ isActive }"
        >
          <button
            :class="[
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors relative',
              isActive
                ? 'bg-primary-50 text-primary-600'
                : 'text-grey-700 hover:bg-grey-100'
            ]"
          >
            <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
            <span v-show="sidebarExpanded" class="font-medium">{{ item.name }}</span>
            <span
              v-if="item.badge && sidebarExpanded"
              class="ml-auto bg-red-500 text-white text-xs font-semibold px-2 py-0.5 rounded-full"
            >
              {{ item.badge }}
            </span>
          </button>
        </RouterLink>

        <!-- Classes Section -->
        <div v-if="classes.length > 0" class="pt-4">
          <div v-show="sidebarExpanded" class="px-3 py-2 text-xs font-semibold text-grey-500 uppercase tracking-wider">
            My Classes ({{ classes.length }})
          </div>
          <div class="space-y-1">
            <RouterLink
              v-for="cls in classes"
              :key="cls.id"
              :to="`/class/${cls.id}`"
              v-slot="{ isActive }"
            >
              <button
                :class="[
                  'w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-600'
                    : 'text-grey-700 hover:bg-grey-100'
                ]"
              >
                <div
                  class="w-2 h-2 rounded-full flex-shrink-0"
                  :style="{ backgroundColor: cls.color || '#3b82f6' }"
                ></div>
                <span v-show="sidebarExpanded" class="text-sm truncate">{{ cls.name }}</span>
              </button>
            </RouterLink>
          </div>
        </div>
      </nav>

      <!-- User Profile -->
      <div class="border-t border-grey-200 p-4">
        <Menu as="div" class="relative">
          <MenuButton class="w-full flex items-center gap-3 hover:bg-grey-100 rounded-lg p-2 transition">
            <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center text-white font-semibold flex-shrink-0">
              {{ userInitials }}
            </div>
            <div v-show="sidebarExpanded" class="flex-1 text-left min-w-0">
              <p class="text-sm font-medium text-grey-900 truncate">{{ authStore.user?.name }}</p>
              <p class="text-xs text-grey-600 truncate">{{ authStore.user?.email }}</p>
            </div>
          </MenuButton>
          <MenuItems class="absolute bottom-full left-0 mb-2 w-48 bg-white rounded-lg shadow-lg border border-grey-200 py-1">
            <MenuItem v-slot="{ active }">
              <button
                @click="handleLogout"
                :class="[
                  'w-full flex items-center gap-2 px-4 py-2 text-sm',
                  active ? 'bg-grey-100' : ''
                ]"
              >
                <ArrowRightOnRectangleIcon class="w-4 h-4" />
                Logout
              </button>
            </MenuItem>
          </MenuItems>
        </Menu>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto custom-scrollbar">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { RouterLink, RouterView, useRouter } from 'vue-router';
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
import {
  HomeIcon,
  CalendarIcon,
  DocumentTextIcon,
  BellIcon,
  Cog6ToothIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/vue/24/outline';
import { useAuthStore } from '@/stores/auth';
import api from '@/services/api';

const router = useRouter();
const authStore = useAuthStore();

const sidebarExpanded = ref(true);
const classes = ref([]);
const unreadNotifications = ref(3); // Mock data

const navigation = [
  { name: 'Dashboard', to: '/', icon: HomeIcon },
  { name: 'Timetable', to: '/timetable', icon: CalendarIcon },
  { name: 'Lessons', to: '/lessons', icon: DocumentTextIcon },
  { name: 'Notifications', to: '/notifications', icon: BellIcon, badge: unreadNotifications.value },
  { name: 'Settings', to: '/settings', icon: Cog6ToothIcon },
];

const userInitials = computed(() => {
  return authStore.user?.initials || authStore.user?.name?.substring(0, 2).toUpperCase() || 'U';
});

async function loadClasses() {
  try {
    const response = await api.getClasses();
    if (response.success) {
      classes.value = response.classes || [];
    }
  } catch (error) {
    console.error('Failed to load classes:', error);
  }
}

function handleLogout() {
  authStore.logout();
  router.push('/auth');
}

onMounted(() => {
  loadClasses();
});
</script>