<template>
  <div class="h-full overflow-y-auto custom-scrollbar bg-grey-50">
    <div class="bg-white border-b border-grey-200 px-8 py-6">
      <div class="flex items-center gap-2 text-sm text-grey-500 mb-4">
        <router-link :to="`/class/${classId}`" class="hover:text-primary-600 transition flex items-center gap-1">
          <ChevronLeftIcon class="w-4 h-4" />
          Back to Class
        </router-link>
        <span>/</span>
        <span class="text-grey-900 font-medium">Lessons</span>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold text-grey-900 mb-1">Class Lessons</h1>
          <p class="text-grey-600">{{ attachedFiles.length }} attached file{{ attachedFiles.length !== 1 ? 's' : '' }}</p>
        </div>
        <button
          @click="attachSelectedAssets"
          :disabled="selectedAssetIds.length === 0 || attaching"
          class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-2.5 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 shadow-sm transition disabled:opacity-50"
        >
          <ArrowUpTrayIcon class="w-5 h-5" />
          {{ attaching ? 'Attaching...' : `Attach Selected (${selectedAssetIds.length})` }}
        </button>
      </div>
    </div>

    <div class="p-8 space-y-8">
      <section class="bg-white rounded-2xl border border-grey-200 shadow-sm p-6">
        <div class="flex items-center justify-between mb-5">
          <div>
            <h2 class="text-lg font-semibold text-grey-900">Attached Files</h2>
            <p class="text-sm text-grey-600">These are the files currently available in this class.</p>
          </div>
          <button
            @click="loadAttachedFiles"
            class="text-sm font-medium text-primary-600 hover:text-primary-700"
          >
            Refresh
          </button>
        </div>

        <div v-if="loadingAttached" class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
        </div>

        <div v-else-if="attachedFiles.length === 0" class="text-center py-12 border-2 border-dashed border-grey-200 rounded-2xl">
          <DocumentIcon class="w-14 h-14 text-grey-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-grey-900 mb-2">No attached files yet</h3>
          <p class="text-grey-600">Choose files from the reusable library below and attach them to this class.</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <article
            v-for="file in attachedFiles"
            :key="file.id"
            class="rounded-xl border border-grey-200 overflow-hidden bg-grey-50/40"
          >
            <div class="h-24 flex items-center justify-center bg-gradient-to-br from-slate-700 via-slate-600 to-slate-800">
              <DocumentTextIcon class="w-10 h-10 text-white/90" />
            </div>
            <div class="p-4">
              <h3 class="font-semibold text-grey-900 truncate" :title="file.name">{{ file.name }}</h3>
              <p class="text-xs text-grey-500 mt-1">{{ formatSize(file.size) }} - {{ formatDate(file.created_at) }}</p>
              <div class="mt-4 flex gap-2">
                <button
                  @click="downloadAttachedFile(file)"
                  class="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-white border border-grey-200 text-grey-700 rounded-lg hover:bg-grey-50 transition text-sm font-medium"
                >
                  <ArrowDownTrayIcon class="w-4 h-4" />
                  Download
                </button>
                <button
                  @click="deleteAttachedFile(file)"
                  class="px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition"
                >
                  <TrashIcon class="w-4 h-4" />
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="bg-white rounded-2xl border border-grey-200 shadow-sm p-6">
        <div class="flex items-center justify-between mb-5">
          <div>
            <h2 class="text-lg font-semibold text-grey-900">Lesson Library</h2>
            <p class="text-sm text-grey-600">Select reusable assets to attach to this class.</p>
          </div>
          <span class="text-sm text-grey-600">{{ lessonLibrary.assets.length }} asset{{ lessonLibrary.assets.length !== 1 ? 's' : '' }}</span>
        </div>

        <div v-if="lessonLibrary.loading" class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
        </div>

        <div v-else-if="lessonLibrary.assets.length === 0" class="text-center py-12 border-2 border-dashed border-grey-200 rounded-2xl">
          <DocumentIcon class="w-14 h-14 text-grey-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-grey-900 mb-2">No reusable assets yet</h3>
          <p class="text-grey-600">Add assets from the main Lessons library first.</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <article
            v-for="asset in lessonLibrary.assets"
            :key="asset.id"
            class="rounded-xl border transition overflow-hidden"
            :class="selectedAssetIds.includes(asset.id) ? 'border-primary-500 ring-1 ring-primary-200' : 'border-grey-200'"
          >
            <label class="cursor-pointer block">
              <div class="h-24 flex items-center justify-center bg-gradient-to-br from-slate-700 via-slate-600 to-slate-800 relative">
                <input
                  type="checkbox"
                  class="absolute top-3 left-3 h-4 w-4 rounded border-grey-300 text-primary-600 focus:ring-primary-500"
                  :value="asset.id"
                  v-model="selectedAssetIds"
                />
                <DocumentTextIcon class="w-10 h-10 text-white/90" />
              </div>
              <div class="p-4 bg-white">
                <h3 class="font-semibold text-grey-900 truncate" :title="asset.name">{{ asset.name }}</h3>
                <p class="text-xs text-grey-500 mt-1">{{ formatSize(asset.size) }} - {{ formatDate(asset.createdAt) }}</p>
              </div>
            </label>
          </article>
        </div>
      </section>
    </div>
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
  TrashIcon,
} from '@heroicons/vue/24/outline';
import { useLessonLibraryStore } from '@/stores/lessonLibraryStore';
import api from '@/services/api';

const route = useRoute();
const classId = computed(() => parseInt(route.params.id));
const lessonLibrary = useLessonLibraryStore();

const attachedFiles = ref([]);
const loadingAttached = ref(true);
const attaching = ref(false);
const selectedAssetIds = ref([]);

function formatDate(dt) {
  if (!dt) return '-';
  return new Date(dt).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatSize(bytes) {
  if (!bytes) return '0 KB';
  const kb = bytes / 1024;
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`;
}

async function loadAttachedFiles() {
  loadingAttached.value = true;
  try {
    const res = await api.getLessons(classId.value, { limit: 100, refresh: true });
    if (res.success) {
      attachedFiles.value = res.uploads || [];
    }
  } catch (err) {
    console.error('Failed to load class lessons:', err);
  } finally {
    loadingAttached.value = false;
  }
}

function downloadAttachedFile(file) {
  const url = `http://localhost:8000/uploads/classes/${classId.value}/${file.name}`;
  window.open(url, '_blank');
}

async function deleteAttachedFile(file) {
  if (!confirm(`Delete "${file.name}" from this class?`)) return;
  try {
    const lessonId = file.upload_id ?? file.id ?? file.uploadId ?? null;
    if (!lessonId) {
      throw new Error('Missing lesson id');
    }
    await api.deleteLesson(lessonId);
    await loadAttachedFiles();
  } catch (err) {
    alert('Failed to delete: ' + err.message);
  }
}

async function attachSelectedAssets() {
  if (selectedAssetIds.value.length === 0) return;
  attaching.value = true;
  try {
    for (const assetId of selectedAssetIds.value) {
      const asset = await lessonLibrary.getById(assetId);
      if (!asset) continue;

      const file = new File([asset.blob], asset.name, {
        type: asset.type || 'application/octet-stream',
      });
      const formData = new FormData();
      formData.append('file', file);
      formData.append('class_id', classId.value);
      await api.uploadLesson(formData);
    }

    selectedAssetIds.value = [];
    await loadAttachedFiles();
  } catch (err) {
    alert('Failed to attach selected assets: ' + err.message);
  } finally {
    attaching.value = false;
  }
}

onMounted(async () => {
  await lessonLibrary.load();
  await loadAttachedFiles();
});
</script>
