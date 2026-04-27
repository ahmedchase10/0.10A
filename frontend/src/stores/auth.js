import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import api from '@/services/api';

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null);
  const token = ref(localStorage.getItem('digi_token') || null);

  const isAuthenticated = computed(() => !!token.value);

  function setAuth(newToken, userData) {
    token.value = newToken;
    user.value = userData;
    localStorage.setItem('digi_token', newToken);
    localStorage.setItem('digi_user', JSON.stringify(userData));
    api.setToken(newToken);
  }

  function clearAuth() {
    token.value = null;
    user.value = null;
    localStorage.removeItem('digi_token');
    localStorage.removeItem('digi_user');
    api.setToken(null);
  }

  function updateUser(userData) {
    user.value = { ...user.value, ...userData };
    localStorage.setItem('digi_user', JSON.stringify(user.value));
  }

  async function login(email, password) {
    const response = await api.login(email, password);
    if (response.success) setAuth(response.token, response.teacher);
    return response;
  }

  async function register(name, email, password, initials) {
    const response = await api.register(name, email, password, initials);
    if (response.success) setAuth(response.token, response.teacher);
    return response;
  }

  function logout() {
    clearAuth();
    import('@/stores/classesStore').then(({ useClassesStore }) => {
      useClassesStore().reset();
    });
  }

  async function init() {
    const savedUser = localStorage.getItem('digi_user');
    if (token.value && savedUser) {
      user.value = JSON.parse(savedUser);
      api.setToken(token.value);


      try {
        await api.getMe();
      } catch {

      }
    }
  }

  const ready = init();

  return { user, token, isAuthenticated, ready, login, register, logout, updateUser };
});