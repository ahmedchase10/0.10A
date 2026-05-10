<template>
  <div class="h-full overflow-y-auto custom-scrollbar bg-grey-50">
    <!-- Header -->
    <div class="bg-white border-b border-grey-200 px-8 py-6">
      <div class="flex items-center gap-2 text-sm text-grey-500 mb-4">
        <router-link to="/" class="hover:text-primary-600 transition">Dashboard</router-link>
        <span>/</span>
        <router-link :to="`/class/${classId}`" class="hover:text-primary-600 transition">Class</router-link>
        <span>/</span>
        <span class="text-grey-900 font-medium">Parent Notifications</span>
      </div>
      <h1 class="text-3xl font-bold text-grey-900">Draft Parent Notification</h1>
      <p class="text-grey-500 mt-2">Use AI to generate professional, empathetic emails based on student flags.</p>
    </div>

    <div class="px-8 py-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Left Column: Context Setup -->
      <div class="space-y-6">
        
        <!-- Student Selection -->
        <div class="bg-white rounded-xl border border-grey-200 shadow-sm p-6">
          <h2 class="text-lg font-semibold text-grey-900 mb-4 flex items-center gap-2">
            <UserIcon class="w-5 h-5 text-primary-500" />
            1. Select Student
          </h2>
          <select 
            v-model="selectedStudentId" 
            @change="handleStudentChange"
            :disabled="loadingStudents"
            class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
          >
            <option :value="null" disabled>{{ loadingStudents ? 'Loading students...' : 'Select a student...' }}</option>
            <option v-for="student in students" :key="student.id" :value="student.id">
              {{ student.name }} ({{ student.email }})
            </option>
          </select>
        </div>

        <!-- Flags Selection (Only if student selected) -->
        <div v-if="selectedStudentId" class="bg-white rounded-xl border border-grey-200 shadow-sm p-6 animate-fade-in">
          <h2 class="text-lg font-semibold text-grey-900 mb-4 flex items-center gap-2">
            <FlagIcon class="w-5 h-5 text-amber-500" />
            2. Select Context (Flags)
          </h2>
          
          <div v-if="loadingFlags" class="flex justify-center py-4">
            <div class="animate-spin rounded-full h-6 w-6 border-2 border-primary-500 border-t-transparent"></div>
          </div>
          
          <div v-else-if="flags.length === 0" class="text-sm text-grey-500 bg-grey-50 rounded-lg p-4">
            No flags recorded for this student. You can still generate an email based purely on your instructions.
          </div>
          
          <div v-else class="space-y-3">
            <label 
              v-for="flag in flags" 
              :key="flag.id" 
              class="flex items-start gap-3 p-3 rounded-lg border border-grey-200 hover:bg-grey-50 cursor-pointer transition"
            >
              <input 
                type="checkbox" 
                v-model="selectedFlags" 
                :value="flag.id"
                class="mt-1 rounded text-primary-600 focus:ring-primary-500"
              />
              <div>
                <p class="text-sm text-grey-900">{{ flag.reason }}</p>
                <p class="text-xs text-grey-500 mt-1">{{ new Date(flag.created_at).toLocaleDateString() }}</p>
              </div>
            </label>
          </div>
        </div>

        <!-- Instructions -->
        <div class="bg-white rounded-xl border border-grey-200 shadow-sm p-6">
          <h2 class="text-lg font-semibold text-grey-900 mb-4 flex items-center gap-2">
            <ChatBubbleBottomCenterTextIcon class="w-5 h-5 text-success-500" />
            3. Teacher Instructions
          </h2>
          <textarea
            v-model="teacherPrompt"
            rows="4"
            placeholder="e.g. Please let the parents know that the student has been disruptive but also mention they show great potential in math..."
            class="w-full px-4 py-3 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
          ></textarea>
          
          <div class="mt-4 flex justify-end">
            <button 
              @click="generateDraft" 
              :disabled="!canGenerate || isGenerating"
              class="flex items-center gap-2 px-6 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <SparklesIcon v-if="!isGenerating" class="w-5 h-5" />
              <div v-else class="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
              {{ isGenerating ? 'Drafting...' : 'Draft Email' }}
            </button>
          </div>
        </div>

      </div>

      <!-- Right Column: Draft Preview & Send -->
      <div class="bg-white rounded-xl border border-grey-200 shadow-sm flex flex-col overflow-hidden h-[calc(100vh-12rem)] sticky top-6">
        <div class="p-4 border-b border-grey-200 bg-grey-50 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-grey-900 flex items-center gap-2">
            <EnvelopeIcon class="w-5 h-5 text-blue-500" />
            Draft Preview
          </h2>
        </div>
        
        <div v-if="!draftEmail" class="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <div class="w-16 h-16 bg-grey-100 rounded-full flex items-center justify-center mb-4">
            <DocumentTextIcon class="w-8 h-8 text-grey-400" />
          </div>
          <h3 class="text-grey-900 font-medium mb-1">No Draft Yet</h3>
          <p class="text-sm text-grey-500 max-w-xs">Select a student, provide context, and click "Draft Email" to see the AI-generated message here.</p>
        </div>

        <div v-else class="flex-1 overflow-y-auto p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-grey-700 mb-1">Recipient Email (To)</label>
            <input 
              v-model="recipientEmail" 
              type="email" 
              class="w-full px-4 py-2 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-grey-700 mb-1">Subject</label>
            <input 
              v-model="draftEmail.subject" 
              type="text" 
              class="w-full px-4 py-2 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          
          <div class="flex-1 flex flex-col">
            <label class="block text-sm font-medium text-grey-700 mb-1">Body</label>
            <textarea 
              v-model="draftEmail.body" 
              rows="12"
              class="w-full flex-1 px-4 py-3 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none font-sans text-sm"
            ></textarea>
          </div>
        </div>

        <div v-if="draftEmail" class="p-4 border-t border-grey-200 bg-grey-50 flex items-center justify-between">
          <p v-if="successMessage" class="text-sm text-success-600 font-medium">{{ successMessage }}</p>
          <p v-else-if="errorMessage" class="text-sm text-red-600 font-medium">{{ errorMessage }}</p>
          <p v-else></p>

          <button 
            @click="sendEmail" 
            :disabled="!canSend || isSending"
            class="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
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
import { useRoute } from 'vue-router';
import api from '@/services/api';
import { 
  UserIcon, 
  FlagIcon, 
  ChatBubbleBottomCenterTextIcon, 
  SparklesIcon,
  EnvelopeIcon,
  DocumentTextIcon,
  PaperAirplaneIcon
} from '@heroicons/vue/24/outline';

