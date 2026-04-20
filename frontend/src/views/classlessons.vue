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
        <span class="text-grey-900 font-medium">Lessons</span>
      </div>
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-grey-900 mb-1">Lessons</h1>
          <p class="text-grey-600">{{ files.length }} file{{ files.length !== 1 ? 's' : '' }} uploaded</p>
        </div>
        <button
          @click="showUploadModal = true"
          class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 shadow-sm transition"
        >
          <ArrowUpTrayIcon class="w-5 h-5" />
          Upload File
        </button>
      </div>
    </div>

    <div class="p-8">
      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
      </div>

      <!-- Empty -->
      <div v-else-if="files.length === 0" class="bg-white rounded-xl border border-grey-200 shadow-sm p-16 text-center">
        <DocumentIcon class="w-14 h-14 text-grey-300 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-grey-900 mb-2">No files uploaded yet</h3>
        <p class="text-grey-600 mb-6">Upload PDF teaching materials for this class.</p>
        <button @click="showUploadModal = true"
          class="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-primary-700 transition">
          <ArrowUpTrayIcon class="w-5 h-5" />
          Upload First File
        </button>
      </div>

      <!-- Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="file in files" :key="file.id"
          class="bg-white rounded-xl border border-grey-200 shadow-sm overflow-hidden hover:shadow-md transition group">
          <div class="h-28 flex items-center justify-center bg-gradient-to-br from-red-500 to-red-600">
            <DocumentTextIcon class="w-14 h-14 text-white" />
          </div>
          <div class="p-5">
            <h3 class="font-semibold text-grey-900 mb-3 truncate" :title="file.name">{{ file.name }}</h3>
            <div class="flex items-center justify-between text-xs text-grey-500 mb-4">
              <span>{{ formatDate(file.created_at) }}</span>
              <span>{{ formatSize(file.size) }}</span>
            </div>
            <div class="flex gap-2">
              <button @click="downloadFile(file)"
                class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition text-sm font-medium">
                <ArrowDownTrayIcon class="w-4 h-4" />
                Download
              </button>
              <button @click="deleteFile(file)"
                class="px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition">
                <TrashIcon class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Upload Modal -->
    <TransitionRoot :show="showUploadModal" as="template">
      <Dialog @close="showUploadModal = false" class="relative z-50">
        <TransitionChild enter="ease-out duration-200" enter-from="opacity-0" enter-to="opacity-100"
          leave="ease-in duration-150" leave-from="opacity-100" leave-to="opacity-0">
          <div class="fixed inset-0 bg-black/25 backdrop-blur-sm" />
        </TransitionChild>
        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild enter="ease-out duration-200" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
              leave="ease-in duration-150" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95">
              <DialogPanel class="w-full max-w-md bg-white rounded-2xl shadow-xl">
                <div class="p-6 border-b border-grey-200">
                  <DialogTitle class="text-xl font-semibold text-grey-900">Upload Lesson File</DialogTitle>
                </div>
                <div class="p-6 space-y-4">
                  <div class="border-2 border-dashed border-grey-300 rounded-lg p-8 text-center hover:border-primary-500 transition">
                    <input type="file" ref="fileInput" @change="handleFileSelect" accept=".pdf" class="hidden" />
                    <button type="button" @click="$refs.fileInput.click()"
                      class="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700">
                      <ArrowUpTrayIcon class="w-6 h-6" />
                      <span class="font-medium">Click to browse files</span>
                    </button>
                    <p class="text-sm text-grey-500 mt-2">PDF files only · Max 150 MB</p>
                    <div v-if="selectedFile" class="mt-4 flex items-center justify-center gap-2 text-sm text-grey-700">
                      <DocumentIcon class="w-5 h-5 text-primary-500" />
                      <span class="font-medium">{{ selectedFile.name }}</span>
                      <span class="text-grey-400">({{ formatSize(selectedFile.size) }})</span>
                    </div>
                  </div>
                  <div v-if="uploadError" class="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p class="text-sm text-red-700">{{ uploadError }}</p>
                  </div>
                  <div class="flex gap-3">
                    <button @click="showUploadModal = false"
                      class="flex-1 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition">
                      Cancel
                    </button>
                    <button @click="handleUpload" :disabled="!selectedFile || uploading"
                      class="flex-1 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50">
                      {{ uploading ? 'Uploading…' : 'Upload' }}
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
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import {
  ChevronLeftIcon,
  ArrowUpTrayIcon,
  ArrowDownTrayIcon,
  DocumentIcon,
  DocumentTextIcon,
  TrashIcon
} from '@heroicons/vue/24/outline';
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import api from '@/services/api';

const route = useRoute();
const classId = computed(() => parseInt(route.params.id));

const loading = ref(true);
const files = ref([]);
const showUploadModal = ref(false);
const uploading = ref(false);
const uploadError = ref('');
const selectedFile = ref(null);

function formatDate(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatSize(bytes) {
  if (!bytes) return '0 KB';
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

async function loadFiles() {
  loading.value = true;
  try {
    const res = await api.getLessons(classId.value, { limit: 100, refresh: true });
    if (res.success) files.value = res.uploads || [];
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.pdf')) { uploadError.value = 'Only PDF files are allowed'; return; }
  if (file.size > 150 * 1024 * 1024) { uploadError.value = 'File exceeds 150 MB'; return; }
  selectedFile.value = file;
  uploadError.value = '';
}

async function handleUpload() {
  if (!selectedFile.value) return;
  uploading.value = true;
  uploadError.value = '';
  try {
    const fd = new FormData();
    fd.append('file', selectedFile.value);
    fd.append('class_id', classId.value);
    const res = await api.uploadLesson(fd);
    if (res.success) {
      files.value.unshift(res.upload);
      showUploadModal.value = false;
      selectedFile.value = null;
      if (res.upload.already_exists) alert('This file already exists in this class.');
    }
  } catch (err) {
    uploadError.value = err.message || 'Upload failed';
  } finally {
    uploading.value = false;
  }
}

function downloadFile(file) {
  window.open(`http://localhost:8000/uploads/classes/${classId.value}/${file.name}`, '_blank');
}

async function deleteFile(file) {
  if (!confirm(`Delete "${file.name}"?`)) return;
  try {
    await api.deleteLesson(file.id);
    files.value = files.value.filter(f => f.id !== file.id);
  } catch (err) {
    alert('Failed to delete: ' + err.message);
  }
}

onMounted(loadFiles);
</script>