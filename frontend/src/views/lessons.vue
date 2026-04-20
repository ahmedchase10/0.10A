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
        class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-3 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 shadow-sm transition"
      >
        <ArrowUpTrayIcon class="w-5 h-5" />
        Upload File
      </button>
    </div>

    <!-- Filter by Class -->
    <div class="mb-6 bg-white rounded-xl shadow-sm border border-grey-200 p-4">
      <div class="flex items-center gap-4">
        <label class="text-sm font-medium text-grey-700">Filter by Class:</label>
        <select
          v-model="selectedClassId"
          @change="loadFiles"
          class="px-4 py-2 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option :value="null">All Classes</option>
          <option v-for="cls in classes" :key="cls.id" :value="cls.id">
            {{ cls.name }}
          </option>
        </select>
        <div class="flex-1"></div>
        <div class="text-sm text-grey-600">
          {{ filteredFiles.length }} file{{ filteredFiles.length !== 1 ? 's' : '' }}
        </div>
      </div>
    </div>

    <!-- Files Grid -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
    </div>

    <div v-else-if="filteredFiles.length === 0" class="bg-white rounded-xl shadow-sm border border-grey-200 p-16 text-center">
      <DocumentIcon class="w-16 h-16 text-grey-300 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-grey-900 mb-2">No files uploaded yet</h3>
      <p class="text-grey-600 mb-6">Upload your first lesson file to get started</p>
      <button
        @click="showUploadModal = true"
        class="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition"
      >
        <ArrowUpTrayIcon class="w-5 h-5" />
        Upload Your First File
      </button>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="file in filteredFiles"
        :key="file.id"
        class="bg-white rounded-xl shadow-sm border border-grey-200 overflow-hidden hover:shadow-md transition group"
      >
        <!-- File Icon Header -->
        <div :class="[
          'h-32 flex items-center justify-center',
          getFileTypeColor(file.file_type)
        ]">
          <component :is="getFileIcon(file.file_type)" class="w-16 h-16 text-white" />
        </div>

        <!-- File Details -->
        <div class="p-6">
          <h3 class="font-semibold text-grey-900 mb-2 truncate" :title="file.file_name">
            {{ file.file_name }}
          </h3>
          
          <div class="space-y-2 mb-4">
            <div v-if="file.class_name" class="flex items-center gap-2 text-sm text-grey-600">
              <AcademicCapIcon class="w-4 h-4" />
              <span>{{ file.class_name }}</span>
            </div>
            <div class="flex items-center gap-2 text-sm text-grey-600">
              <CalendarIcon class="w-4 h-4" />
              <span>{{ formatDate(file.uploaded_at) }}</span>
            </div>
            <div class="flex items-center gap-2 text-sm text-grey-600">
              <DocumentIcon class="w-4 h-4" />
              <span>{{ formatFileSize(file.file_size) }}</span>
            </div>
          </div>

          <!-- File Type Badge -->
          <div class="mb-4">
            <span :class="[
              'inline-block px-3 py-1 rounded-full text-xs font-medium',
              getFileTypeBadge(file.file_type)
            ]">
              {{ file.file_type.toUpperCase() }}
            </span>
          </div>

          <!-- Actions -->
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
                  <DialogTitle class="text-xl font-semibold text-grey-900">Upload Lesson File</DialogTitle>
                </div>

                <form @submit.prevent="handleUpload" class="p-6 space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Assign to Class (Optional)</label>
                    <select
                      v-model="uploadForm.class_id"
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option :value="null">No specific class</option>
                      <option v-for="cls in classes" :key="cls.id" :value="cls.id">
                        {{ cls.name }}
                      </option>
                    </select>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Select File *</label>
                    <div class="border-2 border-dashed border-grey-300 rounded-lg p-8 text-center hover:border-primary-500 transition">
                      <input
                        type="file"
                        ref="fileInput"
                        @change="handleFileSelect"
                        accept=".pdf"
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
                      <p class="text-sm text-grey-500 mt-2">PDF files only</p>
                      <p class="text-xs text-grey-400 mt-1">Max size: 150MB</p>
                      
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
                    <button
                      type="button"
                      @click="showUploadModal = false"
                      class="flex-1 px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      :disabled="!uploadForm.file || uploading"
                      class="flex-1 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 transition disabled:opacity-50"
                    >
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
import { ref, computed, onMounted } from 'vue';
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import {
  ArrowUpTrayIcon,
  ArrowDownTrayIcon,
  DocumentIcon,
  TrashIcon,
  AcademicCapIcon,
  CalendarIcon,
  DocumentTextIcon,
  PhotoIcon,
  PresentationChartBarIcon
} from '@heroicons/vue/24/outline';
import api from '@/services/api';

const loading = ref(true);
const files = ref([]);
const classes = ref([]);
const selectedClassId = ref(null);
const showUploadModal = ref(false);
const uploading = ref(false);
const uploadError = ref('');

const uploadForm = ref({
  class_id: null,
  file: null
});

