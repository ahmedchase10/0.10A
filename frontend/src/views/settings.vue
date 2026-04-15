<template>
  <div class="p-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-grey-900">Settings</h1>
      <p class="text-grey-600 mt-1">Manage your account and preferences</p>
    </div>

    <!-- Tabs -->
    <div class="bg-white rounded-xl shadow-sm border border-grey-200">
      <div class="border-b border-grey-200 px-6">
        <nav class="flex gap-8" aria-label="Tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'py-4 px-1 border-b-2 font-medium text-sm transition',
              activeTab === tab.id
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-grey-500 hover:text-grey-700 hover:border-grey-300'
            ]"
          >
            {{ tab.name }}
          </button>
        </nav>
      </div>

      <!-- Profile Tab -->
      <div v-show="activeTab === 'profile'" class="p-6">
        <h2 class="text-lg font-semibold text-grey-900 mb-6">Profile Information</h2>
        
        <form @submit.prevent="updateProfile" class="space-y-6 max-w-2xl">
          <div class="flex items-center gap-6">
            <div class="w-24 h-24 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center text-white text-3xl font-bold">
              {{ userInitials }}
            </div>
            <div>
              <button
                type="button"
                class="px-4 py-2 bg-grey-100 text-grey-700 rounded-lg hover:bg-grey-200 transition text-sm font-medium"
              >
                Change Avatar
              </button>
              <p class="text-sm text-grey-500 mt-2">JPG, PNG or GIF. Max size 2MB.</p>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-grey-700 mb-2">Full Name</label>
              <input
                v-model="profileForm.name"
                type="text"
                class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-grey-700 mb-2">Initials</label>
              <input
                v-model="profileForm.initials"
                type="text"
                maxlength="5"
                class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-grey-700 mb-2">Email Address</label>
            <input
              v-model="profileForm.email"
              type="email"
              class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-grey-700 mb-2">School</label>
            <input
              v-model="profileForm.school"
              type="text"
              class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Your school name"
            />
          </div>

          <div class="flex items-center justify-between pt-4 border-t border-grey-200">
            <p class="text-sm text-grey-600">Update your profile information</p>
            <button
              type="submit"
              :disabled="updatingProfile"
              class="px-6 py-2.5 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50"
            >
              {{ updatingProfile ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </form>
      </div>

      <!-- Security Tab -->
      <div v-show="activeTab === 'security'" class="p-6">
        <h2 class="text-lg font-semibold text-grey-900 mb-6">Security Settings</h2>
        
        <form @submit.prevent="changePassword" class="space-y-6 max-w-2xl">
          <div class="bg-primary-50 border border-primary-200 rounded-lg p-4">
            <div class="flex items-start gap-3">
              <ShieldCheckIcon class="w-6 h-6 text-primary-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 class="font-medium text-primary-900 mb-1">Password Requirements</h3>
                <ul class="text-sm text-primary-800 space-y-1">
                  <li>• Minimum 8 characters</li>
                  <li>• Mix of letters and numbers recommended</li>
                  <li>• Avoid using common passwords</li>
                </ul>
              </div>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-grey-700 mb-2">Current Password</label>
            <input
              v-model="passwordForm.current"
              type="password"
              class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-grey-700 mb-2">New Password</label>
            <input
              v-model="passwordForm.new"
              type="password"
              minlength="8"
              class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-grey-700 mb-2">Confirm New Password</label>
            <input
              v-model="passwordForm.confirm"
              type="password"
              minlength="8"
              class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div v-if="passwordError" class="bg-red-50 border border-red-200 rounded-lg p-4">
            <p class="text-sm text-red-800">{{ passwordError }}</p>
          </div>

          <div class="flex items-center justify-between pt-4 border-t border-grey-200">
            <p class="text-sm text-grey-600">Keep your account secure</p>
            <button
              type="submit"
              :disabled="changingPassword"
              class="px-6 py-2.5 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50"
            >
              {{ changingPassword ? 'Updating...' : 'Update Password' }}
            </button>
          </div>
        </form>
      </div>

      <!-- Preferences Tab -->
      <div v-show="activeTab === 'preferences'" class="p-6">
        <h2 class="text-lg font-semibold text-grey-900 mb-6">Preferences</h2>
        
        <div class="space-y-6 max-w-2xl">
          <!-- Notifications -->
          <div class="pb-6 border-b border-grey-200">
            <h3 class="font-medium text-grey-900 mb-4">Notifications</h3>
            <div class="space-y-4">
              <label class="flex items-center justify-between cursor-pointer group">
                <div>
                  <p class="font-medium text-grey-900 group-hover:text-primary-600 transition">Email Notifications</p>
                  <p class="text-sm text-grey-600">Receive email updates about your classes</p>
                </div>
                <input type="checkbox" v-model="preferences.emailNotifications" class="w-5 h-5 text-primary-600 rounded focus:ring-2 focus:ring-primary-500" />
              </label>

              <label class="flex items-center justify-between cursor-pointer group">
                <div>
                  <p class="font-medium text-grey-900 group-hover:text-primary-600 transition">Weekly Reports</p>
                  <p class="text-sm text-grey-600">Get weekly summaries of class activity</p>
                </div>
                <input type="checkbox" v-model="preferences.weeklyReports" class="w-5 h-5 text-primary-600 rounded focus:ring-2 focus:ring-primary-500" />
              </label>

              <label class="flex items-center justify-between cursor-pointer group">
                <div>
                  <p class="font-medium text-grey-900 group-hover:text-primary-600 transition">Attendance Reminders</p>
                  <p class="text-sm text-grey-600">Daily reminders to mark attendance</p>
                </div>
                <input type="checkbox" v-model="preferences.attendanceReminders" class="w-5 h-5 text-primary-600 rounded focus:ring-2 focus:ring-primary-500" />
              </label>
            </div>
          </div>

          <!-- Language & Region -->
          <div class="pb-6 border-b border-grey-200">
            <h3 class="font-medium text-grey-900 mb-4">Language & Region</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-grey-700 mb-2">Language</label>
                <select v-model="preferences.language" class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                  <option value="en">English</option>
                  <option value="fr">Français</option>
                  <option value="ar">العربية</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-grey-700 mb-2">Timezone</label>
                <select v-model="preferences.timezone" class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                  <option value="Africa/Tunis">Africa/Tunis (GMT+1)</option>
                  <option value="Europe/Paris">Europe/Paris (GMT+1)</option>
                  <option value="UTC">UTC (GMT+0)</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Theme -->
          <div>
            <h3 class="font-medium text-grey-900 mb-4">Appearance</h3>
            <div>
              <label class="block text-sm font-medium text-grey-700 mb-2">Theme</label>
              <div class="flex gap-3">
                <label class="flex-1 cursor-pointer">
                  <input type="radio" v-model="preferences.theme" value="light" class="sr-only" />
                  <div :class="[
                    'p-4 border-2 rounded-lg transition',
                    preferences.theme === 'light' ? 'border-primary-500 bg-primary-50' : 'border-grey-200 hover:border-grey-300'
                  ]">
                    <div class="flex items-center gap-3">
                      <div class="w-12 h-12 bg-white rounded border border-grey-300 flex items-center justify-center">
                        <SunIcon class="w-6 h-6 text-grey-700" />
                      </div>
                      <div>
                        <p class="font-medium text-grey-900">Light</p>
                        <p class="text-sm text-grey-600">Default theme</p>
                      </div>
                    </div>
                  </div>
                </label>

                <label class="flex-1 cursor-pointer opacity-50">
                  <input type="radio" value="dark" disabled class="sr-only" />
                  <div class="p-4 border-2 border-grey-200 rounded-lg">
                    <div class="flex items-center gap-3">
                      <div class="w-12 h-12 bg-grey-800 rounded border border-grey-700 flex items-center justify-center">
                        <MoonIcon class="w-6 h-6 text-grey-300" />
                      </div>
                      <div>
                        <p class="font-medium text-grey-900">Dark</p>
                        <p class="text-sm text-grey-600">Coming soon</p>
                      </div>
                    </div>
                  </div>
                </label>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-between pt-4 border-t border-grey-200">
            <p class="text-sm text-grey-600">Customize your experience</p>
            <button
              @click="savePreferences"
              class="px-6 py-2.5 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition"
            >
              Save Preferences
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { ShieldCheckIcon, SunIcon, MoonIcon } from '@heroicons/vue/24/outline';
import { useAuthStore } from '@/stores/auth';
import api from '@/services/api';

const authStore = useAuthStore();

const activeTab = ref('profile');
const updatingProfile = ref(false);
const changingPassword = ref(false);
const passwordError = ref('');

const tabs = [
  { id: 'profile', name: 'Profile' },
  { id: 'security', name: 'Security' },
  { id: 'preferences', name: 'Preferences' }
];

const profileForm = ref({
  name: '',
  email: '',
  initials: '',
  school: ''
});

const passwordForm = ref({
  current: '',
  new: '',
  confirm: ''
});

const preferences = ref({
  emailNotifications: true,
  weeklyReports: true,
  attendanceReminders: false,
  language: 'en',
  timezone: 'Africa/Tunis',
  theme: 'light'
});

const userInitials = computed(() => {
  return authStore.user?.initials || profileForm.value.initials || 'U';
});

async function updateProfile() {
  updatingProfile.value = true;
  try {
    const response = await api.updateTeacherProfile(profileForm.value);
    if (response.success) {
      authStore.updateUser(profileForm.value);
      alert('Profile updated successfully!');
    }
  } catch (error) {
    alert('Failed to update profile: ' + error.message);
  } finally {
    updatingProfile.value = false;
  }
}

async function changePassword() {
  passwordError.value = '';
  
  if (passwordForm.value.new !== passwordForm.value.confirm) {
    passwordError.value = 'New passwords do not match';
    return;
  }
  
  if (passwordForm.value.new.length < 8) {
    passwordError.value = 'Password must be at least 8 characters';
    return;
  }
  
  changingPassword.value = true;
  try {
    const response = await api.changePassword(
      passwordForm.value.current,
      passwordForm.value.new
    );
    if (response.success) {
      alert('Password changed successfully!');
      passwordForm.value = { current: '', new: '', confirm: '' };
    }
  } catch (error) {
    passwordError.value = error.message;
  } finally {
    changingPassword.value = false;
  }
}

function savePreferences() {
  localStorage.setItem('user_preferences', JSON.stringify(preferences.value));
  alert('Preferences saved successfully!');
}

function loadPreferences() {
  const saved = localStorage.getItem('user_preferences');
  if (saved) {
    preferences.value = { ...preferences.value, ...JSON.parse(saved) };
  }
}

onMounted(() => {
  if (authStore.user) {
    profileForm.value = {
      name: authStore.user.name || '',
      email: authStore.user.email || '',
      initials: authStore.user.initials || '',
      school: authStore.user.school || ''
    };
  }
  loadPreferences();
});
</script>