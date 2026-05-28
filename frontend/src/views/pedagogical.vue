<template>
  <div class="flex h-full bg-grey-50 dark:bg-grey-950 transition-colors duration-300">

    <!-- ── LEFT PANEL: Setup / Sessions ─────────────────────────────────── -->
    <aside class="w-80 flex-shrink-0 bg-white dark:bg-grey-900 border-r border-grey-200 dark:border-grey-800 flex flex-col overflow-hidden">

      <!-- Panel header -->
      <div class="flex items-center gap-3 px-5 py-4 border-b border-grey-200 dark:border-grey-800 flex-shrink-0">
        <div class="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center flex-shrink-0 shadow-sm">
          <AcademicCapIcon class="w-5 h-5 text-white" />
        </div>
        <div class="flex-1 min-w-0">
          <h1 class="text-sm font-bold text-grey-900 dark:text-grey-50">Pedagogical Agent</h1>
          <p class="text-xs text-grey-500 dark:text-grey-400">AI tutor for your lesson files</p>
        </div>
        <!-- Reasoning toggle -->
        <label class="flex items-center gap-1.5 cursor-pointer flex-shrink-0" title="Enable deep reasoning">
          <span class="text-xs text-grey-500 font-medium">Think</span>
          <div
            class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors"
            :class="agent.reasoning ? 'bg-sky-500' : 'bg-grey-200 dark:bg-grey-700'"
            @click="agent.reasoning = !agent.reasoning"
          >
            <span
              class="inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform"
              :class="agent.reasoning ? 'translate-x-4' : 'translate-x-1'"
            />
          </div>
        </label>
      </div>

      <!-- Scrollable config area -->
      <div class="flex-1 overflow-y-auto p-4 space-y-5 custom-scrollbar">

        <!-- Class selection list -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="block text-xs font-semibold text-grey-500 uppercase tracking-wider">Classes</label>
            <button
              v-if="agent.selectedClassId"
              @click="selectClass(null)"
              class="text-xs text-indigo-600 font-semibold hover:text-indigo-700 transition"
              title="Deselect active class"
            >
              Leave Class
            </button>
          </div>
          <div v-if="classes.length === 0" class="text-sm text-grey-400 dark:text-grey-500 p-3 text-center border border-dashed border-grey-200 dark:border-grey-800 rounded-xl">
            No classes available.
          </div>
          <div v-else class="space-y-2 max-h-64 overflow-y-auto pr-1 custom-scrollbar">
            <button
              v-for="cls in classes"
              :key="cls.id"
              @click="selectClass(cls.id)"
              class="w-full text-left px-3 py-2 rounded-xl border transition-all duration-200 flex items-center gap-3 relative overflow-hidden group"
                :class="agent.selectedClassId === cls.id
                ? 'border-sky-400 bg-sky-50/30 dark:bg-sky-950/20 ring-1 ring-sky-200/50 shadow-xs'
                : 'border-grey-200 bg-white dark:bg-grey-900 hover:bg-grey-50 dark:hover:bg-grey-800 hover:border-grey-300 dark:border-grey-800'"
            >
              <!-- Color strip on selected class or hover -->
              <div
                class="w-1 h-full absolute left-0 top-0 transition-opacity duration-200"
                :style="{ backgroundColor: cls.color || '#3b82f6' }"
                :class="agent.selectedClassId === cls.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-60'"
              ></div>
              
              <!-- Colored circle with first letter -->
              <div
                class="w-7 h-7 rounded-lg flex items-center justify-center text-white font-semibold text-xs flex-shrink-0 transition-transform group-hover:scale-105 ml-1"
                :style="{ background: `linear-gradient(135deg, ${cls.color || '#3b82f6'} 0%, ${adjustColor(cls.color || '#3b82f6', -15)} 100%)` }"
              >
                {{ cls.name.charAt(0).toUpperCase() }}
              </div>
              
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-grey-900 dark:text-grey-50 truncate">{{ cls.name }}</p>
                <p class="text-xs text-grey-500 dark:text-grey-400 truncate" v-if="cls.subject">{{ cls.subject }}</p>
                <p class="text-xs text-grey-400 dark:text-grey-500 truncate" v-else>No subject</p>
              </div>

              <!-- Selected indicator dot -->
              <div
                v-if="agent.selectedClassId === cls.id"
                class="w-2 h-2 rounded-full flex-shrink-0 mr-1 animate-pulse"
                :style="{ backgroundColor: cls.color || '#3b82f6' }"
              ></div>
            </button>
          </div>
        </div>

        <template v-if="agent.selectedClassId">
          <!-- Lesson files -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="block text-xs font-semibold text-grey-500 uppercase tracking-wider">Lesson Files</label>
              <span class="text-xs text-indigo-600 font-medium">{{ agent.selectedFileIds.length }} selected</span>
            </div>

            <div v-if="agent.loadingFiles" class="py-6 flex items-center justify-center">
              <div class="animate-spin rounded-full h-6 w-6 border-2 border-indigo-500 border-t-transparent"></div>
            </div>
            <div
              v-else-if="agent.classFiles.length === 0"
                class="text-sm text-grey-500 dark:text-grey-400 border border-dashed border-grey-200 dark:border-grey-800 rounded-xl p-4 text-center leading-relaxed"
            >
              No embedded files yet.<br>
              <span class="text-xs">Upload files via the class lessons page first.</span>
            </div>
            <div v-else class="space-y-2 max-h-52 overflow-y-auto pr-1 custom-scrollbar">
              <label
                v-for="f in agent.classFiles"
                :key="f.id"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl border cursor-pointer transition"
                :class="agent.selectedFileIds.includes(f.id)
                  ? 'border-sky-400 bg-sky-50 dark:bg-sky-950/20 ring-1 ring-sky-200'
                  : 'border-grey-200 hover:bg-grey-50 dark:border-grey-800 dark:hover:bg-grey-800'"
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
                <span
                  v-if="f.embedded"
                  class="flex-shrink-0 text-xs px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-medium"
                >Ready</span>
                <span
                  v-else
                  class="flex-shrink-0 text-xs px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 font-medium"
                >Pending</span>
              </label>
            </div>
          </div>

          <!-- Sessions -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="block text-xs font-semibold text-grey-500 uppercase tracking-wider">Sessions</label>
              <button
                @click="createNewSession"
                :disabled="agent.creatingSession"
                class="text-xs text-indigo-600 font-semibold hover:text-indigo-700 disabled:opacity-50 transition"
              >
                {{ agent.creatingSession ? 'Creating…' : '+ New' }}
              </button>
            </div>

            <div v-if="agent.loadingSessions" class="py-4 flex items-center justify-center">
              <div class="animate-spin rounded-full h-5 w-5 border-2 border-indigo-500 border-t-transparent"></div>
            </div>
            <div
              v-else-if="agent.sessions.length === 0"
              class="text-sm text-grey-500 border border-dashed border-grey-200 rounded-xl p-3 text-center"
            >
              No sessions yet. Create one to start.
            </div>
            <div v-else class="space-y-1.5 max-h-52 overflow-y-auto pr-1 custom-scrollbar">
              <div
                v-for="s in agent.sessions"
                :key="s.thread_id"
                class="flex items-center gap-2 px-3 py-2.5 rounded-xl border cursor-pointer group transition"
                :class="agent.currentSessionId === s.thread_id
                  ? 'border-sky-400 bg-sky-50 dark:bg-sky-950/20 ring-1 ring-sky-200'
                  : 'border-grey-200 hover:bg-grey-50 dark:border-grey-800 dark:hover:bg-grey-800'"
                @click="openSession(s)"
              >
                <ChatBubbleLeftRightIcon class="w-4 h-4 text-grey-400 flex-shrink-0" />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-grey-900 truncate">{{ s.title }}</p>
                  <p class="text-xs text-grey-400">{{ formatDate(s.created_at) }}</p>
                </div>
                <div class="opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition">
                  <button
                    @click.stop="renameSession(s)"
                    class="p-1 rounded-lg hover:bg-grey-100 text-grey-400 hover:text-grey-600 transition"
                    title="Rename"
                  >
                    <PencilIcon class="w-3.5 h-3.5" />
                  </button>
                  <button
                    @click.stop="deleteSession(s.thread_id)"
                    class="p-1 rounded-lg hover:bg-red-50 text-grey-400 hover:text-red-500 transition"
                    title="Delete"
                  >
                    <TrashIcon class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Start chat button -->
          <button
            @click="startChat"
            :disabled="!agent.currentSessionId"
            class="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-600 to-indigo-500 text-white px-4 py-2.5 rounded-xl font-semibold hover:from-indigo-700 hover:to-indigo-600 transition disabled:opacity-40 text-sm shadow-sm"
          >
            <AcademicCapIcon class="w-4 h-4" />
            Start Chat
          </button>
          <p
            v-if="agent.sessions.length > 0 && !agent.currentSessionId"
            class="text-xs text-grey-400 text-center -mt-2"
          >
            Select a session above, then press Start Chat.
          </p>
        </template>

        <!-- Empty state when no class selected -->
        <div v-if="!agent.selectedClassId" class="text-center py-8">
          <AcademicCapIcon class="w-12 h-12 text-grey-200 mx-auto mb-3" />
          <p class="text-sm text-grey-400">Select a class to get started</p>
        </div>
      </div>
    </aside>

    <!-- ── RIGHT PANEL: Chat ──────────────────────────────────────────────── -->
    <main class="flex-1 flex flex-col overflow-hidden">

      <!-- Empty / Welcome state -->
      <div v-if="!agent.activeSession" class="flex-1 flex flex-col items-center justify-center gap-4 p-8">
        <div class="w-20 h-20 rounded-3xl bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center shadow-lg">
          <AcademicCapIcon class="w-10 h-10 text-white" />
        </div>
        <div class="text-center max-w-sm">
          <h2 class="text-2xl font-bold text-grey-900 mb-2">Pedagogical Agent</h2>
          <p class="text-grey-500 text-sm leading-relaxed">
            Select a class, pick or create a session, then click <strong>Start Chat</strong> to begin an AI-powered tutoring session. Lesson files are optional.
          </p>
        </div>
        <div class="flex flex-wrap gap-3 justify-center mt-2">
          <div class="flex items-center gap-2 px-4 py-2 bg-white rounded-xl border border-grey-200 shadow-xs text-sm text-grey-600">
            <BookOpenIcon class="w-4 h-4 text-indigo-500" />
            RAG over lesson files
          </div>
          <div class="flex items-center gap-2 px-4 py-2 bg-white rounded-xl border border-grey-200 shadow-xs text-sm text-grey-600">
            <LightBulbIcon class="w-4 h-4 text-amber-500" />
            Deep reasoning mode
          </div>
          <div class="flex items-center gap-2 px-4 py-2 bg-white rounded-xl border border-grey-200 shadow-xs text-sm text-grey-600">
            <ChatBubbleLeftRightIcon class="w-4 h-4 text-emerald-500" />
            Persistent sessions
          </div>
        </div>
      </div>

      <!-- Active chat -->
      <template v-else>
        <!-- Chat top bar -->
        <div class="flex items-center gap-3 px-6 py-3 bg-white border-b border-grey-200 flex-shrink-0">
          <button
            @click="exitChat"
            class="p-1.5 rounded-lg hover:bg-grey-100 text-grey-500 transition"
            title="Back to setup"
          >
            <ChevronLeftIcon class="w-4 h-4" />
          </button>
          <div class="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0">
            <AcademicCapIcon class="w-4 h-4 text-indigo-600" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-grey-900 truncate">{{ agent.activeSession.title }}</p>
            <p class="text-xs text-grey-500">
              <span v-if="agent.selectedFileIds.length > 0">
                {{ agent.selectedFileIds.length }} file{{ agent.selectedFileIds.length !== 1 ? 's' : '' }} attached
              </span>
              <span v-else>No lesson files attached</span>
            </p>
          </div>
          <div v-if="agent.isStreaming" class="flex items-center gap-1.5 text-xs text-indigo-600 font-medium">
            <span class="inline-block h-2 w-2 rounded-full bg-indigo-500 animate-pulse"></span>
            Thinking…
          </div>
        </div>

        <!-- Messages scroll area -->
        <div ref="messagesEl" class="flex-1 overflow-y-auto px-6 py-5 space-y-5 custom-scrollbar">
          <!-- History loading -->
          <div v-if="agent.loadingHistory" class="flex items-center justify-center py-16">
            <div class="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent"></div>
          </div>

          <!-- Empty chat -->
          <div v-else-if="agent.messages.length === 0" class="flex flex-col items-center justify-center py-20 text-center gap-3">
            <AcademicCapIcon class="w-12 h-12 text-grey-200" />
            <p class="text-sm text-grey-400 max-w-xs">
              Ask me anything about the selected lesson files. I can explain concepts, answer questions, and reason through problems with you.
            </p>
          </div>

          <!-- Message list -->
          <template v-else>
            <div v-for="(msg, idx) in agent.messages" :key="idx">

              <!-- User bubble -->
              <div v-if="msg.role === 'user'" class="flex justify-end">
                <div class="max-w-[72%] bg-sky-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed shadow-sm">
                  {{ msg.content }}
                </div>
              </div>

              <!-- Assistant bubble -->
              <div v-else-if="msg.role === 'assistant'" class="flex gap-3 items-start">
                <div class="w-8 h-8 rounded-xl bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
                  <AcademicCapIcon class="w-4 h-4 text-indigo-600" />
                </div>
                <div class="flex-1 min-w-0 space-y-2">

                  <!-- Thinking block (collapsible) -->
                  <details v-if="msg.thinking" class="group">
                    <summary class="flex items-center gap-1.5 text-xs text-grey-400 cursor-pointer list-none select-none hover:text-grey-600 transition">
                      <ChevronRightIcon class="w-3.5 h-3.5 transition-transform group-open:rotate-90" />
                      <LightBulbIcon class="w-3.5 h-3.5 text-amber-500" />
                      Reasoning
                      <span class="text-grey-300">·</span>
                      <span class="text-grey-400">click to expand</span>
                    </summary>
                    <pre class="mt-2 text-xs text-grey-500 dark:text-grey-400 bg-amber-50/70 dark:bg-amber-950/30 border border-amber-100 dark:border-amber-900 rounded-xl px-3 py-2.5 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto font-mono custom-scrollbar">{{ normalizeAgentText(msg.thinking) }}</pre>
                  </details>

                  <!-- Tool activity pills -->
                  <div v-if="msg.toolEvents && msg.toolEvents.length" class="flex flex-wrap gap-1.5">
                    <span
                      v-for="(te, ti) in msg.toolEvents"
                      :key="ti"
                      class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium"
                      :class="te.type === 'tool_call' ? 'bg-violet-50 text-violet-700' : 'bg-teal-50 text-teal-700'"
                    >
                      <WrenchScrewdriverIcon class="w-3 h-3" />
                      {{ te.name }}
                    </span>
                  </div>

                  <!-- Answer -->
                  <div
                    v-if="msg.content"
                    class="bg-white dark:bg-grey-900 border border-grey-200 dark:border-grey-800 rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed text-grey-800 dark:text-grey-200 whitespace-pre-wrap shadow-sm"
                  >{{ normalizeAgentText(msg.content) }}</div>

                  <!-- Streaming cursor -->
                  <span
                    v-if="msg.streaming"
                    class="inline-block h-4 w-0.5 bg-indigo-500 animate-pulse ml-0.5 align-text-bottom"
                  ></span>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- Error banner -->
        <div
          v-if="agent.streamError"
          class="flex items-center gap-2 px-5 py-2.5 bg-red-50 border-t border-red-200 flex-shrink-0"
        >
          <ExclamationCircleIcon class="w-4 h-4 text-red-500 flex-shrink-0" />
          <p class="text-xs text-red-700 flex-1 truncate">{{ agent.streamError }}</p>
          <button @click="agent.streamError = null" class="text-red-400 hover:text-red-600 transition">
            <XMarkIcon class="w-4 h-4" />
          </button>
        </div>

        <!-- Input bar -->
        <div class="px-5 py-4 border-t border-grey-200 bg-white flex-shrink-0">
          <div class="flex gap-3 items-end">
            <textarea
              v-model="agent.prompt"
              id="pedagogical-prompt"
              rows="2"
              @keydown.enter.exact.prevent="sendMessage"
              class="flex-1 px-4 py-3 border border-grey-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none leading-relaxed bg-grey-50 focus:bg-white transition"
              placeholder="Ask about the selected lessons… (Enter to send, Shift+Enter for new line)"
              :disabled="agent.isStreaming"
            ></textarea>
            <button
              @click="sendMessage"
              :disabled="!agent.prompt.trim() || agent.isStreaming"
              class="flex-shrink-0 p-3 bg-sky-600 text-white rounded-xl hover:bg-sky-700 transition disabled:opacity-40 shadow-sm"
              title="Send (Enter)"
            >
              <PaperAirplaneIcon class="w-4 h-4" />
            </button>
          </div>
          <p class="text-xs text-grey-400 mt-1.5 pl-1">
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </template>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue';
import {
  AcademicCapIcon,
  ChatBubbleLeftRightIcon,
  PencilIcon,
  TrashIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PaperAirplaneIcon,
  LightBulbIcon,
  WrenchScrewdriverIcon,
  ExclamationCircleIcon,
  XMarkIcon,
  BookOpenIcon,
} from '@heroicons/vue/24/outline';
import { useClassesStore } from '@/stores/classesstore';
import api from '@/services/api';

