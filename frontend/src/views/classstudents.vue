<template>
  <div class="h-full overflow-y-auto custom-scrollbar bg-grey-50">
    <!-- Header -->
    <div class="bg-white border-b border-grey-200 px-8 py-6">
      <div class="flex items-center gap-2 text-sm text-grey-500 mb-4">
        <router-link :to="`/class/${classId}`" class="hover:text-primary-600 transition flex items-center gap-1">
          <ChevronLeftIcon class="w-4 h-4" />
          Back to Class
        </router-link>
        <span>/</span>
        <span class="text-grey-900 font-medium">Students</span>
      </div>
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-grey-900 mb-1">Students</h1>
          <p class="text-grey-600">{{ students.length }} student{{ students.length !== 1 ? 's' : '' }} enrolled</p>
        </div>
        <button
          @click="showAddModal = true"
          class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 shadow-sm transition"
        >
          <PlusIcon class="w-5 h-5" />
          Add Student
        </button>
      </div>
    </div>

    <div class="p-8">
      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
      </div>

      <!-- Empty -->
      <div v-else-if="students.length === 0" class="bg-white rounded-xl border border-grey-200 shadow-sm p-16 text-center">
        <UserGroupIcon class="w-14 h-14 text-grey-300 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-grey-900 mb-2">No students yet</h3>
        <p class="text-grey-600 mb-6">Add your first student to get started.</p>
        <button @click="showAddModal = true"
          class="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-primary-700 transition">
          <PlusIcon class="w-5 h-5" />
          Add First Student
        </button>
      </div>

      <!-- Table -->
      <div v-else class="bg-white rounded-xl border border-grey-200 shadow-sm overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-grey-50 border-b border-grey-200">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-semibold text-grey-600 uppercase tracking-wider">Student</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-grey-600 uppercase tracking-wider">Email</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-grey-600 uppercase tracking-wider">Added</th>
              <th class="px-6 py-3 text-center text-xs font-semibold text-grey-600 uppercase tracking-wider">Flags</th>
              <th class="px-6 py-3 text-center text-xs font-semibold text-grey-600 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-grey-100">
            <tr v-for="student in students" :key="student.id" class="hover:bg-grey-50 transition">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
                    {{ student.name.charAt(0).toUpperCase() }}
                  </div>
                  <span class="font-medium text-grey-900">{{ student.name }}</span>
                </div>
              </td>
              <td class="px-6 py-4 text-grey-600">{{ student.email }}</td>
              <td class="px-6 py-4 text-grey-500">{{ formatDate(student.created_at) }}</td>
              <td class="px-6 py-4 text-center">
                <button
                  @click="openFlagModal(student)"
                  class="inline-flex items-center justify-center p-1.5 rounded-full transition"
                  :class="student.flags?.length ? 'text-orange-600 bg-orange-100 hover:bg-orange-200' : 'text-grey-400 hover:text-orange-500 hover:bg-orange-50'"
                  :title="student.flags?.length ? 'View Flags' : 'Add Flag'"
                >
                  <FlagIcon class="w-5 h-5" :class="student.flags?.length ? 'fill-current' : ''" />
                </button>
              </td>
              <td class="px-6 py-4 text-center">
                <div class="flex items-center justify-center gap-2">
                  <button
                    @click="openReport(student)"
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition font-medium"
                    title="View Report"
                  >
                    <ChartBarIcon class="w-3.5 h-3.5" />
                    Report
                  </button>
                  <button
                    @click="openEditModal(student)"
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-primary-600 bg-primary-50 rounded-lg hover:bg-primary-100 transition font-medium"
                  >
                    <PencilIcon class="w-3.5 h-3.5" />
                    Edit
                  </button>
                  <button
                    @click="removeStudent(student)"
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition font-medium"
                  >
                    <TrashIcon class="w-3.5 h-3.5" />
                    Remove
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Student Modal -->
    <TransitionRoot :show="showAddModal" as="template">
      <Dialog @close="showAddModal = false" class="relative z-50">
        <TransitionChild enter="ease-out duration-200" enter-from="opacity-0" enter-to="opacity-100"
          leave="ease-in duration-150" leave-from="opacity-100" leave-to="opacity-0">
          <div class="fixed inset-0 bg-black/25 backdrop-blur-sm" />
        </TransitionChild>
        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild enter="ease-out duration-200" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
              leave="ease-in duration-150" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95">
              <DialogPanel class="w-full max-w-sm bg-white rounded-2xl shadow-xl">
                <div class="p-6 border-b border-grey-200">
                  <DialogTitle class="text-lg font-semibold text-grey-900">Add Student</DialogTitle>
                </div>
                <form @submit.prevent="submitAdd" class="p-6 space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Full Name *</label>
                    <input v-model="addForm.name" type="text" required
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Ahmed Ben Ali" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Email *</label>
                    <input v-model="addForm.email" type="email" required
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="student@school.tn" />
                  </div>
                  <div v-if="addError" class="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p class="text-sm text-red-700">{{ addError }}</p>
                  </div>
                  <div class="flex gap-3 pt-2">
                    <button type="button" @click="showAddModal = false"
                      class="flex-1 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition">
                      Cancel
                    </button>
                    <button type="submit" :disabled="adding"
                      class="flex-1 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50">
                      {{ adding ? 'Adding…' : 'Add Student' }}
                    </button>
                  </div>
                </form>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>

    <!-- Edit Student Modal -->
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
              <DialogPanel class="w-full max-w-sm bg-white rounded-2xl shadow-xl">
                <div class="p-6 border-b border-grey-200">
                  <DialogTitle class="text-lg font-semibold text-grey-900">Edit Student</DialogTitle>
                </div>
                <form @submit.prevent="submitEdit" class="p-6 space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Full Name *</label>
                    <input v-model="editForm.name" type="text" required
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Email *</label>
                    <input v-model="editForm.email" type="email" required
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500" />
                  </div>
                  <div v-if="editError" class="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p class="text-sm text-red-700">{{ editError }}</p>
                  </div>
                  <div class="flex gap-3 pt-2">
                    <button type="button" @click="showEditModal = false"
                      class="flex-1 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition">
                      Cancel
                    </button>
                    <button type="submit" :disabled="editing"
                      class="flex-1 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50">
                      {{ editing ? 'Saving…' : 'Save Changes' }}
                    </button>
                  </div>
                </form>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>

    <!-- Flag Modal -->
    <TransitionRoot :show="showFlagModal" as="template">
      <Dialog @close="showFlagModal = false" class="relative z-50">
        <TransitionChild enter="ease-out duration-200" enter-from="opacity-0" enter-to="opacity-100"
          leave="ease-in duration-150" leave-from="opacity-100" leave-to="opacity-0">
          <div class="fixed inset-0 bg-black/25 backdrop-blur-sm" />
        </TransitionChild>
        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild enter="ease-out duration-200" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
              leave="ease-in duration-150" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95">
              <DialogPanel class="w-full max-w-md bg-white rounded-2xl shadow-xl flex flex-col max-h-[80vh]">
                <div class="p-6 border-b border-grey-200 flex-shrink-0">
                  <DialogTitle class="text-lg font-semibold text-grey-900">
                    Flags for {{ selectedStudent?.name }}
                  </DialogTitle>
                </div>
                
                <div class="p-6 overflow-y-auto flex-1 custom-scrollbar">
                  <!-- Existing Flags -->
                  <div v-if="studentFlags.length > 0" class="space-y-3 mb-6">
                    <h4 class="text-sm font-medium text-grey-700">Current Flags</h4>
                    <div v-for="flag in studentFlags" :key="flag.id" class="p-3 bg-orange-50 border border-orange-200 rounded-lg flex justify-between items-start gap-2">
                      <div>
                        <p class="text-sm text-orange-900 break-words">{{ flag.reason }}</p>
                        <p class="text-xs text-orange-600 mt-1">{{ formatDate(flag.created_at) }}</p>
                      </div>
                      <button @click="removeFlag(flag.id)" class="text-orange-400 hover:text-orange-700 transition flex-shrink-0 p-1 bg-white rounded-md shadow-sm border border-orange-200">
                        <TrashIcon class="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div v-else class="text-center py-4 mb-4">
                    <p class="text-sm text-grey-500">No flags for this student.</p>
                  </div>

                  <!-- Add New Flag -->
                  <div>
                    <h4 class="text-sm font-medium text-grey-700 mb-2">Add New Flag</h4>
                    <textarea v-model="newFlagReason" rows="3"
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm"
                      placeholder="Reason for flagging..."></textarea>
                    <div v-if="flagError" class="mt-2 text-sm text-red-600">{{ flagError }}</div>
                  </div>
                </div>

                <div class="p-6 border-t border-grey-200 flex gap-3 flex-shrink-0 bg-grey-50 rounded-b-2xl">
                  <button type="button" @click="showFlagModal = false"
                    class="flex-1 px-4 py-2 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-100 transition bg-white">
                    Done
                  </button>
                  <button type="button" @click="submitFlag" :disabled="!newFlagReason.trim() || flagging"
                    class="flex-1 bg-gradient-to-r from-orange-600 to-orange-500 text-white px-4 py-2 rounded-lg font-medium hover:from-orange-700 hover:to-orange-600 transition disabled:opacity-50">
                    {{ flagging ? 'Saving...' : 'Save Flag' }}
                  </button>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>

    <!-- ── Student Report Modal ─────────────────────────────────────────── -->
    <TransitionRoot :show="showReportModal" as="template">
      <Dialog @close="showReportModal = false" class="relative z-50">
        <TransitionChild enter="ease-out duration-200" enter-from="opacity-0" enter-to="opacity-100"
          leave="ease-in duration-150" leave-from="opacity-100" leave-to="opacity-0">
          <div class="fixed inset-0 bg-black/40 backdrop-blur-sm" />
        </TransitionChild>
        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild enter="ease-out duration-200" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
              leave="ease-in duration-150" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95">
              <DialogPanel class="w-full max-w-2xl bg-white rounded-2xl shadow-2xl flex flex-col max-h-[90vh]">

                <!-- Header -->
                <div class="p-6 border-b border-grey-200 flex items-center justify-between flex-shrink-0 bg-gradient-to-r from-indigo-600 to-indigo-500 rounded-t-2xl">
                  <div>
                    <DialogTitle class="text-xl font-bold text-white flex items-center gap-2">
                      <ChartBarIcon class="w-5 h-5" />
                      Student Report
                    </DialogTitle>
                    <p class="text-indigo-200 text-sm mt-0.5">{{ reportStudent?.name }}</p>
                  </div>
                  <button @click="showReportModal = false" class="text-indigo-200 hover:text-white transition p-1">
                    <XMarkIcon class="w-5 h-5" />
                  </button>
                </div>

                <!-- Loading -->
                <div v-if="reportLoading" class="flex justify-center py-16">
                  <div class="animate-spin rounded-full h-10 w-10 border-4 border-indigo-500 border-t-transparent"></div>
                </div>

                <!-- Error -->
                <div v-else-if="reportError" class="p-6 text-center text-red-600">
                  <p>{{ reportError }}</p>
                </div>

                <!-- Content -->
                <div v-else-if="report" class="overflow-y-auto flex-1 custom-scrollbar">

                  <!-- Summary Cards -->
                  <div class="p-6 border-b border-grey-100">
                    <h3 class="text-sm font-semibold text-grey-700 uppercase tracking-wider mb-3">Overview</h3>
                    <div class="grid grid-cols-3 gap-3">
                      <div class="bg-indigo-50 rounded-xl p-4 text-center">
                        <p class="text-2xl font-bold" :class="gradeColor(report.summary.overall_average)">
                          {{ report.summary.overall_average ?? '—' }}
                        </p>
                        <p class="text-xs text-grey-500 mt-1">Overall Avg</p>
                      </div>
                      <div class="bg-blue-50 rounded-xl p-4 text-center">
                        <p class="text-2xl font-bold" :class="gradeColor(report.summary.ds_average)">
                          {{ report.summary.ds_average ?? '—' }}
                        </p>
                        <p class="text-xs text-grey-500 mt-1">DS Average</p>
                      </div>
                      <div class="bg-violet-50 rounded-xl p-4 text-center">
                        <p class="text-2xl font-bold" :class="gradeColor(report.summary.exam_average)">
                          {{ report.summary.exam_average ?? '—' }}
                        </p>
                        <p class="text-xs text-grey-500 mt-1">Exam Average</p>
                      </div>
                    </div>
                    <div class="flex gap-4 mt-3 text-xs text-grey-500">
                      <span>📝 {{ report.summary.total_exams }} exam(s)</span>
                      <span class="text-red-500">⚠ {{ report.summary.grades_below_10 }} below 10</span>
                      <span class="text-emerald-600">✓ {{ report.summary.grades_above_14 }} above 14</span>
                    </div>
                  </div>

                  <!-- Grades Table -->
                  <div v-if="report.grades.length" class="p-6 border-b border-grey-100">
                    <h3 class="text-sm font-semibold text-grey-700 uppercase tracking-wider mb-3">Grades by Exam</h3>
                    <div class="space-y-2">
                      <div v-for="g in report.grades" :key="g.exam_type_id"
                        class="flex items-center justify-between px-4 py-2.5 rounded-lg bg-grey-50 border border-grey-100">
                        <div class="flex items-center gap-2">
                          <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                            :class="g.category === 'DS' ? 'bg-blue-100 text-blue-700' : 'bg-violet-100 text-violet-700'">
                            {{ g.category }}
                          </span>
                          <span class="text-sm text-grey-800 font-medium">{{ g.exam_type_name }}</span>
                        </div>
                        <span class="text-base font-bold" :class="gradeColor(g.value)">{{ g.value }}/20</span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="p-6 border-b border-grey-100 text-sm text-grey-400 italic">No grades recorded yet.</div>

                  <!-- Topic Insights -->
                  <div class="p-6 border-b border-grey-100">
                    <h3 class="text-sm font-semibold text-grey-700 uppercase tracking-wider mb-3">Topic Mastery Insights</h3>

                    <!-- Weak Topics -->
                    <div v-if="report.insights.weak_topics.length" class="mb-4">
                      <p class="text-xs font-semibold text-red-600 mb-2 flex items-center gap-1">
                        <ExclamationTriangleIcon class="w-3.5 h-3.5" /> Weak Topics (below 50%)
                      </p>
                      <div v-for="t in report.insights.weak_topics" :key="t.topic_id"
                        class="mb-2 px-3 py-2 bg-red-50 border border-red-100 rounded-lg">
                        <div class="flex justify-between items-center mb-1">
                          <span class="text-sm font-medium text-grey-800">{{ t.topic_id }}</span>
                          <span class="text-xs font-bold text-red-600">{{ t.mastery_pct }}%</span>
                        </div>
                        <div class="w-full bg-red-100 rounded-full h-1.5">
                          <div class="bg-red-500 h-1.5 rounded-full" :style="{ width: t.mastery_pct + '%' }"></div>
                        </div>
                        <div class="flex gap-3 mt-1 text-xs text-grey-400">
                          <span>{{ t.attempts }} attempt(s)</span>
                          <span :class="trendClass(t.trend)">{{ trendLabel(t.trend) }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- Declining Topics -->
                    <div v-if="report.insights.declining_topics.length" class="mb-4">
                      <p class="text-xs font-semibold text-orange-600 mb-2 flex items-center gap-1">
                        <ArrowTrendingDownIcon class="w-3.5 h-3.5" /> Declining Performance
                      </p>
                      <div v-for="t in report.insights.declining_topics" :key="'d-'+t.topic_id"
                        class="mb-2 px-3 py-2 bg-orange-50 border border-orange-100 rounded-lg">
                        <div class="flex justify-between items-center">
                          <span class="text-sm font-medium text-grey-800">{{ t.topic_id }}</span>
                          <span class="text-xs font-bold text-orange-600">{{ t.mastery_pct }}%</span>
                        </div>
                      </div>
                    </div>

                    <!-- Strong Topics -->
                    <div v-if="report.insights.strong_topics.length" class="mb-2">
                      <p class="text-xs font-semibold text-emerald-600 mb-2 flex items-center gap-1">
                        <CheckCircleIcon class="w-3.5 h-3.5" /> Strong Topics (75%+)
                      </p>
                      <div v-for="t in report.insights.strong_topics" :key="'s-'+t.topic_id"
                        class="mb-2 px-3 py-2 bg-emerald-50 border border-emerald-100 rounded-lg">
                        <div class="flex justify-between items-center mb-1">
                          <span class="text-sm font-medium text-grey-800">{{ t.topic_id }}</span>
                          <span class="text-xs font-bold text-emerald-600">{{ t.mastery_pct }}%</span>
                        </div>
                        <div class="w-full bg-emerald-100 rounded-full h-1.5">
                          <div class="bg-emerald-500 h-1.5 rounded-full" :style="{ width: t.mastery_pct + '%' }"></div>
                        </div>
                      </div>
                    </div>

                    <p v-if="!report.insights.all.length" class="text-sm text-grey-400 italic">No topic insights available yet. Run exam corrections to generate insights.</p>
                  </div>

                  <!-- Flags / Notes -->
                  <div class="p-6">
                    <h3 class="text-sm font-semibold text-grey-700 uppercase tracking-wider mb-3">Teacher Notes & Flags</h3>
                    <div v-if="report.flags.length" class="space-y-2">
                      <div v-for="f in report.flags" :key="f.id"
                        class="px-4 py-3 bg-orange-50 border border-orange-200 rounded-lg">
                        <p class="text-sm text-orange-900">{{ f.reason }}</p>
                        <p class="text-xs text-orange-500 mt-1">{{ formatDate(f.created_at) }}</p>
                      </div>
                    </div>
                    <p v-else class="text-sm text-grey-400 italic">No flags recorded for this student.</p>
                  </div>

                </div>

                <!-- Footer -->
                <div class="p-4 border-t border-grey-200 flex-shrink-0 bg-grey-50 rounded-b-2xl">
                  <button @click="showReportModal = false"
                    class="w-full px-4 py-2 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-100 transition bg-white">
                    Close
                  </button>
                </div>
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
import { useRoute } from 'vue-router';
import {
  ChevronLeftIcon,
  PlusIcon,
  TrashIcon,
  UserGroupIcon,
  FlagIcon,
  PencilIcon,
  ChartBarIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/vue/24/outline';
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import api from '@/services/api';

const route = useRoute();
const classId = computed(() => parseInt(route.params.id));

const loading = ref(true);
const students = ref([]);

const showAddModal = ref(false);
const adding = ref(false);
const addError = ref('');
const addForm = ref({ name: '', email: '' });

const showEditModal = ref(false);
const editing = ref(false);
const editError = ref('');
const editForm = ref({ id: null, name: '', email: '' });

const showFlagModal = ref(false);
const selectedStudent = ref(null);
const studentFlags = ref([]);
const newFlagReason = ref('');
const flagging = ref(false);
const flagError = ref('');

// ── Report state ────────────────────────────────────────────────────────────
const showReportModal = ref(false);
const reportStudent = ref(null);
const report = ref(null);
const reportLoading = ref(false);
const reportError = ref('');

function formatDate(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

async function loadStudents() {
  loading.value = true;
  try {
    const res = await api.getStudents(classId.value);
    if (res.success) {
      const studs = res.students || [];
      await Promise.all(studs.map(async (s) => {
        try {
          const flags = await api.getFlags(classId.value, s.id);
          s.flags = flags || [];
        } catch(e) {
          s.flags = [];
        }
      }));
      students.value = studs;
    }
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function submitAdd() {
  addError.value = '';
  adding.value = true;
  try {
    const res = await api.createStudent({ class_id: classId.value, ...addForm.value });
    if (res.success) {
      res.student.flags = []; // Initialize flags for new student
      students.value.unshift(res.student);
      showAddModal.value = false;
      addForm.value = { name: '', email: '' };
    }
  } catch (err) {
    addError.value = err.message || 'Failed to add student';
  } finally {
    adding.value = false;
  }
}

function openEditModal(student) {
  editForm.value = { id: student.id, name: student.name, email: student.email };
  editError.value = '';
  showEditModal.value = true;
}

async function submitEdit() {
  editError.value = '';
  editing.value = true;
  try {
    const res = await api.updateStudent(classId.value, editForm.value.id, {
      name: editForm.value.name,
      email: editForm.value.email
    });
    if (res.success) {
      const idx = students.value.findIndex(s => s.id === editForm.value.id);
      if (idx !== -1) {
        students.value[idx].name = res.student.name;
        students.value[idx].email = res.student.email;
      }
      showEditModal.value = false;
    }
  } catch (err) {
    editError.value = err.message || 'Failed to update student';
  } finally {
    editing.value = false;
  }
}

async function removeStudent(student) {
  if (!confirm(`Remove "${student.name}" from this class?`)) return;
  try {
    await api.deleteStudent(classId.value, student.id);
    students.value = students.value.filter(s => s.id !== student.id);
  } catch (err) {
    alert('Failed: ' + err.message);
  }
}

async function openFlagModal(student) {
  selectedStudent.value = student;
  studentFlags.value = student.flags || [];
  newFlagReason.value = '';
  flagError.value = '';
  showFlagModal.value = true;
}

async function submitFlag() {
  if (!newFlagReason.value.trim() || !selectedStudent.value) return;
  flagging.value = true;
  flagError.value = '';
  try {
    await api.createFlag(classId.value, selectedStudent.value.id, newFlagReason.value.trim());
    const flags = await api.getFlags(classId.value, selectedStudent.value.id);
    selectedStudent.value.flags = flags;
    studentFlags.value = flags;
    newFlagReason.value = '';
  } catch (err) {
    flagError.value = err.message || 'Failed to add flag';
  } finally {
    flagging.value = false;
  }
}

async function removeFlag(flagId) {
  if (!confirm('Delete this flag?')) return;
  try {
    await api.deleteFlag(flagId);
    if (selectedStudent.value) {
      selectedStudent.value.flags = selectedStudent.value.flags.filter(f => f.id !== flagId);
      studentFlags.value = selectedStudent.value.flags;
    }
  } catch (err) {
    alert('Failed to delete flag: ' + err.message);
  }
}

// ── Report helpers ──────────────────────────────────────────────────────────
async function openReport(student) {
  reportStudent.value = student;
  report.value = null;
  reportError.value = '';
  reportLoading.value = true;
  showReportModal.value = true;
  try {
    const res = await api.getStudentReport(classId.value, student.id);
    if (res.success) report.value = res.report;
    else reportError.value = 'Failed to load report.';
  } catch (e) {
    reportError.value = e.message || 'Failed to load report.';
  } finally {
    reportLoading.value = false;
  }
}

function gradeColor(val) {
  if (val === null || val === undefined) return 'text-grey-400';
  if (val >= 14) return 'text-emerald-600';
  if (val >= 10) return 'text-amber-600';
  return 'text-red-600';
}

function trendLabel(trend) {
  if (trend === 'improving')  return '↑ Improving';
  if (trend === 'declining')  return '↓ Declining';
  return '→ Stable';
}

function trendClass(trend) {
  if (trend === 'improving') return 'text-emerald-500';
  if (trend === 'declining') return 'text-red-500';
  return 'text-grey-400';
}

onMounted(loadStudents);
</script>