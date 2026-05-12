<template>
  <div class="h-full overflow-y-auto custom-scrollbar bg-grey-50">
    <div v-if="pageLoading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
    </div>

    <template v-else-if="workspace.mode === 'classes'">
      <div class="bg-white border-b border-grey-200 px-8 py-6">
        <h1 class="text-3xl font-bold text-grey-900 mb-1">Grading Agent</h1>
        <p class="text-grey-600">Choose a class, prepare one active blueprint, mark the student papers you want to grade, then confirm the batch.</p>
      </div>

      <div class="p-8">
        <div v-if="classes.length === 0" class="bg-white rounded-2xl border border-grey-200 shadow-sm p-16 text-center">
          <AcademicCapIcon class="w-14 h-14 text-grey-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-grey-900 mb-2">No classes yet</h3>
          <p class="text-grey-600">Create a class first to start the grading workflow.</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          <article
            v-for="cls in classes"
            :key="cls.id"
            class="rounded-2xl border border-grey-200 bg-white shadow-sm overflow-hidden hover:shadow-md transition"
          >
            <div class="h-2" :style="{ backgroundColor: cls.color || '#3b82f6' }"></div>
            <div class="p-6 space-y-4">
              <div>
                <h2 class="text-lg font-semibold text-grey-900">{{ cls.name }}</h2>
                <p class="text-sm text-grey-600 mt-1">{{ cls.subject || 'No subject' }}</p>
              </div>

              <div class="flex flex-wrap gap-2 text-xs">
                <span class="px-2.5 py-1 rounded-full bg-grey-100 text-grey-700">{{ cls.school || 'School not set' }}</span>
                <span class="px-2.5 py-1 rounded-full bg-primary-50 text-primary-700">AI grading</span>
              </div>

              <div class="flex items-center gap-2">
                <button
                  @click="openClassWorkspace(cls.id)"
                  class="flex-1 px-4 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition"
                >
                  Open
                </button>
                <router-link
                  :to="`/class/${cls.id}/grades`"
                  class="px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
                >
                  Grades
                </router-link>
              </div>
            </div>
          </article>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="bg-white border-b border-grey-200 px-8 py-6">
        <div class="flex items-center gap-3 text-sm text-grey-500 mb-4">
          <button @click="goBackToClasses" class="hover:text-primary-600 transition flex items-center gap-1">
            <ChevronLeftIcon class="w-4 h-4" />
            Back to Classes
          </button>
          <span>/</span>
          <span class="text-grey-900 font-medium">Grading Session</span>
        </div>

        <div class="flex items-start justify-between gap-4">
          <div>
            <h1 class="text-3xl font-bold text-grey-900 mb-1">{{ activeClass?.name }}</h1>
            <p class="text-grey-600">{{ activeClass?.subject || 'No subject' }} · {{ students.length }} student{{ students.length !== 1 ? 's' : '' }}</p>
          </div>
          <router-link
            :to="activeClass ? `/class/${activeClass.id}/grades` : '/grading'"
            class="px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
          >
            Open Gradebook
          </router-link>
        </div>
      </div>

      <div class="p-8 space-y-6">
        <div v-if="workspace.loading" class="flex items-center justify-center h-64">
          <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
        </div>

        <template v-else>
          <div v-if="feedback.error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {{ feedback.error }}
          </div>

          <div v-if="feedback.success" class="rounded-xl border border-success-200 bg-success-50 px-4 py-3 text-sm text-success-800">
            {{ feedback.success }}
          </div>

          <section class="grid grid-cols-1 xl:grid-cols-[1.1fr_0.9fr] gap-6 items-start">
            <div class="bg-white rounded-2xl border border-grey-200 shadow-sm p-6 space-y-6">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h2 class="text-xl font-semibold text-grey-900">Blueprint Setup</h2>
                  <p class="text-sm text-grey-600 mt-1">Keep one active exam paper and one active blueprint for this grading run.</p>
                </div>
                <label class="flex items-center gap-3 rounded-xl border border-primary-200 bg-primary-50 px-3 py-2">
                  <div>
                    <div class="text-xs font-semibold uppercase tracking-wider text-primary-700">Reasoning</div>
                    <div class="text-xs text-primary-700">{{ sessionForm.reasoning ? 'On' : 'Off' }}</div>
                  </div>
                  <button
                    type="button"
                    @click="sessionForm.reasoning = !sessionForm.reasoning"
                    class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
                    :class="sessionForm.reasoning ? 'bg-primary-500' : 'bg-grey-300'"
                  >
                    <span
                      class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
                      :class="sessionForm.reasoning ? 'translate-x-6' : 'translate-x-1'"
                    />
                  </button>
                </label>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-grey-700 mb-2">Exam Title *</label>
                  <input
                    v-model="sessionForm.title"
                    type="text"
                    class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Midterm 1"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-grey-700 mb-2">Creator Agent Exam</label>
                  <select
                    v-model="sessionForm.creatorSessionId"
                    class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
                    @change="applyCreatorSession"
                  >
                    <option :value="null">None</option>
                    <option v-for="session in creatorSessions" :key="session.session_id" :value="session.session_id">
                      {{ session.title }}
                    </option>
                  </select>
                </div>
              </div>

              <div class="rounded-xl border border-grey-200 bg-grey-50/70 p-4">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <div class="text-sm font-semibold text-grey-900">Current Blueprint</div>
                    <p v-if="selectedBlueprint" class="text-sm text-grey-700 mt-1">{{ selectedBlueprint.title }}</p>
                    <p v-if="selectedBlueprint" class="text-xs text-grey-500 mt-1">Created {{ formatDateTime(selectedBlueprint.created_at) }}</p>
                    <p v-else class="text-sm text-grey-500 mt-1">No blueprint selected yet.</p>
                  </div>
                  <span
                    class="text-xs px-2.5 py-1 rounded-full font-medium"
                    :class="blueprintConfirmed ? 'bg-success-50 text-success-700' : (selectedBlueprint ? 'bg-amber-50 text-amber-700' : 'bg-grey-100 text-grey-600')"
                  >
                    {{ blueprintConfirmed ? 'Confirmed' : (selectedBlueprint ? 'Needs confirmation' : 'Missing') }}
                  </span>
                </div>

                <div class="flex flex-wrap items-center gap-3 mt-4">
                  <button
                    v-if="selectedBlueprint && !blueprintConfirmed"
                    @click="confirmBlueprint"
                    class="px-4 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition"
                  >
                    Confirm Blueprint
                  </button>
                  <button
                    v-if="selectedBlueprint"
                    @click="prepareBlueprintRecreation"
                    class="px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
                  >
                    Recreate Blueprint
                  </button>
                  <button
                    v-if="selectedBlueprint"
                    @click="deleteSelectedBlueprint"
                    class="px-4 py-2.5 border border-red-200 text-red-600 rounded-lg font-medium hover:bg-red-50 transition"
                  >
                    Delete Blueprint
                  </button>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-3">
                  <label class="block text-sm font-medium text-grey-700">Exam Paper</label>
                  <div class="rounded-xl border border-grey-200 bg-grey-50/70 p-4">
                    <div class="text-sm font-semibold text-grey-900">Current file</div>
                    <p class="text-sm text-grey-700 mt-1">{{ activeExamPaper?.filename || 'No exam paper uploaded yet.' }}</p>
                    <p v-if="activeExamPaper" class="text-xs text-grey-500 mt-1">Uploaded {{ formatDateTime(activeExamPaper.created_at) }}</p>
                  </div>
                  <label
                    class="flex items-center justify-center rounded-xl border-2 border-dashed border-grey-300 bg-grey-50/70 px-4 py-6 cursor-pointer hover:border-primary-400 hover:bg-primary-50/40 transition"
                    :class="selectedBlueprint && !recreatingBlueprint ? 'opacity-60 cursor-not-allowed' : ''"
                  >
                    <input
                      type="file"
                      accept="application/pdf"
                      class="hidden"
                      :disabled="selectedBlueprint && !recreatingBlueprint"
                      @change="handleExamPaperFileChange"
                    />
                    <div class="text-center">
                      <DocumentArrowUpIcon class="w-8 h-8 text-grey-400 mx-auto mb-2" />
                      <p class="text-sm font-medium text-grey-700">{{ examPaperUploadLabel }}</p>
                      <p class="text-xs text-grey-500 mt-1">PDF only</p>
                    </div>
                  </label>
                  <button
                    v-if="examPaperUpload"
                    @click="uploadExamPaperForClass"
                    :disabled="uploadingExamPaper || (selectedBlueprint && !recreatingBlueprint)"
                    class="px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition disabled:opacity-50"
                  >
                    {{ uploadingExamPaper ? 'Uploading...' : (activeExamPaper ? 'Replace Exam Paper' : 'Upload Exam Paper') }}
                  </button>
                </div>

                <div class="space-y-3">
                  <label class="block text-sm font-medium text-grey-700">Correction Paper (Optional)</label>
                  <label
                    class="flex items-center justify-center rounded-xl border-2 border-dashed border-grey-300 bg-grey-50/70 px-4 py-6 cursor-pointer hover:border-primary-400 hover:bg-primary-50/40 transition"
                    :class="selectedBlueprint && !recreatingBlueprint ? 'opacity-60 cursor-not-allowed' : ''"
                  >
                    <input
                      type="file"
                      accept="application/pdf"
                      class="hidden"
                      :disabled="selectedBlueprint && !recreatingBlueprint"
                      @change="handleCorrectionFileChange"
                    />
                    <div class="text-center">
                      <DocumentArrowUpIcon class="w-8 h-8 text-grey-400 mx-auto mb-2" />
                      <p class="text-sm font-medium text-grey-700">{{ correctionFileLabel }}</p>
                      <p class="text-xs text-grey-500 mt-1">PDF only</p>
                    </div>
                  </label>
                </div>
              </div>

              <div>
                <div class="flex items-center justify-between gap-3 mb-2">
                  <label class="block text-sm font-medium text-grey-700">Lesson PDFs</label>
                  <span class="text-xs text-grey-500">{{ sessionForm.lessonFileIds.length }} selected</span>
                </div>
                <div class="max-h-60 overflow-y-auto custom-scrollbar border border-grey-200 rounded-xl p-3 bg-grey-50/60 space-y-2">
                  <label
                    v-for="lesson in classLessons"
                    :key="lesson.id"
                    class="flex items-center gap-3 rounded-xl border px-3 py-3 transition"
                    :class="sessionForm.lessonFileIds.includes(lesson.id) ? 'border-primary-300 bg-primary-50' : 'border-grey-200 bg-white'"
                  >
                    <input
                      v-model="sessionForm.lessonFileIds"
                      :value="lesson.id"
                      type="checkbox"
                      :disabled="(selectedBlueprint && !recreatingBlueprint) || !lesson.embedded"
                      class="h-4 w-4 rounded border-grey-300 text-primary-600 focus:ring-primary-500"
                    />
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-medium text-grey-900 truncate">{{ lesson.name || lesson.filename }}</p>
                      <p class="text-xs text-grey-500">{{ lesson.embedded ? 'Embedded' : 'Embedding pending' }}</p>
                    </div>
                  </label>

                  <div v-if="classLessons.length === 0" class="text-sm text-grey-500 text-center py-6">
                    No lesson files found for this class.
                  </div>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-grey-700 mb-2">Grading Preferences</label>
                  <textarea
                    v-model="sessionForm.preferences"
                    rows="5"
                    class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                    placeholder="When to deduct points, common penalties, strictness..."
                  ></textarea>
                </div>

                <div>
                  <label class="block text-sm font-medium text-grey-700 mb-2">Style Guide</label>
                  <textarea
                    v-model="sessionForm.styleGuide"
                    rows="5"
                    class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                    placeholder="Math steps, essay structure, expected notation..."
                  ></textarea>
                </div>
              </div>

              <div class="flex items-center gap-3">
                <button
                  @click="analyseBlueprint"
                  :disabled="analysis.running || (selectedBlueprint && !recreatingBlueprint)"
                  class="px-5 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50"
                >
                  {{ analysis.running ? 'Analysing...' : (recreatingBlueprint ? 'Recreate Blueprint' : 'Generate Blueprint') }}
                </button>
                <span v-if="selectedBlueprint && !recreatingBlueprint" class="text-sm text-success-700 font-medium">
                  Active blueprint ready
                </span>
              </div>
            </div>

            <div class="space-y-6">
              <div class="bg-white rounded-2xl border border-grey-200 shadow-sm p-6">
                <div class="flex items-start justify-between gap-4 mb-4">
                  <div>
                    <h2 class="text-xl font-semibold text-grey-900">Batch Progress</h2>
                    <p class="text-sm text-grey-600 mt-1">Confirm only the students you marked individually after uploading their papers.</p>
                  </div>
                  <span
                    class="text-xs px-2.5 py-1 rounded-full font-medium"
                    :class="blueprintConfirmed ? 'bg-success-50 text-success-700' : 'bg-amber-50 text-amber-700'"
                  >
                    {{ blueprintConfirmed ? 'Blueprint confirmed' : 'Blueprint not confirmed' }}
                  </span>
                </div>

                <div class="grid grid-cols-2 gap-3 mb-4">
                  <div class="rounded-xl bg-grey-50 border border-grey-200 p-4">
                    <div class="text-xs text-grey-500">Students</div>
                    <div class="text-2xl font-bold text-grey-900">{{ students.length }}</div>
                  </div>
                  <div class="rounded-xl bg-grey-50 border border-grey-200 p-4">
                    <div class="text-xs text-grey-500">Marked Students</div>
                    <div class="text-2xl font-bold text-grey-900">{{ markedStudentCount }}</div>
                  </div>
                  <div class="rounded-xl bg-grey-50 border border-grey-200 p-4">
                    <div class="text-xs text-grey-500">Approved</div>
                    <div class="text-2xl font-bold text-grey-900">{{ approvedCount }}</div>
                  </div>
                  <div class="rounded-xl bg-grey-50 border border-grey-200 p-4">
                    <div class="text-xs text-grey-500">Current Status</div>
                    <div class="text-sm font-semibold text-grey-900 mt-1">{{ currentBatchStatus }}</div>
                  </div>
                </div>

                <button
                  @click="startBatch"
                  :disabled="startingBatch || !canStartBatch"
                  class="w-full px-5 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50"
                >
                  {{ startingBatch ? 'Confirming...' : `Confirm ${markedStudentCount} Marked Grade${markedStudentCount !== 1 ? 's' : ''}` }}
                </button>
              </div>

              <div class="bg-white rounded-2xl border border-grey-200 shadow-sm p-6">
                <h2 class="text-xl font-semibold text-grey-900 mb-3">Analysis Stream</h2>
                <div v-if="!analysis.narrative && !analysis.thinking && !analysis.running" class="text-sm text-grey-500">
                  Blueprint progress will appear here.
                </div>
                <div v-else class="space-y-4">
                  <div v-if="analysis.narrative" class="rounded-xl border border-grey-200 bg-grey-50/70 p-4 text-sm text-grey-700 whitespace-pre-wrap max-h-48 overflow-y-auto custom-scrollbar">
                    {{ analysis.narrative }}
                  </div>
                  <details v-if="analysis.thinking" class="rounded-xl border border-primary-200 bg-primary-50 p-4">
                    <summary class="cursor-pointer text-sm font-medium text-primary-700">Reasoning Trace</summary>
                    <div class="mt-3 text-sm text-primary-800 whitespace-pre-wrap max-h-40 overflow-y-auto custom-scrollbar">
                      {{ analysis.thinking }}
                    </div>
                  </details>
                </div>
              </div>
            </div>
          </section>

          <section class="grid grid-cols-1 xl:grid-cols-[0.85fr_1.15fr] gap-6 items-start">
            <div class="bg-white rounded-2xl border border-grey-200 shadow-sm overflow-hidden">
              <div class="px-6 py-5 border-b border-grey-200 flex items-start justify-between gap-3">
                <div>
                  <h2 class="text-xl font-semibold text-grey-900">Students</h2>
                  <p class="text-sm text-grey-600 mt-1">Attach each student paper before starting the queue.</p>
                </div>
                <span class="text-sm text-grey-500">{{ students.length }} total</span>
              </div>

              <div v-if="students.length === 0" class="p-16 text-center">
                <UserGroupIcon class="w-14 h-14 text-grey-300 mx-auto mb-4" />
                <h3 class="text-lg font-medium text-grey-900 mb-2">No students in this class</h3>
                <p class="text-grey-600">Add students first, then come back to grade their work.</p>
              </div>

              <div v-else class="divide-y divide-grey-100">
                <button
                  v-for="student in students"
                  :key="student.id"
                  @click="activeStudentId = student.id"
                  class="w-full px-6 py-4 text-left hover:bg-grey-50 transition"
                  :class="activeStudentId === student.id ? 'bg-primary-50/70' : ''"
                >
                  <div class="flex items-center justify-between gap-4">
                    <div class="flex items-center gap-3 min-w-0">
                      <div class="w-9 h-9 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
                        {{ student.name.charAt(0).toUpperCase() }}
                      </div>
                      <div class="min-w-0">
                        <p class="font-medium text-grey-900 truncate">{{ student.name }}</p>
                        <p class="text-sm text-grey-500 truncate">{{ student.email }}</p>
                      </div>
                    </div>
                    <span class="text-xs px-2.5 py-1 rounded-full font-medium flex-shrink-0" :class="studentPillClass(student.id)">
                      {{ studentStatus(student.id) }}
                    </span>
                  </div>
                </button>
              </div>
            </div>

            <div class="space-y-6">
              <div class="bg-white rounded-2xl border border-grey-200 shadow-sm p-6">
                <template v-if="selectedStudent">
                  <div class="flex items-start justify-between gap-4 mb-5">
                    <div>
                      <h2 class="text-xl font-semibold text-grey-900">{{ selectedStudent.name }}</h2>
                      <p class="text-sm text-grey-600 mt-1">{{ selectedStudent.email }}</p>
                    </div>
                    <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="studentPillClass(selectedStudent.id)">
                      {{ studentStatus(selectedStudent.id) }}
                    </span>
                  </div>

                  <label class="block text-sm font-medium text-grey-700 mb-2">Student Work PDF</label>
                  <label class="flex items-center justify-center rounded-xl border-2 border-dashed border-grey-300 bg-grey-50/70 px-4 py-8 cursor-pointer hover:border-primary-400 hover:bg-primary-50/40 transition">
                    <input type="file" accept="application/pdf" class="hidden" @change="handleStudentFileChange($event, selectedStudent.id)" />
                    <div class="text-center">
                      <DocumentArrowUpIcon class="w-8 h-8 text-grey-400 mx-auto mb-2" />
                      <p class="text-sm font-medium text-grey-700">{{ studentFileLabel(selectedStudent.id) }}</p>
                      <p class="text-xs text-grey-500 mt-1">PDF only</p>
                    </div>
                  </label>

                  <div class="mt-5">
                    <label class="block text-sm font-medium text-grey-700 mb-2">Teacher Notes for This Paper</label>
                    <textarea
                      v-model="studentEntries[selectedStudent.id].notes"
                      rows="4"
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                      placeholder="Special expectations, context, or human-in-the-loop notes for this student's review..."
                    ></textarea>
                  </div>

                  <div class="flex items-center gap-3 mt-5">
                    <button
                      @click="toggleStudentMarked(selectedStudent.id)"
                      :disabled="!studentEntries[selectedStudent.id].file"
                      class="px-4 py-2.5 rounded-lg font-medium transition disabled:opacity-50"
                      :class="studentEntries[selectedStudent.id].marked ? 'bg-success-600 text-white hover:bg-success-700' : 'bg-primary-600 text-white hover:bg-primary-700'"
                    >
                      {{ studentEntries[selectedStudent.id].marked ? 'Marked for Batch' : 'Mark for Grading' }}
                    </button>
                    <button
                      @click="clearStudentEntry(selectedStudent.id)"
                      class="px-4 py-2.5 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition"
                    >
                      Clear
                    </button>
                  </div>
                </template>

                <div v-else class="py-12 text-center">
                  <UserGroupIcon class="w-14 h-14 text-grey-300 mx-auto mb-4" />
                  <h3 class="text-lg font-medium text-grey-900 mb-2">Select a student</h3>
                  <p class="text-grey-600">Open a student from the list to attach their paper.</p>
                </div>
              </div>

              <div class="bg-white rounded-2xl border border-grey-200 shadow-sm p-6">
                <div class="flex items-start justify-between gap-4 mb-4">
                  <div>
                    <h2 class="text-xl font-semibold text-grey-900">Current Review</h2>
                    <p class="text-sm text-grey-600 mt-1">{{ currentStudentName || 'Queue not started yet' }}</p>
                  </div>
                  <button
                    v-if="batch.currentSessionId && !batch.awaitingReview"
                    @click="restartCurrentSession"
                    class="px-3 py-2 border border-grey-300 text-grey-700 rounded-lg text-sm font-medium hover:bg-grey-50 transition"
                  >
                    Restart
                  </button>
                </div>

                <div v-if="currentStudentNote" class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 mb-4 whitespace-pre-wrap">
                  {{ currentStudentNote }}
                </div>

                <div v-if="batch.narrative" class="rounded-xl border border-grey-200 bg-grey-50/70 p-4 text-sm text-grey-700 whitespace-pre-wrap max-h-40 overflow-y-auto custom-scrollbar mb-4">
                  {{ batch.narrative }}
                </div>

                <details v-if="batch.thinking" class="rounded-xl border border-primary-200 bg-primary-50 p-4 mb-4">
                  <summary class="cursor-pointer text-sm font-medium text-primary-700">Reasoning Trace</summary>
                  <div class="mt-3 text-sm text-primary-800 whitespace-pre-wrap max-h-40 overflow-y-auto custom-scrollbar">
                    {{ batch.thinking }}
                  </div>
                </details>

                <div v-if="batch.breakdown.length > 0" class="space-y-3">
                  <article
                    v-for="question in batch.breakdown"
                    :key="question.question_number"
                    class="rounded-xl border border-grey-200 bg-grey-50/60 p-4"
                  >
                    <div class="flex items-start justify-between gap-4 mb-3">
                      <div>
                        <h3 class="font-semibold text-grey-900">{{ question.label || `Q${question.question_number}` }}</h3>
                        <p class="text-xs text-grey-500 mt-1">Max {{ formatPoints(question.max_points) }}</p>
                      </div>
                      <input
                        v-model.number="question.awarded_points"
                        type="number"
                        min="0"
                        :max="question.max_points"
                        step="0.25"
                        class="w-24 px-3 py-2 border border-grey-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <p class="text-sm text-grey-700 whitespace-pre-wrap">{{ question.reasoning }}</p>
                  </article>

                  <div class="flex items-center gap-3 pt-2">
                    <button
                      @click="submitReview('approve')"
                      :disabled="batch.reviewSubmitting"
                      class="px-5 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50"
                    >
                      {{ batch.reviewSubmitting ? 'Submitting...' : 'Approve and Continue' }}
                    </button>
                    <button
                      @click="submitReview('cancel')"
                      :disabled="batch.reviewSubmitting"
                      class="px-5 py-3 border border-red-200 text-red-600 rounded-lg font-medium hover:bg-red-50 transition disabled:opacity-50"
                    >
                      Skip Student
                    </button>
                  </div>
                </div>

                <div v-else class="text-sm text-grey-500">
                  Question-level grading output will appear here once the queue starts.
                </div>
              </div>
            </div>
          </section>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute } from 'vue-router';
