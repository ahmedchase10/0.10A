<template>
  <div class="p-8 space-y-6">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-grey-900">Weekly Timetable</h1>
        <p class="text-grey-600 mt-1">Your teaching schedule at a glance</p>
      </div>
      <button
        @click="handlePrint"
        class="timetable-print-btn flex items-center gap-2 px-4 py-2 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
      >
        <PrinterIcon class="w-5 h-5" />
        Print
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
    </div>

    <div v-else-if="timetableEntries.length === 0" class="text-center py-16 bg-white rounded-2xl shadow-sm border border-grey-200">
      <CalendarDaysIcon class="w-16 h-16 mx-auto text-grey-300 mb-4" />
      <h3 class="text-lg font-medium text-grey-900 mb-2">No timetable entries yet</h3>
      <p class="text-grey-600">Create a class with a schedule to populate this timetable automatically.</p>
    </div>

    <div v-else class="space-y-4">
      <div class="flex flex-wrap gap-2">
        <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-grey-200 shadow-sm text-sm text-grey-700">
          <span class="w-2.5 h-2.5 rounded-full bg-primary-500"></span>
          {{ timetableEntries.length }} scheduled slot{{ timetableEntries.length !== 1 ? 's' : '' }}
        </div>
        <div
          v-for="cls in timetableClasses"
          :key="cls.id"
          class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-grey-200 shadow-sm text-sm text-grey-700"
        >
          <span class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: getClassColor(cls.id) }"></span>
          {{ cls.name }}
        </div>
      </div>

      <div class="overflow-x-auto rounded-2xl border border-grey-200 bg-white shadow-sm">
        <div class="min-w-[1100px]">
          <div
            class="grid border-b border-grey-200 bg-grey-50 sticky top-0 z-10"
            :style="timetableGridStyle"
          >
            <div class="px-4 py-4 text-xs font-semibold uppercase tracking-wider text-grey-500">
              Time
            </div>
            <div
              v-for="day in days"
              :key="day.index"
              class="px-4 py-4 text-center text-xs font-semibold uppercase tracking-wider text-grey-600"
            >
              <div>{{ day.short }}</div>
              <div class="mt-1 text-[11px] font-medium text-grey-400 normal-case">{{ day.long }}</div>
            </div>
          </div>

          <div
            v-for="slot in timeSlots"
            :key="`${slot.start_time}-${slot.end_time}`"
            class="grid border-b border-grey-100 last:border-b-0"
            :style="timetableGridStyle"
          >
            <div class="px-4 py-4 border-r border-grey-100 bg-grey-50/80">
              <div class="text-sm font-semibold text-grey-900">{{ slot.start_time }} - {{ slot.end_time }}</div>
              <div class="text-[11px] text-grey-500 mt-1">Time block</div>
            </div>

            <div
              v-for="day in days"
              :key="`${day.index}-${slot.start_time}-${slot.end_time}`"
              class="min-h-[120px] p-2 border-r border-grey-100 last:border-r-0 bg-white"
            >
              <div v-if="getEntriesForSlot(day.index, slot).length > 0" class="space-y-2">
                <article
                  v-for="entry in getEntriesForSlot(day.index, slot)"
                  :key="entry.id"
                  class="rounded-xl border p-3 shadow-sm"
                  :style="getEntryStyle(entry.class_id)"
                >
                  <div class="flex items-start justify-between gap-2">
                    <div class="min-w-0">
                      <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ backgroundColor: getClassColor(entry.class_id) }"></span>
                        <h3 class="font-semibold text-grey-900 truncate" :title="entry.class_name">{{ entry.class_name }}</h3>
                      </div>
                      <p class="text-xs font-medium mt-1" :style="{ color: getClassColor(entry.class_id) }">
                        {{ entry.subject }}
                      </p>
                    </div>
                    <span class="text-[10px] font-semibold uppercase tracking-wider px-2 py-1 rounded-full bg-white/70 text-grey-600 border border-white/80">
                      {{ day.short }}
                    </span>
                  </div>
                  <div class="mt-3 space-y-1 text-xs text-grey-700">
                    <div class="flex items-center justify-between gap-2">
                      <span class="text-grey-500">Classroom</span>
                      <span class="font-medium text-grey-900">{{ entry.classroom || 'Not set' }}</span>
                    </div>
                    <div class="flex items-center justify-between gap-2">
                      <span class="text-grey-500">School</span>
                      <span class="font-medium text-grey-900 truncate">{{ getClassSchool(entry.class_id) || 'Not set' }}</span>
                    </div>
                  </div>
                </article>
              </div>
              <div
                v-else
                class="h-full min-h-[104px] rounded-xl border border-dashed border-grey-100 bg-grey-50/30 flex items-center justify-center text-[11px] text-grey-400"
              >
                Free
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue';
import { CalendarDaysIcon, PrinterIcon } from '@heroicons/vue/24/outline';
import { useClassesStore } from '@/stores/classesStore';
import api from '@/services/api';

