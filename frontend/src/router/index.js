import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const routes = [
  {
    path: '/auth',
    name: 'Auth',
    component: () => import('@/views/auth.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/appLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/dashboard.vue')
      },
      {
        path: 'class/:id',
        name: 'ClassPage',
        component: () => import('@/views/classpage.vue')
      },
      {
        path: 'class/:id/attendance',
        name: 'ClassAttendance',
        component: () => import('@/views/classattendance.vue')
      },
      {
        path: 'timetable',
        name: 'Timetable',
        component: () => import('@/views/timetable.vue')
      },
      {
        path: 'lessons',
        name: 'Lessons',
        component: () => import('@/views/lessons.vue')
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('@/views/notifications.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings.vue')
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Navigation guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/auth');
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/');
  } else {
    next();
  }
});

export default router;