import {
  AcademicCapIcon,
  ChevronLeftIcon,
  DocumentArrowUpIcon,
  UserGroupIcon,
} from '@heroicons/vue/24/outline';
import api from '@/services/api';
import { useClassesStore } from '@/stores/classesStore';

const route = useRoute();
const classesStore = useClassesStore();

const pageLoading = ref(true);
const workspace = reactive({
  mode: 'classes',
  loading: false,
  classId: null,
});

const feedback = reactive({
  error: '',
  success: '',
});

const creatorSessions = ref([]);
const students = ref([]);
const classLessons = ref([]);
const examTypes = ref([]);
const examPapers = ref([]);
const blueprints = ref([]);
const activeStudentId = ref(null);

const examPaperUpload = ref(null);
const correctionFile = ref(null);
const uploadingExamPaper = ref(false);
const startingBatch = ref(false);
const blueprintConfirmed = ref(false);
const recreatingBlueprint = ref(false);

const sessionForm = reactive({
  title: '',
  creatorSessionId: null,
  selectedBlueprintId: null,
  examPaperId: null,
  lessonFileIds: [],
  preferences: '',
  styleGuide: '',
  reasoning: true,
});

const analysis = reactive({
  running: false,
  narrative: '',
  thinking: '',
});

const batch = reactive({
  batchId: null,
  currentSessionId: null,
  sessions: [],
  narrative: '',
  thinking: '',
  breakdown: [],
  awaitingReview: false,
  reviewSubmitting: false,
});

