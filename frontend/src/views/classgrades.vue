<template>
  <div class="h-full overflow-y-auto custom-scrollbar bg-grey-50">
    <!-- Header -->
    <div class="bg-white border-b border-grey-200 px-8 py-6">
      <div class="flex items-center gap-3 text-sm text-grey-600 mb-4">
        <router-link :to="`/class/${classId}`" class="hover:text-primary-600 transition flex items-center gap-1">
          <ChevronLeftIcon class="w-4 h-4" />
          Back to Class
        </router-link>
        <span>/</span>
        <span class="text-grey-900 font-medium">Grades</span>
      </div>

      <div class="flex items-start justify-between">
        <div>
          <h1 class="text-3xl font-bold text-grey-900 mb-1">Grades</h1>
          <p class="text-grey-600">{{ classData?.name }} — {{ classData?.subject }}</p>
        </div>
        <div class="flex items-center gap-3">
          <button
            @click="showAddExamTypeModal = true"
            class="flex items-center gap-2 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
          >
            <TagIcon class="w-4 h-4" />
            Add Exam Type
          </button>
          <button
            @click="openAddGradeModal()"
            class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 shadow-sm transition"
          >
            <PlusIcon class="w-5 h-5" />
            Add Grade
          </button>
        </div>
      </div>
    </div>

    <div class="p-8">
      <!-- Stats Row -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-xl shadow-sm border border-grey-200 p-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center">
              <UserGroupIcon class="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <div class="text-xl font-bold text-grey-900">{{ students.length }}</div>
              <div class="text-xs text-grey-600">Students</div>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-grey-200 p-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-violet-50 rounded-lg flex items-center justify-center">
              <ClipboardDocumentListIcon class="w-5 h-5 text-violet-600" />
            </div>
            <div>
              <div class="text-xl font-bold text-grey-900">{{ examTypes.length }}</div>
              <div class="text-xs text-grey-600">Exam Types</div>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-grey-200 p-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-success-50 rounded-lg flex items-center justify-center">
              <CheckBadgeIcon class="w-5 h-5 text-success-600" />
            </div>
            <div>
              <div class="text-xl font-bold text-grey-900">{{ classAverage }}</div>
              <div class="text-xs text-grey-600">Class Average</div>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-grey-200 p-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center">
              <ChartBarIcon class="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <div class="text-xl font-bold text-grey-900">{{ gradesFilled }}</div>
              <div class="text-xs text-grey-600">Grades Entered</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Exam Type Filter Pills -->
      <div v-if="examTypes.length > 0" class="mb-4 flex items-center gap-2 flex-wrap">
        <button
          @click="filterExamTypeId = null"
          :class="[
            'px-4 py-1.5 rounded-full text-sm font-medium transition border',
            filterExamTypeId === null
              ? 'bg-primary-600 text-white border-primary-600'
              : 'bg-white text-grey-700 border-grey-300 hover:border-primary-400'
          ]"
        >
          All
        </button>
        <button
          v-for="et in examTypes"
          :key="et.id"
          @click="filterExamTypeId = et.id"
          :class="[
            'px-4 py-1.5 rounded-full text-sm font-medium transition border capitalize',
            filterExamTypeId === et.id
              ? 'bg-primary-600 text-white border-primary-600'
              : 'bg-white text-grey-700 border-grey-300 hover:border-primary-400'
          ]"
        >
          {{ et.name }}
        </button>
      </div>

      <!-- Grades Table -->
      <div class="bg-white rounded-xl shadow-sm border border-grey-200 overflow-hidden">
        <!-- Loading -->
        <div v-if="loading" class="p-16 flex items-center justify-center">
          <div class="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
        </div>

        <!-- No exam types -->
        <div v-else-if="examTypes.length === 0" class="p-16 text-center">
          <ClipboardDocumentListIcon class="w-14 h-14 text-grey-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-grey-900 mb-2">No exam types yet</h3>
          <p class="text-grey-600 mb-6">Create exam types (e.g. "Quiz 1", "Midterm") to start entering grades.</p>
          <button
            @click="showAddExamTypeModal = true"
            class="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-primary-700 transition"
          >
            <PlusIcon class="w-5 h-5" />
            Add First Exam Type
          </button>
        </div>

        <!-- No students -->
        <div v-else-if="students.length === 0" class="p-16 text-center">
          <UserGroupIcon class="w-14 h-14 text-grey-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-grey-900 mb-2">No students in this class</h3>
          <p class="text-grey-600">Add students to start tracking grades.</p>
        </div>

        <!-- Table -->
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-grey-50 border-b border-grey-200">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold text-grey-600 uppercase tracking-wider sticky left-0 bg-grey-50 z-10 min-w-[180px]">
                  Student
                </th>
                <th
                  v-for="et in visibleExamTypes"
                  :key="et.id"
                  class="px-4 py-3 text-center text-xs font-semibold text-grey-600 uppercase tracking-wider min-w-[120px] group"
                >
                  <div class="flex items-center justify-center gap-1">
                    <span class="capitalize">{{ et.name }}</span>
                    <button
                      @click="deleteExamType(et)"
                      class="opacity-0 group-hover:opacity-100 transition p-0.5 rounded hover:bg-red-100 hover:text-red-600"
                      title="Delete exam type"
                    >
                      <XMarkIcon class="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div class="text-grey-400 font-normal normal-case text-[10px] mt-0.5">/ 20</div>
                </th>
                <th class="px-4 py-3 text-center text-xs font-semibold text-grey-600 uppercase tracking-wider min-w-[90px]">
                  Average
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-grey-100">
              <tr
                v-for="student in students"
                :key="student.id"
                class="hover:bg-grey-50 transition"
              >
                <!-- Student Name -->
                <td class="px-6 py-3 sticky left-0 bg-white hover:bg-grey-50 z-10">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
                      {{ student.name.charAt(0).toUpperCase() }}
                    </div>
                    <span class="font-medium text-grey-900 truncate max-w-[130px]" :title="student.name">{{ student.name }}</span>
                  </div>
                </td>

                <!-- Grade Cells -->
                <td
                  v-for="et in visibleExamTypes"
                  :key="et.id"
                  class="px-4 py-3 text-center"
                >
                  <div class="relative group/cell flex items-center justify-center">
                    <!-- Display Mode -->
                    <template v-if="editingCell?.studentId !== student.id || editingCell?.examTypeId !== et.id">
                      <span
                        v-if="getGrade(student.id, et.id) !== null"
                        :class="[
                          'inline-block px-3 py-1 rounded-lg font-semibold cursor-pointer transition hover:opacity-80',
                          getGradeClass(getGrade(student.id, et.id))
                        ]"
                        @click="startEdit(student, et)"
                        :title="'Click to edit'"
                      >
                        {{ getGrade(student.id, et.id).toFixed(2) }}
                      </span>
                      <button
                        v-else
                        @click="startEdit(student, et)"
                        class="w-8 h-8 flex items-center justify-center rounded-lg border-2 border-dashed border-grey-300 text-grey-400 hover:border-primary-400 hover:text-primary-500 transition opacity-0 group-hover/cell:opacity-100"
                        title="Add grade"
                      >
                        <PlusIcon class="w-3.5 h-3.5" />
                      </button>
                    </template>

                    <!-- Edit Mode -->
                    <template v-else>
                      <div class="flex items-center gap-1">
                        <input
                          ref="editInput"
                          v-model="editValue"
                          type="number"
                          min="0"
                          max="20"
                          step="0.25"
                          class="w-16 px-2 py-1 text-center border-2 border-primary-500 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary-300"
                          @keydown.enter="saveEdit"
                          @keydown.escape="cancelEdit"
                          @blur="saveEdit"
                        />
                      </div>
                    </template>
                  </div>
                </td>

                <!-- Average -->
                <td class="px-4 py-3 text-center">
                  <span
                    v-if="getStudentAverage(student.id) !== null"
                    :class="[
                      'inline-block px-3 py-1 rounded-lg font-bold text-xs',
                      getGradeClass(getStudentAverage(student.id))
                    ]"
                  >
                    {{ getStudentAverage(student.id).toFixed(2) }}
                  </span>
                  <span v-else class="text-grey-400">—</span>
                </td>
              </tr>
            </tbody>

            <!-- Column Averages Footer -->
            <tfoot v-if="students.length > 0" class="border-t-2 border-grey-200 bg-grey-50">
              <tr>
                <td class="px-6 py-3 sticky left-0 bg-grey-50 text-xs font-bold text-grey-700 uppercase tracking-wider">
                  Class Avg
                </td>
                <td
                  v-for="et in visibleExamTypes"
                  :key="et.id"
                  class="px-4 py-3 text-center"
                >
                  <span
                    v-if="getExamTypeAverage(et.id) !== null"
                    :class="[
                      'inline-block px-3 py-1 rounded-lg font-bold text-xs',
                      getGradeClass(getExamTypeAverage(et.id))
                    ]"
                  >
                    {{ getExamTypeAverage(et.id).toFixed(2) }}
                  </span>
                  <span v-else class="text-grey-400 text-xs">—</span>
                </td>
                <td class="px-4 py-3 text-center">
                  <span
                    v-if="classAverage !== '—'"
                    :class="[
                      'inline-block px-3 py-1 rounded-lg font-bold text-xs',
                      getGradeClass(parseFloat(classAverage))
                    ]"
                  >
                    {{ classAverage }}
                  </span>
                  <span v-else class="text-grey-400 text-xs">—</span>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- Keyboard hint -->
      <p v-if="examTypes.length > 0 && students.length > 0" class="mt-3 text-xs text-grey-500 text-center">
        Click any cell to enter or edit a grade · Press <kbd class="px-1 py-0.5 bg-grey-100 rounded text-grey-600 font-mono">Enter</kbd> to save · <kbd class="px-1 py-0.5 bg-grey-100 rounded text-grey-600 font-mono">Esc</kbd> to cancel
      </p>
    </div>

    <!-- Add Exam Type Modal -->
    <TransitionRoot :show="showAddExamTypeModal" as="template">
      <Dialog @close="showAddExamTypeModal = false" class="relative z-50">
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
                  <DialogTitle class="text-lg font-semibold text-grey-900">Add Exam Type</DialogTitle>
                  <p class="text-sm text-grey-600 mt-1">e.g. "Quiz 1", "Midterm", "Final Exam"</p>
                </div>
                <div class="p-6 space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Name *</label>
                    <input
                      v-model="newExamTypeName"
                      type="text"
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Quiz 1"
                      @keydown.enter="submitAddExamType"
                    />
                  </div>
                  <div v-if="examTypeError" class="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p class="text-sm text-red-700">{{ examTypeError }}</p>
                  </div>
                  <div class="flex gap-3 pt-2">
                    <button
                      @click="showAddExamTypeModal = false"
                      class="flex-1 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
                    >
                      Cancel
                    </button>
                    <button
                      @click="submitAddExamType"
                      :disabled="creatingExamType || !newExamTypeName.trim()"
                      class="flex-1 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50"
                    >
                      {{ creatingExamType ? 'Adding...' : 'Add' }}
                    </button>
                  </div>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>

    <!-- Add Grade Modal -->
    <TransitionRoot :show="showAddGradeModal" as="template">
      <Dialog @close="showAddGradeModal = false" class="relative z-50">
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
                  <DialogTitle class="text-lg font-semibold text-grey-900">Add / Update Grade</DialogTitle>
                </div>
                <div class="p-6 space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Student *</label>
                    <select
                      v-model="gradeForm.student_id"
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option :value="null" disabled>Select student</option>
                      <option v-for="s in students" :key="s.id" :value="s.id">{{ s.name }}</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Exam Type *</label>
                    <select
                      v-model="gradeForm.exam_type_id"
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option :value="null" disabled>Select exam type</option>
                      <option v-for="et in examTypes" :key="et.id" :value="et.id">{{ et.name }}</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Grade (0 – 20) *</label>
                    <input
                      v-model.number="gradeForm.value"
                      type="number"
                      min="0"
                      max="20"
                      step="0.25"
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="e.g. 15.5"
                    />
                  </div>
                  <div v-if="gradeError" class="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p class="text-sm text-red-700">{{ gradeError }}</p>
                  </div>
                  <div class="flex gap-3 pt-2">
                    <button @click="showAddGradeModal = false"
                      class="flex-1 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition">
                      Cancel
                    </button>
                    <button
                      @click="submitGradeModal"
                      :disabled="savingGrade || gradeForm.student_id === null || gradeForm.exam_type_id === null || gradeForm.value === null"
                      class="flex-1 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50"
                    >
                      {{ savingGrade ? 'Saving...' : 'Save Grade' }}
                    </button>
                  </div>
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
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
  ChevronLeftIcon,
  PlusIcon,
  XMarkIcon,
  TagIcon,
  UserGroupIcon,
  ClipboardDocumentListIcon,
  CheckBadgeIcon,
  ChartBarIcon
} from '@heroicons/vue/24/outline';
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import api from '@/services/api';

