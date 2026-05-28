<template>
  <div class="p-8 space-y-8 bg-grey-50 dark:bg-grey-950 min-h-full transition-colors duration-300">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-grey-900 dark:text-grey-50">Lesson Library</h1>
        <p class="text-grey-600 dark:text-grey-400 mt-1">Upload reusable lesson assets shared across all classes</p>
      </div>
      <div class="flex items-center gap-3">
        <button @click="refreshPage" :disabled="pageRefreshing" class="flex items-center gap-2 px-5 py-3 rounded-lg font-medium border border-grey-300 dark:border-grey-700 text-grey-700 dark:text-grey-200 bg-white dark:bg-grey-900 hover:bg-grey-50 dark:hover:bg-grey-800 transition disabled:opacity-60">
          <ArrowPathIcon class="w-5 h-5" :class="pageRefreshing ? 'animate-spin' : ''" />
          Refresh
        </button>
        <button @click="openFilePicker" class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-3 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 shadow-sm transition">
          <ArrowUpTrayIcon class="w-5 h-5" />
          Add Asset
        </button>
      </div>
    </div>

    <section class="bg-white dark:bg-grey-900 rounded-2xl shadow-sm border border-grey-200 dark:border-grey-800 p-6">
      <div class="flex items-center justify-between gap-4 mb-5">
        <div>
          <h2 class="text-lg font-semibold text-grey-900 dark:text-grey-50">Reusable Assets</h2>
          <p class="text-sm text-grey-600 dark:text-grey-400">Upload files once, then reuse them from class pages.</p>
        </div>
        <div class="text-sm text-grey-600 dark:text-grey-400">{{ globalAssets.length }} asset{{ globalAssets.length !== 1 ? 's' : '' }}</div>
      </div>

      <input ref="fileInput" type="file" class="hidden" accept=".pdf,.doc,.docx,.ppt,.pptx,.txt" multiple @change="handleFilesSelected" />

      <div v-if="globalAssetsLoading" class="flex items-center justify-center py-16">
        <div class="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
      </div>

      <div v-else-if="globalAssets.length === 0" class="text-center py-16 border-2 border-dashed border-grey-200 dark:border-grey-800 rounded-2xl">
        <DocumentIcon class="w-14 h-14 text-grey-300 dark:text-grey-600 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-grey-900 dark:text-grey-50 mb-2">No assets yet</h3>
        <p class="text-grey-600 dark:text-grey-400 mb-6">Drop lesson files here to build a reusable library.</p>
        <button @click="openFilePicker" class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition">
          <ArrowUpTrayIcon class="w-4 h-4" />
          Upload First Asset
        </button>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <article v-for="asset in globalAssets" :key="asset.id" class="rounded-xl border border-grey-200 dark:border-grey-800 overflow-hidden hover:shadow-md transition bg-grey-50/40 dark:bg-grey-950/40">
          <div class="h-28 flex items-center justify-center bg-gradient-to-br from-slate-700 via-slate-600 to-slate-800">
            <DocumentTextIcon class="w-12 h-12 text-white/90" />
          </div>
          <div class="p-4 space-y-3">
            <div>
              <h3 class="font-semibold text-grey-900 dark:text-grey-100 truncate" :title="asset.name">{{ asset.name }}</h3>
              <p class="text-xs text-grey-500 dark:text-grey-400 mt-1">{{ formatSize(asset.size) }} · {{ formatDate(asset.created_at) }}</p>
            </div>
            <button @click="deleteAsset(asset.id)" class="w-full px-3 py-2 bg-red-50 dark:bg-red-950 text-red-600 rounded-lg hover:bg-red-100 dark:hover:bg-red-900 transition flex items-center justify-center gap-2 text-sm font-medium">
              <TrashIcon class="w-4 h-4" />
              Delete
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ArrowUpTrayIcon, ArrowPathIcon, DocumentIcon, DocumentTextIcon, TrashIcon } from '@heroicons/vue/24/outline';
import api from '@/services/api';

const fileInput = ref(null);
const globalAssets = ref([]);
const globalAssetsLoading = ref(false);
const pageRefreshing = ref(false);

function openFilePicker() { fileInput.value?.click(); }

async function loadGlobalAssets() {
  globalAssetsLoading.value = true;
  try {
    const res = await api.getLessons(null, { limit: 100, refresh: true });
    if (res.success) globalAssets.value = res.uploads || [];
  } finally {
    globalAssetsLoading.value = false;
  }
}

async function handleFilesSelected(event) {
  const files = event.target.files;
  if (!files || files.length === 0) return;
  globalAssetsLoading.value = true;
  try {
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      await api.uploadLesson(formData);
    }
  } catch (err) {
    alert('Failed to upload some files: ' + err.message);
  } finally {
    await loadGlobalAssets();
    globalAssetsLoading.value = false;
  }
  event.target.value = '';
}

async function refreshPage() {
  if (pageRefreshing.value) return;
  pageRefreshing.value = true;
  try {
    await loadGlobalAssets();
  } finally {
    pageRefreshing.value = false;
  }
}

function formatDate(dt) {
  if (!dt) return '-';
  return new Date(dt).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatSize(bytes) {
  if (!bytes) return '0 KB';
  const kb = bytes / 1024;
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`;
}

async function deleteAsset(assetId) {
  if (!confirm('Delete this reusable asset?')) return;
  try {
    await api.deleteLesson(assetId);
    await loadGlobalAssets();
  } catch (err) {
    alert('Failed to delete asset: ' + err.message);
  }
}

onMounted(loadGlobalAssets);
</script>
