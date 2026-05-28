<template>
  <div class="h-full overflow-y-auto custom-scrollbar bg-grey-50 dark:bg-grey-950 transition-colors duration-300">
    <!-- Header -->
    <div class="bg-white dark:bg-grey-900 border-b border-grey-200 dark:border-grey-800 px-8 py-6">
      <div class="flex items-center gap-3 text-sm text-grey-600 dark:text-grey-400 mb-4">
        <router-link :to="`/class/${route.params.id}`" class="hover:text-primary-600 dark:hover:text-sky-400 transition flex items-center gap-1">
          <ChevronLeftIcon class="w-4 h-4" />
          Back to Class
        </router-link>
        <span>/</span>
        <span class="text-grey-900 dark:text-grey-50 font-medium">Attendance</span>
      </div>

      <div class="flex items-start justify-between">
        <div>
          <h1 class="text-3xl font-bold text-grey-900 dark:text-grey-50 mb-2">Attendance</h1>
          <p class="text-grey-600 dark:text-grey-400">{{ classData?.name }}</p>
        </div>
        
        <!-- Date Selector -->
        <div class="flex items-center gap-4">
          <button
            @click="previousDay"
            class="p-2 hover:bg-grey-100 dark:hover:bg-grey-800 rounded-lg transition"
          >
            <ChevronLeftIcon class="w-5 h-5 text-grey-600 dark:text-grey-300" />
          </button>
          
          <input
            v-model="selectedDate"
            type="date"
            class="px-4 py-2 border border-grey-300 dark:border-grey-700 bg-white dark:bg-grey-950 text-grey-900 dark:text-grey-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            @change="loadAttendance"
          />
          
          <button
            @click="nextDay"
            :disabled="isToday"
            class="p-2 hover:bg-grey-100 dark:hover:bg-grey-800 rounded-lg transition disabled:opacity-50"
          >
            <ChevronRightIcon class="w-5 h-5 text-grey-600 dark:text-grey-300" />
          </button>
          
          <button
            @click="setToday"
            class="px-4 py-2 bg-grey-100 dark:bg-grey-800 text-grey-700 dark:text-grey-200 rounded-lg hover:bg-grey-200 dark:hover:bg-grey-700 transition text-sm font-medium"
          >
            Today
          </button>
        </div>
      </div>
    </div>

    <div class="p-8">
      <!-- Quick Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-grey-900 rounded-xl shadow-sm border border-grey-200 dark:border-grey-800 p-6">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 bg-primary-50 dark:bg-sky-950 rounded-lg flex items-center justify-center">
              <UserGroupIcon class="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <div class="text-2xl font-bold text-grey-900 dark:text-grey-50">{{ totalStudents }}</div>
              <div class="text-sm text-grey-600 dark:text-grey-400">Total Students</div>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-grey-900 rounded-xl shadow-sm border border-grey-200 dark:border-grey-800 p-6">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 bg-success-50 dark:bg-emerald-950 rounded-lg flex items-center justify-center">
              <CheckCircleIcon class="w-6 h-6 text-success-600" />
            </div>
            <div>
              <div class="text-2xl font-bold text-success-600">{{ presentCount }}</div>
              <div class="text-sm text-grey-600 dark:text-grey-400">Present</div>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-grey-900 rounded-xl shadow-sm border border-grey-200 dark:border-grey-800 p-6">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 bg-red-50 dark:bg-red-950 rounded-lg flex items-center justify-center">
              <XCircleIcon class="w-6 h-6 text-red-600" />
            </div>
            <div>
              <div class="text-2xl font-bold text-red-600">{{ absentCount }}</div>
              <div class="text-sm text-grey-600 dark:text-grey-400">Absent</div>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-grey-900 rounded-xl shadow-sm border border-grey-200 dark:border-grey-800 p-6">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 bg-grey-50 dark:bg-grey-800 rounded-lg flex items-center justify-center">
              <ChartBarIcon class="w-6 h-6 text-grey-600" />
            </div>
            <div>
              <div class="text-2xl font-bold text-grey-900 dark:text-grey-50">{{ attendanceRate }}%</div>
              <div class="text-sm text-grey-600 dark:text-grey-400">Attendance Rate</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Attendance Table -->
      <div class="bg-white dark:bg-grey-900 rounded-xl shadow-sm border border-grey-200 dark:border-grey-800">
        <div class="p-6 border-b border-grey-200 dark:border-grey-800 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-grey-900 dark:text-grey-50">Student Attendance</h2>
          <div class="flex items-center gap-3">
            <button
              @click="markAllPresent"
              class="px-4 py-2 bg-success-50 dark:bg-emerald-950 text-success-700 dark:text-emerald-300 rounded-lg hover:bg-success-100 dark:hover:bg-emerald-900 transition text-sm font-medium"
            >
              Mark All Present
            </button>
            <button
              @click="markAllAbsent"
              class="px-4 py-2 bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-100 dark:hover:bg-red-900 transition text-sm font-medium"
            >
              Mark All Absent
            </button>
            <button
              @click="saveAttendance"
              :disabled="saving || !hasChanges"
              class="px-6 py-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50"
            >
              {{ saving ? 'Saving...' : 'Save Attendance' }}
            </button>
          </div>
        </div>

        <div v-if="loading" class="p-12 flex items-center justify-center">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-primary-500 border-t-transparent"></div>
        </div>

        <div v-else-if="students.length === 0" class="p-12 text-center">
          <UserGroupIcon class="w-12 h-12 text-grey-300 dark:text-grey-600 mx-auto mb-3" />
          <p class="text-grey-600 dark:text-grey-400 mb-4">No students in this class yet</p>
          <router-link
            :to="`/class/${route.params.id}`"
            class="text-primary-600 dark:text-sky-400 font-medium hover:text-primary-700 dark:hover:text-sky-300"
          >
            Add students to start tracking attendance
          </router-link>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-grey-50 dark:bg-grey-950 border-b border-grey-200 dark:border-grey-800">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-grey-500 dark:text-grey-400 uppercase tracking-wider">Student</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-grey-500 dark:text-grey-400 uppercase tracking-wider">Email</th>
                <th class="px-6 py-3 text-center text-xs font-medium text-grey-500 dark:text-grey-400 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-center text-xs font-medium text-grey-500 dark:text-grey-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-grey-200 dark:divide-grey-800">
              <tr
                v-for="student in students"
                :key="student.id"
                :class="[
                  'hover:bg-grey-50 dark:hover:bg-grey-800 transition',
                  attendanceMap[student.id] === true ? 'bg-success-50/30 dark:bg-emerald-950/20' : attendanceMap[student.id] === false ? 'bg-red-50/30 dark:bg-red-950/20' : ''
                ]"
              >
                <td class="px-6 py-4">
                  <div class="flex items-center gap-3">
                      <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center text-white font-semibold">
                      {{ student.name.charAt(0).toUpperCase() }}
                    </div>
                    <span class="font-medium text-grey-900 dark:text-grey-50">{{ student.name }}</span>
                  </div>
                </td>
                <td class="px-6 py-4 text-sm text-grey-600 dark:text-grey-400">{{ student.email }}</td>
                <td class="px-6 py-4 text-center">
                  <span
                    v-if="attendanceMap[student.id] === true"
                    class="inline-flex items-center gap-1 px-3 py-1 bg-success-50 dark:bg-emerald-950 text-success-700 dark:text-emerald-300 rounded-full text-sm font-medium"
                  >
                    <CheckCircleIcon class="w-4 h-4" />
                    Present
                  </span>
                  <span
                    v-else-if="attendanceMap[student.id] === false"
                    class="inline-flex items-center gap-1 px-3 py-1 bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300 rounded-full text-sm font-medium"
                  >
                    <XCircleIcon class="w-4 h-4" />
                    Absent
                  </span>
                  <span v-else class="inline-flex items-center gap-1 px-3 py-1 bg-grey-50 dark:bg-grey-800 text-grey-700 dark:text-grey-200 rounded-full text-sm font-medium">
                    Not Marked
                  </span>
                </td>
                <td class="px-6 py-4">
                  <div class="flex items-center justify-center gap-2">
                    <button
                      @click="markPresent(student.id)"
                      :class="[
                        'px-4 py-2 rounded-lg text-sm font-medium transition',
                        attendanceMap[student.id] === true
                          ? 'bg-success-600 text-white'
                          : 'bg-success-50 dark:bg-emerald-950 text-success-700 dark:text-emerald-300 hover:bg-success-100 dark:hover:bg-emerald-900'
                      ]"
                    >
                      Present
                    </button>
                    <button
                      @click="markAbsent(student.id)"
                      :class="[
                        'px-4 py-2 rounded-lg text-sm font-medium transition',
                        attendanceMap[student.id] === false
                          ? 'bg-red-600 text-white'
                          : 'bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900'
                      ]"
                    >
                      Absent
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  UserGroupIcon,
  CheckCircleIcon,
  XCircleIcon,
  ChartBarIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline';
