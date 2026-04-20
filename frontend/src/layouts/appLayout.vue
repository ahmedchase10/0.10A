<template>
  <div class="flex h-screen bg-grey-50">
    <!-- Sidebar -->
    <aside :class="[
      'bg-white border-r border-grey-200 transition-all duration-300 flex flex-col',
      sidebarExpanded ? 'w-64' : 'w-20'
    ]">
      <!-- Logo -->
      <div class="h-16 flex items-center justify-between px-4 border-b border-grey-200 flex-shrink-0">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <span v-show="sidebarExpanded" class="text-lg font-bold text-grey-900">Digi-School</span>
        </div>
        <button @click="sidebarExpanded = !sidebarExpanded" class="p-2 hover:bg-grey-100 rounded-lg transition">
          <ChevronLeftIcon v-if="sidebarExpanded" class="w-5 h-5 text-grey-600" />
          <ChevronRightIcon v-else class="w-5 h-5 text-grey-600" />
        </button>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        <!-- Top-level links -->
        <RouterLink
          v-for="item in navigation"
          :key="item.name"
          :to="item.to"
          v-slot="{ isActive }"
        >
          <button :class="[
            'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
            isActive
              ? 'bg-primary-50 text-primary-600'
              : 'text-grey-700 hover:bg-grey-100'
          ]">
            <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
            <span v-show="sidebarExpanded" class="font-medium">{{ item.name }}</span>
          </button>
        </RouterLink>

        <!-- Classes section -->
        <div v-if="classes.length > 0" class="pt-4">
          <div v-show="sidebarExpanded" class="px-3 py-2 text-xs font-semibold text-grey-400 uppercase tracking-wider">
            Classes
          </div>

          <div v-for="cls in classes" :key="cls.id">
            <!-- Class header row -->
            <button
              @click="toggleClass(cls.id)"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-left',
                isClassActive(cls.id) ? 'bg-primary-50 text-primary-600' : 'text-grey-700 hover:bg-grey-100'
              ]"
            >
              <div
                class="w-2 h-2 rounded-full flex-shrink-0"
                :style="{ backgroundColor: cls.color || '#3b82f6' }"
              ></div>
              <span v-show="sidebarExpanded" class="text-sm font-medium truncate flex-1">{{ cls.name }}</span>
              <ChevronDownIcon
                v-show="sidebarExpanded"
                :class="['w-4 h-4 flex-shrink-0 transition-transform', expandedClasses.has(cls.id) ? 'rotate-180' : '']"
              />
            </button>

            <!-- Class sub-links (expanded) -->
            <div v-show="sidebarExpanded && expandedClasses.has(cls.id)" class="ml-5 mt-0.5 space-y-0.5 border-l-2 border-grey-200 pl-3">
              <RouterLink
                v-for="sub in classSubLinks(cls.id)"
                :key="sub.to"
                :to="sub.to"
                v-slot="{ isActive }"
              >
                <button :class="[
                  'w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs transition-colors',
                  isActive ? 'bg-primary-50 text-primary-600 font-medium' : 'text-grey-600 hover:bg-grey-100'
                ]">
                  <component :is="sub.icon" class="w-3.5 h-3.5 flex-shrink-0" />
                  {{ sub.label }}
                </button>
              </RouterLink>
            </div>
          </div>
        </div>
      </nav>

      <!-- User Profile -->
      <div class="border-t border-grey-200 p-4 flex-shrink-0">
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
          <MenuItems class="absolute bottom-full left-0 mb-2 w-48 bg-white rounded-lg shadow-lg border border-grey-200 py-1 z-50">
            <MenuItem v-slot="{ active }">
              <RouterLink to="/settings">
                <button :class="['w-full flex items-center gap-2 px-4 py-2 text-sm', active ? 'bg-grey-100' : '']">
                  <Cog6ToothIcon class="w-4 h-4" />
                  Settings
                </button>
              </RouterLink>
            </MenuItem>
            <MenuItem v-slot="{ active }">
              <button @click="handleLogout"
                :class="['w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600', active ? 'bg-red-50' : '']">
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
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router';
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
import {
  HomeIcon,
  CalendarIcon,
  DocumentTextIcon,
  BellIcon,
  Cog6ToothIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  ArrowRightOnRectangleIcon,
  UserGroupIcon,
  ClipboardDocumentCheckIcon,
  ChartBarIcon,
  DocumentArrowUpIcon
} from '@heroicons/vue/24/outline';
import { useAuthStore } from '@/stores/auth';
import api from '@/services/api';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const sidebarExpanded = ref(true);
const classes = ref([]);
const expandedClasses = ref(new Set());

const navigation = [
  { name: 'Dashboard',      to: '/',             icon: HomeIcon },
  { name: 'Timetable',      to: '/timetable',    icon: CalendarIcon },
  { name: 'Lessons',        to: '/lessons',      icon: DocumentTextIcon },
  { name: 'Notifications',  to: '/notifications', icon: BellIcon },
];

function classSubLinks(classId) {
  return [
    { label: 'Students',   to: `/class/${classId}/students`,   icon: UserGroupIcon },
    { label: 'Attendance', to: `/class/${classId}/attendance`, icon: ClipboardDocumentCheckIcon },
    { label: 'Grades',     to: `/class/${classId}/grades`,     icon: ChartBarIcon },
    { label: 'Lessons',    to: `/class/${classId}/lessons`,    icon: DocumentArrowUpIcon },
  ];
}

function isClassActive(classId) {
  return route.path.startsWith(`/class/${classId}`);
}

function toggleClass(classId) {
  if (expandedClasses.value.has(classId)) {
    expandedClasses.value.delete(classId);
  } else {
    expandedClasses.value.add(classId);
    router.push(`/class/${classId}`);
  }
  // Trigger reactivity
  expandedClasses.value = new Set(expandedClasses.value);
}

const userInitials = computed(() => {
  return authStore.user?.initials || authStore.user?.name?.substring(0, 2).toUpperCase() || 'U';
});

async function loadClasses() {
  try {
    const response = await api.getClasses();
    if (response.success) {
      classes.value = response.classes || [];
      // Auto-expand active class
      const match = route.path.match(/^\/class\/(\d+)/);
      if (match) expandedClasses.value.add(parseInt(match[1]));
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