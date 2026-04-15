<template>
  <div class="p-8">
    <!-- Header -->
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

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-16">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="periods.length === 0" class="text-center py-16 bg-white rounded-xl shadow-sm border border-grey-200">
      <CalendarDaysIcon class="w-16 h-16 mx-auto text-grey-300 mb-4" />
      <h3 class="text-lg font-medium text-grey-900 mb-2">No schedule data</h3>
      <p class="text-grey-600">Add period information to your classes to see your timetable</p>
    </div>

    <!-- Timetable Grid -->
    <div v-else class="bg-white rounded-xl shadow-sm border border-grey-200 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-grey-50 border-b border-grey-200">
              <th class="px-6 py-4 text-left text-sm font-semibold text-grey-700 w-32">Period</th>
              <th
                v-for="day in days"
                :key="day"
                class="px-6 py-4 text-left text-sm font-semibold text-grey-700"
              >
                {{ day }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="period in periods"
              :key="period"
              class="border-b border-grey-100 hover:bg-grey-50 transition"
            >
              <td class="px-6 py-4 font-medium text-grey-900 bg-grey-50">{{ period }}</td>
              <td
                v-for="day in days"
                :key="day"
                class="px-6 py-4"
              >
                <div v-if="getClassForSlot(period)" class="flex items-start gap-3">
                  <div
                    class="w-1 h-full min-h-[60px] rounded-full flex-shrink-0"
                    :style="{ backgroundColor: getClassForSlot(period).color || '#3b82f6' }"
                  ></div>
                  <div class="flex-1">
                    <p class="font-medium text-grey-900">{{ getClassForSlot(period).name }}</p>
                    <p class="text-sm text-grey-600">{{ getClassForSlot(period).room || '' }}</p>
                  </div>
                </div>
                <div v-else class="text-grey-400 text-center">—</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Legend -->
      <div v-if="classesWithSubjects.length > 0" class="border-t border-grey-200 p-6">
        <h3 class="text-sm font-semibold text-grey-900 mb-3">Legend</h3>
        <div class="flex flex-wrap gap-4">
          <div
            v-for="cls in classesWithSubjects"
            :key="cls.id"
            class="flex items-center gap-2"
          >
            <div
              class="w-4 h-4 rounded"
              :style="{ backgroundColor: cls.color || '#3b82f6' }"
            ></div>
            <span class="text-sm text-grey-700">{{ cls.subject }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { CalendarDaysIcon, PrinterIcon } from '@heroicons/vue/24/outline';
import api from '@/services/api';

const loading = ref(true);
const classes = ref([]);

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

const periods = computed(() => {
  const periodsSet = new Set();
  
  classes.value.forEach(cls => {
    if (cls.period) {
      const match = cls.period.match(/\d+/);
      if (match) {
        periodsSet.add(`Period ${match[0]}`);
      } else {
        periodsSet.add(cls.period);
      }
    }
  });
  
  return Array.from(periodsSet).sort((a, b) => {
    const numA = parseInt(a.match(/\d+/)?.[0] || 0);
    const numB = parseInt(b.match(/\d+/)?.[0] || 0);
    return numA - numB;
  });
});

const classesWithSubjects = computed(() => {
  return classes.value.filter(cls => cls.subject);
});

function getClassForSlot(period) {
  // Note: This is simplified - in production you'd store day info in database
  return classes.value.find(cls => 
    cls.period && cls.period.includes(period.match(/\d+/)?.[0])
  );
}

function handlePrint() {
  window.print();
}

async function loadTimetable() {
  try {
    const response = await api.getClasses();
    if (response.success) {
      classes.value = response.classes || [];
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