const studentEntries = reactive({});

const classes = computed(() => classesStore.classes);
const activeClass = computed(() => classes.value.find((cls) => cls.id === workspace.classId) || null);
const selectedStudent = computed(() => students.value.find((student) => student.id === activeStudentId.value) || null);
const selectedBlueprint = computed(() => blueprints.value.find((item) => item.id === selectedBlueprintIdNumber.value) || null);
const activeExamPaper = computed(() => examPapers.value[0] || null);
const selectedBlueprintIdNumber = computed(() => sessionForm.selectedBlueprintId == null ? null : Number(sessionForm.selectedBlueprintId));
const availableBlueprints = computed(() => {
  return blueprints.value
    .filter((item) => !item.deleted)
    .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
});
const uploadedStudentCount = computed(() => students.value.filter((student) => Boolean(studentEntries[student.id]?.file)).length);
const markedStudentCount = computed(() => students.value.filter((student) => Boolean(studentEntries[student.id]?.marked && studentEntries[student.id]?.file)).length);
const canStartBatch = computed(() => Boolean(selectedBlueprint.value && blueprintConfirmed.value && sessionForm.title.trim() && markedStudentCount.value > 0));
const approvedCount = computed(() => batch.sessions.filter((session) => session.status === 'approved').length);
const currentBatchStatus = computed(() => {
  if (startingBatch.value) return 'Creating queue';
  if (batch.reviewSubmitting) return 'Submitting review';
  if (batch.awaitingReview) return 'Waiting for teacher review';
  if (batch.currentSessionId) return 'Streaming current student';
  if (batch.batchId && approvedCount.value === batch.sessions.length) return 'Completed';
  return 'Idle';
});
const currentSession = computed(() => batch.sessions.find((session) => session.id === batch.currentSessionId) || null);
const currentStudentName = computed(() => currentSession.value?.student_name || '');
const currentStudentNote = computed(() => {
  const studentId = currentSession.value?.student_id;
  if (!studentId) return '';
  return String(studentEntries[studentId]?.notes || '').trim();
});
const examPaperUploadLabel = computed(() => examPaperUpload.value?.name || 'Choose an exam paper');
const correctionFileLabel = computed(() => correctionFile.value?.name || 'Choose a correction PDF');

