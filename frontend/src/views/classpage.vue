<template>
  <div class="h-full overflow-y-auto custom-scrollbar bg-grey-50">
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

      <div class="flex items-start justify-between">
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
        
        <!-- Quick Stats -->
        <div class="flex gap-4">
          <div class="text-center px-4 py-2 bg-primary-50 rounded-lg">
            <div class="text-2xl font-bold text-primary-600">{{ students.length }}</div>
            <div class="text-xs text-primary-700">Students</div>
          </div>
          <div class="text-center px-4 py-2 bg-success-50 rounded-lg">
            <div class="text-2xl font-bold text-success-600">{{ classFiles.length }}</div>
            <div class="text-xs text-success-700">Files</div>
          </div>
          <div class="text-center px-4 py-2 bg-red-50 rounded-lg">
            <div class="text-2xl font-bold text-red-600">{{ flaggedStudents.length }}</div>
            <div class="text-xs text-red-700">Flagged</div>
          </div>
        </div>
      </div>
    </div>

    <div class="p-8">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column: Students List -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Students Card -->
          <div class="bg-white rounded-xl shadow-sm border border-grey-200">
            <div class="p-6 border-b border-grey-200 flex items-center justify-between">
              <div>
                <h2 class="text-xl font-semibold text-grey-900">Students</h2>
                <p class="text-grey-600 text-sm mt-1">{{ students.length }} student{{ students.length !== 1 ? 's' : '' }} enrolled</p>
              </div>
              <button
                @click="showAddStudent = true"
                class="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition text-sm"
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

            <div v-else class="divide-y divide-grey-200">
              <div
                v-for="student in students"
                :key="student.id"
                class="p-4 hover:bg-grey-50 transition flex items-center justify-between"
              >
                <div class="flex items-center gap-3 flex-1">
                  <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center text-white font-semibold">
                    {{ student.name.charAt(0).toUpperCase() }}
                  </div>
                  <div class="flex-1">
                    <div class="font-medium text-grey-900">{{ student.name }}</div>
                    <div class="text-sm text-grey-600">{{ student.email || 'No email' }}</div>
                  </div>
                  <div v-if="student.flagged" class="flex items-center gap-1 px-2 py-1 bg-red-50 text-red-700 rounded-full text-xs font-medium">
                    <ExclamationTriangleIcon class="w-4 h-4" />
                    Flagged
                  </div>
                </div>
                <button
                  @click="deleteStudent(student.id)"
                  class="ml-4 text-red-600 hover:text-red-700 transition"
                >
                  <TrashIcon class="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          <!-- Lesson Files Card -->
          <div class="bg-white rounded-xl shadow-sm border border-grey-200">
            <div class="p-6 border-b border-grey-200 flex items-center justify-between">
              <div>
                <h2 class="text-xl font-semibold text-grey-900">Lesson Files</h2>
                <p class="text-grey-600 text-sm mt-1">{{ classFiles.length }} file{{ classFiles.length !== 1 ? 's' : '' }} uploaded</p>
              </div>
              <button
                @click="showUploadFile = true"
                class="flex items-center gap-2 bg-success-600 text-white px-4 py-2 rounded-lg hover:bg-success-700 transition text-sm"
              >
                <ArrowUpTrayIcon class="w-5 h-5" />
                Upload File
              </button>
            </div>

            <div v-if="loadingFiles" class="p-12 flex items-center justify-center">
              <div class="animate-spin rounded-full h-8 w-8 border-4 border-success-500 border-t-transparent"></div>
            </div>

            <div v-else-if="classFiles.length === 0" class="p-12 text-center">
              <DocumentIcon class="w-12 h-12 text-grey-300 mx-auto mb-3" />
              <p class="text-grey-600 mb-4">No files uploaded yet</p>
              <button
                @click="showUploadFile = true"
                class="text-success-600 font-medium hover:text-success-700"
              >
                Upload your first file
              </button>
            </div>

            <div v-else class="divide-y divide-grey-200">
              <div
                v-for="file in classFiles"
                :key="file.id"
                class="p-4 hover:bg-grey-50 transition flex items-center justify-between"
              >
                <div class="flex items-center gap-3 flex-1">
                  <div :class="['w-10 h-10 rounded-lg flex items-center justify-center', getFileIconBg(file.file_type)]">
                    <component :is="getFileIcon(file.file_type)" class="w-5 h-5 text-white" />
                  </div>
                  <div class="flex-1">
                    <div class="font-medium text-grey-900">{{ file.file_name }}</div>
                    <div class="text-sm text-grey-600">{{ formatDate(file.uploaded_at) }} • {{ formatFileSize(file.file_size) }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    @click="downloadFile(file)"
                    class="text-primary-600 hover:text-primary-700 transition"
                  >
                    <ArrowDownTrayIcon class="w-5 h-5" />
                  </button>
                  <button
                    @click="deleteFile(file.id)"
                    class="text-red-600 hover:text-red-700 transition"
                  >
                    <TrashIcon class="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Flagged Students -->
        <div class="space-y-6">
          <div class="bg-gradient-to-br from-red-500 to-red-600 rounded-xl shadow-lg p-6 text-white">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                <ExclamationTriangleIcon class="w-6 h-6" />
              </div>
              <div>
                <h2 class="text-xl font-semibold">Flagged Students</h2>
                <p class="text-red-50 text-sm">Requires attention</p>
              </div>
            </div>

            <div v-if="flaggedStudents.length === 0" class="text-center py-8">
              <p class="text-red-100">No students flagged</p>
              <p class="text-sm text-red-200 mt-1">AI will flag students who need attention</p>
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="student in flaggedStudents"
                :key="student.id"
                class="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20"
              >
                <div class="flex items-start justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center text-sm font-semibold">
                      {{ student.name.charAt(0).toUpperCase() }}
                    </div>
                    <span class="font-medium">{{ student.name }}</span>
                  </div>
                  <button
                    @click="unflagStudent(student.id)"
                    class="text-white/80 hover:text-white transition"
                  >
                    <XMarkIcon class="w-5 h-5" />
                  </button>
                </div>
                <p class="text-sm text-red-100">{{ student.flag_reason || 'Behavior concerns detected by AI' }}</p>
                <div class="mt-2 text-xs text-red-200">
                  {{ formatDate(student.flagged_at) }}
                </div>
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="bg-white rounded-xl shadow-sm border border-grey-200 p-6">
            <h3 class="font-semibold text-grey-900 mb-4">Quick Actions</h3>
            <div class="space-y-2">
              <button
                @click="$router.push('/lessons')"
                class="w-full flex items-center gap-3 px-4 py-3 bg-grey-50 hover:bg-grey-100 rounded-lg transition text-left"
              >
                <DocumentTextIcon class="w-5 h-5 text-grey-600" />
                <div>
                  <div class="font-medium text-grey-900 text-sm">View All Files</div>
                  <div class="text-xs text-grey-600">Manage lesson materials</div>
                </div>
              </button>
              <button
                class="w-full flex items-center gap-3 px-4 py-3 bg-grey-50 hover:bg-grey-100 rounded-lg transition text-left"
              >
                <ChartBarIcon class="w-5 h-5 text-grey-600" />
                <div>
                  <div class="font-medium text-grey-900 text-sm">Class Analytics</div>
                  <div class="text-xs text-grey-600">View performance data</div>
                </div>
              </button>
              <button
                class="w-full flex items-center gap-3 px-4 py-3 bg-grey-50 hover:bg-grey-100 rounded-lg transition text-left"
              >
                <ClipboardDocumentCheckIcon class="w-5 h-5 text-grey-600" />
                <div>
                  <div class="font-medium text-grey-900 text-sm">Mark Attendance</div>
                  <div class="text-xs text-grey-600">Today's attendance</div>
                </div>
              </button>
            </div>
          </div>
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
                    <label class="block text-sm font-medium text-grey-700 mb-2">Email *</label>
                    <input
                      v-model="studentForm.email"
                      type="email"
                      required
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="student@email.com"
                    />
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

    <!-- Upload File Modal -->
    <TransitionRoot :show="showUploadFile" as="template">
      <Dialog @close="showUploadFile = false" class="relative z-50">
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
                  <DialogTitle class="text-xl font-semibold text-grey-900">Upload File to {{ classData?.name }}</DialogTitle>
                </div>

                <form @submit.prevent="handleUploadFile" class="p-6 space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Select File *</label>
                    <div class="border-2 border-dashed border-grey-300 rounded-lg p-8 text-center hover:border-primary-500 transition">
                      <input
                        type="file"
                        ref="fileInput"
                        @change="handleFileSelect"
                        accept=".pdf,.doc,.docx,.ppt,.pptx,.txt,.jpg,.jpeg,.png"
                        class="hidden"
                      />
                      <button
                        type="button"
                        @click="$refs.fileInput.click()"
                        class="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700"
                      >
                        <ArrowUpTrayIcon class="w-6 h-6" />
                        <span class="font-medium">Click to browse files</span>
                      </button>
                      <p class="text-sm text-grey-500 mt-2">PDF, DOC, PPT, TXT, or Images</p>
                      
                      <div v-if="uploadForm.file" class="mt-4 flex items-center justify-center gap-2 text-sm text-grey-700">
                        <DocumentIcon class="w-5 h-5 text-primary-500" />
                        <span class="font-medium">{{ uploadForm.file.name }}</span>
                      </div>
                    </div>
                  </div>

                  <div class="flex gap-3 pt-4">
                    <button
                      type="button"
                      @click="showUploadFile = false"
                      class="flex-1 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      :disabled="!uploadForm.file || uploadingFile"
                      class="flex-1 bg-gradient-to-r from-success-600 to-success-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-success-700 hover:to-success-600 transition disabled:opacity-50"
                    >
                      {{ uploadingFile ? 'Uploading...' : 'Upload' }}
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
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import {
  ChevronLeftIcon,
  PlusIcon,
  UserGroupIcon,
  TrashIcon,
  DocumentIcon,
  ArrowUpTrayIcon,
  ArrowDownTrayIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
  DocumentTextIcon,
  PhotoIcon,
  PresentationChartBarIcon,
  ChartBarIcon,
  ClipboardDocumentCheckIcon
} from '@heroicons/vue/24/outline';
import api from '@/services/api';

const route = useRoute();

const classData = ref(null);
const students = ref([]);
const classFiles = ref([]);
const loadingStudents = ref(true);
const loadingFiles = ref(true);
const showAddStudent = ref(false);
const showUploadFile = ref(false);
const addingStudent = ref(false);
const uploadingFile = ref(false);

const studentForm = ref({
  name: '',
  email: ''
});

const uploadForm = ref({
  file: null
});

const flaggedStudents = computed(() => {
  return students.value.filter(s => s.flagged);
});

function getFileIcon(fileType) {
  const type = fileType?.toLowerCase() || '';
  if (['pdf', 'doc', 'docx', 'txt'].includes(type)) return DocumentTextIcon;
  if (['ppt', 'pptx'].includes(type)) return PresentationChartBarIcon;
  if (['jpg', 'jpeg', 'png', 'gif'].includes(type)) return PhotoIcon;
  return DocumentIcon;
}

function getFileIconBg(fileType) {
  const type = fileType?.toLowerCase() || '';
  if (['pdf'].includes(type)) return 'bg-red-500';
  if (['doc', 'docx'].includes(type)) return 'bg-blue-500';
  if (['ppt', 'pptx'].includes(type)) return 'bg-orange-500';
  if (['jpg', 'jpeg', 'png', 'gif'].includes(type)) return 'bg-purple-500';
  return 'bg-grey-500';
}

function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatFileSize(bytes) {
  if (!bytes) return '0 KB';
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
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

async function loadClassFiles() {
  try {
    const response = await api.getLessons(route.params.id);
    if (response.success) {
      classFiles.value = response.files || [];
    }
  } catch (error) {
    console.error('Failed to load files:', error);
  } finally {
    loadingFiles.value = false;
  }
}

async function handleAddStudent() {
  addingStudent.value = true;
  try {
    const response = await api.createStudent({
      class_id: parseInt(route.params.id),
      name: studentForm.value.name,
      email: studentForm.value.email,
      flagged: false
    });
    if (response.success) {
      students.value.push(response.student);
      showAddStudent.value = false;
      studentForm.value = { name: '', email: '' };
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

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;
  uploadForm.value.file = file;
}

async function handleUploadFile() {
  if (!uploadForm.value.file) return;

  uploadingFile.value = true;
  try {
    const formData = new FormData();
    formData.append('file', uploadForm.value.file);
    formData.append('class_id', route.params.id);

    const response = await api.uploadLesson(formData);
    
    if (response.success) {
      classFiles.value.unshift(response.file);
      showUploadFile.value = false;
      uploadForm.value = { file: null };
    }
  } catch (error) {
    alert('Failed to upload file: ' + error.message);
  } finally {
    uploadingFile.value = false;
  }
}

async function downloadFile(file) {
  try {
    window.open(file.file_url, '_blank');
  } catch (error) {
    alert('Failed to download file: ' + error.message);
  }
}

async function deleteFile(fileId) {
  if (!confirm('Are you sure you want to delete this file?')) return;
  
  try {
    await api.deleteLesson(fileId);
    classFiles.value = classFiles.value.filter(f => f.id !== fileId);
  } catch (error) {
    alert('Failed to delete file: ' + error.message);
  }
}

async function unflagStudent(studentId) {
  try {
    const response = await api.updateStudent(studentId, { flagged: false });
    if (response.success) {
      const student = students.value.find(s => s.id === studentId);
      if (student) {
        student.flagged = false;
      }
    }
  } catch (error) {
    alert('Failed to unflag student: ' + error.message);
  }
}

onMounted(() => {
  loadClass();
  loadStudents();
  loadClassFiles();
});
</script>