const filteredFiles = computed(() => {
  if (!selectedClassId.value) return files.value;
  return files.value.filter(file => file.class_id === selectedClassId.value);
});

function getFileIcon(fileType) {
  const type = fileType.toLowerCase();
  if (['pdf', 'doc', 'docx', 'txt'].includes(type)) return DocumentTextIcon;
  if (['ppt', 'pptx'].includes(type)) return PresentationChartBarIcon;
  if (['jpg', 'jpeg', 'png', 'gif'].includes(type)) return PhotoIcon;
  return DocumentIcon;
}

function getFileTypeColor(fileType) {
  const type = fileType.toLowerCase();
  if (['pdf'].includes(type)) return 'bg-gradient-to-br from-red-500 to-red-600';
  if (['doc', 'docx'].includes(type)) return 'bg-gradient-to-br from-blue-500 to-blue-600';
  if (['ppt', 'pptx'].includes(type)) return 'bg-gradient-to-br from-orange-500 to-orange-600';
  if (['jpg', 'jpeg', 'png', 'gif'].includes(type)) return 'bg-gradient-to-br from-purple-500 to-purple-600';
  return 'bg-gradient-to-br from-grey-500 to-grey-600';
}

function getFileTypeBadge(fileType) {
  const type = fileType.toLowerCase();
  if (['pdf'].includes(type)) return 'bg-red-50 text-red-700';
  if (['doc', 'docx'].includes(type)) return 'bg-blue-50 text-blue-700';
  if (['ppt', 'pptx'].includes(type)) return 'bg-orange-50 text-orange-700';
  if (['jpg', 'jpeg', 'png', 'gif'].includes(type)) return 'bg-purple-50 text-purple-700';
  return 'bg-grey-50 text-grey-700';
}

function formatDate(dateString) {
  if (!dateString) return 'Unknown date';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
}

function formatFileSize(bytes) {
  if (!bytes) return '0 KB';
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  const mb = kb / 1024;
  return `${mb.toFixed(1)} MB`;
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  // Backend only accepts PDF files
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    uploadError.value = 'Only PDF files are allowed';
    return;
  }

  // Validate file size (150MB max as per backend)
  if (file.size > 150 * 1024 * 1024) {
    uploadError.value = 'File size must be less than 150MB';
    return;
  }

  uploadForm.value.file = file;
  uploadError.value = '';
}

async function handleUpload() {
  if (!uploadForm.value.file) return;

  uploading.value = true;
  uploadError.value = '';

  try {
    const formData = new FormData();
    formData.append('file', uploadForm.value.file);
    formData.append('class_id', uploadForm.value.class_id);

    const response = await api.uploadLesson(formData);
    
    if (response.success) {
      // Backend returns 'upload' object
      const newFile = {
        id: response.upload.id,
        file_name: response.upload.name,
        file_type: response.upload.name.split('.').pop(),
        file_size: response.upload.size,
        uploaded_at: response.upload.created_at,
        class_id: uploadForm.value.class_id,
        class_name: classes.value.find(c => c.id === uploadForm.value.class_id)?.name || 'Unknown'
      };
      
      files.value.unshift(newFile);
      showUploadModal.value = false;
      uploadForm.value = { class_id: null, file: null };
      
      if (response.upload.already_exists) {
        alert('This file already exists in this class');
      }
    }
  } catch (error) {
    uploadError.value = error.message || 'Failed to upload file';
  } finally {
    uploading.value = false;
  }
}

async function downloadFile(file) {
  try {
    // Files are at /uploads/classes/{class_id}/{filename}
    const fileUrl = `http://localhost:8000/uploads/classes/${file.class_id}/${file.file_name}`;
    window.open(fileUrl, '_blank');
  } catch (error) {
    alert('Failed to download file: ' + error.message);
  }
}

async function deleteFile(fileId) {
   if (!confirm('Are you sure you want to delete this file?')) return;
   try {
     await api.deleteLesson(fileId);
     files.value = files.value.filter(f => f.id !== fileId);
   } catch (error) {
     alert('Failed to delete file: ' + error.message);
   }
}

async function loadFiles() {
  try {
    const response = await api.getLessons(selectedClassId.value, {
      limit: 100,
      offset: 0,
      sort: 'created_at_desc',
      refresh: true
    });
    if (response.success) {
      // Backend returns 'uploads' array
      files.value = (response.uploads || []).map(upload => ({
        id: upload.id,
        file_name: upload.name,
        file_type: upload.name.split('.').pop(),
        file_size: upload.size,
        uploaded_at: upload.created_at,
        class_id: selectedClassId.value,
        class_name: classes.value.find(c => c.id === selectedClassId.value)?.name || 'Unknown'
      }));
    }
  } catch (error) {
    console.error('Failed to load files:', error);
  } finally {
    loading.value = false;
  }
}

async function loadClasses() {
  try {
    const response = await api.getClasses();
    if (response.success) {
      classes.value = response.classes || [];
    }
  } catch (error) {
    console.error('Failed to load classes:', error);
  }
}

onMounted(() => {
  loadClasses();
  loadFiles();
  deleteFile();
});
</script>