function setFeedback(type, message) {
  feedback.error = type === 'error' ? message : '';
  feedback.success = type === 'success' ? message : '';
}

function clearFeedback() {
  feedback.error = '';
  feedback.success = '';
}

function ensureStudentEntry(studentId) {
  if (!(studentId in studentEntries)) {
    studentEntries[studentId] = {
      file: null,
      notes: '',
      marked: false,
    };
  }
}

function resetWorkspaceState() {
  students.value = [];
  classLessons.value = [];
  examTypes.value = [];
  examPapers.value = [];
  blueprints.value = [];
  activeStudentId.value = null;
  examPaperUpload.value = null;
  correctionFile.value = null;
  blueprintConfirmed.value = false;
  recreatingBlueprint.value = false;
  sessionForm.title = '';
  sessionForm.creatorSessionId = null;
  sessionForm.selectedBlueprintId = null;
  sessionForm.examPaperId = null;
  sessionForm.lessonFileIds = [];
  sessionForm.preferences = '';
  sessionForm.styleGuide = '';
  sessionForm.reasoning = true;
  analysis.running = false;
  analysis.narrative = '';
  analysis.thinking = '';
  batch.batchId = null;
  batch.currentSessionId = null;
  batch.sessions = [];
  batch.narrative = '';
  batch.thinking = '';
  batch.breakdown = [];
  batch.awaitingReview = false;
  batch.reviewSubmitting = false;
  Object.keys(studentEntries).forEach((key) => {
    delete studentEntries[key];
  });
}