const route = useRoute();
const classId = computed(() => parseInt(route.params.id));

// ── Data ────────────────────────────────────────────
const classData = ref(null);
const students = ref([]);
const examTypes = ref([]);
const grades = ref([]); // flat list from backend

const loading = ref(true);
const filterExamTypeId = ref(null);

// ── Exam Type Modal ──────────────────────────────────
const showAddExamTypeModal = ref(false);
const newExamTypeName = ref('');
const creatingExamType = ref(false);
const examTypeError = ref('');

// ── Grade Modal ──────────────────────────────────────
const showAddGradeModal = ref(false);
const gradeForm = ref({ student_id: null, exam_type_id: null, value: null });
const savingGrade = ref(false);
const gradeError = ref('');

// ── Inline Edit ──────────────────────────────────────
const editingCell = ref(null); // { studentId, examTypeId }
const editValue = ref('');
const editInput = ref(null);

// ── Computed ─────────────────────────────────────────

const visibleExamTypes = computed(() => {
  if (filterExamTypeId.value === null) return examTypes.value;
  return examTypes.value.filter(et => et.id === filterExamTypeId.value);
});

// grade map: gradeMap[studentId][examTypeId] = { id, value }
const gradeMap = computed(() => {
  const map = {};
  grades.value.forEach(g => {
    if (!map[g.student_id]) map[g.student_id] = {};
    map[g.student_id][g.exam_type_id] = { id: g.id, value: g.value };
  });
  return map;
});

