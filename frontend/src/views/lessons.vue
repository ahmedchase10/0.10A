<template>
  <div class="p-8 space-y-8">
    <!-- ── Page header ─────────────────────────────────────────────── -->
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-grey-900">Lesson Library</h1>
        <p class="text-grey-600 mt-1">Reusable assets and a workspace for the pedagogical agent</p>
      </div>
      <button
        @click="openFilePicker"
        class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-3 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 shadow-sm transition"
      >
        <ArrowUpTrayIcon class="w-5 h-5" />
        Add Asset
      </button>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[1.4fr_1fr] gap-6">
      <!-- ── LEFT: Reusable asset library ──────────────────────────── -->
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

      <!-- ── RIGHT: Pedagogical Agent ──────────────────────────────── -->
      <aside class="flex flex-col gap-0 bg-white rounded-2xl shadow-sm border border-grey-200 overflow-hidden" style="height: 700px;">

        <!-- Header -->
        <div class="flex items-center gap-3 px-5 py-4 border-b border-grey-100 flex-shrink-0">
          <div class="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center flex-shrink-0">
            <AcademicCapIcon class="w-5 h-5 text-indigo-600" />
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-base font-semibold text-grey-900">Pedagogical Agent</h2>
            <p class="text-xs text-grey-500 truncate">Ask anything about your lesson files</p>
          </div>
          <!-- Reasoning toggle -->
          <label class="flex items-center gap-1.5 cursor-pointer flex-shrink-0" title="Enable deep reasoning">
            <span class="text-xs text-grey-500 font-medium">Think</span>
            <div
              class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors"
              :class="agent.reasoning ? 'bg-indigo-500' : 'bg-grey-200'"
              @click="agent.reasoning = !agent.reasoning"
            >
              <span
                class="inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform"
                :class="agent.reasoning ? 'translate-x-4' : 'translate-x-1'"
              />
            </div>
          </label>
        </div>

        <!-- Setup panel (shown when no active session) -->
        <div v-if="!agent.activeSession" class="flex-1 overflow-y-auto p-5 space-y-4">

          <!-- Class selector -->
          <div>
            <label class="block text-xs font-semibold text-grey-700 mb-1.5 uppercase tracking-wide">Class</label>
            <select
              v-model="agent.selectedClassId"
              class="w-full px-3 py-2.5 border border-grey-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
              @change="onClassChange"
            >
              <option :value="null" disabled>Select a class…</option>
              <option v-for="cls in classes" :key="cls.id" :value="cls.id">{{ cls.name }}</option>
            </select>
          </div>

          <!-- Class lesson files (embedded uploads) -->
          <div v-if="agent.selectedClassId">
            <div class="flex items-center justify-between mb-1.5">
              <label class="block text-xs font-semibold text-grey-700 uppercase tracking-wide">Select lesson files</label>
              <span class="text-xs text-grey-500">{{ agent.selectedFileIds.length }} selected</span>
            </div>

            <div v-if="agent.loadingFiles" class="py-6 flex items-center justify-center">
              <div class="animate-spin rounded-full h-6 w-6 border-2 border-indigo-500 border-t-transparent"></div>
            </div>
            <div v-else-if="agent.classFiles.length === 0" class="text-sm text-grey-500 border border-dashed border-grey-200 rounded-xl p-4 text-center">
              No embedded files in this class yet.<br>
              <span class="text-xs">Upload files via the class lessons page first.</span>
            </div>
            <div v-else class="space-y-2 max-h-44 overflow-y-auto pr-1 custom-scrollbar">
              <label
                v-for="f in agent.classFiles"
                :key="f.id"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl border cursor-pointer transition"
                :class="agent.selectedFileIds.includes(f.id)
                  ? 'border-indigo-400 bg-indigo-50 ring-1 ring-indigo-200'
                  : 'border-grey-200 hover:bg-grey-50'"
              >
                <input
                  type="checkbox"
                  :value="f.id"
                  v-model="agent.selectedFileIds"
                  class="h-4 w-4 rounded border-grey-300 text-indigo-600 focus:ring-indigo-500"
                />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-grey-900 truncate">{{ f.name }}</p>
                  <p class="text-xs text-grey-500">{{ formatSize(f.size) }}</p>
                </div>
                <!-- Embedding status -->
                <span v-if="f.embedded" class="flex-shrink-0 text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-medium">Ready</span>
                <span v-else class="flex-shrink-0 text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 font-medium">Embedding…</span>
              </label>
            </div>
          </div>

          <!-- Sessions -->
          <div v-if="agent.selectedClassId">
            <div class="flex items-center justify-between mb-1.5">
              <label class="block text-xs font-semibold text-grey-700 uppercase tracking-wide">Sessions</label>
              <button
                @click="createNewSession"
                :disabled="agent.creatingSession"
                class="text-xs text-indigo-600 font-medium hover:text-indigo-700 disabled:opacity-50"
              >
                {{ agent.creatingSession ? 'Creating…' : '+ New session' }}
              </button>
            </div>

            <div v-if="agent.loadingSessions" class="py-4 flex items-center justify-center">
              <div class="animate-spin rounded-full h-5 w-5 border-2 border-indigo-500 border-t-transparent"></div>
            </div>
            <div v-else-if="agent.sessions.length === 0" class="text-sm text-grey-500 border border-dashed border-grey-200 rounded-xl p-3 text-center">
              No sessions yet. Create one to start chatting.
            </div>
            <div v-else class="space-y-2 max-h-40 overflow-y-auto pr-1 custom-scrollbar">
              <div
                v-for="s in agent.sessions"
                :key="s.thread_id"
                class="flex items-center gap-2 px-3 py-2 rounded-xl border cursor-pointer group transition"
                :class="agent.currentSessionId === s.thread_id
                  ? 'border-primary-400 bg-primary-50 ring-1 ring-primary-200'
                  : 'border-grey-200 hover:bg-grey-50'"
                @click="openSession(s)"
              >
                <ChatBubbleLeftRightIcon class="w-4 h-4 text-grey-400 flex-shrink-0" />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-grey-900 truncate">{{ s.title }}</p>
                  <p class="text-xs text-grey-500">{{ formatDate(s.created_at) }}</p>
                </div>
                <div class="opacity-0 group-hover:opacity-100 flex items-center transition">
                  <button
                    @click.stop="renameSession(s)"
                    class="p-1 rounded-lg hover:bg-grey-100 text-grey-500 transition mr-1"
                    title="Rename session"
                  >
                    <PencilIcon class="w-3.5 h-3.5" />
                  </button>
                  <button
                    @click.stop="deleteSession(s.thread_id)"
                    class="p-1 rounded-lg hover:bg-red-50 text-red-500 transition"
                    title="Delete session"
                  >
                    <TrashIcon class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Start button -->
          <button
            v-if="agent.selectedClassId"
            @click="startChat"
            :disabled="agent.selectedFileIds.length === 0 || agent.sessions.length === 0 || !agent.currentSessionId"
            class="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-600 to-indigo-500 text-white px-4 py-2.5 rounded-xl font-medium hover:from-indigo-700 hover:to-indigo-600 transition disabled:opacity-40 text-sm"
          >
            <AcademicCapIcon class="w-4 h-4" />
            Start Chat
          </button>
          <p v-if="agent.selectedClassId && agent.sessions.length > 0 && !agent.currentSessionId" class="text-xs text-grey-500 text-center -mt-1">
            Click a session to select it, then press Start Chat.
          </p>
        </div>

        <!-- Chat area (active session) -->
        <template v-else>
          <!-- Chat header bar -->
          <div class="flex items-center gap-2 px-4 py-2.5 bg-indigo-50/60 border-b border-indigo-100 flex-shrink-0">
            <button
              @click="exitChat"
              class="p-1 rounded-lg hover:bg-white/70 text-indigo-500 transition"
              title="Back to setup"
            >
              <ChevronLeftIcon class="w-4 h-4" />
            </button>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-indigo-900 truncate">{{ agent.activeSession.title }}</p>
              <p class="text-xs text-indigo-500">{{ agent.selectedFileIds.length }} file{{ agent.selectedFileIds.length !== 1 ? 's' : '' }} attached</p>
            </div>
            <span v-if="agent.isStreaming" class="flex items-center gap-1 text-xs text-indigo-500">
              <span class="inline-block h-2 w-2 rounded-full bg-indigo-400 animate-pulse"></span>
              Thinking…
            </span>
          </div>

          <!-- Messages -->
          <div ref="messagesEl" class="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
            <div v-if="agent.loadingHistory" class="flex items-center justify-center py-12">
              <div class="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent"></div>
            </div>

            <div v-else-if="agent.messages.length === 0" class="text-center py-12">
              <AcademicCapIcon class="w-10 h-10 text-grey-300 mx-auto mb-3" />
              <p class="text-sm text-grey-500">Ask me anything about the selected lesson files.</p>
            </div>

            <template v-else>
              <div v-for="(msg, idx) in agent.messages" :key="idx">
              <!-- User message -->
              <div v-if="msg.role === 'user'" class="flex justify-end">
                <div class="max-w-[80%] bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed">
                  {{ msg.content }}
                </div>
              </div>

              <!-- Assistant message -->
              <div v-else-if="msg.role === 'assistant'" class="flex gap-2.5 items-start">
                <div class="w-7 h-7 rounded-xl bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <AcademicCapIcon class="w-4 h-4 text-indigo-600" />
                </div>
                <div class="flex-1 space-y-2">
                  <!-- Thinking block (collapsible) -->
                  <details v-if="msg.thinking" class="group">
                    <summary class="flex items-center gap-1.5 text-xs text-grey-500 cursor-pointer list-none select-none hover:text-grey-700">
                      <ChevronRightIcon class="w-3.5 h-3.5 transition group-open:rotate-90" />
                      <LightBulbIcon class="w-3.5 h-3.5 text-amber-500" />
                      Reasoning
                    </summary>
                    <pre class="mt-2 text-xs text-grey-500 bg-amber-50/60 border border-amber-100 rounded-xl px-3 py-2.5 whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto font-mono custom-scrollbar">{{ msg.thinking }}</pre>
                  </details>

                  <!-- Tool activity pills -->
                  <div v-if="msg.toolEvents && msg.toolEvents.length" class="flex flex-wrap gap-1.5">
                    <span
                      v-for="(te, ti) in msg.toolEvents"
                      :key="ti"
                      class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full"
                      :class="te.type === 'tool_call' ? 'bg-violet-50 text-violet-700' : 'bg-teal-50 text-teal-700'"
                    >
                      <WrenchScrewdriverIcon class="w-3 h-3" />
                      {{ te.name }}
                    </span>
                  </div>

                  <!-- Answer content -->
                  <div
                    v-if="msg.content"
                    class="bg-grey-50 border border-grey-200 rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed text-grey-800 whitespace-pre-wrap"
                  >{{ msg.content }}</div>

                  <!-- Streaming cursor -->
                  <span v-if="msg.streaming" class="inline-block h-4 w-0.5 bg-indigo-500 animate-pulse ml-0.5 align-text-bottom"></span>
                </div>
              </div>
            </div>
            </template>
          </div>

          <!-- Error banner -->
          <div v-if="agent.streamError" class="flex items-center gap-2 px-4 py-2.5 bg-red-50 border-t border-red-200 flex-shrink-0">
            <ExclamationCircleIcon class="w-4 h-4 text-red-500 flex-shrink-0" />
            <p class="text-xs text-red-700 flex-1 truncate">{{ agent.streamError }}</p>
            <button @click="agent.streamError = null" class="text-red-400 hover:text-red-600">
              <XMarkIcon class="w-4 h-4" />
            </button>
          </div>

          <!-- Input -->
          <div class="px-4 py-3 border-t border-grey-100 flex-shrink-0">
            <div class="flex gap-2 items-end">
              <textarea
                v-model="agent.prompt"
                id="pedagogical-prompt"
                rows="2"
                @keydown.enter.exact.prevent="sendMessage"
                class="flex-1 px-3 py-2.5 border border-grey-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none leading-relaxed"
                placeholder="Ask about the selected lessons… (Enter to send)"
                :disabled="agent.isStreaming"
              ></textarea>
              <button
                @click="sendMessage"
                :disabled="!agent.prompt.trim() || agent.isStreaming"
                class="flex-shrink-0 p-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition disabled:opacity-40"
                title="Send (Enter)"
              >
                <PaperAirplaneIcon class="w-4 h-4" />
              </button>
            </div>
          </div>
        </template>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue';