async function bootstrapPage() {
  try {
    await Promise.all([
      classesStore.load(),
      loadCreatorSessions(),
    ]);

    const classIdFromQuery = Number(route.query.classId || 0);
    if (classIdFromQuery) {
      await openClassWorkspace(classIdFromQuery);
    }
  } finally {
    pageLoading.value = false;
  }
}

async function loadCreatorSessions() {
  try {
    const response = await api.listCreatorSessions({ limit: 100, offset: 0 });
    if (response.success) creatorSessions.value = response.sessions || [];
  } catch (error) {
    console.error('Failed to load creator sessions:', error);
  }
}

async function openClassWorkspace(classId) {
  workspace.mode = 'session';
  workspace.loading = true;
  workspace.classId = Number(classId);
  resetWorkspaceState();
  clearFeedback();

  try {
    const [studentsRes, lessonsRes, examTypesRes, papersRes, blueprintsRes] = await Promise.all([
      api.getStudents(classId),
      api.getLessons(classId, { limit: 100, refresh: true }),
      api.getExamTypes(classId),
      api.listExamPapers(classId),
      api.listGradingBlueprints(),
    ]);

    students.value = studentsRes.success ? (studentsRes.students || []) : [];
    classLessons.value = lessonsRes.success ? (lessonsRes.uploads || []) : [];
    examTypes.value = examTypesRes.success ? (examTypesRes.exam_types || []) : [];
    examPapers.value = papersRes.success ? (papersRes.exam_papers || []) : [];
    blueprints.value = blueprintsRes.success ? (blueprintsRes.blueprints || []) : [];

    students.value.forEach((student) => ensureStudentEntry(student.id));
    activeStudentId.value = students.value[0]?.id || null;
    const latestBlueprint = availableBlueprints.value[0] || null;
    if (latestBlueprint) {
      sessionForm.selectedBlueprintId = latestBlueprint.id;
      applyExistingBlueprint();
    }
    if (activeExamPaper.value) {
      sessionForm.examPaperId = activeExamPaper.value.id;
    }
  } catch (error) {
    setFeedback('error', error.message || 'Failed to load this class workspace.');
  } finally {
    workspace.loading = false;
  }
}

