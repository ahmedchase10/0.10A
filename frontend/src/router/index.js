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
      // ── Top-level pages ───────────────────────────
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/dashboard.vue')
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
        path: 'creator',
        name: 'Creator',
        component: () => import('@/views/creator.vue')
      },
      {
        path: 'grading',
        name: 'Grading',
        component: () => import('@/views/grading.vue')
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
      },

      // ── Class hub + sub-pages ─────────────────────
      {
        path: 'class/:id',
        name: 'ClassPage',
        component: () => import('@/views/classpage.vue')
      },
      {
        path: 'class/:id/students',
        name: 'ClassStudents',
        component: () => import('@/views/classstudents.vue')
      },
      {
        path: 'class/:id/attendance',
        name: 'ClassAttendance',
        component: () => import('@/views/classattendance.vue')
      },
      {
        path: 'class/:id/grades',
        name: 'ClassGrades',
        component: () => import('@/views/classgrades.vue')
      },
      {
        path: 'class/:id/lessons',
        name: 'ClassLessons',
        component: () => import('@/views/classlessons.vue')
      },
      {
        path: 'class/:id/parentnotification',
        name: 'ParentNotification',
        component: () => import('@/views/parentnotification.vue')
      },
      {
        path: 'class/:id/insights',
        name: 'ClassInsights',
        component: () => import('@/views/classinsights.vue')
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

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