function getGrade(studentId, examTypeId) {
  return gradeMap.value[studentId]?.[examTypeId]?.value ?? null;
}

function getGradeClass(value) {
  if (value === null) return '';
  if (value >= 16) return 'bg-success-100 text-success-800';
  if (value >= 12) return 'bg-blue-100 text-blue-800';
  if (value >= 10) return 'bg-amber-100 text-amber-800';
  return 'bg-red-100 text-red-800';
}

function getStudentAverage(studentId) {
  const studentGrades = examTypes.value
    .map(et => getGrade(studentId, et.id))
    .filter(v => v !== null);
  if (studentGrades.length === 0) return null;
  return studentGrades.reduce((a, b) => a + b, 0) / studentGrades.length;
}

function getExamTypeAverage(examTypeId) {
  const vals = students.value
    .map(s => getGrade(s.id, examTypeId))
    .filter(v => v !== null);
  if (vals.length === 0) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

const classAverage = computed(() => {
  const avgs = students.value
    .map(s => getStudentAverage(s.id))
    .filter(v => v !== null);
  if (avgs.length === 0) return '—';
  return (avgs.reduce((a, b) => a + b, 0) / avgs.length).toFixed(2);
});

const gradesFilled = computed(() => grades.value.length);

// ── Load Data ────────────────────────────────────────

async function loadAll() {
  loading.value = true;
  try {
    const [classesRes, studentsRes, examTypesRes, gradesRes] = await Promise.all([
      api.getClasses(),
      api.getStudents(classId.value),
      api.getExamTypes(classId.value),
      api.getGrades(classId.value)
    ]);

    if (classesRes.success) {
      classData.value = classesRes.classes.find(c => c.id === classId.value) || null;
    }
    if (studentsRes.success) students.value = studentsRes.students || [];
    if (examTypesRes.success) examTypes.value = examTypesRes.exam_types || [];
    if (gradesRes.success) grades.value = gradesRes.grades || [];
  } catch (err) {
    console.error('Failed to load grades page:', err);
  } finally {
    loading.value = false;
  }
}

// ── Exam Type CRUD ────────────────────────────────────

async function submitAddExamType() {
  examTypeError.value = '';
  const name = newExamTypeName.value.trim();
  if (!name) return;
  creatingExamType.value = true;
  try {
    const res = await api.createExamType(classId.value, name);
    if (res.success) {
      examTypes.value.push(res.exam_type);
      newExamTypeName.value = '';
      showAddExamTypeModal.value = false;
    }
  } catch (err) {
    examTypeError.value = err.message || 'Failed to add exam type';
  } finally {
    creatingExamType.value = false;
  }
}

async function deleteExamType(et) {
  if (!confirm(`Delete exam type "${et.name}"? All related grades will be removed.`)) return;
  try {
    await api.deleteExamType(classId.value, et.id);
    examTypes.value = examTypes.value.filter(e => e.id !== et.id);
    grades.value = grades.value.filter(g => g.exam_type_id !== et.id);
    if (filterExamTypeId.value === et.id) filterExamTypeId.value = null;
  } catch (err) {
    alert('Failed to delete: ' + err.message);
  }
}

// ── Grade CRUD ────────────────────────────────────────

function openAddGradeModal(student = null, examType = null) {
  gradeForm.value = {
    student_id: student?.id ?? null,
    exam_type_id: examType?.id ?? null,
    value: null
  };
  gradeError.value = '';
  showAddGradeModal.value = true;
}

async function submitGradeModal() {
  gradeError.value = '';
  const { student_id, exam_type_id, value } = gradeForm.value;
  if (student_id === null || exam_type_id === null || value === null) return;
  if (value < 0 || value > 20) { gradeError.value = 'Grade must be between 0 and 20'; return; }

  savingGrade.value = true;
  try {
    const res = await api.saveGrade(classId.value, student_id, exam_type_id, value);
    if (res.success) {
      upsertGradeLocally(res.grade);
      showAddGradeModal.value = false;
    }
  } catch (err) {
    gradeError.value = err.message || 'Failed to save grade';
  } finally {
    savingGrade.value = false;
  }
}

// ── Inline Edit ──────────────────────────────────────

function startEdit(student, examType) {
  const current = getGrade(student.id, examType.id);
  editingCell.value = { studentId: student.id, examTypeId: examType.id };
  editValue.value = current !== null ? String(current) : '';
  nextTick(() => {
    if (editInput.value) {
      const el = Array.isArray(editInput.value) ? editInput.value[0] : editInput.value;
      el?.focus();
      el?.select();
    }
  });
}

async function saveEdit() {
  if (!editingCell.value) return;
  const { studentId, examTypeId } = editingCell.value;
  const raw = editValue.value.trim();

  // Empty = delete grade if it exists
  if (raw === '') {
    const existing = gradeMap.value[studentId]?.[examTypeId];
    if (existing) {
      try {
        await api.deleteGrade(classId.value, existing.id);
        grades.value = grades.value.filter(g => g.id !== existing.id);
      } catch (err) {
        console.error('Delete failed:', err);
      }
    }
    editingCell.value = null;
    return;
  }

  const val = parseFloat(raw);
  if (isNaN(val) || val < 0 || val > 20) {
    cancelEdit();
    return;
  }

  try {
    const res = await api.saveGrade(classId.value, studentId, examTypeId, val);
    if (res.success) upsertGradeLocally(res.grade);
  } catch (err) {
    console.error('Save failed:', err);
  } finally {
    editingCell.value = null;
  }
}

function cancelEdit() {
  editingCell.value = null;
}

function upsertGradeLocally(grade) {
  const idx = grades.value.findIndex(
    g => g.student_id === grade.student_id && g.exam_type_id === grade.exam_type_id
  );
  if (idx >= 0) {
    grades.value[idx] = grade;
  } else {
    grades.value.push(grade);
  }
}

// ── Init ─────────────────────────────────────────────
onMounted(loadAll);

watch(showAddExamTypeModal, (val) => {
  if (!val) { newExamTypeName.value = ''; examTypeError.value = ''; }
});
</script>