import {
  ArrowUpTrayIcon,
  ArrowDownTrayIcon,
  DocumentIcon,
  DocumentTextIcon,
  TrashIcon,
  PencilIcon,
  AcademicCapIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  LightBulbIcon,
  WrenchScrewdriverIcon,
  ExclamationCircleIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline';
import { useLessonLibraryStore } from '@/stores/lessonLibraryStore';
import { useClassesStore } from '@/stores/classesstore';
import api from '@/services/api';

// ── Stores ───────────────────────────────────────────────────────────────────

const lessonLibrary = useLessonLibraryStore();
const classesStore = useClassesStore();
const fileInput = ref(null);

const classes = computed(() => classesStore.classes);

// ── Agent state ───────────────────────────────────────────────────────────────

const messagesEl = ref(null);

const agent = reactive({
  // setup
  selectedClassId: null,
  classFiles: [],
  loadingFiles: false,
  selectedFileIds: [],

  // sessions
  sessions: [],
  loadingSessions: false,
  creatingSession: false,
  currentSessionId: null,   // thread_id selected in the session list

  // chat
  activeSession: null,       // full session object once user clicks "Start Chat"
  messages: [],              // [{ role, content, thinking, toolEvents, streaming }]
  prompt: '',
  reasoning: true,
  isStreaming: false,
  streamError: null,
  loadingHistory: false,
});

// ── Library helpers ───────────────────────────────────────────────────────────

function openFilePicker() { fileInput.value?.click(); }

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

// ── Agent: class change ───────────────────────────────────────────────────────

async function onClassChange() {
  agent.classFiles = [];
  agent.selectedFileIds = [];
  agent.sessions = [];
  agent.currentSessionId = null;

  if (!agent.selectedClassId) return;
  await Promise.all([loadClassFiles(), loadSessions()]);
}

async function loadClassFiles() {
  agent.loadingFiles = true;
  try {
    const res = await api.getLessons(agent.selectedClassId, { limit: 100, refresh: true });
    if (res.success) {
      // Backend returns uploads array; filter to embedded only (ready for RAG)
      // but still show all so teacher can see what's pending
      agent.classFiles = res.uploads || [];
    }
  } catch (err) {
    console.error('Failed to load class files:', err);
  } finally {
    agent.loadingFiles = false;
  }
}

// ── Agent: sessions ───────────────────────────────────────────────────────────

async function loadSessions() {
  agent.loadingSessions = true;
  try {
    const res = await api.listAgentSessions(agent.selectedClassId);
    if (res.success) agent.sessions = res.sessions || [];
  } catch (err) {
    console.error('Failed to load sessions:', err);
  } finally {
    agent.loadingSessions = false;
  }
}

async function createNewSession() {
  if (!agent.selectedClassId) return;
  const defaultTitle = `Session ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}`;
  const title = prompt('Enter a name for the new session:', defaultTitle);
  if (!title) return; // User cancelled
  
  agent.creatingSession = true;
  try {
    const res = await api.createAgentSession(agent.selectedClassId, title);
    if (res.success) {
      agent.sessions.unshift(res.session);
      agent.currentSessionId = res.session.thread_id;
    }
  } catch (err) {
    alert('Failed to create session: ' + err.message);
  } finally {
    agent.creatingSession = false;
  }
}

function openSession(session) {
  agent.currentSessionId = session.thread_id;
}

async function renameSession(session) {
  const newTitle = prompt('Enter a new name for the session:', session.title);
  if (!newTitle || newTitle === session.title) return;
  
  try {
    const res = await api.renameAgentSession(session.thread_id, newTitle);
    if (res.success) {
      const idx = agent.sessions.findIndex(s => s.thread_id === session.thread_id);
      if (idx !== -1) {
        agent.sessions[idx].title = res.session.title;
        // Also update active session if it's currently open
        if (agent.activeSession && agent.activeSession.thread_id === session.thread_id) {
          agent.activeSession.title = res.session.title;
        }
      }
    }
  } catch (err) {
    alert('Failed to rename session: ' + err.message);
  }
}

async function deleteSession(threadId) {
  if (!confirm('Delete this session?')) return;
  try {
    await api.deleteAgentSession(threadId);
    agent.sessions = agent.sessions.filter(s => s.thread_id !== threadId);
    if (agent.currentSessionId === threadId) agent.currentSessionId = null;
  } catch (err) {
    alert('Failed to delete session: ' + err.message);
  }
}

// ── Agent: chat ───────────────────────────────────────────────────────────────

function startChat() {
  const session = agent.sessions.find(s => s.thread_id === agent.currentSessionId);
  if (!session) return;
  agent.activeSession = session;
  agent.messages = [];
  agent.streamError = null;
  loadHistory(session.thread_id);
}

async function loadHistory(threadId) {
  agent.loadingHistory = true;
  try {
    const res = await api.getAgentSessionHistory(threadId);
    if (res.success && res.history) {
      agent.messages = res.history;
      await scrollToBottom();
    }
  } catch (err) {
    console.error('Failed to load history:', err);
  } finally {
    agent.loadingHistory = false;
  }
}

function exitChat() {
  if (agent.isStreaming) return; // don't exit mid-stream
  agent.activeSession = null;
  agent.messages = [];
  agent.streamError = null;
}

async function sendMessage() {
  const prompt = agent.prompt.trim();
  if (!prompt || agent.isStreaming) return;

  // Guard: need at least one embedded file
  const embeddedIds = agent.selectedFileIds.filter(id => {
    const f = agent.classFiles.find(f => f.id === id);
    return f && f.embedded;
  });
  if (embeddedIds.length === 0) {
    agent.streamError = 'Please select at least one embedded (Ready) file before asking.';
    return;
  }

  agent.prompt = '';
  agent.streamError = null;

  // Add user message
  agent.messages.push({ role: 'user', content: prompt });

  // Prepare assistant message slot
  const assistantMsg = reactive({
    role: 'assistant',
    content: '',
    thinking: '',
    toolEvents: [],
    streaming: true,
  });
  agent.messages.push(assistantMsg);

  await scrollToBottom();

  agent.isStreaming = true;

  try {
    await api.streamPedagogical(
      {
        thread_id: agent.activeSession.thread_id,
        file_ids: embeddedIds,
        prompt,
        reasoning: agent.reasoning,
      },
      ({ event, data }) => {
        if (event === 'thinking') {
          assistantMsg.thinking += data;
        } else if (event === 'content') {
          assistantMsg.content += data;
          scrollToBottom();
        } else if (event === 'tool_call' || event === 'tool_result') {
          try {
            const payload = JSON.parse(data);
            assistantMsg.toolEvents.push(payload);
          } catch { /* ignore malformed */ }
        }
        // 'done' and 'error' are handled by streamPedagogical itself
      }
    );
  } catch (err) {
    agent.streamError = err.message || 'Stream error';
  } finally {
    assistantMsg.streaming = false;
    agent.isStreaming = false;
    await scrollToBottom();
  }
}

async function scrollToBottom() {
  await nextTick();
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
  }
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

onMounted(async () => {
  await Promise.all([
    lessonLibrary.load(),
    classesStore.load(),
  ]);
});
</script>
