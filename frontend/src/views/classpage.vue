<template>
  <div class="h-full overflow-y-auto custom-scrollbar">
    <!-- Header -->
    <div class="bg-white border-b border-grey-200 px-8 py-6">
      <div class="flex items-center gap-3 text-sm text-grey-600 mb-4">
        <router-link to="/" class="hover:text-primary-600 transition flex items-center gap-1">
          <ChevronLeftIcon class="w-4 h-4" />
          Dashboard
        </router-link>
        <span>/</span>
        <span class="text-grey-900 font-medium">{{ classData?.name }}</span>
      </div>

      <div class="flex items-start gap-4">
        <div 
          class="w-1.5 h-16 rounded-full flex-shrink-0"
          :style="{ backgroundColor: classData?.color || '#3b82f6' }"
        ></div>
        <div class="flex-1">
          <h1 class="text-3xl font-bold text-grey-900 mb-2">{{ classData?.name }}</h1>
          <div class="flex flex-wrap gap-2">
            <span v-if="classData?.subject" class="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm font-medium">
              {{ classData.subject }}
            </span>
            <span v-if="classData?.period" class="px-3 py-1 bg-grey-100 text-grey-700 rounded-full text-sm">
              {{ classData.period }}
            </span>
            <span v-if="classData?.room" class="px-3 py-1 bg-grey-100 text-grey-700 rounded-full text-sm">
              {{ classData.room }}
            </span>
            <span v-if="classData?.school" class="px-3 py-1 bg-grey-100 text-grey-700 rounded-full text-sm">
              {{ classData.school }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="p-8 space-y-6">
      <!-- AI Command Zone -->
      <div class="bg-gradient-to-br from-primary-600 via-primary-500 to-primary-700 rounded-2xl shadow-lg p-6 text-white">
        <div class="flex items-start justify-between mb-6">
          <div class="flex items-start gap-3">
            <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm flex-shrink-0">
              <CommandLineIcon class="w-6 h-6" />
            </div>
            <div>
              <h2 class="text-xl font-semibold mb-1">AI Command Console</h2>
              <p class="text-primary-50">Speak or type naturally to execute commands</p>
            </div>
          </div>
          <div class="flex items-center gap-2 px-3 py-1.5 bg-white/20 rounded-full backdrop-blur-sm">
            <div class="w-2 h-2 bg-success-400 rounded-full animate-pulse"></div>
            <span class="text-sm font-medium">Ready</span>
          </div>
        </div>

        <div class="space-y-4">
          <div class="relative">
            <textarea
              v-model="aiCommand"
              @keydown.enter.meta="executeCommand"
              @keydown.enter.ctrl="executeCommand"
              rows="3"
              class="w-full px-4 py-3 bg-white/95 text-grey-900 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-white/50"
              placeholder='Try: "Ahmed and Sara were absent today" or "Homework is exercises 10-15"'
            ></textarea>
            <div class="absolute bottom-3 right-3 flex items-center gap-2">
              <button 
                @click="startVoiceInput"
                class="p-2 hover:bg-white/20 rounded-lg transition text-white"
                title="Voice input"
              >
                <MicrophoneIcon class="w-5 h-5" />
              </button>
              <button
                @click="executeCommand"
                class="px-4 py-2 bg-white text-primary-600 rounded-lg font-medium hover:bg-primary-50 transition flex items-center gap-2"
              >
                <span>Execute</span>
                <PaperAirplaneIcon class="w-4 h-4" />
              </button>
            </div>
          </div>

          <div class="flex flex-wrap gap-2">
            <span class="text-sm text-primary-100">Quick Actions:</span>
            <button
              v-for="action in quickActions"
              :key="action"
              @click="aiCommand = action"
              class="px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition backdrop-blur-sm"
            >
              {{ action }}
            </button>
          </div>
        </div>
      </div>

      <!-- Students Section -->
      <div class="bg-white rounded-xl shadow-sm border border-grey-200">
        <div class="p-6 border-b border-grey-200 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-grey-900">Students</h2>
            <p class="text-grey-600 text-sm mt-1">{{ students.length }} students in this class</p>
          </div>
          <button
            @click="showAddStudent = true"
            class="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition"
          >
            <PlusIcon class="w-5 h-5" />
            Add Student
          </button>
        </div>

        <div v-if="loadingStudents" class="p-12 flex items-center justify-center">
          <div class="animate-spin rounded-full h-8 w-8 border-4 border-primary-500 border-t-transparent"></div>
        </div>

        <div v-else-if="students.length === 0" class="p-12 text-center">
          <UserGroupIcon class="w-12 h-12 text-grey-300 mx-auto mb-3" />
          <p class="text-grey-600 mb-4">No students in this class yet</p>
          <button
            @click="showAddStudent = true"
            class="text-primary-600 font-medium hover:text-primary-700"
          >
            Add your first student
          </button>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-grey-50 border-b border-grey-200">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-grey-500 uppercase tracking-wider">Name</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-grey-500 uppercase tracking-wider">Behavior</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-grey-500 uppercase tracking-wider">Parent Email</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-grey-500 uppercase tracking-wider">Notes</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-grey-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-grey-200">
              <tr v-for="student in students" :key="student.id" class="hover:bg-grey-50 transition">
                <td class="px-6 py-4">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center text-white font-semibold">
                      {{ student.name.charAt(0).toUpperCase() }}
                    </div>
                    <span class="font-medium text-grey-900">{{ student.name }}</span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <span :class="getBehaviorClass(student.behavior)">
                    {{ student.behavior || 'Good' }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-grey-600">{{ student.parent_email || '—' }}</td>
                <td class="px-6 py-4 text-sm text-grey-600 max-w-xs truncate">{{ student.notes || '—' }}</td>
                <td class="px-6 py-4">
                  <button
                    @click="deleteStudent(student.id)"
                    class="text-red-600 hover:text-red-700 transition"
                  >
                    <TrashIcon class="w-5 h-5" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Add Student Modal -->
    <TransitionRoot :show="showAddStudent" as="template">
      <Dialog @close="showAddStudent = false" class="relative z-50">
        <TransitionChild
          enter="ease-out duration-300"
          enter-from="opacity-0"
          enter-to="opacity-100"
          leave="ease-in duration-200"
          leave-from="opacity-100"
          leave-to="opacity-0"
        >
          <div class="fixed inset-0 bg-black/25 backdrop-blur-sm" />
        </TransitionChild>

        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild
              enter="ease-out duration-300"
              enter-from="opacity-0 scale-95"
              enter-to="opacity-100 scale-100"
              leave="ease-in duration-200"
              leave-from="opacity-100 scale-100"
              leave-to="opacity-0 scale-95"
            >
              <DialogPanel class="w-full max-w-md bg-white rounded-2xl shadow-xl">
                <div class="p-6 border-b border-grey-200">
                  <DialogTitle class="text-xl font-semibold text-grey-900">Add Student</DialogTitle>
                </div>

                <form @submit.prevent="handleAddStudent" class="p-6 space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Student Name *</label>
                    <input
                      v-model="studentForm.name"
                      type="text"
                      required
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Ahmed Ben Ali"
                    />
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Parent Email</label>
                    <input
                      v-model="studentForm.parent_email"
                      type="email"
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="parent@email.com"
                    />
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Behavior</label>
                    <select
                      v-model="studentForm.behavior"
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="Excellent">Excellent</option>
                      <option value="Good">Good</option>
                      <option value="Fair">Fair</option>
                      <option value="Needs Improvement">Needs Improvement</option>
                    </select>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Notes</label>
                    <textarea
                      v-model="studentForm.notes"
                      rows="3"
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                      placeholder="Additional notes about the student..."
                    ></textarea>
                  </div>

                  <div class="flex gap-3 pt-4">
                    <button
                      type="button"
                      @click="showAddStudent = false"
                      class="flex-1 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      :disabled="addingStudent"
                      class="flex-1 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50"
                    >
                      {{ addingStudent ? 'Adding...' : 'Add Student' }}
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
import { useRoute } from 'vue-router';
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import {
  ChevronLeftIcon,
  CommandLineIcon,
  MicrophoneIcon,
  PaperAirplaneIcon,
  PlusIcon,
  UserGroupIcon,
  TrashIcon
} from '@heroicons/vue/24/outline';
import api from '@/services/api';

const route = useRoute();

const classData = ref(null);
const students = ref([]);
const loadingStudents = ref(true);
const showAddStudent = ref(false);
const addingStudent = ref(false);
const aiCommand = ref('');

const quickActions = [
  'Mark attendance for today',
  'Show class statistics',
  'Generate report cards'
];

const studentForm = ref({
  name: '',
  parent_email: '',
  behavior: 'Good',
  notes: ''
});

function getBehaviorClass(behavior) {
  const classes = 'px-3 py-1 rounded-full text-sm font-medium ';
  switch(behavior) {
    case 'Excellent':
      return classes + 'bg-success-50 text-success-700';
    case 'Good':
      return classes + 'bg-primary-50 text-primary-700';
    case 'Fair':
      return classes + 'bg-yellow-50 text-yellow-700';
    case 'Needs Improvement':
      return classes + 'bg-red-50 text-red-700';
    default:
      return classes + 'bg-grey-100 text-grey-700';
  }
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
  } finally {
    loadingStudents.value = false;
  }
}

async function handleAddStudent() {
  addingStudent.value = true;
  try {
    const response = await api.createStudent({
      class_id: parseInt(route.params.id),
      ...studentForm.value
    });
    if (response.success) {
      students.value.push(response.student);
      showAddStudent.value = false;
      studentForm.value = {
        name: '',
        parent_email: '',
        behavior: 'Good',
        notes: ''
      };
    }
  } catch (error) {
    alert('Failed to add student: ' + error.message);
  } finally {
    addingStudent.value = false;
  }
}

async function deleteStudent(studentId) {
  if (!confirm('Are you sure you want to remove this student?')) return;
  
  try {
    await api.deleteStudent(studentId);
    students.value = students.value.filter(s => s.id !== studentId);
  } catch (error) {
    alert('Failed to delete student: ' + error.message);
  }
}

function executeCommand() {
  if (!aiCommand.value.trim()) return;
  
  alert(`AI Command: "${aiCommand.value}"\n\nThis will be processed by the multi-agent system.`);
  aiCommand.value = '';
}

function startVoiceInput() {
  alert('Voice input will be implemented with the AI orchestrator.');
}

onMounted(() => {
  loadClass();
  loadStudents();
});
</script>