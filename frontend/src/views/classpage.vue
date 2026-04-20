<template>
  <div class="h-full overflow-y-auto custom-scrollbar bg-grey-50">

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="bg-white border-b border-grey-200">
        <!-- Color bar -->
        <div class="h-2 w-full" :style="{ backgroundColor: classData?.color || '#3b82f6' }"></div>

        <div class="px-8 py-6">
          <!-- Breadcrumb -->
          <div class="flex items-center gap-2 text-sm text-grey-500 mb-4">
            <router-link to="/" class="hover:text-primary-600 transition">Dashboard</router-link>
            <span>/</span>
            <span class="text-grey-900 font-medium truncate">{{ classData?.name }}</span>
          </div>

          <div class="flex items-start justify-between gap-4">
            <div>
              <h1 class="text-3xl font-bold text-grey-900 mb-2">{{ classData?.name }}</h1>
              <div class="flex flex-wrap items-center gap-3">
                <span v-if="classData?.subject" class="inline-flex items-center gap-1.5 px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm font-medium">
                  <AcademicCapIcon class="w-3.5 h-3.5" />
                  {{ classData.subject }}
                </span>
                <span v-if="classData?.period" class="inline-flex items-center gap-1.5 px-3 py-1 bg-grey-100 text-grey-700 rounded-full text-sm">
                  <ClockIcon class="w-3.5 h-3.5" />
                  {{ classData.period }}
                </span>
                <span v-if="classData?.room" class="inline-flex items-center gap-1.5 px-3 py-1 bg-grey-100 text-grey-700 rounded-full text-sm">
                  <HomeIcon class="w-3.5 h-3.5" />
                  {{ classData.room }}
                </span>
                <span v-if="classData?.school" class="inline-flex items-center gap-1.5 px-3 py-1 bg-grey-100 text-grey-700 rounded-full text-sm">
                  <BuildingOfficeIcon class="w-3.5 h-3.5" />
                  {{ classData.school }}
                </span>
              </div>
            </div>

            <!-- Edit / Delete -->
            <div class="flex items-center gap-2 flex-shrink-0">
              <button
                @click="showEditModal = true"
                class="flex items-center gap-2 px-4 py-2 border border-grey-300 text-grey-700 rounded-lg text-sm font-medium hover:bg-grey-50 transition"
              >
                <PencilIcon class="w-4 h-4" />
                Edit
              </button>
              <button
                @click="handleDeleteClass"
                class="flex items-center gap-2 px-4 py-2 border border-red-200 text-red-600 rounded-lg text-sm font-medium hover:bg-red-50 transition"
              >
                <TrashIcon class="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="px-8 pt-6 grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-xl border border-grey-200 shadow-sm p-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center">
              <UserGroupIcon class="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <div class="text-xl font-bold text-grey-900">{{ stats.students }}</div>
              <div class="text-xs text-grey-500">Students</div>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl border border-grey-200 shadow-sm p-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-violet-50 rounded-lg flex items-center justify-center">
              <ClipboardDocumentListIcon class="w-5 h-5 text-violet-600" />
            </div>
            <div>
              <div class="text-xl font-bold text-grey-900">{{ stats.examTypes }}</div>
              <div class="text-xs text-grey-500">Exam Types</div>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl border border-grey-200 shadow-sm p-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-success-50 rounded-lg flex items-center justify-center">
              <DocumentArrowUpIcon class="w-5 h-5 text-success-600" />
            </div>
            <div>
              <div class="text-xl font-bold text-grey-900">{{ stats.lessons }}</div>
              <div class="text-xs text-grey-500">Lessons</div>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl border border-grey-200 shadow-sm p-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center">
              <CalendarDaysIcon class="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <div class="text-xl font-bold text-grey-900">{{ formatShortDate(classData?.created_at) }}</div>
              <div class="text-xs text-grey-500">Created</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation Cards -->
      <div class="px-8 pb-8 grid grid-cols-1 md:grid-cols-2 gap-5">

        <!-- Students -->
        <router-link :to="`/class/${classId}/students`" class="group">
          <div class="bg-white rounded-xl border border-grey-200 shadow-sm p-6 hover:shadow-md hover:border-primary-300 transition cursor-pointer">
            <div class="flex items-start justify-between mb-4">
              <div class="w-12 h-12 bg-primary-50 group-hover:bg-primary-100 rounded-xl flex items-center justify-center transition">
                <UserGroupIcon class="w-6 h-6 text-primary-600" />
              </div>
              <ChevronRightIcon class="w-5 h-5 text-grey-400 group-hover:text-primary-500 group-hover:translate-x-1 transition" />
            </div>
            <h3 class="text-lg font-semibold text-grey-900 mb-1">Students</h3>
            <p class="text-sm text-grey-500">Manage class roster, add or remove students.</p>
            <div class="mt-4 flex items-center gap-2">
              <span class="text-xs font-medium text-primary-600 bg-primary-50 px-2.5 py-1 rounded-full">
                {{ stats.students }} enrolled
              </span>
            </div>
          </div>
        </router-link>

        <!-- Attendance -->
        <router-link :to="`/class/${classId}/attendance`" class="group">
          <div class="bg-white rounded-xl border border-grey-200 shadow-sm p-6 hover:shadow-md hover:border-success-300 transition cursor-pointer">
            <div class="flex items-start justify-between mb-4">
              <div class="w-12 h-12 bg-success-50 group-hover:bg-success-100 rounded-xl flex items-center justify-center transition">
                <ClipboardDocumentCheckIcon class="w-6 h-6 text-success-600" />
              </div>
              <ChevronRightIcon class="w-5 h-5 text-grey-400 group-hover:text-success-500 group-hover:translate-x-1 transition" />
            </div>
            <h3 class="text-lg font-semibold text-grey-900 mb-1">Attendance</h3>
            <p class="text-sm text-grey-500">Mark and review daily attendance records.</p>
            <div class="mt-4 flex items-center gap-2">
              <span class="text-xs font-medium text-success-700 bg-success-50 px-2.5 py-1 rounded-full">
                Today: {{ formatTodayDate() }}
              </span>
            </div>
          </div>
        </router-link>

        <!-- Grades -->
        <router-link :to="`/class/${classId}/grades`" class="group">
          <div class="bg-white rounded-xl border border-grey-200 shadow-sm p-6 hover:shadow-md hover:border-violet-300 transition cursor-pointer">
            <div class="flex items-start justify-between mb-4">
              <div class="w-12 h-12 bg-violet-50 group-hover:bg-violet-100 rounded-xl flex items-center justify-center transition">
                <ChartBarIcon class="w-6 h-6 text-violet-600" />
              </div>
              <ChevronRightIcon class="w-5 h-5 text-grey-400 group-hover:text-violet-500 group-hover:translate-x-1 transition" />
            </div>
            <h3 class="text-lg font-semibold text-grey-900 mb-1">Grades</h3>
            <p class="text-sm text-grey-500">Enter, edit, and review grades per exam type.</p>
            <div class="mt-4 flex items-center gap-2">
              <span class="text-xs font-medium text-violet-700 bg-violet-50 px-2.5 py-1 rounded-full">
                {{ stats.examTypes }} exam type{{ stats.examTypes !== 1 ? 's' : '' }}
              </span>
            </div>
          </div>
        </router-link>

        <!-- Lessons -->
        <router-link :to="`/class/${classId}/lessons`" class="group">
          <div class="bg-white rounded-xl border border-grey-200 shadow-sm p-6 hover:shadow-md hover:border-amber-300 transition cursor-pointer">
            <div class="flex items-start justify-between mb-4">
              <div class="w-12 h-12 bg-amber-50 group-hover:bg-amber-100 rounded-xl flex items-center justify-center transition">
                <DocumentTextIcon class="w-6 h-6 text-amber-600" />
              </div>
              <ChevronRightIcon class="w-5 h-5 text-grey-400 group-hover:text-amber-500 group-hover:translate-x-1 transition" />
            </div>
            <h3 class="text-lg font-semibold text-grey-900 mb-1">Lessons</h3>
            <p class="text-sm text-grey-500">Upload and manage PDF teaching materials.</p>
            <div class="mt-4 flex items-center gap-2">
              <span class="text-xs font-medium text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full">
                {{ stats.lessons }} file{{ stats.lessons !== 1 ? 's' : '' }} uploaded
              </span>
            </div>
          </div>
        </router-link>

      </div>
    </template>

    <!-- Edit Class Modal -->
    <TransitionRoot :show="showEditModal" as="template">
      <Dialog @close="showEditModal = false" class="relative z-50">
        <TransitionChild enter="ease-out duration-200" enter-from="opacity-0" enter-to="opacity-100"
          leave="ease-in duration-150" leave-from="opacity-100" leave-to="opacity-0">
          <div class="fixed inset-0 bg-black/25 backdrop-blur-sm" />
        </TransitionChild>
        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild enter="ease-out duration-200" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
              leave="ease-in duration-150" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95">
              <DialogPanel class="w-full max-w-md bg-white rounded-2xl shadow-xl">
                <div class="p-6 border-b border-grey-200">
                  <DialogTitle class="text-xl font-semibold text-grey-900">Edit Class</DialogTitle>
                </div>
                <form @submit.prevent="submitEdit" class="p-6 space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Class Name *</label>
                    <input v-model="editForm.name" type="text" required
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="e.g. 3G — Mathematics" />
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">Subject</label>
                      <input v-model="editForm.subject" type="text"
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="Mathematics" />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">Period</label>
                      <input v-model="editForm.period" type="text"
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="Period 3" />
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">Room</label>
                      <input v-model="editForm.room" type="text"
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="Room 204" />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">School</label>
                      <input v-model="editForm.school" type="text"
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="Lycée Pilote" />
                    </div>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Color</label>
                    <div class="grid grid-cols-6 gap-3">
                      <label v-for="color in colors" :key="color" class="relative cursor-pointer">
                        <input type="radio" v-model="editForm.color" :value="color" class="sr-only" />
                        <div
                          :class="['w-10 h-10 rounded-lg transition', editForm.color === color ? 'ring-2 ring-offset-2 ring-primary-500' : '']"
                          :style="{ backgroundColor: color }"
                        ></div>
                      </label>
                    </div>
                  </div>
                  <div v-if="editError" class="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p class="text-sm text-red-700">{{ editError }}</p>
                  </div>
                  <div class="flex gap-3 pt-2">
                    <button type="button" @click="showEditModal = false"
                      class="flex-1 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition">
                      Cancel
                    </button>
                    <button type="submit" :disabled="saving"
                      class="flex-1 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50">
                      {{ saving ? 'Saving…' : 'Save Changes' }}
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
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  AcademicCapIcon,
  ClockIcon,
  HomeIcon,
  BuildingOfficeIcon,
  UserGroupIcon,
  ClipboardDocumentCheckIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
  DocumentTextIcon,
  DocumentArrowUpIcon,
  CalendarDaysIcon,
  ChevronRightIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/vue/24/outline';
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import api from '@/services/api';