const loading = ref(true);
const timetableEntries = ref([]);
const classesStore = useClassesStore();

const days = [
  { index: 0, short: 'Mon', long: 'Monday' },
  { index: 1, short: 'Tue', long: 'Tuesday' },
  { index: 2, short: 'Wed', long: 'Wednesday' },
  { index: 3, short: 'Thu', long: 'Thursday' },
  { index: 4, short: 'Fri', long: 'Friday' },
  { index: 5, short: 'Sat', long: 'Saturday' },
  { index: 6, short: 'Sun', long: 'Sunday' },
];

const timetableGridStyle = { gridTemplateColumns: '140px repeat(7, minmax(140px, 1fr))' };

const timetableClasses = computed(() => {
  const seen = new Map();
  for (const entry of timetableEntries.value) {
    if (!seen.has(entry.class_id)) {
      seen.set(entry.class_id, {
        id: entry.class_id,
        name: entry.class_name,
      });
    }
  }
  return Array.from(seen.values());
});

const timeSlots = computed(() => {
  const seen = new Map();
  for (const entry of timetableEntries.value) {
    const key = `${entry.start_time}-${entry.end_time}`;
    if (!seen.has(key)) {
      seen.set(key, {
        start_time: entry.start_time,
        end_time: entry.end_time,
      });
    }
  }
  return Array.from(seen.values()).sort((a, b) => a.start_time.localeCompare(b.start_time) || a.end_time.localeCompare(b.end_time));
});

function getClassMeta(classId) {
  return classesStore.classes.find(cls => cls.id === classId) || null;
}

function getClassSchool(classId) {
  return getClassMeta(classId)?.school || '';
}

function getClassColor(classId) {
  return getClassMeta(classId)?.color || '#3b82f6';
}

function getEntriesForSlot(dayIndex, slot) {
  return timetableEntries.value.filter(
    entry => entry.day_of_week === dayIndex
      && entry.start_time === slot.start_time
      && entry.end_time === slot.end_time
  );
}

function hexToRgba(hex, alpha) {
  const cleaned = hex.replace('#', '').trim();
  if (cleaned.length === 3) {
    const r = parseInt(cleaned[0] + cleaned[0], 16);
    const g = parseInt(cleaned[1] + cleaned[1], 16);
    const b = parseInt(cleaned[2] + cleaned[2], 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  if (cleaned.length === 6) {
    const r = parseInt(cleaned.slice(0, 2), 16);
    const g = parseInt(cleaned.slice(2, 4), 16);
    const b = parseInt(cleaned.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  return hex;
}

function getEntryStyle(classId) {
  const color = getClassColor(classId);
  return {
    backgroundColor: hexToRgba(color, 0.12),
    borderColor: hexToRgba(color, 0.28),
    boxShadow: `inset 3px 0 0 ${color}`,
  };
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
  .timetable-print-btn {
    display: none;
  }
}
</style>
