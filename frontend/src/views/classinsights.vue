<template>
  <div class="h-full overflow-y-auto custom-scrollbar bg-slate-950 text-slate-100">

    <!-- Header -->
    <div class="bg-slate-900/95 border-b border-slate-800 px-8 py-6">
      <div class="flex items-center gap-2 text-sm text-slate-400 mb-4">
        <router-link :to="`/class/${classId}`" class="hover:text-primary-600 transition flex items-center gap-1">
          <ChevronLeftIcon class="w-4 h-4" />
          Back to Class
        </router-link>
        <span>/</span>
        <span class="text-slate-100 font-medium">Insights</span>
      </div>
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-slate-100 mb-1 flex items-center gap-3">
            <span class="inline-flex items-center justify-center w-10 h-10 bg-indigo-100 rounded-xl">
              <LightBulbIcon class="w-5 h-5 text-indigo-600" />
            </span>
            Class Insights
          </h1>
          <p class="text-slate-400 ml-13">AI-generated analytics from exam corrections</p>
        </div>
        <!-- Scope filter -->
        <div class="flex items-center gap-2">
          <button v-for="s in scopes" :key="s.value"
            @click="activeScope = s.value; loadAll()"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium transition border',
              activeScope === s.value
                ? 'bg-indigo-600 text-white border-indigo-600'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:border-indigo-400 hover:text-indigo-300'
            ]">
            {{ s.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Tab bar -->
    <div class="bg-slate-900 border-b border-slate-800 px-8">
      <nav class="flex gap-1">
        <button v-for="tab in tabs" :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'px-5 py-3.5 text-sm font-medium border-b-2 transition',
            activeTab === tab.id
              ? 'border-indigo-600 text-indigo-700'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          ]">
          {{ tab.label }}
        </button>
      </nav>
    </div>

    <div class="p-8">
      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-20">
        <div class="animate-spin rounded-full h-12 w-12 border-4 border-indigo-500 border-t-transparent"></div>
      </div>

      <!-- ── TAB: Cohort Topic Insights ──────────────────────────────────── -->
      <div v-else-if="activeTab === 'cohort'">
        <div v-if="!cohortInsights.length" class="bg-slate-900 rounded-xl border border-slate-800 p-16 text-center">
          <LightBulbIcon class="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <p class="text-slate-400">No cohort insights yet. Grade some exams first.</p>
        </div>

        <div v-else class="space-y-4">
          <!-- Summary row -->
          <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="bg-slate-900 rounded-xl border border-slate-800 p-5 shadow-sm">
              <p class="text-2xl font-bold text-slate-100">{{ cohortInsights.length }}</p>
              <p class="text-sm text-slate-400 mt-1">Topics Analysed</p>
            </div>
            <div class="bg-red-900/20 rounded-xl border border-red-800 p-5 shadow-sm">
              <p class="text-2xl font-bold text-red-300">{{ weakTopics.length }}</p>
              <p class="text-sm text-red-300 mt-1">Topics Needing Remediation</p>
            </div>
            <div class="bg-emerald-900/20 rounded-xl border border-emerald-800 p-5 shadow-sm">
              <p class="text-2xl font-bold text-emerald-300">{{ strongTopics.length }}</p>
              <p class="text-sm text-emerald-300 mt-1">Topics Well Mastered</p>
            </div>
          </div>

          <!-- Cohort topic cards sorted weakest first -->
          <div v-for="t in cohortInsights" :key="t.topic_id"
            class="bg-slate-900 rounded-xl border shadow-sm overflow-hidden"
            :class="t.weak_student_pct >= 50 ? 'border-red-800' : t.cohort_avg_pct >= 70 ? 'border-emerald-800' : 'border-slate-800'">
            <div class="p-5">
              <div class="flex items-start justify-between gap-4 mb-3">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                      :class="t.exam_type_scope === 'DS' ? 'bg-blue-100 text-blue-700' : 'bg-violet-100 text-violet-700'">
                      {{ t.exam_type_scope }}
                    </span>
                    <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                      :class="insightBadgeClass(t.insight_type)">
                      {{ formatInsightType(t.insight_type) }}
                    </span>
                  </div>
                  <h3 class="text-base font-semibold text-slate-100">{{ t.topic_id }}</h3>
                </div>
                <div class="text-right flex-shrink-0">
                  <p class="text-xl font-bold" :class="pctColor(t.cohort_avg_pct)">
                    {{ t.cohort_avg_pct.toFixed(1) }}%
                  </p>
                  <p class="text-xs text-slate-500">Class average</p>
                </div>
              </div>

              <!-- Two progress bars -->
              <div class="space-y-2 mb-3">
                <div>
                  <div class="flex justify-between text-xs text-slate-400 mb-1">
                    <span>Class average score</span>
                    <span>{{ t.cohort_avg_pct.toFixed(1) }}%</span>
                  </div>
                  <div class="w-full bg-slate-800 rounded-full h-2">
                    <div class="h-2 rounded-full transition-all"
                      :class="t.cohort_avg_pct >= 70 ? 'bg-emerald-500' : t.cohort_avg_pct >= 50 ? 'bg-amber-400' : 'bg-red-500'"
                      :style="{ width: t.cohort_avg_pct + '%' }">
                    </div>
                  </div>
                </div>
                <div>
                  <div class="flex justify-between text-xs text-slate-400 mb-1">
                    <span>Students below 50%</span>
                    <span class="text-red-500 font-medium">{{ t.weak_student_pct.toFixed(1) }}%</span>
                  </div>
                  <div class="w-full bg-slate-800 rounded-full h-2">
                    <div class="h-2 rounded-full bg-red-400 transition-all"
                      :style="{ width: t.weak_student_pct + '%' }">
                    </div>
                  </div>
                </div>
              </div>

              <!-- Recommendation -->
              <div v-if="t.recommendation"
                class="mt-3 px-3 py-2 bg-indigo-900/30 border border-indigo-800 rounded-lg flex items-start gap-2">
                <LightBulbIcon class="w-4 h-4 text-indigo-300 flex-shrink-0 mt-0.5" />
                <p class="text-sm text-indigo-200">{{ t.recommendation }}</p>
              </div>
            </div>

            <div class="px-5 py-2 bg-slate-900 border-t border-slate-800 text-xs text-slate-500">
              Last updated: {{ formatDate(t.updated_at) }}
            </div>
          </div>
        </div>
      </div>

      <!-- ── TAB: Exam Topic Performance ─────────────────────────────────── -->
      <div v-else-if="activeTab === 'exam'">
        <div v-if="!examTopicSummary.length" class="bg-slate-900 rounded-xl border border-slate-800 p-16 text-center">
          <ChartBarIcon class="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <p class="text-slate-400">No exam-topic data yet. Correction insights will appear here.</p>
        </div>

        <div v-else>
          <!-- Summary cards -->
          <div class="grid grid-cols-2 gap-4 mb-6">
            <div class="bg-slate-900 rounded-xl border border-slate-800 p-5 shadow-sm">
              <p class="text-2xl font-bold text-slate-100">{{ examTopicSummary.length }}</p>
              <p class="text-sm text-slate-400 mt-1">Topics with Data</p>
            </div>
            <div class="bg-amber-900/20 rounded-xl border border-amber-800 p-5 shadow-sm">
              <p class="text-2xl font-bold text-amber-300">
                {{ examTopicSummary.filter(t => t.avg_pct < 50).length }}
              </p>
              <p class="text-sm text-amber-300 mt-1">Topics Below 50% Average</p>
            </div>
          </div>

          <!-- Topic performance table -->
          <div class="bg-white rounded-xl border border-grey-200 shadow-sm overflow-hidden">
            <div class="px-6 py-4 border-b border-grey-100 bg-grey-50">
              <h3 class="text-sm font-semibold text-grey-700">Topic Performance Breakdown</h3>
              <p class="text-xs text-grey-400 mt-0.5">Sorted weakest → strongest across all students</p>
            </div>
            <div class="divide-y divide-grey-100">
              <div v-for="t in examTopicSummary" :key="t.topic_id"
                class="px-6 py-4 hover:bg-grey-50 transition">
                <div class="flex items-center gap-4">
                  <!-- Rank dot -->
                  <div class="w-2 h-2 rounded-full flex-shrink-0"
                    :class="t.avg_pct >= 70 ? 'bg-emerald-400' : t.avg_pct >= 50 ? 'bg-amber-400' : 'bg-red-400'">
                  </div>

                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                      <p class="text-sm font-medium text-grey-800 truncate">{{ t.topic_id }}</p>
                      <span class="text-xs px-1.5 py-0.5 rounded font-medium flex-shrink-0"
                        :class="t.exam_type === 'DS' ? 'bg-blue-50 text-blue-600' : 'bg-violet-50 text-violet-600'">
                        {{ t.exam_type }}
                      </span>
                    </div>
                    <div class="w-full bg-grey-100 rounded-full h-1.5">
                      <div class="h-1.5 rounded-full transition-all"
                        :class="t.avg_pct >= 70 ? 'bg-emerald-500' : t.avg_pct >= 50 ? 'bg-amber-400' : 'bg-red-500'"
                        :style="{ width: t.avg_pct + '%' }">
                      </div>
                    </div>
                  </div>

                  <div class="text-right flex-shrink-0 w-24">
                    <p class="text-base font-bold" :class="pctColor(t.avg_pct)">{{ t.avg_pct }}%</p>
                    <p class="text-xs text-grey-400">{{ t.avg_score }}/{{ t.max_score }} avg</p>
                  </div>
                  <div class="text-right flex-shrink-0 w-16">
                    <p class="text-xs text-grey-500">{{ t.student_count }}</p>
                    <p class="text-xs text-grey-400">students</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Heatmap: exam_id rows × topic_id columns -->
          <div v-if="heatmapTopics.length && heatmapExams.length" class="mt-6 bg-white rounded-xl border border-grey-200 shadow-sm overflow-hidden">
            <div class="px-6 py-4 border-b border-grey-100 bg-grey-50">
              <h3 class="text-sm font-semibold text-grey-700">Per-Student × Topic Heatmap</h3>
              <p class="text-xs text-grey-400 mt-0.5">Each row = one student, each column = one topic</p>
            </div>
            <div class="overflow-x-auto">
              <table class="text-xs w-full">
                <thead class="bg-grey-50 border-b border-grey-100">
                  <tr>
                    <th class="px-4 py-2 text-left text-grey-500 font-medium sticky left-0 bg-grey-50 min-w-32">Student</th>
                    <th v-for="topic in heatmapTopics" :key="topic"
                      class="px-3 py-2 text-center text-grey-500 font-medium max-w-24 truncate"
                      :title="topic">
                      {{ topic.length > 14 ? topic.slice(0, 13) + '…' : topic }}
                    </th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-grey-50">
                  <tr v-for="sid in heatmapExams" :key="sid" class="hover:bg-grey-50">
                    <td class="px-4 py-2 font-medium text-grey-700 sticky left-0 bg-white">
                      {{ getStudentName(sid) }}
                    </td>
                    <td v-for="topic in heatmapTopics" :key="topic"
                      class="px-3 py-2 text-center">
                      <span v-if="heatmapCell(sid, topic) !== null"
                        class="inline-block w-10 py-0.5 rounded text-xs font-semibold"
                        :class="heatmapCellClass(heatmapCell(sid, topic))">
                        {{ heatmapCell(sid, topic) }}%
                      </span>
                      <span v-else class="text-grey-300">—</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import {
  ChevronLeftIcon,
  LightBulbIcon,
  ChartBarIcon,
} from '@heroicons/vue/24/outline';
import api from '@/services/api';

const route   = useRoute();
const classId = computed(() => parseInt(route.params.id));

// ── State ──────────────────────────────────────────────────────────────────
const loading        = ref(true);
const activeTab      = ref('cohort');
const activeScope    = ref(null); // null = all, 'DS', 'EXAMEN'

const cohortInsights   = ref([]);
const examTopicRows    = ref([]);
const examTopicSummary = ref([]);

const scopes = [
  { value: null,     label: 'All' },
  { value: 'DS',     label: 'DS' },
  { value: 'EXAMEN', label: 'Examen' },
];

const tabs = [
  { id: 'cohort', label: '🏫 Cohort Topic Insights' },
  { id: 'exam',   label: '📊 Exam Topic Performance' },
];

// ── Derived ────────────────────────────────────────────────────────────────
const weakTopics   = computed(() => cohortInsights.value.filter(t => t.weak_student_pct >= 50));
const strongTopics = computed(() => cohortInsights.value.filter(t => t.cohort_avg_pct  >= 70));

// Heatmap: unique student IDs and topic IDs from exam-topic rows
const heatmapExams   = computed(() => [...new Set(examTopicRows.value.map(r => r.student_id))]);
const heatmapTopics  = computed(() => [...new Set(examTopicRows.value.map(r => r.topic_id))]);
const heatmapLookup  = computed(() => {
  const map = {};
  for (const r of examTopicRows.value) {
    map[`${r.student_id}|${r.topic_id}`] = r.pct;
  }
  return map;
});

// ── Helpers ────────────────────────────────────────────────────────────────
function heatmapCell(studentId, topicId) {
  const v = heatmapLookup.value[`${studentId}|${topicId}`];
  return v !== undefined ? Math.round(v) : null;
}

function heatmapCellClass(pct) {
  if (pct >= 70) return 'bg-emerald-100 text-emerald-700';
  if (pct >= 50) return 'bg-amber-100 text-amber-700';
  return 'bg-red-100 text-red-700';
}

function pctColor(pct) {
  if (pct >= 70) return 'text-emerald-600';
  if (pct >= 50) return 'text-amber-600';
  return 'text-red-600';
}

function insightBadgeClass(type) {
  if (type === 'cohort_topic_weakness') return 'bg-red-100 text-red-700';
  if (type === 'remediation_needed')    return 'bg-orange-100 text-orange-700';
  return 'bg-grey-100 text-grey-600';
}

function formatInsightType(type) {
  const map = {
    cohort_topic_weakness:  'Class Weakness',
    remediation_needed:     'Remediation Needed',
  };
  return map[type] || type.replace(/_/g, ' ');
}

function formatDate(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// Build a student name from student_id — just show "Student #ID" unless we have extra data
const studentNames = ref({});
function getStudentName(id) {
  return studentNames.value[id] || `Student #${id}`;
}

// ── Data loading ───────────────────────────────────────────────────────────
async function loadAll() {
  loading.value = true;
  try {
    const [cohortRes, examRes] = await Promise.allSettled([
      api.getCohortInsights(classId.value, activeScope.value),
      api.getExamTopicPerformance(classId.value),
    ]);

    if (cohortRes.status === 'fulfilled' && cohortRes.value.success) {
      // Filter by scope client-side if needed (backend also filters but belt-and-suspenders)
      cohortInsights.value = cohortRes.value.insights || [];
    }

    if (examRes.status === 'fulfilled' && examRes.value.success) {
      examTopicRows.value    = examRes.value.rows || [];
      examTopicSummary.value = examRes.value.topic_summary || [];

      // Populate student name map from exam rows
      const names = {};
      for (const r of examTopicRows.value) {
        if (!names[r.student_id]) names[r.student_id] = `Student #${r.student_id}`;
      }
      studentNames.value = names;

      // Try to resolve real names from students endpoint
      try {
        const studsRes = await api.getStudents(classId.value);
        if (studsRes.success) {
          for (const s of (studsRes.students || [])) {
            names[s.id] = s.name;
          }
          studentNames.value = { ...names };
        }
      } catch { /* non-critical */ }
    }
  } finally {
    loading.value = false;
  }
}

onMounted(loadAll);
</script>