function goBackToClasses() {
  workspace.mode = 'classes';
  workspace.classId = null;
  resetWorkspaceState();
  clearFeedback();
}

async function applyCreatorSession() {
  if (!sessionForm.creatorSessionId) return;
  try {
    const response = await api.getCreatorSession(sessionForm.creatorSessionId);
    if (!response.success) return;
    const session = response.session;
    sessionForm.title = session?.title || sessionForm.title;
    sessionForm.lessonFileIds = Array.isArray(session?.doc_ids)
      ? session.doc_ids.filter((id) => classLessons.value.some((lesson) => lesson.id === id))
      : [];
    const notes = String(session?.preferences?.notes || '').trim();
    if (notes) sessionForm.preferences = notes;
  } catch (error) {
    setFeedback('error', error.message || 'Failed to load the selected creator session.');
  }
}

function applyExistingBlueprint() {
  const blueprint = selectedBlueprint.value;
  if (!blueprint) return;
  sessionForm.title = blueprint.title || sessionForm.title;
  sessionForm.lessonFileIds = Array.isArray(blueprint.lesson_doc_ids) ? [...blueprint.lesson_doc_ids] : [];
  sessionForm.preferences = blueprint.preferences || '';
  sessionForm.styleGuide = blueprint.style_guide || '';
  blueprintConfirmed.value = false;
  recreatingBlueprint.value = false;
}

