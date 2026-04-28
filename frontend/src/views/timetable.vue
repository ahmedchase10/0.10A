<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-grey-900">Weekly Timetable</h1>
        <p class="text-grey-600 mt-1">Your teaching schedule at a glance</p>
      </div>
      <button
        @click="handlePrint"
        class="flex items-center gap-2 px-4 py-2 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
      >
        <PrinterIcon class="w-5 h-5" />
        Print
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
    </div>

    <div v-else-if="timetableEntries.length === 0" class="text-center py-16 bg-white rounded-xl shadow-sm border border-grey-200">
      <CalendarDaysIcon class="w-16 h-16 mx-auto text-grey-300 mb-4" />
      <h3 class="text-lg font-medium text-grey-900 mb-2">No timetable entries yet</h3>
      <p class="text-grey-600">Create a class with a schedule to populate this timetable automatically.</p>
    </div>

    <div v-else class="bg-white rounded-xl shadow-sm border border-grey-200 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-grey-50 border-b border-grey-200">
              <th class="px-6 py-4 text-left text-sm font-semibold text-grey-700 w-36">Day</th>
              <th class="px-6 py-4 text-left text-sm font-semibold text-grey-700 w-36">Time</th>
              <th class="px-6 py-4 text-left text-sm font-semibold text-grey-700">Class</th>
              <th class="px-6 py-4 text-left text-sm font-semibold text-grey-700">Subject</th>
              <th class="px-6 py-4 text-left text-sm font-semibold text-grey-700">School</th>
              <th class="px-6 py-4 text-left text-sm font-semibold text-grey-700">Classroom</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="entry in timetableEntries"
              :key="entry.id"
              class="border-b border-grey-100 hover:bg-grey-50 transition"
            >
              <td class="px-6 py-4 font-medium text-grey-900">
                {{ dayLabel(entry.day_of_week) }}
              </td>
              <td class="px-6 py-4 text-grey-700">
                {{ entry.start_time }} - {{ entry.end_time }}
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div
                    class="w-3 h-3 rounded-full flex-shrink-0"
                    :style="{ backgroundColor: getClassColor(entry.class_id) }"
                  ></div>
                  <span class="font-medium text-grey-900">{{ entry.class_name }}</span>
                </div>
              </td>
              <td class="px-6 py-4 text-grey-700">
                {{ entry.subject }}
              </td>
              <td class="px-6 py-4 text-grey-700">
                {{ getClassSchool(entry.class_id) || 'No school set' }}
              </td>
              <td class="px-6 py-4 text-grey-700">
                {{ entry.classroom || 'No classroom set' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { CalendarDaysIcon, PrinterIcon } from '@heroicons/vue/24/outline';
import { useClassesStore } from '@/stores/classesStore';
import api from '@/services/api';

const loading = ref(true);
const timetableEntries = ref([]);
const classesStore = useClassesStore();

const dayMap = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday'
];

function dayLabel(day) {
  return dayMap[day] || `Day ${day}`;
}

function getClassMeta(classId) {
  return classesStore.classes.find(cls => cls.id === classId) || null;
}

function getClassSchool(classId) {
  return getClassMeta(classId)?.school || '';
}

function getClassColor(classId) {
  return getClassMeta(classId)?.color || '#3b82f6';
}

function handlePrint() {
  window.print();
}

async function loadTimetable() {
  try {
    await classesStore.load();
    const response = await api.getTimetable();
    if (response.success) {
      timetableEntries.value = response.timetable || [];
    }
  } catch (err) {
    console.error('Failed to load timetable:', err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadTimetable();
});
</script>

<style scoped>
@media print {
  .flex.items-center.justify-between.mb-8 button {
    display: none;
  }
}
</style>
