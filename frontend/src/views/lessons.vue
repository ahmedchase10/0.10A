<template>
  <div class="p-8">
    <!-- Header -->
    <div class="mb-8 flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-grey-900">Lesson Files</h1>
        <p class="text-grey-600 mt-1">Upload and manage teaching materials</p>
      </div>
      <button
        @click="showUploadModal = true"
        :disabled="!selectedClassId"
        class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-3 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 shadow-sm transition disabled:opacity-50"
      >
        <ArrowUpTrayIcon class="w-5 h-5" />
        Upload File
      </button>
    </div>

    <!-- Filter by Class -->
    <div class="mb-6 bg-white rounded-xl shadow-sm border border-grey-200 p-4">
      <div class="flex items-center gap-4">
        <label class="text-sm font-medium text-grey-700">Class:</label>
        <select
          v-model="selectedClassId"
          @change="loadFiles"
          class="px-4 py-2 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <!-- BUG-02: no "All Classes" null option — class_id is required by backend -->
          <option v-for="cls in classes" :key="cls.id" :value="cls.id">
            {{ cls.name }}
          </option>
        </select>
        <div class="flex-1"></div>
        <div class="text-sm text-grey-600">
          {{ files.length }} file{{ files.length !== 1 ? 's' : '' }}
        </div>
      </div>
    </div>

    <!-- No classes at all -->
    <div v-if="!loading && classes.length === 0" class="bg-white rounded-xl shadow-sm border border-grey-200 p-16 text-center">
      <AcademicCapIcon class="w-16 h-16 text-grey-300 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-grey-900 mb-2">No classes yet</h3>
      <p class="text-grey-600 mb-6">Create a class first, then upload lesson files to it.</p>
      <router-link to="/"
        class="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition">
        Go to Dashboard
      </router-link>
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
    </div>

    <!-- Empty files for selected class -->
    <div v-else-if="files.length === 0" class="bg-white rounded-xl shadow-sm border border-grey-200 p-16 text-center">
      <DocumentIcon class="w-16 h-16 text-grey-300 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-grey-900 mb-2">No files uploaded yet</h3>
      <p class="text-grey-600 mb-6">Upload your first lesson file for this class.</p>
      <button
        @click="showUploadModal = true"
        class="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition"
      >
        <ArrowUpTrayIcon class="w-5 h-5" />
        Upload Your First File
      </button>
    </div>

    <!-- Files Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="file in files"
        :key="file.id"
        class="bg-white rounded-xl shadow-sm border border-grey-200 overflow-hidden hover:shadow-md transition group"
      >
        <div :class="['h-32 flex items-center justify-center', getFileTypeColor(file.file_type)]">
          <component :is="getFileIcon(file.file_type)" class="w-16 h-16 text-white" />
        </div>

        <div class="p-6">
          <h3 class="font-semibold text-grey-900 mb-2 truncate" :title="file.file_name">
            {{ file.file_name }}
          </h3>

          <div class="space-y-2 mb-4">
            <div class="flex items-center gap-2 text-sm text-grey-600">
              <CalendarIcon class="w-4 h-4" />
              <span>{{ formatDate(file.uploaded_at) }}</span>
            </div>
            <div class="flex items-center gap-2 text-sm text-grey-600">
              <DocumentIcon class="w-4 h-4" />
              <span>{{ formatFileSize(file.file_size) }}</span>
            </div>
          </div>

          <div class="mb-4">
            <span :class="['inline-block px-3 py-1 rounded-full text-xs font-medium', getFileTypeBadge(file.file_type)]">
              {{ file.file_type.toUpperCase() }}
            </span>
          </div>

          <div class="flex gap-2">
            <button
              @click="downloadFile(file)"
              class="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition"
            >
              <ArrowDownTrayIcon class="w-4 h-4" />
              Download
            </button>
            <button
              @click="deleteFile(file.id)"
              class="px-4 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition"
            >
              <TrashIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Upload Modal -->
    <TransitionRoot :show="showUploadModal" as="template">
      <Dialog @close="showUploadModal = false" class="relative z-50">
        <TransitionChild enter="ease-out duration-300" enter-from="opacity-0" enter-to="opacity-100"
          leave="ease-in duration-200" leave-from="opacity-100" leave-to="opacity-0">
          <div class="fixed inset-0 bg-black/25 backdrop-blur-sm" />
        </TransitionChild>
        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild enter="ease-out duration-300" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
              leave="ease-in duration-200" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95">
              <DialogPanel class="w-full max-w-md bg-white rounded-2xl shadow-xl">
                <div class="p-6 border-b border-grey-200">
                  <DialogTitle class="text-xl font-semibold text-grey-900">Upload Lesson File</DialogTitle>
                </div>
                <form @submit.prevent="handleUpload" class="p-6 space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Select File *</label>
                    <div class="border-2 border-dashed border-grey-300 rounded-lg p-8 text-center hover:border-primary-500 transition">
                      <input type="file" ref="fileInput" @change="handleFileSelect" accept=".pdf" class="hidden" />
                      <button type="button" @click="$refs.fileInput.click()"
                        class="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700">
                        <ArrowUpTrayIcon class="w-6 h-6" />
                        <span class="font-medium">Click to browse files</span>
                      </button>
                      <p class="text-sm text-grey-500 mt-2">PDF files only · Max 150 MB</p>
                      <div v-if="uploadForm.file" class="mt-4 flex items-center justify-center gap-2 text-sm text-grey-700">
                        <DocumentIcon class="w-5 h-5 text-primary-500" />
                        <span class="font-medium">{{ uploadForm.file.name }}</span>
                        <span class="text-grey-500">({{ formatFileSize(uploadForm.file.size) }})</span>
                      </div>
                    </div>
                  </div>

                  <div v-if="uploadError" class="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p class="text-sm text-red-800">{{ uploadError }}</p>
                  </div>

                  <div class="flex gap-3 pt-4">
                    <button type="button" @click="showUploadModal = false"
                      class="flex-1 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition">
                      Cancel
                    </button>
                    <button type="submit" :disabled="!uploadForm.file || uploading"
                      class="flex-1 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50">
                      {{ uploading ? 'Uploading...' : 'Upload File' }}
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
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import {
  ArrowUpTrayIcon, ArrowDownTrayIcon, DocumentIcon, TrashIcon,
  AcademicCapIcon, CalendarIcon, DocumentTextIcon, PhotoIcon,
  PresentationChartBarIcon
} from '@heroicons/vue/24/outline';
import api from '@/services/api';