function confirmBlueprint() {
  if (!selectedBlueprint.value) return;
  blueprintConfirmed.value = true;
  setFeedback('success', 'Blueprint confirmed for this grading run.');
}

function prepareBlueprintRecreation() {
  blueprintConfirmed.value = false;
  recreatingBlueprint.value = true;
  sessionForm.selectedBlueprintId = null;
  sessionForm.examPaperId = activeExamPaper.value?.id || null;
  setFeedback('success', 'Blueprint recreation mode enabled. Update the files or preferences, then generate a new blueprint.');
}

function handleExamPaperFileChange(event) {
  examPaperUpload.value = event.target.files?.[0] || null;
}

function handleCorrectionFileChange(event) {
  correctionFile.value = event.target.files?.[0] || null;
}

function handleStudentFileChange(event, studentId) {
  ensureStudentEntry(studentId);
  studentEntries[studentId].file = event.target.files?.[0] || null;
  if (!studentEntries[studentId].file) {
    studentEntries[studentId].marked = false;
  }
}

function studentFileLabel(studentId) {
  return studentEntries[studentId]?.file?.name || 'Attach the student paper';
}

function toggleStudentMarked(studentId) {
  ensureStudentEntry(studentId);
  if (!studentEntries[studentId].file) return;
  studentEntries[studentId].marked = !studentEntries[studentId].marked;
}

function clearStudentEntry(studentId) {
  ensureStudentEntry(studentId);
  studentEntries[studentId].file = null;
  studentEntries[studentId].notes = '';
  studentEntries[studentId].marked = false;
}

function studentStatus(studentId) {
  const queueSession = batch.sessions.find((session) => session.student_id === studentId);
  if (queueSession?.status === 'approved') return 'Approved';
  if (queueSession?.status === 'cancelled') return 'Skipped';
  if (queueSession?.id === batch.currentSessionId) return batch.awaitingReview ? 'Reviewing' : 'Grading';
  if (studentEntries[studentId]?.marked && studentEntries[studentId]?.file) return 'Marked';
  if (studentEntries[studentId]?.file) return 'Uploaded';
  return 'Pending';
}

function studentPillClass(studentId) {
  const status = studentStatus(studentId);
  if (status === 'Approved') return 'bg-success-50 text-success-700';
  if (status === 'Skipped') return 'bg-red-50 text-red-700';
  if (status === 'Reviewing' || status === 'Grading') return 'bg-primary-50 text-primary-700';
  if (status === 'Marked') return 'bg-blue-50 text-blue-700';
  if (status === 'Uploaded') return 'bg-violet-50 text-violet-700';
  return 'bg-grey-100 text-grey-600';
}

async function uploadExamPaperForClass() {
  if (!examPaperUpload.value || !workspace.classId) return;
  uploadingExamPaper.value = true;
  clearFeedback();

  try {
    const hadExistingPaper = Boolean(activeExamPaper.value);
    if (activeExamPaper.value) {
      await api.deleteExamPaper(activeExamPaper.value.id);
      examPapers.value = examPapers.value.filter((paper) => paper.id !== activeExamPaper.value.id);
      sessionForm.examPaperId = null;
    }

    const formData = new FormData();
    formData.append('class_id', String(workspace.classId));
    formData.append('file', examPaperUpload.value);

    const response = await api.uploadExamPaper(formData);
    if (response.success) {
      sessionForm.examPaperId = response.exam_paper.id;
      examPapers.value = [response.exam_paper];
      examPaperUpload.value = null;
      setFeedback('success', hadExistingPaper ? 'Exam paper replaced.' : (response.duplicate ? 'Exam paper already existed and was reused.' : 'Exam paper uploaded.'));
    }
  } catch (error) {
    setFeedback('error', error.message || 'Failed to upload the exam paper.');
  } finally {
    uploadingExamPaper.value = false;
  }
}

function parseSseJson(data, fallback = {}) {
  try {
    return JSON.parse(data);
  } catch {
    return fallback;
  }
}

async function analyseBlueprint() {
  if (sessionForm.selectedBlueprintId && !recreatingBlueprint.value) return;
  if (!sessionForm.title.trim()) {
    setFeedback('error', 'Please enter an exam title.');
    return;
  }
  if (!sessionForm.examPaperId) {
    setFeedback('error', 'Please choose or upload an exam paper.');
    return;
  }

  clearFeedback();
  analysis.running = true;
  analysis.narrative = '';
  analysis.thinking = '';

  try {
    const formData = new FormData();
    formData.append('exam_paper_id', String(sessionForm.examPaperId));
    formData.append('lesson_file_ids', JSON.stringify(sessionForm.lessonFileIds));
    formData.append('preferences', sessionForm.preferences || '');
    formData.append('style_guide', sessionForm.styleGuide || '');
    formData.append('title', sessionForm.title.trim());
    formData.append('reasoning', sessionForm.reasoning ? 'true' : 'false');
    if (correctionFile.value) formData.append('correction_pdf', correctionFile.value);

    await api.streamGradingAnalyse(formData, ({ event, data }) => {
      if (event === 'thinking') {
        analysis.thinking += data;
        return;
      }
      if (event === 'content') {
        analysis.narrative += data;
        return;
      }
      if (event === 'blueprint_saved') {
        const payload = parseSseJson(data);
        sessionForm.selectedBlueprintId = payload.blueprint_id || null;
        blueprintConfirmed.value = false;
        recreatingBlueprint.value = false;
        setFeedback('success', `Blueprint "${payload.title}" is ready.`);
      }
    });

    const refreshed = await api.listGradingBlueprints();
    if (refreshed.success) {
      blueprints.value = refreshed.blueprints || [];
      applyExistingBlueprint();
    }
  } catch (error) {
    setFeedback('error', error.message || 'Blueprint analysis failed.');
  } finally {
    analysis.running = false;
  }
}