import api from '@/services/api';

const route = useRoute();

const classData = ref(null);
const students = ref([]);
const attendanceMap = ref({});
const originalAttendanceMap = ref({});
const loading = ref(true);
const saving = ref(false);
const selectedDate = ref(new Date().toISOString().split('T')[0]);

const totalStudents = computed(() => students.value.length);

const presentCount = computed(() => {
  return Object.values(attendanceMap.value).filter(v => v === true).length;
});

const absentCount = computed(() => {
  return Object.values(attendanceMap.value).filter(v => v === false).length;
});

const attendanceRate = computed(() => {
  if (totalStudents.value === 0) return 0;
  return Math.round((presentCount.value / totalStudents.value) * 100);
});

const isToday = computed(() => {
  return selectedDate.value === new Date().toISOString().split('T')[0];
});

const hasChanges = computed(() => {
  return JSON.stringify(attendanceMap.value) !== JSON.stringify(originalAttendanceMap.value);
});

function previousDay() {
  const date = new Date(selectedDate.value);
  date.setDate(date.getDate() - 1);
  selectedDate.value = date.toISOString().split('T')[0];
}

function nextDay() {
  const date = new Date(selectedDate.value);
  date.setDate(date.getDate() + 1);
  if (date <= new Date()) {
    selectedDate.value = date.toISOString().split('T')[0];
  }
}