const route = useRoute();
const classId = computed(() => parseInt(route.params.id));

const students = ref([]);
const selectedStudentId = ref(null);
const loadingStudents = ref(false);

const flags = ref([]);
const loadingFlags = ref(false);
const selectedFlags = ref([]);

const teacherPrompt = ref('');
const draftEmail = ref(null);
const recipientEmail = ref('');

const isGenerating = ref(false);
const isSending = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

onMounted(async () => {
  loadingStudents.value = true;
  try {
    const res = await api.getStudents(classId.value);
    if (res.success && res.students) {
      const allStudents = res.students;
      const flaggedStudents = [];
      
      // Filter for flagged students
      await Promise.all(allStudents.map(async (student) => {
        try {
          const flags = await api.getFlags(classId.value, student.id);
          if (Array.isArray(flags) && flags.length > 0) {
            flaggedStudents.push(student);
          }
        } catch (err) {
          console.error(`Failed to load flags for student ${student.id}`, err);
        }
      }));
      
      students.value = flaggedStudents;
    }
  } catch (err) {
    console.error("Failed to load students", err);
  } finally {
    loadingStudents.value = false;
  }
});

async function handleStudentChange() {
  draftEmail.value = null;
  flags.value = [];
  selectedFlags.value = [];
  successMessage.value = '';
  errorMessage.value = '';
  
  if (!selectedStudentId.value) return;

  // Auto-fill recipient email
  const student = students.value.find(s => s.id === selectedStudentId.value);
  if (student && student.email) {
    recipientEmail.value = student.email;
  }

  // Fetch flags
  loadingFlags.value = true;
  try {
    const res = await api.getFlags(classId.value, selectedStudentId.value);
    if (Array.isArray(res)) {
      flags.value = res;
    }
  } catch (err) {
    console.error("Failed to load flags", err);
  } finally {
    loadingFlags.value = false;
  }
}

const canGenerate = computed(() => {
  return !!selectedStudentId.value;
});

const canSend = computed(() => {
  return draftEmail.value && draftEmail.value.subject && draftEmail.value.body && recipientEmail.value;
});

async function generateDraft() {
  if (!canGenerate.value) return;
  
  isGenerating.value = true;
  successMessage.value = '';
  errorMessage.value = '';
  draftEmail.value = null;

  try {
    const payload = {
      custom: false,
      teacher_prompt: teacherPrompt.value,
      class_id: classId.value,
      student_id: selectedStudentId.value,
      selected_flags: selectedFlags.value.length > 0 ? selectedFlags.value : null
    };

    const res = await api.generateEmail(payload);
    draftEmail.value = {
      subject: res.subject || '',
      body: res.body || ''
    };
  } catch (err) {
    console.error("Email generation failed", err);
    errorMessage.value = err.message || "Failed to generate email.";
  } finally {
    isGenerating.value = false;
  }
}

async function sendEmail() {
  if (!canSend.value) return;

  isSending.value = true;
  successMessage.value = '';
  errorMessage.value = '';

  try {
    const payload = {
      to: recipientEmail.value,
      subject: draftEmail.value.subject,
      body: draftEmail.value.body
    };

    const res = await api.sendEmail(payload);
    successMessage.value = res.message || "Email sent successfully!";
  } catch (err) {
    console.error("Email sending failed", err);
    if ((err.message && err.message.includes("unauthorized")) || err.status === 401 || err.message.toLowerCase().includes("gmail")) {
       errorMessage.value = "Gmail not connected. Please connect your Gmail in Settings.";
    } else {
       errorMessage.value = err.message || "Failed to send email.";
    }
  } finally {
    isSending.value = false;
  }
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