const loading         = ref(true);
const files           = ref([]);
const classes         = ref([]);
// BUG-02: null removed — stays null until we know the first class id
const selectedClassId = ref(null);
const showUploadModal = ref(false);
const uploading       = ref(false);
const uploadError     = ref('');
const uploadForm      = ref({ file: null });

// ── helpers ────────────────────────────────────────────────────────────────
function getFileIcon(fileType) {
  const t = (fileType || '').toLowerCase();
  if (['pdf','doc','docx','txt'].includes(t)) return DocumentTextIcon;
  if (['ppt','pptx'].includes(t))            return PresentationChartBarIcon;
  if (['jpg','jpeg','png','gif'].includes(t)) return PhotoIcon;
  return DocumentIcon;
}
function getFileTypeColor(fileType) {
  const t = (fileType || '').toLowerCase();
  if (t === 'pdf')               return 'bg-gradient-to-br from-red-500 to-red-600';
  if (['doc','docx'].includes(t)) return 'bg-gradient-to-br from-blue-500 to-blue-600';
  if (['ppt','pptx'].includes(t)) return 'bg-gradient-to-br from-orange-500 to-orange-600';
  if (['jpg','jpeg','png','gif'].includes(t)) return 'bg-gradient-to-br from-purple-500 to-purple-600';
  return 'bg-gradient-to-br from-grey-500 to-grey-600';
}
function getFileTypeBadge(fileType) {
  const t = (fileType || '').toLowerCase();
  if (t === 'pdf')               return 'bg-red-50 text-red-700';
  if (['doc','docx'].includes(t)) return 'bg-blue-50 text-blue-700';
  if (['ppt','pptx'].includes(t)) return 'bg-orange-50 text-orange-700';
  if (['jpg','jpeg','png','gif'].includes(t)) return 'bg-purple-50 text-purple-700';
  return 'bg-grey-50 text-grey-700';
}
function formatDate(ds) {
  if (!ds) return '—';
  return new Date(ds).toLocaleDateString('en-US', { year:'numeric', month:'short', day:'numeric' });
}
function formatFileSize(bytes) {
  if (!bytes) return '0 KB';
  const kb = bytes / 1024;
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb/1024).toFixed(1)} MB`;
}

// ── data loading ────────────────────────────────────────────────────────────
async function loadFiles() {
  if (!selectedClassId.value) return; // BUG-02: guard
  loading.value = true;
  try {
    const res = await api.getLessons(selectedClassId.value, { limit: 100, refresh: true });
    if (res.success) {
      files.value = (res.uploads || []).map(u => ({
        id:          u.id,
        file_name:   u.name,
        file_type:   u.name.split('.').pop(),
        file_size:   u.size,
        uploaded_at: u.created_at,
      }));
    }
  } catch (err) {
    console.error('loadFiles error:', err);
  } finally {
    loading.value = false;
  }
}

// ── upload ──────────────────────────────────────────────────────────────────
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.pdf')) { uploadError.value = 'Only PDF files are allowed'; return; }
  if (file.size > 150 * 1024 * 1024)             { uploadError.value = 'File exceeds 150 MB'; return; }
  uploadForm.value.file = file;
  uploadError.value     = '';
}

async function handleUpload() {
  if (!uploadForm.value.file || !selectedClassId.value) return;
  uploading.value   = true;
  uploadError.value = '';
  try {
    const fd = new FormData();
    fd.append('file', uploadForm.value.file);
    fd.append('class_id', selectedClassId.value);
    const res = await api.uploadLesson(fd);
    if (res.success) {
      if (!res.upload.already_exists) {
        files.value.unshift({
          id:          res.upload.id,
          file_name:   res.upload.name,
          file_type:   res.upload.name.split('.').pop(),
          file_size:   res.upload.size,
          uploaded_at: res.upload.created_at,
        });
      }
      showUploadModal.value = false;
      uploadForm.value.file = null;
      if (res.upload.already_exists) alert('This file already exists in this class.');
    }
  } catch (err) {
    uploadError.value = err.message || 'Upload failed';
  } finally {
    uploading.value = false;
  }
}

function downloadFile(file) {
  window.open(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/uploads/classes/${selectedClassId.value}/${file.file_name}`, '_blank');
}

async function deleteFile(fileId) {
  if (!confirm('Delete this file?')) return;
  try {
    await api.deleteLesson(fileId);
    files.value = files.value.filter(f => f.id !== fileId);
  } catch (err) {
    alert('Failed to delete: ' + err.message);
  }
}

// ── mount ───────────────────────────────────────────────────────────────────
// BUG-02: load classes first, then default to first class before fetching files
onMounted(async () => {
  try {
    const res = await api.getClasses();
    if (res.success) classes.value = res.classes || [];
  } catch (err) {
    console.error('loadClasses error:', err);
  }

  // BUG-02: only fetch files when we have a valid class_id
  if (classes.value.length > 0) {
    selectedClassId.value = classes.value[0].id;
    await loadFiles();
  } else {
    loading.value = false;
  }
});
</script>