function setToday() {
  selectedDate.value = new Date().toISOString().split('T')[0];
}

function markPresent(studentId) {
  attendanceMap.value[studentId] = true;
}

function markAbsent(studentId) {
  attendanceMap.value[studentId] = false;
}

function markAllPresent() {
  students.value.forEach(student => {
    attendanceMap.value[student.id] = true;
  });
}

function markAllAbsent() {
  students.value.forEach(student => {
    attendanceMap.value[student.id] = false;
  });
}

async function loadClass() {
  try {
    const response = await api.getClasses();
    if (response.success) {
      classData.value = response.classes.find(c => c.id === parseInt(route.params.id));
    }
  } catch (error) {
    console.error('Failed to load class:', error);
  }
}

async function loadStudents() {
  try {
    const response = await api.getStudents(route.params.id);
    if (response.success) {
      students.value = response.students || [];
    }
  } catch (error) {
    console.error('Failed to load students:', error);
  }
}

async function loadAttendance() {
  loading.value = true;
  try {
    const response = await api.getAttendance(route.params.id, selectedDate.value);
    if (response.success) {
      // Map attendance data
      const newMap = {};
      response.attendance.forEach(record => {
        newMap[record.student_id] = record.present;
      });
      attendanceMap.value = newMap;
      originalAttendanceMap.value = { ...newMap };
    }
  } catch (error) {
    // No attendance records for this date yet
    attendanceMap.value = {};
    originalAttendanceMap.value = {};
  } finally {
    loading.value = false;
  }
}

async function saveAttendance() {
  if (!hasChanges.value) return;
  
  saving.value = true;
  try {
    const records = Object.entries(attendanceMap.value)
      .filter(([_, present]) => present !== undefined)
      .map(([student_id, present]) => ({
        student_id: parseInt(student_id),
        present
      }));

    if (records.length === 0) {
      alert('Please mark attendance for at least one student');
      return;
    }

    const response = await api.createAttendance({
      class_id: parseInt(route.params.id),
      session_date: selectedDate.value,
      records
    });

    if (response.success) {
      originalAttendanceMap.value = { ...attendanceMap.value };
      alert('Attendance saved successfully!');
    }
  } catch (error) {
    alert('Failed to save attendance: ' + error.message);
  } finally {
    saving.value = false;
  }
}

// Watch for date changes
watch(selectedDate, () => {
  loadAttendance();
});

onMounted(async () => {
  await loadClass();
  await loadStudents();
  await loadAttendance();
});
</script>