async function deleteSelectedBlueprint() {
  if (!selectedBlueprint.value) return;
  try {
    await api.deleteGradingBlueprint(selectedBlueprint.value.id);
    blueprints.value = blueprints.value.filter((item) => item.id !== selectedBlueprint.value.id);
    sessionForm.selectedBlueprintId = null;
    blueprintConfirmed.value = false;
    recreatingBlueprint.value = false;
    setFeedback('success', 'Blueprint deleted.');
  } catch (error) {
    setFeedback('error', error.message || 'Failed to delete blueprint.');
  }
}

async function ensureExamType() {
  const title = sessionForm.title.trim();
  const normalized = title.toLowerCase();
  const existing = examTypes.value.find((item) => String(item.name || '').trim().toLowerCase() === normalized);
  if (existing) return existing;
  const response = await api.createExamType(workspace.classId, title);
  if (response.success) {
    examTypes.value.push(response.exam_type);
    return response.exam_type;
  }
  throw new Error('Failed to create the exam type.');
}

async function startBatch() {
  if (!canStartBatch.value || !selectedBlueprint.value) return;

  startingBatch.value = true;
  clearFeedback();

  try {
    const examType = await ensureExamType();
    const formData = new FormData();
    formData.append('blueprint_id', String(selectedBlueprint.value.id));
    formData.append('class_id', String(workspace.classId));
    formData.append('exam_type_id', String(examType.id));

    students.value.forEach((student) => {
      const entry = studentEntries[student.id];
      if (!entry?.file || !entry?.marked) return;
      formData.append('student_ids', String(student.id));
      formData.append('exam_pdfs', entry.file, entry.file.name);
      formData.append('student_notes', entry.notes || '');
    });

    const response = await api.startGradingBatch(formData);
    if (!response.success) return;

    batch.batchId = response.batch_id;
    batch.sessions = (response.sessions || []).map((session) => ({
      id: session.session_id,
      student_id: session.student_id,
      student_name: session.student_name,
      queue_position: session.queue_position,
      status: 'pending',
    }));

    setFeedback('success', 'Marked students confirmed. Streaming the first student now.');
    await streamSession(response.first_session_id);
  } catch (error) {
    setFeedback('error', error.message || 'Failed to start the grading queue.');
  } finally {
    startingBatch.value = false;
  }
}

function resetCurrentStreamState() {
  batch.narrative = '';
  batch.thinking = '';
  batch.breakdown = [];
  batch.awaitingReview = false;
}

async function streamSession(sessionId, forceRestart = false) {
  batch.currentSessionId = sessionId;
  resetCurrentStreamState();

  const current = batch.sessions.find((session) => session.id === sessionId);
  if (current) current.status = 'reviewing';

  try {
    await api.streamGradingSession(sessionId, ({ event, data }) => {
      if (event === 'thinking') {
        batch.thinking += data;
        return;
      }
      if (event === 'content') {
        batch.narrative += data;
        return;
      }
      if (event === 'interrupt') {
        const payload = parseSseJson(data);
        batch.breakdown = Array.isArray(payload.breakdown)
          ? payload.breakdown.map((item) => ({
              ...item,
              awarded_points: Number(item.awarded_points ?? 0),
              max_points: Number(item.max_points ?? 0),
            }))
          : [];
        batch.awaitingReview = true;
      }
    }, { forceRestart });
  } catch (error) {
    setFeedback('error', error.message || 'Failed while streaming the grading session.');
  }
}

async function restartCurrentSession() {
  if (!batch.currentSessionId) return;
  await streamSession(batch.currentSessionId, true);
}

async function submitReview(action) {
  if (!batch.currentSessionId) return;

  batch.reviewSubmitting = true;
  clearFeedback();

  try {
    const payload = {
      action,
      decisions: action === 'approve'
        ? batch.breakdown.map((question) => ({
            question_number: question.question_number,
            awarded_points: Number(question.awarded_points ?? 0),
          }))
        : [],
    };

    const response = await api.reviewGradingSession(batch.currentSessionId, payload);
    const current = batch.sessions.find((session) => session.id === batch.currentSessionId);
    if (current) current.status = action === 'approve' ? 'approved' : 'cancelled';

    batch.awaitingReview = false;

    if (response.next_session_id) {
      await streamSession(response.next_session_id);
    } else {
      batch.currentSessionId = null;
      setFeedback('success', action === 'approve' ? 'Batch completed and grades saved.' : 'Batch completed.');
    }
  } catch (error) {
    setFeedback('error', error.message || 'Failed to submit the teacher review.');
  } finally {
    batch.reviewSubmitting = false;
  }
}

function formatPoints(value) {
  const numeric = Number(value || 0);
  return Number.isInteger(numeric) ? numeric : numeric.toFixed(2);
}

function formatDateTime(value) {
  if (!value) return '-';
  return new Date(value).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

onMounted(bootstrapPage);
</script>