// ── Stores ────────────────────────────────────────────────────────────────────

const classesStore = useClassesStore();
const classes = computed(() => classesStore.classes);

// ── Refs ──────────────────────────────────────────────────────────────────────

const messagesEl = ref(null);

// ── Agent state ───────────────────────────────────────────────────────────────

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
  currentSessionId: null,

  // chat
  activeSession: null,
  messages: [],
  prompt: '',
  reasoning: true,
  isStreaming: false,
  streamError: null,
  loadingHistory: false,
});

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(dt) {
  if (!dt) return '-';
  return new Date(dt).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

function formatSize(bytes) {
  if (!bytes) return '0 KB';
  const kb = bytes / 1024;
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`;
}

function normalizeAgentText(text) {
  if (!text) return '';
  let output = String(text)
    .replace(/\r\n?/g, '\n')
    .replace(/\u00a0/g, ' ')
    .replace(/[\u200b-\u200d\u2060]/g, '')
    .replace(/[ \t]{2,}/g, ' ');

  output = output
    .replace(/([A-Za-zÀ-ÿ0-9])([({["'"'])/g, '$1 $2')
    .replace(/([)}\]>"'"'.,;:!?])(?!\s|$)(?=[A-Za-zÀ-ÿ0-9])/g, '$1 ')
    .replace(/([a-zà-ÿ])([A-ZÀ-ß])/g, '$1 $2')
    .replace(/([A-Za-zÀ-ÿ])([0-9])/g, '$1 $2')
    .replace(/([0-9])([A-Za-zÀ-ÿ])/g, '$1 $2')
    .replace(/\uFFFD+/g, '')
    .replace(/[•·]{3,}/g, '•')
    .replace(/[|]{3,}/g, '|')
    .replace(/[—–-]{4,}/g, '—')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ ]+\n/g, '\n')
    .trim();

  return output;
}

// ── Class / file loading ──────────────────────────────────────────────────────

function adjustColor(color, percent) {
  const num = parseInt(color.replace('#', ''), 16);
  const amt = Math.round(2.55 * percent);
  const R = Math.max(0, Math.min(255, (num >> 16) + amt));
  const G = Math.max(0, Math.min(255, ((num >> 8) & 0x00ff) + amt));
  const B = Math.max(0, Math.min(255, (num & 0x0000ff) + amt));
  return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
}

function selectClass(classId) {
  if (agent.selectedClassId === classId) {
    agent.selectedClassId = null;
  } else {
    agent.selectedClassId = classId;
  }
  onClassChange();
}

async function onClassChange() {
  agent.classFiles = [];
  agent.selectedFileIds = [];
  agent.sessions = [];
  agent.currentSessionId = null;
  agent.activeSession = null;
  agent.messages = [];

  if (!agent.selectedClassId) return;
  await Promise.all([loadClassFiles(), loadSessions()]);
}

async function loadClassFiles() {
  agent.loadingFiles = true;
  try {
    const res = await api.getLessons(agent.selectedClassId, { limit: 100, refresh: true });
    if (res.success) agent.classFiles = res.uploads || [];
  } catch (err) {
    console.error('Failed to load class files:', err);
  } finally {
    agent.loadingFiles = false;
  }
}

// ── Sessions ──────────────────────────────────────────────────────────────────

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
  const defaultTitle = `Session ${new Date().toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })}`;
  const title = prompt('Name for the new session:', defaultTitle);
  if (!title) return;

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
  const newTitle = prompt('New name:', session.title);
  if (!newTitle || newTitle === session.title) return;

  try {
    const res = await api.renameAgentSession(session.thread_id, newTitle);
    if (res.success) {
      const idx = agent.sessions.findIndex(s => s.thread_id === session.thread_id);
      if (idx !== -1) agent.sessions[idx].title = res.session.title;
      if (agent.activeSession?.thread_id === session.thread_id) {
        agent.activeSession.title = res.session.title;
      }
    }
  } catch (err) {
    alert('Failed to rename session: ' + err.message);
  }
}

async function deleteSession(threadId) {
  if (!confirm('Delete this session and its history?')) return;
  try {
    await api.deleteAgentSession(threadId);
    agent.sessions = agent.sessions.filter(s => s.thread_id !== threadId);
    if (agent.currentSessionId === threadId) agent.currentSessionId = null;
    if (agent.activeSession?.thread_id === threadId) {
      agent.activeSession = null;
      agent.messages = [];
    }
  } catch (err) {
    alert('Failed to delete session: ' + err.message);
  }
}

// ── Chat ──────────────────────────────────────────────────────────────────────

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
  if (agent.isStreaming) return;
  agent.activeSession = null;
  agent.messages = [];
  agent.streamError = null;
}

async function sendMessage() {
  const prompt = agent.prompt.trim();
  if (!prompt || agent.isStreaming) return;

  // Send embedded files when available, otherwise allow session-only chat.
  const embeddedIds = agent.selectedFileIds.filter(id => {
    const f = agent.classFiles.find(f => f.id === id);
    return f && f.embedded;
  });

  agent.prompt = '';
  agent.streamError = null;

  agent.messages.push({ role: 'user', content: prompt });

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
  await classesStore.load();
});
</script>
