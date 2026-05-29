<template>
  <div class="h-full overflow-y-auto custom-scrollbar bg-grey-50 dark:bg-grey-950 transition-colors duration-300">

    <!-- ─── Progress Header (all steps except class selection) ─── -->
    <div v-if="step !== 'classes'" class="bg-white dark:bg-grey-900 border-b border-grey-200 dark:border-grey-800 px-8 py-4 sticky top-0 z-10">
      <div class="flex items-center gap-2 text-sm text-grey-600 dark:text-grey-400 mb-3">
        <button @click="goBack" class="hover:text-primary-600 dark:hover:text-sky-400 transition flex items-center gap-1 font-medium">
          <ChevronLeftIcon class="w-4 h-4" />
          {{ backLabel }}
        </button>
        <template v-if="selectedClass">
          <span>/</span>
          <span class="text-grey-900 dark:text-grey-50 font-medium">{{ selectedClass.name }}</span>
        </template>
      </div>
      <div class="flex items-center gap-1 flex-wrap">
        <template v-for="(s, idx) in visibleSteps" :key="s.key">
          <div class="flex items-center gap-1.5">
            <div
              class="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full transition"
              :class="currentStepIndex > idx
                ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                : currentStepIndex === idx
                  ? 'bg-primary-100 text-primary-700 ring-2 ring-primary-300 dark:bg-sky-950 dark:text-sky-300 dark:ring-sky-800'
                  : 'bg-grey-100 text-grey-400 dark:bg-grey-800 dark:text-grey-500'"
            >
              <CheckCircleIcon v-if="currentStepIndex > idx" class="w-3.5 h-3.5" />
              <span v-else class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold"
                :class="currentStepIndex === idx ? 'bg-primary-600 text-white' : 'bg-grey-300 text-grey-500 dark:bg-grey-700 dark:text-grey-300'">
                {{ idx + 1 }}
              </span>
              <span class="hidden sm:block">{{ s.label }}</span>
            </div>
            <ChevronRightIcon v-if="idx < visibleSteps.length - 1" class="w-3 h-3 text-grey-300 dark:text-grey-700 flex-shrink-0" />
          </div>
        </template>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════
         STEP 1 — Class Selection
    ═══════════════════════════════════════════════════════ -->
    <section v-if="step === 'classes'" class="p-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-grey-900 dark:text-grey-50">Grading Agent</h1>
        <p class="text-grey-600 dark:text-grey-400 mt-1">Select a class to start an AI-powered grading session.</p>
      </div>

      <div v-if="loadingClasses" class="flex items-center justify-center h-48">
        <div class="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
      </div>

      <div v-else-if="classes.length === 0"
        class="text-center py-20 border-2 border-dashed border-grey-200 dark:border-grey-800 rounded-2xl bg-white dark:bg-grey-900">
        <AcademicCapIcon class="w-16 h-16 text-grey-300 dark:text-grey-600 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-grey-900 dark:text-grey-50 mb-2">No classes yet</h3>
        <p class="text-grey-600 dark:text-grey-400">Create a class first to start grading.</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <button
          v-for="cls in classes"
          :key="cls.id"
          @click="selectClass(cls)"
          class="text-left bg-white dark:bg-grey-900 rounded-2xl border border-grey-200 dark:border-grey-800 p-6 hover:shadow-md transition group border-l-4"
          :style="{ borderLeftColor: cls.color || '#3b82f6' }"
        >
          <div class="flex items-start justify-between mb-4">
            <div 
              class="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg flex-shrink-0 transition-transform group-hover:scale-105"
              :style="{ background: `linear-gradient(135deg, ${cls.color || '#3b82f6'} 0%, ${adjustColor(cls.color || '#3b82f6', -15)} 100%)` }"
            >
              {{ cls.name.charAt(0).toUpperCase() }}
            </div>
            <ChevronRightIcon class="w-5 h-5 transition mt-1" :style="{ color: cls.color || '#3b82f6' }" />
          </div>
          <h3 class="text-lg font-semibold text-grey-900 dark:text-grey-50">{{ cls.name }}</h3>
          <p class="text-sm text-grey-500 dark:text-grey-400 mt-1">{{ cls.subject || 'No subject' }}</p>
        </button>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════
         STEP 2 — Session Setup
    ═══════════════════════════════════════════════════════ -->
    <section v-else-if="step === 'setup'" class="p-8">
      <div class="max-w-3xl mx-auto space-y-6">
        <div>
          <h2 class="text-2xl font-bold text-grey-900 dark:text-grey-50">Configure Grading Session</h2>
          <p class="text-grey-600 dark:text-grey-400 mt-1">Build a new correction blueprint or reuse an existing one.</p>
        </div>

        <!-- Mode tabs -->
        <div class="flex gap-1 p-1 bg-grey-100 dark:bg-grey-800 rounded-xl w-fit">
          <button
            @click="setupMode = 'new'"
            :class="setupMode === 'new' ? 'bg-white dark:bg-grey-900 text-grey-900 dark:text-grey-50 shadow-sm' : 'text-grey-600 dark:text-grey-400 hover:text-grey-800 dark:hover:text-grey-200'"
            class="px-5 py-2 rounded-lg text-sm font-medium transition"
          >New Blueprint</button>
          <button
            @click="switchToExisting"
            :class="setupMode === 'existing' ? 'bg-white dark:bg-grey-900 text-grey-900 dark:text-grey-50 shadow-sm' : 'text-grey-600 dark:text-grey-400 hover:text-grey-800 dark:hover:text-grey-200'"
            class="px-5 py-2 rounded-lg text-sm font-medium transition"
          >Use Existing Blueprint</button>
        </div>

        <!-- ── NEW BLUEPRINT ── -->
        <template v-if="setupMode === 'new'">
          <div class="bg-white dark:bg-grey-900 rounded-2xl border border-grey-200 dark:border-grey-800 p-6 space-y-6">

            <!-- Exam Title -->
            <div>
              <label class="block text-sm font-medium text-grey-700 dark:text-grey-300 mb-2">Exam Title *</label>
              <input v-model="examTitle" type="text"
                class="w-full px-4 py-2.5 border border-grey-300 dark:border-grey-700 bg-white dark:bg-grey-950 text-grey-900 dark:text-grey-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="e.g. Midterm Exam 2026" />
            </div>

            <!-- Exam Category Selector -->
            <div>
              <label class="block text-sm font-medium text-grey-700 dark:text-grey-300 mb-2">Exam Category *</label>
              <div class="grid grid-cols-3 gap-3">
                <button
                  type="button"
                  @click="examCategory = 'EXERCISE'"
                  :class="[
                    'px-4 py-2.5 rounded-xl border text-sm font-semibold transition text-center flex flex-col items-center justify-center gap-1',
                    examCategory === 'EXERCISE'
                      ? 'border-primary-500 bg-primary-50 text-primary-700 ring-1 ring-primary-300'
                      : 'border-grey-200 hover:border-primary-300 bg-white dark:bg-grey-950 text-grey-600 dark:text-grey-300'
                  ]"
                >
                  <span>Exercise</span>
                </button>
                <button
                  type="button"
                  @click="examCategory = 'MIDTERM'"
                  :class="[
                    'px-4 py-2.5 rounded-xl border text-sm font-semibold transition text-center flex flex-col items-center justify-center gap-1',
                    examCategory === 'MIDTERM'
                      ? 'border-violet-500 bg-violet-50 text-violet-700 ring-1 ring-violet-300'
                      : 'border-grey-200 hover:border-violet-300 bg-white dark:bg-grey-950 text-grey-600 dark:text-grey-300'
                  ]"
                >
                  <span>Midterm</span>
                </button>
                <button
                  type="button"
                  @click="examCategory = 'FINAL'"
                  :class="[
                    'px-4 py-2.5 rounded-xl border text-sm font-semibold transition text-center flex flex-col items-center justify-center gap-1',
                    examCategory === 'FINAL'
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-700 ring-1 ring-emerald-300'
                      : 'border-grey-200 hover:border-emerald-300 bg-white dark:bg-grey-950 text-grey-600 dark:text-grey-300'
                  ]"
                >
                  <span>Final</span>
                </button>
              </div>
              <p class="text-xs text-grey-500 dark:text-grey-400 mt-2">
                This sets the category in Class Grades for average calculations and insights.
              </p>
            </div>

            <!-- Exam Paper -->
            <div>
              <label class="block text-sm font-medium text-grey-700 dark:text-grey-300 mb-2">Exam Paper PDF *</label>

              <!-- Existing papers -->
              <div v-if="existingExamPapers.length > 0" class="space-y-2 mb-3">
                <p class="text-xs text-grey-500 dark:text-grey-400">Previously uploaded for this class:</p>
                <div class="space-y-2 max-h-44 overflow-y-auto custom-scrollbar">
                  <label v-for="paper in existingExamPapers" :key="paper.id"
                    class="flex items-center gap-3 rounded-xl border px-4 py-3 cursor-pointer transition"
                      :class="selectedExamPaperId === paper.id
                      ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-300 dark:bg-primary-950 dark:border-primary-400'
                      : 'border-grey-200 hover:border-primary-300 bg-grey-50 dark:bg-grey-950 dark:border-grey-800'">
                    <input type="radio" v-model="selectedExamPaperId" :value="paper.id" class="sr-only" />
                    <div class="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0 dark:bg-primary-900/30">
                      <DocumentTextIcon class="w-4 h-4 text-primary-600 dark:text-primary-300" />
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-grey-900 dark:text-grey-50 truncate">{{ paper.filename }}</p>
                      <p class="text-xs text-grey-500 dark:text-grey-400">{{ formatSize(paper.size) }} · {{ formatDate(paper.created_at) }}</p>
                    </div>
                    <CheckCircleIcon v-if="selectedExamPaperId === paper.id"
                      class="w-5 h-5 text-primary-600 dark:text-primary-300 flex-shrink-0" />
                  </label>
                  <label
                    class="flex items-center gap-3 rounded-xl border px-4 py-3 cursor-pointer transition"
                      :class="selectedExamPaperId === null
                      ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-300 dark:bg-primary-950 dark:border-primary-400'
                      : 'border-grey-200 hover:border-primary-300 bg-grey-50 dark:bg-grey-950 dark:border-grey-800'">
                    <input type="radio" v-model="selectedExamPaperId" :value="null" class="sr-only" />
                    <CloudArrowUpIcon class="w-4 h-4 text-grey-500 dark:text-grey-400" />
                    <span class="text-sm text-grey-700 dark:text-grey-200">Upload a new paper</span>
                  </label>
                </div>
              </div>

              <!-- Upload area -->
              <div v-if="existingExamPapers.length === 0 || selectedExamPaperId === null">
                <div
                  class="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition"
                  :class="examPaperFile ? 'border-primary-400 bg-primary-50 dark:bg-primary-950 dark:border-primary-500' : 'border-grey-300 hover:border-primary-400 dark:border-grey-700 dark:bg-grey-950 dark:hover:border-primary-500'"
                  @click="$refs.examPaperInput.click()"
                  @dragover.prevent
                  @drop.prevent="e => { examPaperFile = e.dataTransfer.files[0] }"
                >
                  <CloudArrowUpIcon class="w-8 h-8 mx-auto mb-2"
                    :class="examPaperFile ? 'text-primary-500' : 'text-grey-400'" />
                  <p class="text-sm" :class="examPaperFile ? 'text-primary-700 font-medium dark:text-primary-300' : 'text-grey-600 dark:text-grey-300'">
                    {{ examPaperFile ? examPaperFile.name : 'Click or drag & drop exam paper PDF' }}
                  </p>
                  <p v-if="examPaperFile" class="text-xs text-primary-500 mt-1">{{ formatSize(examPaperFile.size) }}</p>
                  <button v-if="examPaperFile" @click.stop="examPaperFile = null"
                    class="mt-2 text-xs text-red-500 hover:text-red-600">Remove</button>
                </div>
                <input ref="examPaperInput" type="file" accept=".pdf" class="hidden"
                  @change="e => { examPaperFile = e.target.files[0]; e.target.value = '' }" />
              </div>
            </div>

            <!-- Correction PDF (optional) -->
            <div>
              <label class="block text-sm font-medium text-grey-700 mb-1">
                Correction Paper
                <span class="text-grey-400 font-normal">(optional — deleted from server after analysis)</span>
              </label>
              <div
                class="border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition"
                :class="correctionFile ? 'border-emerald-400 bg-emerald-50 dark:bg-emerald-950 dark:border-emerald-500' : 'border-grey-200 hover:border-grey-400 dark:border-grey-700 dark:bg-grey-950 dark:hover:border-grey-500'"
                @click="$refs.correctionInput.click()"
                @dragover.prevent
                @drop.prevent="e => { correctionFile = e.dataTransfer.files[0] }"
              >
                <DocumentCheckIcon class="w-6 h-6 mx-auto mb-1"
                  :class="correctionFile ? 'text-emerald-600 dark:text-emerald-300' : 'text-grey-400 dark:text-grey-500'" />
                <p class="text-sm" :class="correctionFile ? 'text-emerald-700 font-medium dark:text-emerald-300' : 'text-grey-500 dark:text-grey-300'">
                  {{ correctionFile ? correctionFile.name : 'Upload correction paper (optional)' }}
                </p>
                <button v-if="correctionFile" @click.stop="correctionFile = null"
                  class="mt-1 text-xs text-red-500 hover:text-red-600">Remove</button>
              </div>
              <input ref="correctionInput" type="file" accept=".pdf" class="hidden"
                @change="e => { correctionFile = e.target.files[0]; e.target.value = '' }" />
            </div>

            <!-- Lesson PDFs for RAG -->
            <div v-if="classLessons.length > 0">
              <label class="block text-sm font-medium text-grey-700 mb-2 dark:text-grey-300">
                Lesson PDFs for Context
                <span class="text-grey-400 font-normal dark:text-grey-500">(optional, for RAG)</span>
              </label>
              <div class="space-y-2 max-h-48 overflow-y-auto custom-scrollbar border border-grey-200 rounded-xl p-3 bg-grey-50 dark:bg-grey-950 dark:border-grey-800">
                <label v-for="lesson in classLessons" :key="lesson.id"
                  class="flex items-center gap-3 rounded-lg border px-3 py-2 cursor-pointer transition"
                  :class="selectedLessonIds.includes(lesson.id)
                    ? 'border-primary-300 bg-primary-50 dark:bg-primary-950 dark:border-primary-500'
                    : 'border-transparent bg-white hover:border-grey-300 dark:bg-grey-900 dark:hover:border-grey-700'">
                  <input v-model="selectedLessonIds" :value="lesson.id" type="checkbox" :disabled="!lesson.embedded"
                    class="h-4 w-4 rounded border-grey-300 text-primary-600 focus:ring-primary-500 disabled:opacity-50 dark:border-grey-600 dark:bg-grey-900" />
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-grey-900 truncate dark:text-grey-50">{{ lesson.name }}</p>
                  </div>
                  <span class="text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0"
                    :class="lesson.embedded ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'">
                    {{ lesson.embedded ? 'Ready' : 'Embedding…' }}
                  </span>
                </label>
              </div>
            </div>

            <!-- Preferences -->
            <div>
              <label class="block text-sm font-medium text-grey-700 mb-2">
                Grading Preferences
                <span class="text-grey-400 font-normal">(optional)</span>
              </label>
              <textarea v-model="preferences" rows="3"
                class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none bg-white text-grey-900 placeholder-grey-400 dark:bg-grey-950 dark:border-grey-700 dark:text-grey-100 dark:placeholder-grey-500"
                placeholder="e.g. Q1: 4 pts. Deduct 1 pt for missing units. Partial credit allowed on Q3." />
            </div>

            <!-- Style Guide -->
            <div>
              <label class="block text-sm font-medium text-grey-700 mb-2">
                Style Guide
                <span class="text-grey-400 font-normal">(optional)</span>
              </label>
              <textarea v-model="styleGuide" rows="2"
                class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                placeholder="e.g. Math: show full derivation steps. Essays: minimum 3 arguments." />
            </div>

            <!-- Reasoning toggle -->
            <div class="flex items-center justify-between p-4 bg-violet-50 border border-violet-200 rounded-xl dark:bg-grey-900 dark:border-grey-800">
              <div>
                <p class="text-sm font-semibold text-violet-900 dark:text-grey-50">Reasoning Mode</p>
                <p class="text-xs text-violet-600 mt-0.5">Deep thinking — slower but significantly more accurate</p>
              </div>
              <div
                class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer"
                :class="reasoning ? 'bg-violet-600' : 'bg-grey-300 dark:bg-grey-700'"
                @click="reasoning = !reasoning"
              >
                <span
                  class="inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform"
                  :class="reasoning ? 'translate-x-6' : 'translate-x-1'"
                />
              </div>
            </div>

            <div v-if="setupError" class="bg-red-50 border border-red-200 rounded-xl p-4 dark:bg-red-950 dark:border-red-800">
              <p class="text-sm text-red-700 dark:text-red-300">{{ setupError }}</p>
            </div>

            <button @click="startAnalysis" :disabled="!canStartAnalysis || analyseLoading"
              class="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-3 rounded-xl font-semibold hover:from-primary-700 hover:to-primary-600 shadow-sm transition disabled:opacity-50">
              <SparklesIcon class="w-5 h-5" />
              {{ analyseLoading ? 'Uploading…' : 'Analyse & Build Blueprint' }}
            </button>
          </div>
        </template>

        <!-- ── EXISTING BLUEPRINT ── -->
        <template v-else>
            <div class="bg-white rounded-2xl border border-grey-200 p-6 space-y-5 dark:bg-grey-900 dark:border-grey-800">
            <div>
              <label class="block text-sm font-medium text-grey-700 mb-2 dark:text-grey-300">Exam Title *</label>
              <input v-model="examTitle" type="text"
                class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white text-grey-900 placeholder-grey-400 dark:bg-grey-950 dark:border-grey-700 dark:text-grey-100 dark:placeholder-grey-500"
                placeholder="e.g. Midterm Exam 2026" />
              <p class="text-xs text-grey-500 mt-1 dark:text-grey-400">Used to auto-create or match an exam type in Class Grades.</p>
            </div>

            <!-- Exam Category Selector -->
            <div>
              <label class="block text-sm font-medium text-grey-700 mb-2 dark:text-grey-300">Exam Category *</label>
              <div class="grid grid-cols-3 gap-3">
                <button
                  type="button"
                  @click="examCategory = 'EXERCISE'"
                  :class="[
                    'px-4 py-2.5 rounded-xl border text-sm font-semibold transition text-center flex flex-col items-center justify-center gap-1',
                    examCategory === 'EXERCISE'
                      ? 'border-primary-500 bg-primary-50 text-primary-700 ring-1 ring-primary-300'
                      : 'border-grey-200 hover:border-primary-300 bg-white text-grey-600 dark:bg-grey-950 dark:border-grey-700 dark:text-grey-300'
                  ]"
                >
                  <span>Exercise</span>
                </button>
                <button
                  type="button"
                  @click="examCategory = 'MIDTERM'"
                  :class="[
                    'px-4 py-2.5 rounded-xl border text-sm font-semibold transition text-center flex flex-col items-center justify-center gap-1',
                    examCategory === 'MIDTERM'
                      ? 'border-violet-500 bg-violet-50 text-violet-700 ring-1 ring-violet-300'
                      : 'border-grey-200 hover:border-violet-300 bg-white text-grey-600 dark:bg-grey-950 dark:border-grey-700 dark:text-grey-300'
                  ]"
                >
                  <span>Midterm</span>
                </button>
                <button
                  type="button"
                  @click="examCategory = 'FINAL'"
                  :class="[
                    'px-4 py-2.5 rounded-xl border text-sm font-semibold transition text-center flex flex-col items-center justify-center gap-1',
                    examCategory === 'FINAL'
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-700 ring-1 ring-emerald-300'
                      : 'border-grey-200 hover:border-emerald-300 bg-white text-grey-600 dark:bg-grey-950 dark:border-grey-700 dark:text-grey-300'
                  ]"
                >
                  <span>Final</span>
                </button>
              </div>
              <p class="text-xs text-grey-500 mt-2 dark:text-grey-400">
                This sets the category in Class Grades for average calculations and insights.
              </p>
            </div>

            <div v-if="loadingBlueprints" class="flex items-center justify-center py-10">
              <div class="animate-spin rounded-full h-8 w-8 border-4 border-primary-500 border-t-transparent"></div>
            </div>

            <div v-else-if="blueprints.length === 0"
              class="text-center py-10 border-2 border-dashed border-grey-200 rounded-xl dark:border-grey-800 dark:bg-grey-950">
              <SparklesIcon class="w-12 h-12 text-grey-300 mx-auto mb-3 dark:text-grey-600" />
              <p class="text-grey-600 text-sm dark:text-grey-400">No blueprints yet. Create one using the "New Blueprint" tab.</p>
            </div>

            <div v-else class="space-y-2 max-h-80 overflow-y-auto custom-scrollbar">
              <label v-for="bp in blueprints" :key="bp.id"
                class="flex items-start gap-3 rounded-xl border px-4 py-4 cursor-pointer transition"
                :class="selectedBlueprintId === bp.id
                  ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-300 dark:bg-primary-950 dark:border-primary-400'
                  : 'border-grey-200 hover:border-primary-300 dark:bg-grey-950 dark:border-grey-800 dark:hover:border-primary-500'">
                <input type="radio" v-model="selectedBlueprintId" :value="bp.id"
                  class="mt-0.5 h-4 w-4 text-primary-600 border-grey-300 dark:border-grey-600 dark:bg-grey-900" />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold text-grey-900 dark:text-grey-50">{{ bp.title }}</p>
                  <p class="text-xs text-grey-500 mt-0.5 dark:text-grey-400">Created {{ formatDate(bp.created_at) }}</p>
                  <p v-if="bp.preferences" class="text-xs text-grey-600 mt-1 line-clamp-2 dark:text-grey-400">{{ bp.preferences }}</p>
                </div>
                <CheckCircleIcon v-if="selectedBlueprintId === bp.id"
                  class="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5 dark:text-primary-300" />
              </label>
            </div>

            <div v-if="setupError" class="bg-red-50 border border-red-200 rounded-xl p-3 dark:bg-red-950 dark:border-red-800">
              <p class="text-sm text-red-700 dark:text-red-300">{{ setupError }}</p>
            </div>

            <button @click="useExistingBlueprint"
              :disabled="!selectedBlueprintId || !examTitle.trim()"
              class="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-3 rounded-xl font-semibold hover:from-primary-700 hover:to-primary-600 shadow-sm transition disabled:opacity-50">
              Continue to Student Assignment
              <ChevronRightIcon class="w-5 h-5" />
            </button>
          </div>
        </template>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════
         STEP 3 — Analysing (Phase 1 SSE)
    ═══════════════════════════════════════════════════════ -->
    <section v-else-if="step === 'analysing'" class="p-8">
      <div class="max-w-3xl mx-auto space-y-6">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-grey-900">Building Blueprint</h2>
            <p class="text-grey-600 mt-1">AI is reading the exam paper and preparing the correction blueprint.</p>
          </div>
          <div v-if="analyseLoading" class="flex items-center gap-2 text-primary-600">
            <span class="inline-block h-2.5 w-2.5 rounded-full bg-primary-500 animate-pulse"></span>
            <span class="text-sm font-medium">Analysing…</span>
          </div>
          <div v-else-if="blueprintReady && !analyseError" class="flex items-center gap-2 text-emerald-600">
            <CheckCircleIcon class="w-5 h-5" />
            <span class="text-sm font-medium">Blueprint ready!</span>
          </div>
        </div>

        <!-- Success CTA -->
        <div v-if="blueprintReady && !analyseLoading && !analyseError"
          class="bg-emerald-50 border border-emerald-200 rounded-2xl p-5">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 bg-emerald-200 rounded-full flex items-center justify-center flex-shrink-0">
              <CheckCircleIcon class="w-6 h-6 text-emerald-700" />
            </div>
            <div>
              <p class="font-semibold text-emerald-900">Blueprint Created Successfully</p>
              <p class="text-sm text-emerald-700">{{ examTitle }}</p>
            </div>
          </div>
          <button @click="proceedToStudents"
            class="w-full flex items-center justify-center gap-2 bg-emerald-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-emerald-700 transition">
            Continue to Student Assignment
            <ChevronRightIcon class="w-5 h-5" />
          </button>
        </div>

        <!-- Error -->
        <div v-if="analyseError" class="bg-red-50 border border-red-200 rounded-xl p-4 dark:bg-red-950 dark:border-red-800">
          <p class="text-sm font-semibold text-red-700 mb-1 dark:text-red-300">Analysis failed</p>
          <p class="text-sm text-red-600 dark:text-red-300">{{ analyseError }}</p>
          <button @click="step = 'setup'" class="mt-3 text-sm text-red-600 hover:text-red-700 font-medium">
            ← Back to setup
          </button>
        </div>

        <!-- Live stream panel -->
        <div class="bg-white rounded-2xl border border-grey-200 overflow-hidden dark:bg-grey-900 dark:border-grey-800">
          <div class="flex items-center justify-between px-5 py-4 border-b border-grey-200 dark:border-grey-800">
            <h3 class="text-sm font-semibold text-grey-900 dark:text-grey-50">Agent Activity</h3>
            <span v-if="analyseToolEvents.length" class="text-xs text-grey-500 dark:text-grey-400">
              {{ analyseToolEvents.length }} tool call{{ analyseToolEvents.length !== 1 ? 's' : '' }}
            </span>
          </div>
          <div class="p-5 space-y-4">
            <!-- Content stream -->
            <div v-if="analyseContent"
              class="rounded-lg bg-grey-50 border border-grey-200 p-4 text-sm text-grey-700 whitespace-pre-wrap max-h-52 overflow-y-auto custom-scrollbar leading-relaxed dark:bg-grey-950 dark:border-grey-800 dark:text-grey-200">
              {{ analyseContent }}
            </div>

            <!-- Tool events badges -->
            <div v-if="analyseToolEvents.length" class="flex flex-wrap gap-2">
              <span v-for="(ev, i) in analyseToolEvents" :key="i"
                class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium"
                :class="ev.type === 'tool_call' ? 'bg-violet-50 text-violet-700 border border-violet-200 dark:bg-violet-950 dark:text-violet-300 dark:border-violet-800' : 'bg-teal-50 text-teal-700 border border-teal-200 dark:bg-teal-950 dark:text-teal-300 dark:border-teal-800'">
                <WrenchScrewdriverIcon class="w-3 h-3" />
                {{ ev.name }}
              </span>
            </div>

            <!-- Thinking (collapsible) -->
            <details v-if="analyseThinking" class="rounded-xl border border-amber-200 bg-amber-50 p-4 dark:bg-amber-950 dark:border-amber-800">
              <summary class="cursor-pointer text-sm font-medium text-amber-800 dark:text-amber-200 select-none flex items-center gap-2">
                <span>🧠</span> Reasoning — click to expand
              </summary>
              <pre class="mt-3 whitespace-pre-wrap text-xs text-amber-900 dark:text-amber-100 font-mono max-h-52 overflow-y-auto custom-scrollbar leading-relaxed">{{ analyseThinking }}</pre>
            </details>

            <!-- Loading skeleton -->
            <div v-if="analyseLoading && !analyseContent && !analyseThinking" class="space-y-3">
              <div class="h-4 bg-grey-100 dark:bg-grey-800 rounded-full animate-pulse w-3/4"></div>
              <div class="h-4 bg-grey-100 dark:bg-grey-800 rounded-full animate-pulse w-1/2"></div>
              <div class="h-4 bg-grey-100 dark:bg-grey-800 rounded-full animate-pulse w-2/3"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════
         STEP 4 — Student Assignment
    ═══════════════════════════════════════════════════════ -->
    <section v-else-if="step === 'students'" class="p-8">
      <div class="max-w-4xl mx-auto space-y-6">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-grey-900">Assign Student Papers</h2>
            <p class="text-grey-600 mt-1">Upload each student's answer PDF, then start the grading queue.</p>
          </div>
          <div class="text-right">
            <p class="text-sm font-semibold text-grey-700">{{ assignedCount }} / {{ students.length }} assigned</p>
            <p class="text-xs text-grey-500 mt-0.5">{{ selectedClass?.name }}</p>
          </div>
        </div>

        <!-- Exam type card -->
        <div class="bg-white rounded-2xl border border-grey-200 p-6 space-y-4">
          <div>
            <h3 class="text-sm font-semibold text-grey-900">Exam Type in Class Grades</h3>
            <p class="text-xs text-grey-500 mt-0.5">Grades will be saved under this exam type.</p>
          </div>

          <div v-if="loadingExamTypes" class="flex items-center gap-2 text-sm text-grey-500 py-2">
            <div class="animate-spin rounded-full h-4 w-4 border-2 border-primary-500 border-t-transparent"></div>
            Loading exam types…
          </div>

          <div v-else class="space-y-3">
            <div v-if="matchedExamType"
              class="flex items-center gap-3 rounded-xl bg-emerald-50 border border-emerald-200 px-4 py-3">
              <CheckCircleIcon class="w-5 h-5 text-emerald-600 flex-shrink-0" />
              <div>
                <p class="text-sm font-semibold text-emerald-900">Matched: "{{ matchedExamType.name }}"</p>
                <p class="text-xs text-emerald-700">Grades will be saved under this existing exam type.</p>
              </div>
            </div>
            <div v-else
              class="flex items-center gap-3 rounded-xl bg-blue-50 border border-blue-200 px-4 py-3">
              <InformationCircleIcon class="w-5 h-5 text-blue-600 flex-shrink-0" />
              <div>
                <p class="text-sm font-semibold text-blue-900">Will auto-create: "{{ examTitle }}"</p>
                <p class="text-xs text-blue-700">A new exam type (Exercise category) will be created automatically.</p>
              </div>
            </div>

            <!-- Manual override -->
            <details class="group">
              <summary class="cursor-pointer text-xs text-grey-500 hover:text-grey-700 select-none">
                Override exam type manually
              </summary>
              <div class="mt-3 space-y-1.5 pl-2">
                <label class="flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer transition"
                  :class="selectedExamTypeId === null
                    ? 'border-primary-400 bg-primary-50'
                    : 'border-grey-200 hover:border-grey-300'">
                  <input type="radio" v-model="selectedExamTypeId" :value="null"
                    class="h-3.5 w-3.5 text-primary-600" />
                  <span class="text-xs text-grey-700">Auto (create/match by title)</span>
                </label>
                <label v-for="et in examTypes" :key="et.id"
                  class="flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer transition"
                  :class="selectedExamTypeId === et.id
                    ? 'border-primary-400 bg-primary-50'
                    : 'border-grey-200 hover:border-grey-300'">
                  <input type="radio" v-model="selectedExamTypeId" :value="et.id"
                    class="h-3.5 w-3.5 text-primary-600" />
                  <span class="text-xs text-grey-700">{{ et.name }}</span>
                </label>
              </div>
            </details>
          </div>
        </div>

        <!-- Students list -->
        <div class="bg-white rounded-2xl border border-grey-200 overflow-hidden dark:bg-grey-900 dark:border-grey-800">
          <div class="px-6 py-4 border-b border-grey-200 flex items-center justify-between dark:border-grey-800">
            <h3 class="text-sm font-semibold text-grey-900 dark:text-grey-50">Students</h3>
            <div class="flex gap-2">
              <button @click="clearAllFiles" v-if="assignedCount > 0"
                class="text-xs text-grey-500 hover:text-red-600 transition">Clear all</button>
            </div>
          </div>

          <div v-if="loadingStudents" class="flex items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-4 border-primary-500 border-t-transparent"></div>
          </div>

          <div v-else-if="students.length === 0" class="p-12 text-center text-grey-500">
            <UserGroupIcon class="w-12 h-12 text-grey-300 mx-auto mb-3" />
            <p class="text-sm">No students in this class.</p>
          </div>

          <div v-else class="divide-y divide-grey-100">
            <div v-for="student in students" :key="student.id"
              class="px-6 py-4 flex items-center gap-4 hover:bg-grey-50 transition dark:hover:bg-grey-800/50">
              <div class="w-9 h-9 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
                {{ student.name.charAt(0).toUpperCase() }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-grey-900 truncate dark:text-grey-50">{{ student.name }}</p>
              </div>
              <div class="flex items-center gap-2">
                <span v-if="studentFiles[student.id]"
                  class="hidden sm:inline-flex text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full font-medium items-center gap-1 dark:bg-emerald-950 dark:border-emerald-800 dark:text-emerald-300">
                  <CheckIcon class="w-3 h-3" />
                  {{ truncateName(studentFiles[student.id].name, 18) }}
                </span>
                <button @click="triggerStudentFileInput(student.id)"
                  class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition"
                  :class="studentFiles[student.id]
                    ? 'border border-grey-300 text-grey-600 hover:bg-grey-100 dark:border-grey-700 dark:text-grey-300 dark:hover:bg-grey-800'
                    : 'bg-primary-600 text-white hover:bg-primary-700'">
                  <CloudArrowUpIcon class="w-3.5 h-3.5" />
                  {{ studentFiles[student.id] ? 'Change' : 'Upload PDF' }}
                </button>
                <input
                  :ref="el => { if (el) studentInputRefs[student.id] = el }"
                  type="file" accept=".pdf" class="hidden"
                  @change="e => handleStudentFile(student.id, e)"
                />
              </div>
            </div>
          </div>
        </div>

        <div v-if="batchError" class="bg-red-50 border border-red-200 rounded-xl p-4 dark:bg-red-950 dark:border-red-800">
          <p class="text-sm text-red-700 dark:text-red-300">{{ batchError }}</p>
        </div>

        <button @click="startGrading" :disabled="assignedCount === 0 || batchLoading"
          class="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-primary-600 text-white px-6 py-3.5 rounded-xl font-semibold hover:from-violet-700 hover:to-primary-700 shadow-md transition disabled:opacity-50 text-base">
          <SparklesIcon class="w-5 h-5" />
          {{ batchLoading
            ? 'Starting…'
            : `Start Grading Queue (${assignedCount} student${assignedCount !== 1 ? 's' : ''})` }}
        </button>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════
         STEP 5 — Grading Queue
    ═══════════════════════════════════════════════════════ -->
    <section v-else-if="step === 'grading'" class="p-8">
      <div class="max-w-5xl mx-auto grid grid-cols-1 xl:grid-cols-[260px_1fr] gap-6 items-start">

        <!-- Sidebar queue -->
        <div class="bg-white rounded-2xl border border-grey-200 overflow-hidden xl:sticky xl:top-24 dark:bg-grey-900 dark:border-grey-800">
          <div class="px-5 py-4 border-b border-grey-200 dark:border-grey-800">
            <h3 class="text-sm font-semibold text-grey-900 dark:text-grey-50">Grading Queue</h3>
            <p class="text-xs text-grey-500 mt-0.5 dark:text-grey-400">{{ completedCount }} / {{ sessions.length }} done</p>
            <!-- Progress bar -->
            <div class="mt-3 h-1.5 bg-grey-100 rounded-full overflow-hidden dark:bg-grey-800">
              <div class="h-full bg-gradient-to-r from-violet-500 to-primary-500 rounded-full transition-all"
                :style="{ width: `${sessions.length > 0 ? (completedCount / sessions.length) * 100 : 0}%` }">
              </div>
            </div>
          </div>
          <div class="divide-y divide-grey-100 max-h-[60vh] overflow-y-auto custom-scrollbar dark:divide-grey-800">
            <div v-for="sess in sessions" :key="sess.session_id"
              class="px-4 py-3 flex items-center gap-3 transition"
              :class="currentSessionId === sess.session_id ? 'bg-primary-50 dark:bg-primary-950/40' : ''">
              <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                :class="sess.status === 'approved'
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                  : sess.status === 'cancelled'
                    ? 'bg-grey-100 text-grey-400 dark:bg-grey-800 dark:text-grey-500'
                    : currentSessionId === sess.session_id
                      ? 'bg-primary-100 text-primary-700 dark:bg-primary-950 dark:text-primary-300'
                      : 'bg-grey-100 text-grey-400 dark:bg-grey-800 dark:text-grey-500'">
                <CheckIcon v-if="sess.status === 'approved'" class="w-4 h-4" />
                <XMarkIcon v-else-if="sess.status === 'cancelled'" class="w-4 h-4" />
                <span v-else>{{ sess.queue_position + 1 }}</span>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-semibold text-grey-900 truncate dark:text-grey-50">{{ sess.student_name }}</p>
                <p class="text-xs mt-0.5 capitalize"
                  :class="sess.status === 'approved'
                    ? 'text-emerald-600 dark:text-emerald-300'
                    : sess.status === 'cancelled'
                      ? 'text-grey-400 dark:text-grey-500'
                      : currentSessionId === sess.session_id
                        ? 'text-primary-600 dark:text-primary-300'
                        : 'text-grey-400 dark:text-grey-500'">
                  {{ currentSessionId === sess.session_id && gradingLoading
                    ? (isReviewing ? 'reviewing…' : 'grading…')
                    : sess.status }}
                </p>
              </div>
              <span v-if="sess.normalised_grade != null"
                class="text-xs font-bold px-2 py-0.5 rounded-full flex-shrink-0"
                :class="getGradeClass(sess.normalised_grade)">
                {{ sess.normalised_grade.toFixed(1) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Main grading panel -->
        <div class="space-y-4">
          <div class="bg-white rounded-2xl border border-grey-200 overflow-hidden dark:bg-grey-900 dark:border-grey-800">
            <!-- Panel header -->
            <div class="px-6 py-4 border-b border-grey-200 flex items-center justify-between dark:border-grey-800">
              <div>
                <h2 class="text-lg font-semibold text-grey-900 dark:text-grey-50">{{ currentStudentName || 'Loading…' }}</h2>
                <p class="text-sm text-grey-500 dark:text-grey-400 mt-0.5">{{ examTitle }}</p>
              </div>
              <div v-if="gradingLoading && !isReviewing" class="flex items-center gap-2 text-primary-600 dark:text-primary-300">
                <span class="inline-block h-2.5 w-2.5 rounded-full bg-primary-500 animate-pulse"></span>
                <span class="text-sm font-medium">Grading…</span>
              </div>
              <div v-else-if="isReviewing" class="flex items-center gap-2 text-amber-600 dark:text-amber-300">
                <ClipboardDocumentCheckIcon class="w-4 h-4" />
                <span class="text-sm font-medium">Review required</span>
              </div>
            </div>

            <!-- Agent narrative -->
            <div v-if="gradingContent && !isReviewing" class="px-6 py-4 border-b border-grey-100 dark:border-grey-800">
              <p class="text-sm text-grey-600 dark:text-grey-300 whitespace-pre-wrap leading-relaxed">{{ gradingContent }}</p>
            </div>

            <!-- Tool events -->
            <div v-if="gradingToolEvents.length && !isReviewing"
              class="px-6 py-3 border-b border-grey-100 dark:border-grey-800 flex flex-wrap gap-2">
              <span v-for="(ev, i) in gradingToolEvents" :key="i"
                class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium"
                :class="ev.type === 'tool_call'
                  ? 'bg-violet-50 text-violet-700 border border-violet-200 dark:bg-violet-950 dark:text-violet-300 dark:border-violet-800'
                  : 'bg-teal-50 text-teal-700 border border-teal-200 dark:bg-teal-950 dark:text-teal-300 dark:border-teal-800'">
                <WrenchScrewdriverIcon class="w-3 h-3" />
                {{ ev.name }}
              </span>
            </div>

            <!-- Thinking panel -->
            <div v-if="gradingThinking && !isReviewing" class="px-6 py-4 border-b border-grey-100 dark:border-grey-800">
              <details class="rounded-xl border border-amber-200 bg-amber-50 p-3 dark:bg-amber-950 dark:border-amber-800">
                <summary class="cursor-pointer text-sm font-medium text-amber-800 dark:text-amber-200 select-none flex items-center gap-2">
                  <span>🧠</span> Reasoning — click to expand
                </summary>
                <pre class="mt-2 whitespace-pre-wrap text-xs text-amber-900 dark:text-amber-100 font-mono max-h-40 overflow-y-auto custom-scrollbar leading-relaxed">{{ gradingThinking }}</pre>
              </details>
            </div>

            <!-- Question results -->
            <div v-if="questionResults.length > 0" class="px-6 py-5 space-y-3">
              <h4 class="text-xs font-semibold uppercase tracking-wider text-grey-500 dark:text-grey-400">Question Breakdown</h4>
              <div v-for="qr in questionResults" :key="qr.question_number"
                class="rounded-xl border p-4 space-y-2"
                :class="qr.awarded_points >= qr.max_points
                  ? 'border-emerald-200 bg-emerald-50 dark:bg-emerald-950 dark:border-emerald-800'
                  : qr.awarded_points === 0
                    ? 'border-red-200 bg-red-50 dark:bg-red-950 dark:border-red-800'
                    : 'border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800'">
                <div class="flex items-center justify-between gap-3">
                  <span class="text-sm font-semibold text-grey-900 dark:text-grey-50">{{ qr.label }}</span>
                  <div class="flex items-center gap-2">
                    <template v-if="isReviewing">
                      <input
                        v-model.number="reviewDecisions[qr.question_number]"
                        type="number" :min="0" :max="qr.max_points" :step="0.25"
                        class="w-16 px-2 py-1 text-center border border-grey-300 rounded-lg text-sm font-bold focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white text-grey-900 dark:bg-grey-950 dark:border-grey-700 dark:text-grey-100"
                      />
                    </template>
                    <template v-else>
                      <span class="text-sm font-bold"
                        :class="qr.awarded_points >= qr.max_points
                          ? 'text-emerald-700'
                          : qr.awarded_points === 0
                            ? 'text-red-700'
                            : 'text-amber-700'">
                        {{ qr.awarded_points }}
                      </span>
                    </template>
                    <span class="text-xs text-grey-500 dark:text-grey-400">/ {{ qr.max_points }} pts</span>
                  </div>
                </div>
                <p class="text-xs text-grey-600 leading-relaxed dark:text-grey-300">{{ qr.reasoning }}</p>
              </div>

              <!-- Total score when reviewing -->
              <div v-if="isReviewing" class="rounded-xl border-2 border-primary-200 bg-primary-50 p-4 mt-2 dark:bg-primary-950 dark:border-primary-800">
                <div class="flex items-center justify-between">
                  <span class="text-sm font-semibold text-primary-900 dark:text-primary-200">Total Score</span>
                  <div class="text-right">
                    <p class="text-xl font-bold text-primary-800 dark:text-primary-200">
                      {{ reviewTotal.toFixed(1) }} / {{ reviewMax.toFixed(1) }}
                    </p>
                    <p class="text-xs text-primary-600 mt-0.5 dark:text-primary-300">
                      ≈ {{ normalisedReview.toFixed(2) }} / 20
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Loading skeleton -->
            <div v-if="gradingLoading && questionResults.length === 0 && !gradingError" class="px-6 py-8 space-y-3">
              <div class="h-4 bg-grey-100 rounded-full animate-pulse w-3/4 dark:bg-grey-800"></div>
              <div class="h-4 bg-grey-100 rounded-full animate-pulse w-1/2 dark:bg-grey-800"></div>
              <div class="h-4 bg-grey-100 rounded-full animate-pulse w-2/3 dark:bg-grey-800"></div>
            </div>

            <!-- Grading error -->
            <div v-if="gradingError" class="px-6 py-4">
              <div class="bg-red-50 border border-red-200 rounded-xl p-4">
                <p class="text-sm font-semibold text-red-700 mb-1">Grading error</p>
                <p class="text-sm text-red-600">{{ gradingError }}</p>
              </div>
            </div>

            <!-- Review action buttons -->
            <div v-if="isReviewing" class="px-6 py-4 border-t border-grey-200 flex items-center gap-3">
              <button @click="approveSession" :disabled="reviewSubmitting"
                class="flex-1 flex items-center justify-center gap-2 bg-emerald-600 text-white px-5 py-3 rounded-xl font-semibold hover:bg-emerald-700 transition disabled:opacity-50">
                <CheckIcon class="w-4 h-4" />
                {{ reviewSubmitting ? 'Saving…' : 'Approve & Save Grade' }}
              </button>
              <button @click="cancelSession" :disabled="reviewSubmitting"
                class="flex items-center justify-center gap-2 border border-red-300 text-red-600 px-5 py-3 rounded-xl font-medium hover:bg-red-50 transition disabled:opacity-50">
                <XMarkIcon class="w-4 h-4" />
                Skip
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════
         STEP 6 — Complete
    ═══════════════════════════════════════════════════════ -->
    <section v-else-if="step === 'complete'" class="p-8">
      <div class="max-w-2xl mx-auto space-y-8 text-center">
        <div>
          <div class="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircleIcon class="w-10 h-10 text-emerald-600" />
          </div>
          <h2 class="text-3xl font-bold text-grey-900">Grading Complete!</h2>
          <p class="text-grey-600 mt-2">All students in the batch have been processed.</p>
        </div>

        <!-- Stats row -->
        <div class="grid grid-cols-3 gap-4">
          <div class="bg-white rounded-2xl border border-grey-200 p-5">
            <p class="text-2xl font-bold text-grey-900">{{ sessions.filter(s => s.status === 'approved').length }}</p>
            <p class="text-xs text-grey-500 mt-1">Approved</p>
          </div>
          <div class="bg-white rounded-2xl border border-grey-200 p-5">
            <p class="text-2xl font-bold text-grey-900">{{ sessions.filter(s => s.status === 'cancelled').length }}</p>
            <p class="text-xs text-grey-500 mt-1">Skipped</p>
          </div>
          <div class="bg-white rounded-2xl border border-grey-200 p-5">
            <p class="text-2xl font-bold text-grey-900">{{ batchAverage }}</p>
            <p class="text-xs text-grey-500 mt-1">Batch Average</p>
          </div>
        </div>

        <!-- Results list -->
        <div class="bg-white rounded-2xl border border-grey-200 overflow-hidden text-left">
          <div class="px-6 py-4 border-b border-grey-200">
            <p class="text-sm font-semibold text-grey-900">Results — {{ examTitle }}</p>
          </div>
          <div class="divide-y divide-grey-100">
            <div v-for="sess in sessions" :key="sess.session_id"
              class="px-5 py-4 flex items-center gap-4">
              <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                :class="sess.status === 'approved'
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'bg-grey-100 text-grey-400'">
                <CheckIcon v-if="sess.status === 'approved'" class="w-4 h-4" />
                <XMarkIcon v-else class="w-4 h-4" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-grey-900">{{ sess.student_name }}</p>
                <p class="text-xs text-grey-500 capitalize mt-0.5">{{ sess.status }}</p>
              </div>
              <span v-if="sess.normalised_grade != null"
                class="text-sm font-bold px-3 py-1 rounded-lg"
                :class="getGradeClass(sess.normalised_grade)">
                {{ sess.normalised_grade.toFixed(2) }} / 20
              </span>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-center gap-4">
          <router-link :to="`/class/${selectedClass?.id}/grades`"
            class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-3 rounded-xl font-semibold hover:from-primary-700 hover:to-primary-600 shadow-sm transition">
            <ChartBarIcon class="w-4 h-4" />
            View Class Grades
          </router-link>
          <button @click="startOver"
            class="flex items-center gap-2 border border-grey-300 text-grey-700 px-6 py-3 rounded-xl font-medium hover:bg-grey-50 transition">
            <ArrowPathIcon class="w-4 h-4" />
            Grade Another Class
          </button>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckIcon,
  CheckCircleIcon,
  XMarkIcon,
  CloudArrowUpIcon,
  DocumentTextIcon,
  DocumentCheckIcon,
  SparklesIcon,
  UserGroupIcon,
  AcademicCapIcon,
  WrenchScrewdriverIcon,
  ClipboardDocumentCheckIcon,
  InformationCircleIcon,
  ChartBarIcon,
  ArrowPathIcon,
} from '@heroicons/vue/24/outline';
import api from '@/services/api';

// ── Router ──────────────────────────────────────────────────────
const route  = useRoute();
const router = useRouter();

// ── Step Management ─────────────────────────────────────────────
const step = ref('classes');

const visibleSteps = computed(() => [
  { key: 'setup',      label: 'Session Setup' },
  { key: 'analysing',  label: 'Blueprint',    skip: setupMode.value === 'existing' },
  { key: 'students',   label: 'Students' },
  { key: 'grading',    label: 'Grading' },
  { key: 'complete',   label: 'Complete' },
].filter(s => !s.skip));

const currentStepIndex = computed(() => {
  const idx = visibleSteps.value.findIndex(s => s.key === step.value);
  return idx >= 0 ? idx : 0;
});

const backLabel = computed(() => {
  if (step.value === 'setup')     return 'Classes';
  if (step.value === 'analysing') return 'Setup';
  if (step.value === 'students')  return 'Setup';
  if (step.value === 'grading')   return 'Students';
  if (step.value === 'complete')  return 'Classes';
  return 'Back';
});

function goBack() {
  if (step.value === 'setup')     { step.value = 'classes'; }
  else if (step.value === 'analysing') { step.value = 'setup'; }
  else if (step.value === 'students')  { step.value = 'setup'; }
  else if (step.value === 'complete')  { startOver(); }
}

// ── Classes ──────────────────────────────────────────────────────
const classes      = ref([]);
const loadingClasses = ref(true);
const selectedClass = ref(null);

async function loadClasses() {
  loadingClasses.value = true;
  try {
    const res = await api.getClasses();
    if (res.success) classes.value = res.classes || [];
  } catch (err) {
    console.error('loadClasses:', err);
  } finally {
    loadingClasses.value = false;
  }
}

async function selectClass(cls) {
  selectedClass.value = cls;
  step.value = 'setup';
  setupMode.value = 'new';
  resetSetup();
  await Promise.all([
    loadExistingExamPapers(cls.id),
    loadLessons(cls.id),
    loadExamTypes(cls.id),
    loadStudents(cls.id),
  ]);
}

// ── Setup State ──────────────────────────────────────────────────
const setupMode          = ref('new');      // 'new' | 'existing'
const examTitle          = ref('');
const examCategory       = ref('EXERCISE'); // 'EXERCISE' | 'MIDTERM' | 'FINAL'
const reasoning          = ref(true);       // on by default per requirements
const examPaperFile      = ref(null);
const selectedExamPaperId = ref(null);
const existingExamPapers = ref([]);
const correctionFile     = ref(null);
const preferences        = ref('');
const styleGuide         = ref('');
const selectedLessonIds  = ref([]);
const classLessons       = ref([]);
const blueprints         = ref([]);
const selectedBlueprintId = ref(null);
const loadingBlueprints  = ref(false);
const setupError         = ref('');
const analyseLoading     = ref(false);

function resetSetup() {
  examTitle.value          = '';
  examCategory.value       = 'EXERCISE';
  examPaperFile.value      = null;
  selectedExamPaperId.value = null;
  correctionFile.value     = null;
  preferences.value        = '';
  styleGuide.value         = '';
  selectedLessonIds.value  = [];
  selectedBlueprintId.value = null;
  setupError.value         = '';
  analyseThinking.value    = '';
  analyseContent.value     = '';
  analyseToolEvents.value  = [];
  analyseError.value       = '';
  blueprintId.value        = null;
}

async function switchToExisting() {
  setupMode.value = 'existing';
  if (blueprints.value.length === 0) {
    loadingBlueprints.value = true;
    try {
      const res = await api.listGradingBlueprints();
      if (res.success) blueprints.value = res.blueprints || [];
    } catch (err) {
      console.error('loadBlueprints:', err);
    } finally {
      loadingBlueprints.value = false;
    }
  }
}

// Exam paper ready check
const canStartAnalysis = computed(() => {
  const hasTitle = examTitle.value.trim().length > 0;
  const hasPaper = selectedExamPaperId.value !== null || examPaperFile.value !== null;
  return hasTitle && hasPaper && !analyseLoading.value;
});

async function loadExistingExamPapers(classId) {
  try {
    const res = await api.listGradingExamPapers(classId);
    if (res.success) existingExamPapers.value = res.exam_papers || [];
    // Pre-select first if there is one
    if (existingExamPapers.value.length > 0) {
      selectedExamPaperId.value = existingExamPapers.value[0].id;
    }
  } catch (err) {
    console.error('loadExistingExamPapers:', err);
  }
}

async function loadLessons(classId) {
  try {
    const res = await api.getLessons(classId);
    if (res.success) classLessons.value = res.uploads || [];
  } catch (err) {
    console.error('loadLessons:', err);
  }
}

// ── Phase 1 — Analysis SSE ───────────────────────────────────────
const blueprintId       = ref(null);
const blueprintReady    = ref(false);
const analyseThinking   = ref('');
const analyseContent    = ref('');
const analyseToolEvents = ref([]);
const analyseError      = ref('');

async function startAnalysis() {
  setupError.value = '';
  analyseError.value = '';
  analyseThinking.value  = '';
  analyseContent.value   = '';
  analyseToolEvents.value = [];
  blueprintId.value      = null;
  blueprintReady.value   = false;
  analyseLoading.value   = true;

  let resolvedExamPaperId = selectedExamPaperId.value;

  try {
    // If uploading a new exam paper, do that first
    if (selectedExamPaperId.value === null) {
      if (!examPaperFile.value) {
        setupError.value = 'Please upload an exam paper PDF.';
        analyseLoading.value = false;
        return;
      }
      const fd = new FormData();
      fd.append('class_id', String(selectedClass.value.id));
      fd.append('file', examPaperFile.value);
      const paperRes = await api.uploadGradingExamPaper(fd);
      if (!paperRes.success) throw new Error('Failed to upload exam paper');
      resolvedExamPaperId = paperRes.exam_paper.id;
      existingExamPapers.value.push(paperRes.exam_paper);
    }

    step.value = 'analysing';

    // Build analyse form
    const fd = new FormData();
    fd.append('exam_paper_id', String(resolvedExamPaperId));
    fd.append('title', examTitle.value.trim());
    fd.append('reasoning', String(reasoning.value));
    if (preferences.value.trim()) fd.append('preferences', preferences.value.trim());
    if (styleGuide.value.trim())  fd.append('style_guide', styleGuide.value.trim());
    if (selectedLessonIds.value.length > 0) {
      fd.append('lesson_file_ids', JSON.stringify(selectedLessonIds.value));
    }
    if (correctionFile.value) {
      fd.append('correction_pdf', correctionFile.value);
    }

    await api.streamGradingAnalyse(fd, ({ event, data }) => {
      if (event === 'thinking')   analyseThinking.value  += data;
      if (event === 'content')    analyseContent.value   += data;
      if (event === 'tool_call') {
        try { analyseToolEvents.value.push({ type: 'tool_call', ...JSON.parse(data) }); } catch {}
      }
      if (event === 'tool_result') {
        try { analyseToolEvents.value.push({ type: 'tool_result', ...JSON.parse(data) }); } catch {}
      }
      if (event === 'blueprint_saved') {
        try {
          const payload = JSON.parse(data);
          blueprintId.value = payload.blueprint_id;
          blueprintReady.value = true;
        } catch {}
      }
      if (event === 'blueprint_ready') {
        blueprintReady.value = true;
      }
    });

    analyseLoading.value = false;

  } catch (err) {
    analyseLoading.value = false;
    analyseError.value = err.message || 'Analysis failed';
    if (step.value !== 'analysing') step.value = 'analysing';
  }
}

async function useExistingBlueprint() {
  setupError.value = '';
  if (!selectedBlueprintId.value) { setupError.value = 'Please select a blueprint.'; return; }
  if (!examTitle.value.trim())    { setupError.value = 'Please enter an exam title.'; return; }
  blueprintId.value = selectedBlueprintId.value;
  await proceedToStudents();
}

async function proceedToStudents() {
  step.value = 'students';
  // Make sure students + exam types are loaded
  if (students.value.length === 0) await loadStudents(selectedClass.value.id);
  if (examTypes.value.length === 0) await loadExamTypes(selectedClass.value.id);
}

// ── Students & Exam Types ────────────────────────────────────────
const students        = ref([]);
const loadingStudents = ref(false);
const examTypes       = ref([]);
const loadingExamTypes = ref(false);
const selectedExamTypeId = ref(null);
const studentFiles    = reactive({});   // { [studentId]: File }
const studentInputRefs = reactive({});  // { [studentId]: HTMLInputElement }
const batchError      = ref('');
const batchLoading    = ref(false);

const assignedCount = computed(() => Object.values(studentFiles).filter(Boolean).length);

const matchedExamType = computed(() => {
  if (selectedExamTypeId.value !== null) return null;
  return examTypes.value.find(
    et => et.name.toLowerCase() === examTitle.value.trim().toLowerCase()
  ) || null;
});

async function loadStudents(classId) {
  loadingStudents.value = true;
  try {
    const res = await api.getStudents(classId);
    if (res.success) students.value = res.students || [];
  } catch (err) {
    console.error('loadStudents:', err);
  } finally {
    loadingStudents.value = false;
  }
}

async function loadExamTypes(classId) {
  loadingExamTypes.value = true;
  try {
    const res = await api.getExamTypes(classId);
    if (res.success) examTypes.value = res.exam_types || [];
  } catch (err) {
    console.error('loadExamTypes:', err);
  } finally {
    loadingExamTypes.value = false;
  }
}

function triggerStudentFileInput(studentId) {
  if (studentInputRefs[studentId]) {
    studentInputRefs[studentId].click();
  }
}

function handleStudentFile(studentId, event) {
  const file = event.target.files[0];
  if (file) {
    studentFiles[studentId] = file;
  }
  event.target.value = '';
}

function clearAllFiles() {
  students.value.forEach(s => { delete studentFiles[s.id]; });
}

async function startGrading() {
  batchError.value = '';
  if (assignedCount.value === 0) { batchError.value = 'Upload at least one student PDF.'; return; }

  batchLoading.value = true;
  try {
    // Resolve exam type ID
    let examTypeId = selectedExamTypeId.value;
    if (examTypeId === null) {
      if (matchedExamType.value) {
        examTypeId = matchedExamType.value.id;
      } else {
        // Auto-create the exam type with examTitle and selected category
        const createRes = await api.createExamType(
          selectedClass.value.id,
          examTitle.value.trim(),
          examCategory.value,
          true
        );
        if (!createRes.success) throw new Error('Failed to create exam type');
        examTypes.value.push(createRes.exam_type);
        examTypeId = createRes.exam_type.id;
      }
    }

    // Build multipart form
    const fd = new FormData();
    fd.append('blueprint_id', String(blueprintId.value));
    fd.append('class_id', String(selectedClass.value.id));
    fd.append('exam_type_id', String(examTypeId));

    // Only include students that have files, in student order
    const assignedStudents = students.value.filter(s => studentFiles[s.id]);
    assignedStudents.forEach(s => {
      fd.append('student_ids', String(s.id));
      fd.append('exam_pdfs', studentFiles[s.id], studentFiles[s.id].name);
    });

    const res = await api.startGradingBatch(fd);
    if (!res.success) throw new Error('Failed to start grading batch');

    // Initialise queue state
    batchId.value = res.batch_id;
    sessions.value = res.sessions.map(s => ({ ...s, status: 'pending', normalised_grade: null }));
    step.value = 'grading';

    // Start first session
    if (res.first_session_id) {
      await runSession(res.first_session_id);
    }
  } catch (err) {
    batchError.value = err.message || 'Failed to start grading';
  } finally {
    batchLoading.value = false;
  }
}

// ── Phase 2 — Grading SSE ────────────────────────────────────────
const batchId          = ref(null);
const sessions         = ref([]);
const currentSessionId = ref(null);
const currentStudentName = ref('');
const questionResults  = ref([]);
const gradingBreakdown = ref([]);
const gradingThinking  = ref('');
const gradingContent   = ref('');
const gradingToolEvents = ref([]);
const gradingError     = ref('');
const gradingLoading   = ref(false);
const isReviewing      = ref(false);
const reviewDecisions  = reactive({});
const reviewSubmitting = ref(false);

const completedCount = computed(() =>
  sessions.value.filter(s => s.status === 'approved' || s.status === 'cancelled').length
);

const reviewTotal = computed(() =>
  questionResults.value.reduce((sum, qr) => {
    const v = reviewDecisions[qr.question_number];
    return sum + (typeof v === 'number' ? v : qr.awarded_points);
  }, 0)
);

const reviewMax = computed(() =>
  questionResults.value.reduce((sum, qr) => sum + qr.max_points, 0)
);

const normalisedReview = computed(() => {
  if (reviewMax.value === 0) return 0;
  return Math.min(20, Math.max(0, (reviewTotal.value / reviewMax.value) * 20));
});

const batchAverage = computed(() => {
  const graded = sessions.value.filter(s => s.normalised_grade != null);
  if (graded.length === 0) return '—';
  const avg = graded.reduce((a, b) => a + b.normalised_grade, 0) / graded.length;
  return avg.toFixed(2);
});

function getGradeClass(value) {
  if (value >= 16) return 'bg-emerald-100 text-emerald-800';
  if (value >= 12) return 'bg-blue-100 text-blue-800';
  if (value >= 10) return 'bg-amber-100 text-amber-800';
  return 'bg-red-100 text-red-800';
}

async function runSession(sessionId, forceRestart = false) {
  // Reset per-student state
  currentSessionId.value   = sessionId;
  questionResults.value    = [];
  gradingBreakdown.value   = [];
  gradingThinking.value    = '';
  gradingContent.value     = '';
  gradingToolEvents.value  = [];
  gradingError.value       = '';
  isReviewing.value        = false;
  gradingLoading.value     = true;
  Object.keys(reviewDecisions).forEach(k => delete reviewDecisions[k]);

  // Set student name
  const sess = sessions.value.find(s => s.session_id === sessionId);
  currentStudentName.value = sess?.student_name || '';

  // Mark as reviewing in local state during stream
  updateSessionStatus(sessionId, 'reviewing');

  try {
    await api.streamGradingSession(sessionId, ({ event, data }) => {
      if (event === 'thinking')    gradingThinking.value  += data;
      if (event === 'content')     gradingContent.value   += data;
      if (event === 'tool_call') {
        try { gradingToolEvents.value.push({ type: 'tool_call', ...JSON.parse(data) }); } catch {}
      }
      if (event === 'tool_result') {
        try { gradingToolEvents.value.push({ type: 'tool_result', ...JSON.parse(data) }); } catch {}
      }
      if (event === 'question_result') {
        try {
          const qr = JSON.parse(data);
          const existing = questionResults.value.findIndex(q => q.question_number === qr.question_number);
          if (existing >= 0) {
            questionResults.value[existing] = qr;
          } else {
            questionResults.value.push(qr);
          }
        } catch {}
      }
      if (event === 'interrupt') {
        try {
          const payload = JSON.parse(data);
          gradingBreakdown.value = payload.breakdown || questionResults.value;
          // Set review decisions from agent's values
          gradingBreakdown.value.forEach(qr => {
            reviewDecisions[qr.question_number] = qr.awarded_points;
          });
          // Sync question results to breakdown for completeness
          if (gradingBreakdown.value.length > 0) {
            questionResults.value = [...gradingBreakdown.value];
          }
          isReviewing.value = true;
          gradingLoading.value = false;
          updateSessionStatus(sessionId, 'reviewing');
        } catch {}
      }
    }, { forceRestart });

    // Stream ended without interrupt (shouldn't happen normally)
    if (!isReviewing.value) {
      gradingLoading.value = false;
    }
  } catch (err) {
    gradingLoading.value = false;
    gradingError.value   = err.message || 'Grading stream failed';
    updateSessionStatus(sessionId, 'pending');
  }
}

function updateSessionStatus(sessionId, status, extra = {}) {
  const idx = sessions.value.findIndex(s => s.session_id === sessionId);
  if (idx >= 0) {
    sessions.value[idx] = { ...sessions.value[idx], status, ...extra };
  }
}

async function approveSession() {
  if (reviewSubmitting.value) return;
  reviewSubmitting.value = true;
  try {
    const decisions = questionResults.value.map(qr => ({
      question_number: qr.question_number,
      awarded_points: typeof reviewDecisions[qr.question_number] === 'number'
        ? reviewDecisions[qr.question_number]
        : qr.awarded_points,
    }));

    const res = await api.reviewGradingSession(currentSessionId.value, {
      action: 'approve',
      decisions,
    });

    if (res.success) {
      updateSessionStatus(currentSessionId.value, 'approved', {
        normalised_grade: res.normalised_grade,
      });
      isReviewing.value = false;

      if (res.next_session_id) {
        await runSession(res.next_session_id);
      } else {
        step.value = 'complete';
      }
    }
  } catch (err) {
    gradingError.value = err.message || 'Failed to save review';
  } finally {
    reviewSubmitting.value = false;
  }
}

async function cancelSession() {
  if (reviewSubmitting.value) return;
  reviewSubmitting.value = true;
  try {
    const res = await api.reviewGradingSession(currentSessionId.value, {
      action: 'cancel',
      decisions: [],
    });

    if (res.success) {
      updateSessionStatus(currentSessionId.value, 'cancelled');
      isReviewing.value = false;

      if (res.next_session_id) {
        await runSession(res.next_session_id);
      } else {
        step.value = 'complete';
      }
    }
  } catch (err) {
    gradingError.value = err.message || 'Failed to cancel session';
  } finally {
    reviewSubmitting.value = false;
  }
}

// ── Reset / start-over ────────────────────────────────────────────
function startOver() {
  selectedClass.value      = null;
  step.value               = 'classes';
  setupMode.value          = 'new';
  examTitle.value          = '';
  examCategory.value       = 'EXERCISE';
  examPaperFile.value      = null;
  selectedExamPaperId.value = null;
  existingExamPapers.value = [];
  correctionFile.value     = null;
  preferences.value        = '';
  styleGuide.value         = '';
  selectedLessonIds.value  = [];
  classLessons.value       = [];
  blueprints.value         = [];
  selectedBlueprintId.value = null;
  blueprintId.value        = null;
  blueprintReady.value     = false;
  analyseThinking.value    = '';
  analyseContent.value     = '';
  analyseToolEvents.value  = [];
  analyseError.value       = '';
  setupError.value         = '';
  students.value           = [];
  examTypes.value          = [];
  selectedExamTypeId.value = null;
  Object.keys(studentFiles).forEach(k => delete studentFiles[k]);
  batchId.value            = null;
  sessions.value           = [];
  currentSessionId.value   = null;
  questionResults.value    = [];
  gradingError.value       = '';
  isReviewing.value        = false;
}

// ── Helpers ───────────────────────────────────────────────────────
function formatSize(bytes) {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(str) {
  if (!str) return '';
  try {
    return new Date(str).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return str; }
}

function truncateName(name, max) {
  return name.length > max ? name.slice(0, max) + '…' : name;
}

function adjustColor(color, percent) {
  if (!color) return '#3b82f6';
  const num = parseInt(color.replace('#', ''), 16);
  const amt = Math.round(2.55 * percent);
  const R = Math.max(0, Math.min(255, (num >> 16) + amt));
  const G = Math.max(0, Math.min(255, ((num >> 8) & 0x00ff) + amt));
  const R2 = R.toString(16).padStart(2, '0');
  const G2 = G.toString(16).padStart(2, '0');
  const B = Math.max(0, Math.min(255, (num & 0x0000ff) + amt));
  const B2 = B.toString(16).padStart(2, '0');
  return `#${R2}${G2}${B2}`;
}

// ── Mount: handle ?classId query param ────────────────────────────
onMounted(async () => {
  await loadClasses();
  const qClassId = route.query.classId ? parseInt(route.query.classId) : null;
  if (qClassId) {
    const found = classes.value.find(c => c.id === qClassId);
    if (found) await selectClass(found);
  }
});
</script>
