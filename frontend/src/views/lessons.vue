<template>
  <div class="p-8 space-y-8">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-grey-900">Lesson Library</h1>
        <p class="text-grey-600 mt-1">Reusable assets and a workspace for the creator agent</p>
      </div>
      <button
        @click="openFilePicker"
        class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-3 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 shadow-sm transition"
      >
        <ArrowUpTrayIcon class="w-5 h-5" />
        Add Asset
      </button>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[1.4fr_0.9fr] gap-6">
      <section class="bg-white rounded-2xl shadow-sm border border-grey-200 p-6">
        <div class="flex items-center justify-between gap-4 mb-5">
          <div>
            <h2 class="text-lg font-semibold text-grey-900">Reusable Assets</h2>
            <p class="text-sm text-grey-600">Upload files once, then reuse them from class pages.</p>
          </div>
          <div class="text-sm text-grey-600">
            {{ lessonLibrary.assets.length }} asset{{ lessonLibrary.assets.length !== 1 ? 's' : '' }}
          </div>
        </div>

        <input
          ref="fileInput"
          type="file"
          class="hidden"
          accept=".pdf,.doc,.docx,.ppt,.pptx,.txt"
          multiple
          @change="handleFilesSelected"
        />

        <div v-if="lessonLibrary.loading" class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
        </div>

        <div v-else-if="lessonLibrary.assets.length === 0" class="text-center py-16 border-2 border-dashed border-grey-200 rounded-2xl">
          <DocumentIcon class="w-14 h-14 text-grey-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-grey-900 mb-2">No assets yet</h3>
          <p class="text-grey-600 mb-6">Drop lesson files here to build a reusable library.</p>
          <button
            @click="openFilePicker"
            class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition"
          >
            <ArrowUpTrayIcon class="w-4 h-4" />
            Upload First Asset
          </button>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <article
            v-for="asset in lessonLibrary.assets"
            :key="asset.id"
            class="rounded-xl border border-grey-200 overflow-hidden hover:shadow-md transition bg-grey-50/40"
          >
            <div class="h-28 flex items-center justify-center bg-gradient-to-br from-slate-700 via-slate-600 to-slate-800">
              <DocumentTextIcon class="w-12 h-12 text-white/90" />
            </div>
            <div class="p-4 space-y-3">
              <div>
                <h3 class="font-semibold text-grey-900 truncate" :title="asset.name">{{ asset.name }}</h3>
                <p class="text-xs text-grey-500 mt-1">{{ formatSize(asset.size) }} - {{ formatDate(asset.createdAt) }}</p>
              </div>
              <div class="flex gap-2">
                <button
                  @click="downloadAsset(asset)"
                  class="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-white border border-grey-200 text-grey-700 rounded-lg hover:bg-grey-50 transition text-sm font-medium"
                >
                  <ArrowDownTrayIcon class="w-4 h-4" />
                  Download
                </button>
                <button
                  @click="deleteAsset(asset.id)"
                  class="px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition"
                >
                  <TrashIcon class="w-4 h-4" />
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <aside class="space-y-6">
        <section class="bg-white rounded-2xl shadow-sm border border-grey-200 p-6">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-11 h-11 rounded-xl bg-primary-50 flex items-center justify-center">
              <SparklesIcon class="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <h2 class="text-lg font-semibold text-grey-900">Creator Agent Studio</h2>
              <p class="text-sm text-grey-600">Reserve this area for agent prompts, outputs, and drafts.</p>
            </div>
          </div>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-grey-700 mb-2">Prompt</label>
              <textarea
                v-model="agentForm.prompt"
                rows="5"
                class="w-full px-4 py-3 border border-grey-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Describe the lesson file you want the creator agent to produce..."
              ></textarea>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-grey-700 mb-2">Subject</label>
                <input
                  v-model="agentForm.subject"
                  type="text"
                  class="w-full px-4 py-2.5 border border-grey-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Mathematics"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-grey-700 mb-2">Format</label>
                <select
                  v-model="agentForm.output"
                  class="w-full px-4 py-2.5 border border-grey-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
                >
                  <option value="lesson-plan">Lesson plan</option>
                  <option value="worksheet">Worksheet</option>
                  <option value="revision-sheet">Revision sheet</option>
                  <option value="exam-prep">Exam prep</option>
                </select>
              </div>
            </div>

            <button
              @click="queueAgentRequest"
              :disabled="!agentForm.prompt.trim()"
              class="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-slate-900 to-slate-700 text-white px-4 py-3 rounded-xl font-medium hover:from-slate-800 hover:to-slate-600 transition disabled:opacity-50"
            >
              Queue Request
            </button>

            <p class="text-xs text-grey-500">
              This panel is ready to connect to the creator_agent endpoint when we wire it up.
            </p>
          </div>
        </section>

        <section class="bg-white rounded-2xl shadow-sm border border-grey-200 p-6">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h2 class="text-lg font-semibold text-grey-900">Queued Drafts</h2>
              <p class="text-sm text-grey-600">Prompts waiting for agent generation.</p>
            </div>
            <span class="text-sm text-grey-600">{{ agentQueue.length }}</span>
          </div>

          <div v-if="agentQueue.length === 0" class="text-sm text-grey-500 rounded-xl border border-dashed border-grey-200 p-4">
            No draft requests yet.
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="item in agentQueue"
              :key="item.id"
              class="rounded-xl border border-grey-200 p-4"
            >
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="font-medium text-grey-900">{{ item.subject || 'Untitled subject' }}</p>
                  <p class="text-xs text-grey-500">{{ item.output }} - {{ formatDate(item.createdAt) }}</p>
                </div>
                <span class="text-xs font-medium px-2 py-1 rounded-full bg-amber-50 text-amber-700">Waiting</span>
              </div>
              <p class="text-sm text-grey-600 mt-3">{{ item.prompt }}</p>
            </div>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import {
  ArrowUpTrayIcon,
  ArrowDownTrayIcon,
  DocumentIcon,
  DocumentTextIcon,
  TrashIcon,
  SparklesIcon,
} from '@heroicons/vue/24/outline';
import { useLessonLibraryStore } from '@/stores/lessonLibraryStore';

const lessonLibrary = useLessonLibraryStore();
const fileInput = ref(null);
const agentQueue = ref([]);
const agentForm = ref({
  prompt: '',
  subject: '',
  output: 'lesson-plan',
});

function openFilePicker() {
  fileInput.value?.click();
}

async function handleFilesSelected(event) {
  const files = event.target.files;
  if (!files || files.length === 0) return;
  await lessonLibrary.addFiles(files);
  event.target.value = '';
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

function downloadAsset(asset) {
  const url = URL.createObjectURL(asset.blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = asset.name;
  link.click();
  URL.revokeObjectURL(url);
}

async function deleteAsset(assetId) {
  if (!confirm('Delete this reusable asset?')) return;
  await lessonLibrary.remove(assetId);
}

function queueAgentRequest() {
  const prompt = agentForm.value.prompt.trim();
  if (!prompt) return;

  agentQueue.value.unshift({
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    prompt,
    subject: agentForm.value.subject.trim(),
    output: agentForm.value.output,
    createdAt: new Date().toISOString(),
  });

  agentForm.value.prompt = '';
}

onMounted(() => {
  lessonLibrary.load();
});
</script>
