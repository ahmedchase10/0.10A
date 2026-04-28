<template>
  <div class="min-h-screen bg-gradient-to-br from-primary-600 via-primary-500 to-primary-700 flex items-center justify-center p-4">
    <!-- Animated background -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-1/2 -right-1/2 w-full h-full bg-white/5 rounded-full blur-3xl"></div>
      <div class="absolute -bottom-1/2 -left-1/2 w-full h-full bg-white/5 rounded-full blur-3xl"></div>
    </div>

    <!-- Auth Card -->
    <div class="relative w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-2xl p-8">
        <!-- Logo & Title -->
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl mb-4">
            <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h1 class="text-3xl font-bold text-grey-900 mb-2">Digi-School AI</h1>
          <p class="text-grey-600">Voice-First Teaching Assistant</p>
        </div>

        <!-- Tabs -->
        <div class="flex gap-2 mb-6 bg-grey-100 p-1 rounded-lg">
          <button
            @click="mode = 'login'"
            :class="[
              'flex-1 py-2 px-4 rounded-md font-medium transition-all',
              mode === 'login' 
                ? 'bg-white text-primary-600 shadow-sm' 
                : 'text-grey-600 hover:text-grey-900'
            ]"
          >
            Login
          </button>
          <button
            @click="mode = 'signup'"
            :class="[
              'flex-1 py-2 px-4 rounded-md font-medium transition-all',
              mode === 'signup' 
                ? 'bg-white text-primary-600 shadow-sm' 
                : 'text-grey-600 hover:text-grey-900'
            ]"
          >
            Sign Up
          </button>
        </div>

        <!-- Error Alert -->
        <div v-if="error" class="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p class="text-sm text-red-800">{{ error }}</p>
        </div>

        <!-- Login Form -->
        <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-grey-700 mb-2">Email</label>
            <input
              v-model="loginForm.email"
              type="email"
              required
              class="w-full px-4 py-3 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition"
              placeholder="teacher@school.edu"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-grey-700 mb-2">Password</label>
            <input
              v-model="loginForm.password"
              type="password"
              required
              class="w-full px-4 py-3 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition"
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-gradient-to-r from-primary-600 to-primary-500 text-white py-3 px-4 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition disabled:opacity-50"
          >
            <span v-if="loading">Logging in...</span>
            <span v-else>Login</span>
          </button>
        </form>

        <!-- Signup Form -->
        <form v-else @submit.prevent="handleSignup" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-grey-700 mb-2">Full Name</label>
            <input
              v-model="signupForm.name"
              type="text"
              required
              class="w-full px-4 py-3 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition"
              placeholder="John Smith"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-grey-700 mb-2">Email</label>
            <input
              v-model="signupForm.email"
              type="email"
              required
              class="w-full px-4 py-3 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition"
              placeholder="teacher@school.edu"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-grey-700 mb-2">Password</label>
            <input
              v-model="signupForm.password"
              type="password"
              required
              minlength="8"
              class="w-full px-4 py-3 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition"
              placeholder="Minimum 8 characters"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-gradient-to-r from-primary-600 to-primary-500 text-white py-3 px-4 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition disabled:opacity-50"
          >
            <span v-if="loading">Creating account...</span>
            <span v-else>Create Account</span>
          </button>
        </form>

        <!-- Footer -->
        <div class="mt-6 text-center">
          <p class="text-sm text-grey-600 flex items-center justify-center gap-2">
            <svg class="w-4 h-4 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            Your data is secure and encrypted
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const mode = ref('login');
const loading = ref(false);
const error = ref('');

const loginForm = ref({
  email: '',
  password: ''
});

const signupForm = ref({
  name: '',
  email: '',
  password: ''
});

async function handleLogin() {
  loading.value = true;
  error.value = '';
  
  try {
    await authStore.login(loginForm.value.email, loginForm.value.password);
    router.push('/');
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

async function handleSignup() {
  loading.value = true;
  error.value = '';
  
  try {
    await authStore.register(
      signupForm.value.name,
      signupForm.value.email,
      signupForm.value.password
    );
    router.push('/');
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}
</script>
