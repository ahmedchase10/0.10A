<template>
  <div class="h-full overflow-y-auto custom-scrollbar bg-grey-50 dark:bg-grey-950 transition-colors duration-300">
    <div class="bg-white dark:bg-grey-900 border-b border-grey-200 dark:border-grey-800 px-8 py-6">
      <div class="flex items-center gap-2 text-sm text-grey-500 dark:text-grey-400 mb-4">
        <router-link to="/" class="hover:text-primary-600 transition">Dashboard</router-link>
        <span>/</span>
        <span class="text-grey-900 dark:text-grey-50 font-medium">Mail</span>
      </div>
      <h1 class="text-3xl font-bold text-grey-900 dark:text-grey-50">Mail Composer</h1>
      <p class="text-grey-500 dark:text-grey-400 mt-2">Write a prompt, generate a draft email, edit it freely, and send it through Gmail.</p>
    </div>

    <div class="px-8 py-6 grid grid-cols-1 xl:grid-cols-2 gap-6">
      <div class="space-y-6">
        <div class="bg-white dark:bg-grey-900 rounded-xl border border-grey-200 dark:border-grey-800 shadow-sm p-6">
          <h2 class="text-lg font-semibold text-grey-900 dark:text-grey-50 mb-4">1. Recipient and Prompt</h2>

          <div class="mb-4">
            <label class="block text-sm font-medium text-grey-700 dark:text-grey-300 mb-2">Recipient Email</label>
            <input
              v-model="recipientEmail"
              type="email"
              placeholder="recipient@example.com"
              class="w-full px-4 py-2.5 border border-grey-300 dark:border-grey-700 bg-white dark:bg-grey-950 text-grey-900 dark:text-grey-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div class="mb-4">
            <label class="block text-sm font-medium text-grey-700 dark:text-grey-300 mb-2">Prompt</label>
            <textarea
              v-model="teacherPrompt"
              rows="7"
              placeholder="e.g. Write a polite follow-up email asking the parent to review the student's recent behavior and encouraging a meeting next week."
              class="w-full px-4 py-3 border border-grey-300 dark:border-grey-700 bg-white dark:bg-grey-950 text-grey-900 dark:text-grey-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
            ></textarea>
          </div>

          <div class="flex items-center justify-between gap-3">
            <p v-if="backendClassLabel" class="text-xs text-grey-500 dark:text-grey-400">
              Using your class context in the backend: <span class="font-medium">{{ backendClassLabel }}</span>
            </p>
            <p v-else class="text-xs text-amber-600 dark:text-amber-400">
              No class found yet. Add one class to enable draft generation.
            </p>

            <button
              @click="generateDraft"
              :disabled="!canGenerate || isGenerating"
              class="flex items-center gap-2 px-6 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <SparklesIcon v-if="!isGenerating" class="w-5 h-5" />
              <div v-else class="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
              {{ isGenerating ? 'Generating...' : 'Generate Draft' }}
            </button>
          </div>
        </div>

      </div>

      <div class="bg-white dark:bg-grey-900 rounded-xl border border-grey-200 dark:border-grey-800 shadow-sm flex flex-col overflow-hidden h-[calc(100vh-12rem)] sticky top-6">
        <div class="p-4 border-b border-grey-200 dark:border-grey-800 bg-grey-50 dark:bg-grey-950 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-grey-900 dark:text-grey-50 flex items-center gap-2">
            <EnvelopeIcon class="w-5 h-5 text-blue-500" />
            Draft Preview
          </h2>
        </div>

        <div v-if="!draftEmail" class="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <div class="w-16 h-16 bg-grey-100 dark:bg-grey-800 rounded-full flex items-center justify-center mb-4">
            <DocumentTextIcon class="w-8 h-8 text-grey-400 dark:text-grey-300" />
          </div>
          <h3 class="text-grey-900 dark:text-grey-50 font-medium mb-1">No Draft Yet</h3>
          <p class="text-sm text-grey-500 dark:text-grey-400 max-w-xs">Enter a recipient email and prompt, then generate a subject and body you can edit before sending.</p>
        </div>

        <div v-else class="flex-1 overflow-y-auto p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-grey-700 dark:text-grey-300 mb-1">Recipient Email (To)</label>
            <input
              v-model="recipientEmail"
              type="email"
              class="w-full px-4 py-2 border border-grey-300 dark:border-grey-700 bg-white dark:bg-grey-950 text-grey-900 dark:text-grey-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-grey-700 dark:text-grey-300 mb-1">Subject</label>
            <input
              v-model="draftEmail.subject"
              type="text"
              class="w-full px-4 py-2 border border-grey-300 dark:border-grey-700 bg-white dark:bg-grey-950 text-grey-900 dark:text-grey-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div class="flex-1 flex flex-col">
            <label class="block text-sm font-medium text-grey-700 dark:text-grey-300 mb-1">Body</label>
            <textarea
              v-model="draftEmail.body"
              rows="14"
              class="w-full flex-1 px-4 py-3 border border-grey-300 dark:border-grey-700 bg-white dark:bg-grey-950 text-grey-900 dark:text-grey-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none font-sans text-sm"
            ></textarea>
          </div>

          <div v-if="errorMessage" class="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 rounded-lg p-3">
            <p class="text-sm text-red-700 dark:text-red-200">{{ errorMessage }}</p>
          </div>
          <div v-if="successMessage" class="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-900 rounded-lg p-3">
            <p class="text-sm text-green-700 dark:text-green-200">{{ successMessage }}</p>
          </div>
        </div>

        <div v-if="draftEmail" class="p-4 border-t border-grey-200 dark:border-grey-800 bg-grey-50 dark:bg-grey-950 flex items-center justify-end gap-3">
          <button
            @click="sendEmail"
            :disabled="!canSend || isSending"
            class="flex items-center gap-2 px-6 py-2.5 bg-sky-600 text-white rounded-lg font-medium hover:bg-sky-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PaperAirplaneIcon v-if="!isSending" class="w-5 h-5 -rotate-45" />
            <div v-else class="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
            {{ isSending ? 'Sending...' : 'Send via Gmail' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useClassesStore } from '@/stores/classesStore';
import api from '@/services/api';
import {
  SparklesIcon,
  EnvelopeIcon,
  DocumentTextIcon,
  PaperAirplaneIcon
} from '@heroicons/vue/24/outline';

const classesStore = useClassesStore();

const recipientEmail = ref('');
const teacherPrompt = ref('');
const draftEmail = ref(null);
const isGenerating = ref(false);
const isSending = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

const backendClassId = computed(() => classesStore.classes[0]?.id ?? null);
const backendClassLabel = computed(() => classesStore.classes[0]?.name ?? '');
const canGenerate = computed(() => {
  return !!recipientEmail.value.trim() && !!teacherPrompt.value.trim() && !!backendClassId.value;
});

const canSend = computed(() => {
  return !!recipientEmail.value.trim() && !!draftEmail.value?.subject && !!draftEmail.value?.body;
});

async function loadContext() {
  await classesStore.load();
}

async function generateDraft() {
  if (!canGenerate.value) return;

  isGenerating.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    const res = await api.generateEmail({
      custom: true,
      teacher_prompt: teacherPrompt.value,
      class_id: backendClassId.value,
      recipient_email: recipientEmail.value
    });

    draftEmail.value = {
      subject: res.subject || '',
      body: res.body || ''
    };
    if (res.recipient_email) {
      recipientEmail.value = res.recipient_email;
    }
  } catch (err) {
    errorMessage.value = err.message || 'Failed to generate email draft.';
  } finally {
    isGenerating.value = false;
  }
}

async function sendEmail() {
  if (!canSend.value) return;

  isSending.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    const res = await api.sendEmail({
      to: recipientEmail.value,
      subject: draftEmail.value.subject,
      body: draftEmail.value.body
    });
    successMessage.value = res.message || 'Email sent successfully!';
  } catch (err) {
    if ((err?.message && err.message.toLowerCase().includes('gmail')) || err.status === 401) {
      errorMessage.value = 'Gmail is not connected yet. Please connect it first.';
    } else {
      errorMessage.value = err.message || 'Failed to send email.';
    }
  } finally {
    isSending.value = false;
  }
}

onMounted(loadContext);
</script>
