<template>
  <div class="p-8">
    <!-- Header -->
    <div class="mb-8 flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-grey-900">My Classes</h1>
        <p class="text-grey-600 mt-1">Manage your teaching schedule</p>
      </div>
      <button
        @click="showCreateModal = true"
        class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-3 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 shadow-sm transition"
      >
        <PlusIcon class="w-5 h-5" />
        New Class
      </button>
    </div>

    <!-- Loading -->
    <div v-if="classesStore.loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="classesStore.classes.length === 0" class="text-center py-16">
      <div class="inline-flex items-center justify-center w-16 h-16 bg-grey-100 rounded-full mb-4">
        <AcademicCapIcon class="w-8 h-8 text-grey-400" />
      </div>
      <h3 class="text-lg font-medium text-grey-900 mb-2">No classes yet</h3>
      <p class="text-grey-600 mb-6">Create your first class to get started</p>
      <button
        @click="showCreateModal = true"
        class="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition"
      >
        <PlusIcon class="w-5 h-5" />
        Create Your First Class
      </button>
    </div>

    <!-- Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="cls in classesStore.classes"
        :key="cls.id"
        class="bg-white rounded-xl shadow-sm border border-grey-200 overflow-hidden hover:shadow-md transition group cursor-pointer"
        @click="$router.push(`/class/${cls.id}`)"
      >
        <div
          class="h-32 p-6 relative overflow-hidden"
          :style="{ background: `linear-gradient(135deg, ${cls.color || '#3b82f6'} 0%, ${adjustColor(cls.color || '#3b82f6', -20)} 100%)` }"
        >
          <div class="relative z-10">
            <h3 class="text-xl font-semibold text-white mb-1">{{ cls.name }}</h3>
            <p class="text-white/90 text-sm">{{ cls.subject || 'No subject' }}</p>
          </div>
          <div class="absolute inset-0 bg-white/10 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition"></div>
        </div>

        <div class="p-6 space-y-3">
          <div class="flex items-center gap-2 text-sm text-grey-600">
            <ClockIcon class="w-4 h-4" />
            {{ formatScheduleSummary(getClassSchedule(cls.id)) }}
          </div>
          <div class="flex items-center gap-2 text-sm text-grey-600">
            <HomeIcon class="w-4 h-4" />
            {{ getClassSchedule(cls.id)?.classroom || 'No classroom set' }}
          </div>
          <div class="flex items-center gap-2 text-sm text-grey-600">
            <BuildingOfficeIcon class="w-4 h-4" />
            {{ cls.school || 'No school set' }}
          </div>
        </div>

        <div class="px-6 py-4 bg-grey-50 border-t border-grey-200">
          <button class="text-primary-600 font-medium text-sm hover:text-primary-700 transition flex items-center gap-2 group">
            Open Class
            <ChevronRightIcon class="w-4 h-4 group-hover:translate-x-1 transition" />
          </button>
        </div>
      </div>
    </div>

    <!-- Create Class Modal -->
    <TransitionRoot :show="showCreateModal" as="template">
      <Dialog @close="showCreateModal = false" class="relative z-50">
        <TransitionChild enter="ease-out duration-300" enter-from="opacity-0" enter-to="opacity-100"
          leave="ease-in duration-200" leave-from="opacity-100" leave-to="opacity-0">
          <div class="fixed inset-0 bg-black/25 backdrop-blur-sm" />
        </TransitionChild>

        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild enter="ease-out duration-300" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
              leave="ease-in duration-200" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95">
              <DialogPanel class="w-full max-w-md bg-white rounded-2xl shadow-xl">
                <div class="p-6 border-b border-grey-200">
                  <DialogTitle class="text-xl font-semibold text-grey-900">Create New Class</DialogTitle>
                </div>

                <form @submit.prevent="handleCreateClass" class="p-6 space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Class Name *</label>
                    <input
                      v-model="createForm.name"
                      type="text"
                      required
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="e.g. 3G - Mathematics"
                    />
                  </div>

                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">Subject</label>
                      <input
                        v-model="createForm.subject"
                        type="text"
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="Mathematics"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">School</label>
                      <input
                        v-model="createForm.school"
                        type="text"
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="Lycee Pilote"
                      />
                    </div>
                  </div>

                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">Day *</label>
                      <select
                        v-model="createForm.day_of_week"
                        required
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
                      >
                        <option :value="null" disabled>Select day</option>
                        <option v-for="day in dayOptions" :key="day.value" :value="day.value">
                          {{ day.label }}
                        </option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">Classroom</label>
                      <input
                        v-model="createForm.classroom"
                        type="text"
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="Room 204"
                      />
                    </div>
                  </div>

                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">Start Time *</label>
                      <input
                        v-model="createForm.start_time"
                        type="time"
                        required
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">End Time *</label>
                      <input
                        v-model="createForm.end_time"
                        type="time"
                        required
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Class Color</label>
                    <div class="grid grid-cols-6 gap-3">
                      <label v-for="color in colors" :key="color" class="relative cursor-pointer">
                        <input type="radio" v-model="createForm.color" :value="color" class="sr-only" />
                        <div
                          :class="['w-10 h-10 rounded-lg transition', createForm.color === color ? 'ring-2 ring-offset-2 ring-primary-500' : '']"
                          :style="{ backgroundColor: color }"
                        ></div>
                      </label>
                    </div>
                  </div>

                  <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p class="text-sm text-red-800">{{ error }}</p>
                  </div>

                  <div class="flex gap-3 pt-4">
                    <button
                      type="button"
                      @click="showCreateModal = false"
                      class="flex-1 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      :disabled="creating"
                      class="flex-1 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50"
                    >
                      {{ creating ? 'Creating...' : 'Create Class' }}
                    </button>
                  </div>
                </form>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import {
  PlusIcon,
  AcademicCapIcon,
  ClockIcon,
  HomeIcon,
  BuildingOfficeIcon,
  ChevronRightIcon
} from '@heroicons/vue/24/outline';
import { useClassesStore } from '@/stores/classesStore';
import api from '@/services/api';

