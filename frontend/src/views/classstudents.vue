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
                  @click="removeStudent(student)"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition font-medium"
                >
                  <TrashIcon class="w-3.5 h-3.5" />
                  Remove
                </button>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import {
  ChevronLeftIcon,
  PlusIcon,
  TrashIcon,
  UserGroupIcon
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

function formatDate(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

async function loadStudents() {
  loading.value = true;
  try {
    const res = await api.getStudents(classId.value);
    if (res.success) students.value = res.students || [];
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

async function removeStudent(student) {
  if (!confirm(`Remove "${student.name}" from this class?`)) return;
  try {
    await api.deleteStudent(classId.value, student.id);
    students.value = students.value.filter(s => s.id !== student.id);
  } catch (err) {
    alert('Failed: ' + err.message);
  }
}

onMounted(loadStudents);
</script>