const route = useRoute();
const router = useRouter();
const classId = computed(() => parseInt(route.params.id));

const loading = ref(true);
const classData = ref(null);
const stats = ref({ students: 0, examTypes: 0, lessons: 0 });

// Edit modal
const showEditModal = ref(false);
const saving = ref(false);
const editError = ref('');
const editForm = ref({ name: '', subject: '', period: '', room: '', school: '', color: '#3b82f6' });

const colors = [
  '#3b82f6', '#22c55e', '#06b6d4', '#8b5cf6',
  '#ec4899', '#f59e0b', '#ef4444', '#10b981',
  '#6366f1', '#84cc16', '#f97316', '#14b8a6'
];

function formatShortDate(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

function formatTodayDate() {
  return new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

async function loadClass() {
  try {
    const res = await api.getClasses();
    if (res.success) {
      classData.value = res.classes.find(c => c.id === classId.value) || null;
    }
  } catch (e) {
    console.error(e);
  }
}

async function loadStats() {
  try {
    const [studentsRes, examTypesRes, lessonsRes] = await Promise.allSettled([
      api.getStudents(classId.value),
      api.getExamTypes(classId.value),
      api.getLessons(classId.value, { limit: 1, refresh: false })
    ]);

    if (studentsRes.status === 'fulfilled' && studentsRes.value.success)
      stats.value.students = studentsRes.value.students?.length ?? 0;

    if (examTypesRes.status === 'fulfilled' && examTypesRes.value.success)
      stats.value.examTypes = examTypesRes.value.exam_types?.length ?? 0;

    if (lessonsRes.status === 'fulfilled' && lessonsRes.value.success)
      stats.value.lessons = lessonsRes.value.uploads?.length ?? 0;
  } catch (e) {
    console.error(e);
  }
}

function openEdit() {
  if (!classData.value) return;
  editForm.value = {
    name: classData.value.name || '',
    subject: classData.value.subject || '',
    period: classData.value.period || '',
    room: classData.value.room || '',
    school: classData.value.school || '',
    color: classData.value.color || '#3b82f6'
  };
  editError.value = '';
  showEditModal.value = true;
}

async function submitEdit() {
  editError.value = '';
  saving.value = true;
  try {
    const res = await api.updateClass(classId.value, {
      name: editForm.value.name,
      subject: editForm.value.subject
    });
    if (res.success) {
      // Merge all fields locally (backend only stores name+subject, rest is local display)
      classData.value = { ...classData.value, ...editForm.value, ...res.class };
      showEditModal.value = false;
    }
  } catch (err) {
    editError.value = err.message || 'Failed to update class';
  } finally {
    saving.value = false;
  }
}

async function handleDeleteClass() {
  if (!confirm(`Delete class "${classData.value?.name}"? This cannot be undone.`)) return;
  try {
    await api.deleteClass(classId.value);
    router.push('/');
  } catch (err) {
    alert('Failed to delete: ' + err.message);
  }
}

onMounted(async () => {
  await loadClass();
  await loadStats();
  loading.value = false;
});
</script>