const classesStore = useClassesStore();

const showCreateModal = ref(false);
const creating = ref(false);
const error = ref('');
const timetable = ref([]);

const colors = [
  '#3b82f6', '#22c55e', '#06b6d4', '#8b5cf6',
  '#ec4899', '#f59e0b', '#ef4444', '#10b981',
  '#6366f1', '#84cc16', '#f97316', '#14b8a6'
];

const dayOptions = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' }
];

const createForm = ref({
  name: '',
  subject: '',
  school: '',
  color: '#3b82f6',
  day_of_week: null,
  start_time: '08:00',
  end_time: '09:00',
  classroom: ''
});

function adjustColor(color, percent) {
  const num = parseInt(color.replace('#', ''), 16);
  const amt = Math.round(2.55 * percent);
  const R = Math.max(0, Math.min(255, (num >> 16) + amt));
  const G = Math.max(0, Math.min(255, ((num >> 8) & 0x00ff) + amt));
  const B = Math.max(0, Math.min(255, (num & 0x0000ff) + amt));
  return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
}

function dayLabel(day) {
  return dayOptions.find(option => option.value === day)?.label || 'Unknown day';
}

function getClassSchedule(classId) {
  return timetable.value.find(entry => entry.class_id === classId) || null;
}

function formatScheduleSummary(entry) {
  if (!entry) return 'No schedule set';
  return `${dayLabel(entry.day_of_week)} ${entry.start_time} - ${entry.end_time}`;
}

async function loadTimetable() {
  try {
    const response = await api.getTimetable();
    if (response.success) {
      timetable.value = response.timetable || [];
    }
  } catch (err) {
    console.error('Failed to load timetable on dashboard:', err);
  }
}

async function handleCreateClass() {
  creating.value = true;
  error.value = '';
  try {
    const classResponse = await api.createClass({
      name: createForm.value.name,
      subject: createForm.value.subject,
      school: createForm.value.school || null,
      color: createForm.value.color || null
    });

    if (classResponse.success) {
      classesStore.add(classResponse.class);

      try {
        await api.createTimetable([{
          class_id: classResponse.class.id,
          day_of_week: createForm.value.day_of_week,
          start_time: createForm.value.start_time,
          end_time: createForm.value.end_time,
          classroom: createForm.value.classroom || null
        }]);
      } catch (scheduleErr) {
        console.error('Failed to create timetable entry:', scheduleErr);
      }

      await loadTimetable();
      showCreateModal.value = false;
      createForm.value = {
        name: '',
        subject: '',
        school: '',
        color: '#3b82f6',
        day_of_week: null,
        start_time: '08:00',
        end_time: '09:00',
        classroom: ''
      };
    }
  } catch (err) {
    error.value = err.message;
  } finally {
    creating.value = false;
  }
}

onMounted(() => {
  classesStore.load().then(loadTimetable);
});
</script>
