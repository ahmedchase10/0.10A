<template>
  <div class="p-8 space-y-8">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-grey-900">Creator Agent</h1>
        <p class="text-grey-600 mt-1">Generate grounded exams from class lesson PDFs, preview them, then export them as PDF.</p>
      </div>
      <button
        v-if="selectedClassId && workspace.mode === 'idle'"
        @click="startNewSessionForClass"
        class="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-3 rounded-lg font-medium hover:from-primary-700 hover:to-primary-600 shadow-sm transition"
      >
        <PlusIcon class="w-5 h-5" />
        New Session
      </button>
    </div>

    <div v-if="loadingPage" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
    </div>

    <template v-else>
      <section v-if="!selectedClassId" class="space-y-6">
        <div class="bg-white rounded-2xl border border-grey-200 shadow-sm p-6">
          <div class="mb-6">
            <h2 class="text-xl font-semibold text-grey-900">Select a Class</h2>
            <p class="text-sm text-grey-600 mt-1">Choose a class to view past exam sessions or create a new one.</p>
          </div>
          
          <div v-if="classes.length === 0" class="text-center py-12 border-2 border-dashed border-grey-200 rounded-2xl">
            <h3 class="text-lg font-medium text-grey-900 mb-2">No classes yet</h3>
            <p class="text-grey-600">Create a class in the Dashboard to get started.</p>
          </div>
          
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <div
              v-for="cls in classes"
              :key="cls.id"
              @click="selectClass(cls.id)"
              class="cursor-pointer group relative bg-white rounded-2xl p-6 border transition-all duration-300 hover:-translate-y-1 hover:shadow-xl overflow-hidden"
              :style="{ borderColor: cls.color || '#3b82f6', boxShadow: `0 4px 20px ${cls.color || '#3b82f6'}20` }"
            >
              <div class="absolute top-0 right-0 w-32 h-32 transform translate-x-16 -translate-y-16 rounded-full opacity-10 transition-transform group-hover:scale-150 duration-700"
                   :style="{ background: `linear-gradient(135deg, ${cls.color || '#3b82f6'} 0%, ${adjustColor(cls.color || '#3b82f6', -15)} 100%)` }">
              </div>
              <div class="relative flex items-start justify-between z-10">
                <div class="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-sm mb-4"
                     :style="{ background: `linear-gradient(135deg, ${cls.color || '#3b82f6'} 0%, ${adjustColor(cls.color || '#3b82f6', -15)} 100%)` }">
                  {{ cls.name.charAt(0).toUpperCase() }}
                </div>
              </div>
              <div class="relative z-10">
                <h3 class="font-bold text-xl text-grey-900 group-hover:text-primary-600 transition-colors">{{ cls.name }}</h3>
                <p class="text-grey-500 text-sm mt-1">{{ cls.subject || 'No subject' }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section v-else-if="selectedClassId && workspace.mode === 'idle'" class="space-y-6">
        <div class="bg-white rounded-2xl border border-grey-200 shadow-sm p-6">
            <div class="flex items-start justify-between gap-4 mb-6">
              <div>
                <button @click="selectedClassId = null" class="flex items-center gap-2 text-sm text-grey-500 hover:text-grey-700 mb-2 transition">
                  <ChevronLeftIcon class="w-4 h-4" /> Back to Classes
                </button>
                <h2 class="text-xl font-semibold text-grey-900">Previous Sessions</h2>
                <p class="text-sm text-grey-600 mt-1">Reopen an exam generation session to preview, refine, or download it.</p>
              </div>
              <span class="text-sm text-grey-500">{{ filteredSessions.length }} session{{ filteredSessions.length !== 1 ? 's' : '' }}</span>
            </div>

            <div v-if="sessionsLoading" class="flex items-center justify-center py-16">
              <div class="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent"></div>
            </div>

            <div v-else-if="filteredSessions.length === 0" class="text-center py-16 border-2 border-dashed border-grey-200 rounded-2xl">
              <SparklesIcon class="w-14 h-14 text-grey-300 mx-auto mb-4" />
              <h3 class="text-lg font-medium text-grey-900 mb-2">No creator sessions yet</h3>
              <p class="text-grey-600 mb-6">Start a session to generate your first exam from lesson documents.</p>
              <button
                @click="startNewSessionForClass"
                class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition"
              >
                <PlusIcon class="w-4 h-4" />
                Create First Session
              </button>
            </div>

            <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <article
                v-for="session in filteredSessions"
                :key="session.session_id"
                class="rounded-xl border border-grey-200 bg-grey-50/70 overflow-hidden hover:shadow-md transition"
              >
                <div class="p-5 space-y-4">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <h3 class="font-semibold text-grey-900 truncate" :title="session.title">{{ session.title }}</h3>
                      <p class="text-xs text-grey-500 mt-1">{{ formatDate(session.created_at) }}</p>
                    </div>
                    <span
                      class="flex-shrink-0 text-xs px-2.5 py-1 rounded-full font-medium"
                      :class="session.has_exam ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
                    >
                      {{ session.has_exam ? 'Ready' : 'Pending' }}
                    </span>
                  </div>

                  <div class="space-y-2 text-sm text-grey-600">
                    <p>{{ session.doc_ids.length }} document{{ session.doc_ids.length !== 1 ? 's' : '' }}</p>
                    <p v-if="session.loop_count > 0">Evaluator revisions: {{ session.loop_count }}</p>
                    <p class="line-clamp-2">{{ summarizeDocNames(session.doc_ids) }}</p>
                  </div>

                  <div class="flex items-center gap-2">
                    <button
                      @click="openSession(session.session_id)"
                      class="flex-1 px-4 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition"
                    >
                      Open
                    </button>
                    <button
                      @click="deleteSession(session.session_id)"
                      class="px-4 py-2.5 border border-red-200 text-red-600 rounded-lg font-medium hover:bg-red-50 transition"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </article>
            </div>
          </div>
      </section>

      <section v-else class="grid grid-cols-1 xl:grid-cols-[0.95fr_1.05fr] gap-6 items-start">
        <div class="bg-white rounded-2xl border border-grey-200 shadow-sm overflow-hidden">
          <div class="flex items-center justify-between gap-4 px-6 py-5 border-b border-grey-200">
            <div class="min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <button
                  @click="closeWorkspace"
                  class="p-1.5 rounded-lg hover:bg-grey-100 transition text-grey-500"
                  title="Back to sessions"
                >
                  <ChevronLeftIcon class="w-4 h-4" />
                </button>
                <h2 class="text-xl font-semibold text-grey-900 truncate">
                  {{ workspace.mode === 'draft' ? draft.title || 'New Session' : (activeSession?.title || 'Session') }}
                </h2>
              </div>
              <p class="text-sm text-grey-600">
                {{ workspace.mode === 'draft'
                  ? 'Configure the first generation request for this exam session.'
                  : 'Refine the saved session or export the latest generated exam.' }}
              </p>
            </div>

            <label class="flex items-center gap-2 cursor-pointer flex-shrink-0">
              <span class="text-sm text-grey-600">Think</span>
              <div
                class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
                :class="stream.reasoning ? 'bg-primary-500' : 'bg-grey-200'"
                @click="stream.reasoning = !stream.reasoning"
              >
                <span
                  class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
                  :class="stream.reasoning ? 'translate-x-6' : 'translate-x-1'"
                />
              </div>
            </label>
          </div>

          <div class="p-6 space-y-6">
            <div
              v-if="stream.error"
              class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {{ stream.error }}
            </div>

            <template v-if="workspace.mode === 'draft'">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-grey-700 mb-2">Session Title *</label>
                  <input
                    v-model="draft.title"
                    type="text"
                    class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Mid-term Exam 2026"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-grey-700 mb-2">Class *</label>
                  <select
                    v-model="draft.classId"
                    disabled
                    class="w-full px-4 py-2.5 border border-grey-300 rounded-lg bg-grey-100 text-grey-700 cursor-not-allowed"
                  >
                    <option :value="null" disabled>Select a class</option>
                    <option v-for="cls in classes" :key="cls.id" :value="cls.id">{{ cls.name }}</option>
                  </select>
                </div>
              </div>

              <div>
                <div class="flex items-center justify-between gap-3 mb-2">
                  <label class="block text-sm font-medium text-grey-700">Lesson PDFs *</label>
                  <button
                    v-if="selectedDocsHavePendingOverview && draft.classId"
                    @click="retryOverview"
                    :disabled="retryingOverview"
                    class="text-sm font-medium text-primary-600 hover:text-primary-700 disabled:opacity-50"
                  >
                    {{ retryingOverview ? 'Retrying...' : 'Retry Overview' }}
                  </button>
                </div>

                <div v-if="draft.loadingFiles" class="flex items-center justify-center py-10 border border-grey-200 rounded-xl">
                  <div class="animate-spin rounded-full h-8 w-8 border-4 border-primary-500 border-t-transparent"></div>
                </div>

                <div v-else-if="draft.classId && draft.classFiles.length === 0" class="border border-dashed border-grey-200 rounded-xl p-4 text-sm text-grey-500 text-center">
                  No lesson PDFs were found for this class yet.
                </div>

                <div v-else class="space-y-2 max-h-60 overflow-y-auto pr-1 custom-scrollbar border border-grey-200 rounded-xl p-3 bg-grey-50/60">
                  <label
                    v-for="file in draft.classFiles"
                    :key="file.id"
                    class="flex items-center gap-3 rounded-xl border px-3 py-3 transition"
                    :class="draft.docIds.includes(file.id)
                      ? 'border-primary-300 bg-primary-50'
                      : 'border-grey-200 bg-white'"
                  >
                    <input
                      v-model="draft.docIds"
                      :value="file.id"
                      type="checkbox"
                      :disabled="!file.embedded"
                      class="h-4 w-4 rounded border-grey-300 text-primary-600 focus:ring-primary-500 disabled:opacity-60"
                    />
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-grey-900 truncate">{{ file.name }}</p>
                      <p class="text-xs text-grey-500">{{ formatSize(file.size) }}</p>
                    </div>
                    <div class="flex flex-col items-end gap-1 text-xs">
                      <span
                        class="px-2 py-0.5 rounded-full font-medium"
                        :class="file.embedded ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
                      >
                        {{ file.embedded ? 'Ready' : 'Embedding' }}
                      </span>
                      <span
                        class="px-2 py-0.5 rounded-full font-medium"
                        :class="file.overview_ready ? 'bg-sky-50 text-sky-700' : 'bg-grey-100 text-grey-600'"
                      >
                        {{ file.overview_ready ? 'Overview ready' : 'Overview pending' }}
                      </span>
                    </div>
                  </label>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-grey-700 mb-2">Topics</label>
                  <textarea
                    v-model="draft.topicsText"
                    rows="4"
                    class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                    placeholder="KNN, Decision Trees, Overfitting"
                  ></textarea>
                  <p class="text-xs text-grey-500 mt-2">Separate topics with commas or new lines.</p>
                </div>

                <div class="space-y-4">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">Questions *</label>
                      <input
                        v-model.number="draft.questionCount"
                        type="number"
                        min="1"
                        max="50"
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-grey-700 mb-2">Total Points *</label>
                      <input
                        v-model.number="draft.totalPoints"
                        type="number"
                        min="1"
                        step="0.5"
                        class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-grey-700 mb-2">Language</label>
                    <select
                      v-model="draft.language"
                      class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
                    >
                      <option v-for="option in languageOptions" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <div class="rounded-xl border border-grey-200 bg-grey-50/70 p-4 space-y-4">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <h3 class="text-sm font-semibold text-grey-900">Difficulty Distribution</h3>
                    <p class="text-xs text-grey-500 mt-1">Use the slider for quick changes or switch to manual entry to type exact percentages.</p>
                  </div>
                  <div class="flex rounded-lg border border-grey-200 bg-white p-1 text-xs font-medium text-grey-600">
                    <button
                      type="button"
                      @click="setDifficultyInputMode('slider')"
                      class="rounded-md px-3 py-1.5 transition"
                      :class="difficultyInputMode === 'slider' ? 'bg-primary-600 text-white shadow-sm' : 'hover:bg-grey-50'"
                    >
                      Slider
                    </button>
                    <button
                      type="button"
                      @click="setDifficultyInputMode('manual')"
                      class="rounded-md px-3 py-1.5 transition"
                      :class="difficultyInputMode === 'manual' ? 'bg-primary-600 text-white shadow-sm' : 'hover:bg-grey-50'"
                    >
                      Manual
                    </button>
                  </div>
                </div>

                <div v-if="difficultyInputMode === 'slider'" class="space-y-3">
                  <div
                    ref="difficultyTrackRef"
                    class="relative h-12 select-none touch-none"
                    @pointerdown="onDifficultyTrackPointerDown"
                  >
                    <div class="absolute top-4 left-0 right-0 h-4 rounded-full overflow-hidden border border-grey-200 bg-white">
                      <div class="absolute inset-0" :style="difficultyGradientStyle"></div>
                    </div>

                    <div
                      class="absolute top-3 -translate-x-1/2 cursor-pointer touch-none outline-none"
                      :style="{ left: `${difficultyAnchors.easyEnd}%` }"
                      @pointerdown.stop.prevent="startDifficultyDrag('easy', $event)"
                      @keydown="onDifficultyHandleKeydown('easy', $event)"
                      tabindex="0"
                      role="slider"
                      aria-label="Easy difficulty boundary"
                      :aria-valuemin="0"
                      :aria-valuemax="99"
                      :aria-valuenow="difficultyAnchors.easyEnd"
                    >
                      <div class="flex flex-col items-center gap-1">
                        <div class="w-5 h-5 rounded-full bg-white border-2 border-emerald-500 shadow"></div>
                        <span class="text-[10px] font-semibold text-emerald-700 bg-white/95 px-1.5 py-0.5 rounded-full shadow-sm">Easy</span>
                      </div>
                    </div>

                    <div
                      class="absolute top-3 -translate-x-1/2 cursor-pointer touch-none outline-none"
                      :style="{ left: `${difficultyAnchors.mediumEnd}%` }"
                      @pointerdown.stop.prevent="startDifficultyDrag('medium', $event)"
                      @keydown="onDifficultyHandleKeydown('medium', $event)"
                      tabindex="0"
                      role="slider"
                      aria-label="Medium difficulty boundary"
                      :aria-valuemin="1"
                      :aria-valuemax="100"
                      :aria-valuenow="difficultyAnchors.mediumEnd"
                    >
                      <div class="flex flex-col items-center gap-1">
                        <div class="w-5 h-5 rounded-full bg-white border-2 border-amber-500 shadow"></div>
                        <span class="text-[10px] font-semibold text-amber-700 bg-white/95 px-1.5 py-0.5 rounded-full shadow-sm">Medium</span>
                      </div>
                    </div>
                  </div>

                  <div class="grid grid-cols-3 gap-3 text-sm">
                    <div class="rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2">
                      <p class="text-xs font-semibold uppercase tracking-wider text-emerald-700">Easy</p>
                      <p class="font-semibold text-emerald-900">{{ difficultySplit.easy }}%</p>
                    </div>
                    <div class="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
                      <p class="text-xs font-semibold uppercase tracking-wider text-amber-700">Medium</p>
                      <p class="font-semibold text-amber-900">{{ difficultySplit.medium }}%</p>
                    </div>
                    <div class="rounded-lg bg-red-50 border border-red-200 px-3 py-2">
                      <p class="text-xs font-semibold uppercase tracking-wider text-red-700">Hard</p>
                      <p class="font-semibold text-red-900">{{ difficultySplit.hard }}%</p>
                    </div>
                  </div>
                </div>

                <div v-else class="space-y-4">
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                    <div class="rounded-lg border border-emerald-200 bg-white p-3">
                      <label class="block text-xs font-semibold uppercase tracking-wider text-emerald-700 mb-2">Easy %</label>
                      <input
                        v-model.number="manualDifficulty.easy"
                        type="number"
                        min="0"
                        max="99"
                        step="1"
                        class="w-full rounded-lg border border-grey-300 px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div class="rounded-lg border border-amber-200 bg-white p-3">
                      <label class="block text-xs font-semibold uppercase tracking-wider text-amber-700 mb-2">Medium %</label>
                      <input
                        v-model.number="manualDifficulty.medium"
                        type="number"
                        min="1"
                        max="99"
                        step="1"
                        class="w-full rounded-lg border border-grey-300 px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div class="rounded-lg border border-red-200 bg-white p-3">
                      <label class="block text-xs font-semibold uppercase tracking-wider text-red-700 mb-2">Hard %</label>
                      <input
                        v-model.number="manualDifficulty.hard"
                        type="number"
                        min="0"
                        max="99"
                        step="1"
                        class="w-full rounded-lg border border-grey-300 px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </div>

                  <div class="flex items-center justify-between gap-3 rounded-lg border border-grey-200 bg-white px-4 py-3 text-sm">
                    <div>
                      <p class="font-medium text-grey-900">Manual total: {{ manualDifficultyTotal }}%</p>
                      <p class="text-xs text-grey-500 mt-1">The values must add up to 100 before they can be applied.</p>
                    </div>
                    <button
                      type="button"
                      @click="applyManualDifficultyDistribution"
                      class="px-4 py-2 rounded-lg font-medium transition"
                      :class="manualDifficultyIsValid ? 'bg-primary-600 text-white hover:bg-primary-700' : 'bg-grey-200 text-grey-500 cursor-not-allowed'"
                      :disabled="!manualDifficultyIsValid"
                    >
                      Apply values
                    </button>
                  </div>

                  <div v-if="difficultyInputError" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {{ difficultyInputError }}
                  </div>

                  <div class="grid grid-cols-3 gap-3 text-sm">
                    <div class="rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2">
                      <p class="text-xs font-semibold uppercase tracking-wider text-emerald-700">Current Easy</p>
                      <p class="font-semibold text-emerald-900">{{ difficultySplit.easy }}%</p>
                    </div>
                    <div class="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
                      <p class="text-xs font-semibold uppercase tracking-wider text-amber-700">Current Medium</p>
                      <p class="font-semibold text-amber-900">{{ difficultySplit.medium }}%</p>
                    </div>
                    <div class="rounded-lg bg-red-50 border border-red-200 px-3 py-2">
                      <p class="text-xs font-semibold uppercase tracking-wider text-red-700">Current Hard</p>
                      <p class="font-semibold text-red-900">{{ difficultySplit.hard }}%</p>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-grey-700 mb-3">Exercise Types</label>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <label
                    v-for="option in exerciseTypeOptions"
                    :key="option.value"
                    class="flex items-center gap-3 rounded-xl border border-grey-200 bg-grey-50/60 px-3 py-3"
                  >
                    <input
                      v-model="draft.exerciseTypes"
                      :value="option.value"
                      type="checkbox"
                      class="h-4 w-4 rounded border-grey-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span class="text-sm text-grey-800">{{ option.label }}</span>
                  </label>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-grey-700 mb-2">Optional Teacher Instructions</label>
                <textarea
                  v-model="draft.notes"
                  rows="5"
                  class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                  placeholder="Focus on practical examples. Avoid pure theory. Keep wording concise."
                ></textarea>
              </div>

              <div>
                <label class="block text-sm font-medium text-grey-700 mb-2">Generation Prompt</label>
                <textarea
                  v-model="draft.prompt"
                  rows="3"
                  class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                  placeholder="Generate the exam based on the preferences."
                ></textarea>
              </div>

              <div class="flex items-center gap-3">
                <button
                  @click="generateNewSession"
                  :disabled="stream.isStreaming || !canGenerateDraft"
                  class="flex-1 px-5 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50"
                >
                  {{ stream.isStreaming ? 'Generating...' : 'Generate Exam' }}
                </button>
                <button
                  @click="closeWorkspace"
                  :disabled="stream.isStreaming"
                  class="px-5 py-3 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            </template>

            <template v-else>
              <div class="rounded-xl border border-grey-200 bg-grey-50/70 p-4 space-y-4">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <h3 class="text-sm font-semibold text-grey-900">Session Setup</h3>
                    <p class="text-xs text-grey-500 mt-1">These values come from the saved backend session and stay compatible with the creator route.</p>
                  </div>
                  <span
                    class="text-xs px-2.5 py-1 rounded-full font-medium"
                    :class="activeSession?.exam ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
                  >
                    {{ activeSession?.exam ? 'Exam saved' : 'No exam yet' }}
                  </span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-grey-700">
                  <div class="rounded-lg border border-grey-200 bg-white p-3">
                    <p class="text-xs font-semibold uppercase tracking-wider text-grey-500 mb-1">Documents</p>
                    <p>{{ summarizeDocNames(activeSession?.doc_ids || []) }}</p>
                  </div>
                  <div class="rounded-lg border border-grey-200 bg-white p-3">
                    <p class="text-xs font-semibold uppercase tracking-wider text-grey-500 mb-1">Language</p>
                    <p>{{ activeSession?.preferences?.language || 'French' }}</p>
                  </div>
                  <div class="rounded-lg border border-grey-200 bg-white p-3">
                    <p class="text-xs font-semibold uppercase tracking-wider text-grey-500 mb-1">Question Count</p>
                    <p>{{ activeSession?.preferences?.question_count ?? '-' }}</p>
                  </div>
                  <div class="rounded-lg border border-grey-200 bg-white p-3">
                    <p class="text-xs font-semibold uppercase tracking-wider text-grey-500 mb-1">Total Points</p>
                    <p>{{ activeSession?.preferences?.total_points ?? '-' }}</p>
                  </div>
                </div>

                <div class="rounded-lg border border-grey-200 bg-white p-3 text-sm text-grey-700">
                  <p class="text-xs font-semibold uppercase tracking-wider text-grey-500 mb-1">Teacher Instructions</p>
                  <p class="whitespace-pre-wrap">{{ activeSession?.preferences?.notes || 'None provided.' }}</p>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-grey-700 mb-2">Refinement Prompt</label>
                <textarea
                  v-model="refinement.prompt"
                  rows="4"
                  class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                  placeholder="Make question 3 harder. Add one more MCQ about Euclidean distance."
                ></textarea>
              </div>

              <div>
                <label class="block text-sm font-medium text-grey-700 mb-2">Optional Teacher Instructions</label>
                <textarea
                  v-model="refinement.notes"
                  rows="4"
                  class="w-full px-4 py-2.5 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                  placeholder="Optional extra instructions to include inside your refinement prompt."
                ></textarea>
                <p class="text-xs text-grey-500 mt-2">The backend resume flow only accepts a prompt, so these instructions are appended to that prompt for compatibility.</p>
              </div>

              <div class="flex items-center gap-3">
                <button
                  @click="refineSession"
                  :disabled="stream.isStreaming || !canRefineSession"
                  class="flex-1 px-5 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50"
                >
                  {{ stream.isStreaming ? 'Refining...' : 'Refine Exam' }}
                </button>
                <button
                  @click="downloadPreviewPdf"
                  :disabled="!previewExam"
                  class="px-5 py-3 border border-grey-300 text-grey-700 rounded-lg font-medium hover:bg-grey-50 transition disabled:opacity-50"
                >
                  Download PDF
                </button>
              </div>
            </template>

            <div class="rounded-xl border border-grey-200 bg-grey-50/70 p-4 space-y-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <h3 class="text-sm font-semibold text-grey-900">Live Agent Activity</h3>
                  <p class="text-xs text-grey-500 mt-1">Streaming events from the creator and evaluator loop.</p>
                </div>
                <span v-if="stream.isStreaming" class="inline-flex items-center gap-2 text-sm text-primary-600">
                  <span class="inline-block h-2.5 w-2.5 rounded-full bg-primary-500 animate-pulse"></span>
                  Streaming
                </span>
              </div>

              <div v-if="stream.narrative" class="rounded-lg border border-grey-200 bg-white p-3 text-sm text-grey-700 whitespace-pre-wrap">
                {{ stream.narrative }}
              </div>

              <details v-if="stream.thinking" class="rounded-lg border border-amber-200 bg-amber-50/70 p-3">
                <summary class="cursor-pointer text-sm font-medium text-amber-800">Reasoning</summary>
                <pre class="mt-3 whitespace-pre-wrap text-xs text-amber-900 font-mono max-h-48 overflow-y-auto custom-scrollbar">{{ stream.thinking }}</pre>
              </details>

              <div v-if="stream.toolEvents.length" class="flex flex-wrap gap-2">
                <span
                  v-for="(event, index) in stream.toolEvents"
                  :key="`${event.type}-${event.name}-${index}`"
                  class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium"
                  :class="event.type === 'tool_call' ? 'bg-violet-50 text-violet-700' : 'bg-teal-50 text-teal-700'"
                >
                  <WrenchScrewdriverIcon class="w-3.5 h-3.5" />
                  {{ event.name }}
                </span>
              </div>

              <div v-if="stream.evaluatorFeedback.length" class="rounded-lg border border-amber-200 bg-amber-50/70 p-3">
                <p class="text-sm font-medium text-amber-800 mb-2">Evaluator Feedback</p>
                <ul class="space-y-2 text-sm text-amber-900">
                  <li v-for="item in stream.evaluatorFeedback" :key="`${item.question_id}-${item.reason}`">
                    {{ item.question_id }}: {{ item.reason }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl border border-grey-200 shadow-sm overflow-hidden">
          <div class="flex items-center justify-between gap-4 px-6 py-5 border-b border-grey-200">
            <div>
              <h2 class="text-xl font-semibold text-grey-900">Preview</h2>
              <p class="text-sm text-grey-600 mt-1">Latest exam draft rendered from streamed `exam_json`.</p>
            </div>
            <button
              @click="downloadPreviewPdf"
              :disabled="!previewExam"
              class="flex items-center gap-2 px-4 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50"
            >
              <ArrowDownTrayIcon class="w-4 h-4" />
              Download PDF
            </button>
          </div>

          <div class="h-[calc(100vh-220px)] overflow-y-auto custom-scrollbar bg-grey-50/60">
            <div v-if="!previewExam" class="h-full flex flex-col items-center justify-center px-8 text-center">
              <DocumentMagnifyingGlassIcon class="w-16 h-16 text-grey-300 mb-4" />
              <h3 class="text-lg font-medium text-grey-900 mb-2">No exam preview yet</h3>
              <p class="text-grey-600 max-w-md">Generate a new session or open an existing one to see the exam preview here before exporting it.</p>
            </div>

            <div v-else class="max-w-4xl mx-auto p-6 lg:p-10">
              <div class="bg-white rounded-2xl shadow-sm border border-grey-200 min-h-full p-8 space-y-8">
                <div class="border-b border-grey-200 pb-6">
                  <div class="flex items-start justify-between gap-4">
                    <div>
                      <p class="text-xs uppercase tracking-[0.2em] text-grey-500 font-semibold">Generated Exam</p>
                      <h3 class="text-3xl font-bold text-grey-900 mt-2">{{ previewTitle }}</h3>
                    </div>
                    <div class="text-right text-sm text-grey-600">
                      <p>{{ previewQuestionCount }} question{{ previewQuestionCount !== 1 ? 's' : '' }}</p>
                      <p>{{ previewTotalPoints }} total points</p>
                    </div>
                  </div>

                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 text-sm text-grey-700">
                    <div class="rounded-xl bg-grey-50 border border-grey-200 p-4">
                      <p class="text-xs uppercase tracking-wider text-grey-500 font-semibold mb-2">Topics</p>
                      <p>{{ previewTopics }}</p>
                    </div>
                    <div class="rounded-xl bg-grey-50 border border-grey-200 p-4">
                      <p class="text-xs uppercase tracking-wider text-grey-500 font-semibold mb-2">Teacher Instructions</p>
                      <p class="whitespace-pre-wrap">{{ previewNotes }}</p>
                    </div>
                  </div>
                </div>

                <section class="space-y-6">
                  <article
                    v-for="(question, index) in previewExam.questions"
                    :key="question.id || index"
                    class="rounded-2xl border border-grey-200 p-5"
                  >
                    <div class="flex items-start justify-between gap-4 mb-3">
                      <div>
                        <p class="text-xs uppercase tracking-wider text-grey-500 font-semibold">Question {{ index + 1 }}</p>
                        <h4 class="text-lg font-semibold text-grey-900 mt-1">{{ question.text }}</h4>
                      </div>
                      <div class="text-right text-sm text-grey-600">
                        <p class="font-medium text-grey-900">{{ formatPoints(question.max_points) }}</p>
                        <p class="capitalize">{{ question.difficulty || 'Unspecified' }}</p>
                      </div>
                    </div>

                    <div class="flex flex-wrap gap-2 mb-4">
                      <span class="px-2.5 py-1 rounded-full bg-primary-50 text-primary-700 text-xs font-medium uppercase">
                        {{ question.type || 'question' }}
                      </span>
                      <span class="px-2.5 py-1 rounded-full bg-grey-100 text-grey-700 text-xs font-medium">
                        {{ resolveDocName(question.source_doc_id) }}
                      </span>
                    </div>

                    <ul v-if="Array.isArray(question.options) && question.options.length" class="space-y-2 mb-4">
                      <li
                        v-for="(option, optionIndex) in question.options"
                        :key="optionIndex"
                        class="rounded-lg border border-grey-200 bg-grey-50 px-3 py-2 text-sm text-grey-800"
                      >
                        {{ option }}
                      </li>
                    </ul>

                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 text-sm">
                      <div class="rounded-xl bg-emerald-50 border border-emerald-200 p-4">
                        <p class="text-xs uppercase tracking-wider text-emerald-700 font-semibold mb-2">Suggested Answer</p>
                        <p class="whitespace-pre-wrap text-emerald-950">{{ question.suggested_answer || 'No answer provided.' }}</p>
                      </div>
                      <div class="rounded-xl bg-sky-50 border border-sky-200 p-4">
                        <p class="text-xs uppercase tracking-wider text-sky-700 font-semibold mb-2">Source Hint</p>
                        <p class="whitespace-pre-wrap text-sky-950">{{ question.source_hint || 'No source hint provided.' }}</p>
                      </div>
                    </div>
                  </article>
                </section>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue';
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import {
  PlusIcon,
  SparklesIcon,
  DocumentMagnifyingGlassIcon,
  ChevronLeftIcon,
  ArrowDownTrayIcon,
  WrenchScrewdriverIcon,
} from '@heroicons/vue/24/outline';
import { useClassesStore } from '@/stores/classesStore';
import api from '@/services/api';

const classesStore = useClassesStore();

const exerciseTypeOptions = [
  { value: 'mcq', label: 'MCQ' },
  { value: 'open', label: 'Open' },
  { value: 'table', label: 'Table' },
  { value: 'fill', label: 'Fill' },
  { value: 'true-false', label: 'True / False' },
];

const languageOptions = [
  { value: 'French', label: 'French' },
  { value: 'English', label: 'English' },
  { value: 'Arabic', label: 'Arabic' },
];

const loadingPage = ref(true);
const sessionsLoading = ref(false);
const retryingOverview = ref(false);
const creatingSession = ref(false);
const sessions = ref([]);
const allUploads = ref([]);
const activeSession = ref(null);
const selectedClassId = ref(null);

const filteredSessions = computed(() => {
  if (!selectedClassId.value) return [];
  return sessions.value.filter(s => s.preferences?.class_id === selectedClassId.value);
});

function adjustColor(color, percent) {
  if (!color) return '#3b82f6';
  const num = parseInt(color.replace('#', ''), 16),
        amt = Math.round(2.55 * percent),
        R = (num >> 16) + amt,
        G = (num >> 8 & 0x00FF) + amt,
        B = (num & 0x0000FF) + amt;
  return `#${(
    0x1000000 +
    (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
    (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
    (B < 255 ? (B < 1 ? 0 : B) : 255)
  ).toString(16).slice(1)}`;
}

function selectClass(classId) {
  selectedClassId.value = classId;
}

async function startNewSessionForClass() {
  resetDraft();
  resetStream();
  activeSession.value = null;
  refinement.prompt = '';
  refinement.notes = '';
  draft.classId = selectedClassId.value;
  draft.title = 'New Session';
  
  creatingSession.value = true;
  try {
    workspace.mode = 'draft';
    await loadDraftClassFiles();
  } finally {
    creatingSession.value = false;
  }
}

const workspace = reactive({
  mode: 'idle',
});

function createDefaultDraft() {
  return {
    title: '',
    classId: null,
    classFiles: [],
    loadingFiles: false,
    docIds: [],
    topicsText: '',
    difficulty: { easy: 30, medium: 50, hard: 20 },
    exerciseTypes: ['mcq', 'open'],
    questionCount: 10,
    totalPoints: 20,
    language: 'French',
    notes: '',
    prompt: 'Generate the exam based on the preferences.',
  };
}

const draft = reactive(createDefaultDraft());
const difficultyAnchors = reactive({
  easyEnd: 30,
  mediumEnd: 80,
});
const difficultyInputMode = ref('slider');
const difficultyInputError = ref('');
const manualDifficulty = reactive({
  easy: 30,
  medium: 50,
  hard: 20,
});
const difficultyTrackRef = ref(null);
const activeDifficultyHandle = ref(null);

const refinement = reactive({
  prompt: '',
  notes: '',
});

const stream = reactive({
  isStreaming: false,
  reasoning: true,
  narrative: '',
  thinking: '',
  toolEvents: [],
  evaluatorFeedback: [],
  currentDraft: null,
  error: '',
});

const classes = computed(() => classesStore.classes);
const uploadsById = computed(() => new Map(allUploads.value.map((file) => [file.id, file])));
const normalizedDifficultyAnchors = computed(() => {
  const easy = clampInt(difficultyAnchors.easyEnd, 0, 99);
  const mediumEnd = clampInt(difficultyAnchors.mediumEnd, easy + 1, 100);
  return { easy, mediumEnd };
});
const difficultyTotal = computed(() => {
  return Number(difficultySplit.value.easy || 0) + Number(difficultySplit.value.medium || 0) + Number(difficultySplit.value.hard || 0);
});
const manualDifficultyTotal = computed(() => {
  return Number(manualDifficulty.easy || 0) + Number(manualDifficulty.medium || 0) + Number(manualDifficulty.hard || 0);
});
const manualDifficultyBoundsValid = computed(() => {
  const easy = Number(manualDifficulty.easy);
  const medium = Number(manualDifficulty.medium);
  const hard = Number(manualDifficulty.hard);
  return easy >= 0 && easy <= 99
    && medium >= 1 && medium <= 99
    && hard >= 0 && hard <= 99;
});
const manualDifficultyIsValid = computed(() => manualDifficultyBoundsValid.value && manualDifficultyTotal.value === 100);
const canGenerateDraft = computed(() => {
  return Boolean(draft.title.trim())
    && Boolean(draft.classId)
    && draft.docIds.length > 0
    && draft.exerciseTypes.length > 0
    && difficultyTotal.value === 100;
});
const canRefineSession = computed(() => {
  return Boolean(activeSession.value?.session_id) && Boolean(buildRefinementPrompt().trim());
});
const difficultySplit = computed(() => ({
  easy: normalizedDifficultyAnchors.value.easy,
  medium: normalizedDifficultyAnchors.value.mediumEnd - normalizedDifficultyAnchors.value.easy,
  hard: 100 - normalizedDifficultyAnchors.value.mediumEnd,
}));
const difficultyGradientStyle = computed(() => {
  const easy = normalizedDifficultyAnchors.value.easy;
  const medium = normalizedDifficultyAnchors.value.mediumEnd;
  return {
    background: `linear-gradient(to right,
      #16a34a 0%,
      #16a34a ${easy}%,
      #f59e0b ${easy}%,
      #f59e0b ${medium}%,
      #ef4444 ${medium}%,
      #ef4444 100%)`
  };
});
const selectedDocsHavePendingOverview = computed(() => {
  return draft.classFiles.some((file) => draft.docIds.includes(file.id) && !file.overview_ready);
});

const previewExam = computed(() => stream.currentDraft || activeSession.value?.exam || null);
const previewTitle = computed(() => {
  if (workspace.mode === 'draft') return draft.title || 'Untitled Exam';
  return activeSession.value?.title || 'Untitled Exam';
});
const previewPreferences = computed(() => {
  if (workspace.mode === 'draft') {
    return {
      topics: parseTopics(draft.topicsText),
      total_points: draft.totalPoints,
      notes: draft.notes,
    };
  }
  return activeSession.value?.preferences || {};
});
const previewQuestionCount = computed(() => Array.isArray(previewExam.value?.questions) ? previewExam.value.questions.length : 0);
const previewTotalPoints = computed(() => {
  if (!previewExam.value?.questions) return previewPreferences.value.total_points || 0;
  return previewExam.value.questions.reduce((sum, question) => sum + Number(question.max_points || 0), 0);
});
const previewTopics = computed(() => {
  const topics = previewPreferences.value.topics || [];
  return Array.isArray(topics) && topics.length ? topics.join(', ') : 'All supported topics from the selected documents';
});
const previewNotes = computed(() => {
  return String(previewPreferences.value.notes || '').trim() || 'No extra teacher instructions.';
});

function resetDraft() {
  Object.assign(draft, createDefaultDraft());
  difficultyAnchors.easyEnd = 30;
  difficultyAnchors.mediumEnd = 80;
  normalizeDifficultyAnchors();
  syncManualDifficultyFromAnchors();
  difficultyInputMode.value = 'slider';
  difficultyInputError.value = '';
}

function resetStream() {
  stream.isStreaming = false;
  stream.narrative = '';
  stream.thinking = '';
  stream.toolEvents = [];
  stream.evaluatorFeedback = [];
  stream.currentDraft = null;
  stream.error = '';
}

function formatDate(value) {
  if (!value) return '-';
  return new Date(value).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatSize(bytes) {
  if (!bytes) return '0 KB';
  const kb = bytes / 1024;
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`;
}

function formatPoints(value) {
  const num = Number(value || 0);
  return `${Number.isInteger(num) ? num : num.toFixed(1)} pt${num === 1 ? '' : 's'}`;
}

function resolveDocName(docId) {
  const match = uploadsById.value.get(docId);
  return match?.name || `Document ${String(docId).slice(0, 8)}`;
}

function summarizeDocNames(docIds) {
  if (!Array.isArray(docIds) || docIds.length === 0) return 'No documents attached.';
  return docIds.map(resolveDocName).join(', ');
}

function parseTopics(value) {
  return String(value || '')
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function clampInt(value, min, max) {
  const numeric = Number.isFinite(Number(value)) ? Math.round(Number(value)) : min;
  return Math.min(max, Math.max(min, numeric));
}

function normalizeDifficultyAnchors() {
  const nextEasy = clampInt(difficultyAnchors.easyEnd, 0, 99);
  const nextMediumEnd = clampInt(difficultyAnchors.mediumEnd, nextEasy + 1, 100);
  difficultyAnchors.easyEnd = nextEasy;
  difficultyAnchors.mediumEnd = nextMediumEnd;
  draft.difficulty = { ...difficultySplit.value };
}

function syncManualDifficultyFromAnchors() {
  manualDifficulty.easy = difficultySplit.value.easy;
  manualDifficulty.medium = difficultySplit.value.medium;
  manualDifficulty.hard = difficultySplit.value.hard;
}

function setDifficultyInputMode(mode) {
  stopDifficultyDrag();
  if (mode === 'manual') {
    syncManualDifficultyFromAnchors();
    difficultyInputError.value = '';
  } else {
    difficultyInputError.value = '';
  }
  difficultyInputMode.value = mode;
}

function applyManualDifficultyDistribution() {
  const easy = Number(manualDifficulty.easy);
  const medium = Number(manualDifficulty.medium);
  const hard = Number(manualDifficulty.hard);

  if (!Number.isFinite(easy) || !Number.isFinite(medium) || !Number.isFinite(hard)) {
    difficultyInputError.value = 'Please enter numeric percentages only.';
    return;
  }

  if (easy < 0 || easy > 99 || medium < 1 || medium > 99 || hard < 0 || hard > 99) {
    difficultyInputError.value = 'Keep easy between 0 and 99, medium between 1 and 99, and hard between 0 and 99.';
    return;
  }

  const total = easy + medium + hard;

  if (total !== 100) {
    difficultyInputError.value = `The manual values add up to ${total}%, not 100%.`;
    return;
  }

  difficultyInputError.value = '';
  difficultyAnchors.easyEnd = easy;
  difficultyAnchors.mediumEnd = easy + medium;
  normalizeDifficultyAnchors();
  syncManualDifficultyFromAnchors();
  difficultyInputMode.value = 'slider';
}

function getDifficultyPercentFromEvent(event) {
  const rect = difficultyTrackRef.value?.getBoundingClientRect();
  if (!rect || !rect.width) return 0;
  const clientX = event.clientX ?? event.touches?.[0]?.clientX ?? rect.left;
  const pct = ((clientX - rect.left) / rect.width) * 100;
  return clampInt(pct, 0, 100);
}

function moveDifficultyHandle(handle, percent) {
  if (handle === 'easy') {
    difficultyAnchors.easyEnd = clampInt(percent, 0, difficultyAnchors.mediumEnd - 1);
  } else if (handle === 'medium') {
    difficultyAnchors.mediumEnd = clampInt(percent, difficultyAnchors.easyEnd + 1, 100);
  }
  normalizeDifficultyAnchors();
}

function nudgeDifficultyHandle(handle, delta) {
  if (handle === 'easy') {
    moveDifficultyHandle(handle, difficultyAnchors.easyEnd + delta);
  } else if (handle === 'medium') {
    moveDifficultyHandle(handle, difficultyAnchors.mediumEnd + delta);
  }
}

function onDifficultyHandleKeydown(handle, event) {
  const step = event.shiftKey ? 5 : 1;
  switch (event.key) {
    case 'ArrowLeft':
    case 'ArrowDown':
      event.preventDefault();
      nudgeDifficultyHandle(handle, -step);
      break;
    case 'ArrowRight':
    case 'ArrowUp':
      event.preventDefault();
      nudgeDifficultyHandle(handle, step);
      break;
    case 'Home':
      event.preventDefault();
      moveDifficultyHandle(handle, handle === 'easy' ? 0 : difficultyAnchors.easyEnd + 1);
      break;
    case 'End':
      event.preventDefault();
      moveDifficultyHandle(handle, handle === 'easy' ? difficultyAnchors.mediumEnd - 1 : 100);
      break;
    case 'PageDown':
      event.preventDefault();
      nudgeDifficultyHandle(handle, -10);
      break;
    case 'PageUp':
      event.preventDefault();
      nudgeDifficultyHandle(handle, 10);
      break;
    default:
      break;
  }
}

function startDifficultyDrag(handle, event) {
  activeDifficultyHandle.value = handle;
  moveDifficultyHandle(handle, getDifficultyPercentFromEvent(event));
  window.addEventListener('pointermove', onDifficultyPointerMove);
  window.addEventListener('pointerup', stopDifficultyDrag);
  window.addEventListener('pointercancel', stopDifficultyDrag);
}

function onDifficultyTrackPointerDown(event) {
  const percent = getDifficultyPercentFromEvent(event);
  const easyDistance = Math.abs(percent - difficultyAnchors.easyEnd);
  const mediumDistance = Math.abs(percent - difficultyAnchors.mediumEnd);
  const handle = easyDistance <= mediumDistance ? 'easy' : 'medium';
  startDifficultyDrag(handle, event);
}

function onDifficultyPointerMove(event) {
  if (!activeDifficultyHandle.value) return;
  moveDifficultyHandle(activeDifficultyHandle.value, getDifficultyPercentFromEvent(event));
}

function stopDifficultyDrag() {
  activeDifficultyHandle.value = null;
  window.removeEventListener('pointermove', onDifficultyPointerMove);
  window.removeEventListener('pointerup', stopDifficultyDrag);
  window.removeEventListener('pointercancel', stopDifficultyDrag);
}

async function loadSessions() {
  sessionsLoading.value = true;
  try {
    const response = await api.listCreatorSessions({ limit: 100, offset: 0 });
    if (response.success) {
      sessions.value = response.sessions || [];
    }
  } catch (error) {
    console.error('Failed to load creator sessions:', error);
  } finally {
    sessionsLoading.value = false;
  }
}

async function loadAllUploads() {
  try {
    const response = await api.getLessons(null, { limit: 100, refresh: true });
    if (response.success) {
      allUploads.value = response.uploads || [];
    }
  } catch (error) {
    console.error('Failed to load uploads:', error);
  }
}

async function loadDraftClassFiles() {
  if (!draft.classId) {
    draft.classFiles = [];
    draft.docIds = [];
    return;
  }

  draft.loadingFiles = true;
  try {
    const response = await api.getLessons(draft.classId, { limit: 100, refresh: true });
    if (response.success) {
      draft.classFiles = response.uploads || [];
      allUploads.value = mergeUploads(allUploads.value, draft.classFiles);
      draft.docIds = draft.docIds.filter((id) => draft.classFiles.some((file) => file.id === id));
    }
  } catch (error) {
    stream.error = error.message || 'Failed to load class lesson files.';
  } finally {
    draft.loadingFiles = false;
  }
}

function mergeUploads(base, additions) {
  const map = new Map(base.map((item) => [item.id, item]));
  for (const item of additions) {
    map.set(item.id, item);
  }
  return Array.from(map.values());
}

function openNewSessionModal() {
  resetDraft();
  resetStream();
  activeSession.value = null;
  refinement.prompt = '';
  refinement.notes = '';
  creatingSession.value = false;
  showCreateModal.value = true;
}

function closeCreateModal() {
  creatingSession.value = false;
  showCreateModal.value = false;
}

async function startDraftWorkspace() {
  if (!draft.title.trim() || !draft.classId) return;
  creatingSession.value = true;
  try {
    closeCreateModal();
    resetStream();
    activeSession.value = null;
    workspace.mode = 'draft';
    await loadDraftClassFiles();
  } finally {
    creatingSession.value = false;
  }
}

async function handleDraftClassChange() {
  draft.docIds = [];
  stream.error = '';
  await loadDraftClassFiles();
}

async function openSession(sessionId) {
  resetStream();
  refinement.prompt = '';
  refinement.notes = '';
  try {
    const response = await api.getCreatorSession(sessionId);
    if (response.success) {
      activeSession.value = response.session;
      stream.currentDraft = response.session.exam || null;
      updateDifficultyFromSessionPreferences(response.session.preferences);
      difficultyInputMode.value = 'slider';
      workspace.mode = 'session';
    }
  } catch (error) {
    stream.error = error.message || 'Failed to open the session.';
  }
}

async function deleteSession(sessionId) {
  if (!confirm('Delete this creator session?')) return;
  try {
    await api.deleteCreatorSession(sessionId);
    if (activeSession.value?.session_id === sessionId) {
      closeWorkspace();
    }
    await loadSessions();
  } catch (error) {
    alert(`Failed to delete session: ${error.message}`);
  }
}

function closeWorkspace() {
  workspace.mode = 'idle';
  activeSession.value = null;
  refinement.prompt = '';
  refinement.notes = '';
  resetStream();
}

async function retryOverview() {
  if (!draft.classId) return;
  retryingOverview.value = true;
  try {
    await api.retryCreatorOverview(draft.classId);
    await loadDraftClassFiles();
  } catch (error) {
    stream.error = error.message || 'Failed to retry overview generation.';
  } finally {
    retryingOverview.value = false;
  }
}

function validateDraftBeforeGenerate() {
  if (!draft.title.trim()) {
    throw new Error('Please enter a session title.');
  }
  if (!draft.classId) {
    throw new Error('Please choose a class.');
  }
  if (draft.docIds.length === 0) {
    throw new Error('Please select at least one embedded lesson PDF.');
  }
  if (draft.exerciseTypes.length === 0) {
    throw new Error('Please select at least one exercise type.');
  }
  if (difficultyTotal.value !== 100) {
    throw new Error('Difficulty percentages must add up to 100.');
  }
}

async function generateNewSession() {
  try {
    validateDraftBeforeGenerate();
    resetStream();
    stream.isStreaming = true;

    let savedSessionId = null;

    await api.streamCreatorGenerate(
      {
        session_id: null,
        doc_ids: draft.docIds,
        title: draft.title.trim(),
        preferences: {
          class_id: draft.classId,
          topics: parseTopics(draft.topicsText),
          difficulty_distribution: difficultyDistributionForBackend(),
          exercise_types: draft.exerciseTypes,
          question_count: Number(draft.questionCount || 10),
          total_points: Number(draft.totalPoints || 20),
          language: draft.language || 'French',
          notes: draft.notes || '',
        },
        prompt: draft.prompt?.trim() || 'Generate the exam based on the preferences.',
        reasoning: stream.reasoning,
      },
      handleCreatorStreamEvent
    );

    const savedEvent = stream.toolEvents.find((event) => event.type === 'exam_saved');
    savedSessionId = savedEvent?.session_id || null;

    await Promise.all([loadSessions(), loadAllUploads()]);

    if (savedSessionId) {
      await openSession(savedSessionId);
    }
  } catch (error) {
    stream.error = error.message || 'Exam generation failed.';
  } finally {
    stream.isStreaming = false;
  }
}

async function refineSession() {
  if (!activeSession.value?.session_id) return;

  const prompt = buildRefinementPrompt();
  if (!prompt) {
    stream.error = 'Please add a refinement prompt before continuing.';
    return;
  }

  try {
    resetStream();
    stream.currentDraft = activeSession.value.exam || null;
    stream.isStreaming = true;

    await api.streamCreatorGenerate(
      {
        session_id: activeSession.value.session_id,
        doc_ids: activeSession.value.doc_ids || [],
        title: activeSession.value.title,
        preferences: activeSession.value.preferences || {},
        prompt,
        reasoning: stream.reasoning,
      },
      handleCreatorStreamEvent
    );

    await Promise.all([
      openSession(activeSession.value.session_id),
      loadSessions(),
    ]);
  } catch (error) {
    stream.error = error.message || 'Exam refinement failed.';
  } finally {
    stream.isStreaming = false;
  }
}

function buildRefinementPrompt() {
  const base = String(refinement.prompt || '').trim();
  const notes = String(refinement.notes || '').trim();
  if (!base && !notes) return '';
  if (base && !notes) return base;
  if (!base && notes) return `Additional teacher instructions:\n${notes}`;
  return `${base}\n\nAdditional teacher instructions:\n${notes}`;
}

function handleCreatorStreamEvent({ event, data }) {
  if (event === 'thinking') {
    stream.thinking += data;
    return;
  }

  if (event === 'content') {
    stream.narrative += data;
    return;
  }

  if (event === 'tool_call' || event === 'tool_result' || event === 'exam_saved') {
    try {
      const payload = JSON.parse(data);
      stream.toolEvents.push({ type: event, ...payload });
    } catch {
      stream.toolEvents.push({ type: event, name: event, raw: data });
    }
    return;
  }

  if (event === 'exam_draft') {
    try {
      const payload = JSON.parse(data);
      stream.currentDraft = { questions: payload.questions || [] };
    } catch {
      stream.error = 'Received an invalid exam draft payload.';
    }
    return;
  }

  if (event === 'evaluator_feedback') {
    try {
      const payload = JSON.parse(data);
      stream.evaluatorFeedback = payload.flagged || [];
    } catch {
      stream.evaluatorFeedback = [];
    }
  }
}

function buildPdfLines() {
  const exam = previewExam.value;
  if (!exam?.questions?.length) return [];

  const lines = [];
  lines.push(previewTitle.value);
  lines.push('');
  lines.push(`Language: ${previewPreferences.value.language || 'French'}`);
  lines.push(`Topics: ${previewTopics.value}`);
  lines.push(`Teacher Instructions: ${previewNotes.value}`);
  lines.push(`Total Points: ${previewTotalPoints.value}`);
  lines.push('');

  for (const [index, question] of exam.questions.entries()) {
    lines.push(`Question ${index + 1} (${question.type || 'question'}, ${question.difficulty || 'unspecified'}, ${formatPoints(question.max_points)})`);
    lines.push(question.text || '');

    if (Array.isArray(question.options) && question.options.length) {
      for (const option of question.options) {
        lines.push(`  ${option}`);
      }
    }

    lines.push(`Suggested Answer: ${question.suggested_answer || 'N/A'}`);
    lines.push(`Source: ${resolveDocName(question.source_doc_id)} | ${question.source_hint || 'No source hint'}`);
    lines.push('');
  }

  return lines.flatMap((line) => wrapPdfLine(line, 92));
}

function wrapPdfLine(line, maxLength) {
  const value = String(line ?? '');
  if (!value) return [''];
  const words = value.split(/\s+/);
  const lines = [];
  let current = '';

  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length > maxLength) {
      if (current) lines.push(current);
      if (word.length > maxLength) {
        for (let index = 0; index < word.length; index += maxLength) {
          lines.push(word.slice(index, index + maxLength));
        }
        current = '';
      } else {
        current = word;
      }
    } else {
      current = next;
    }
  }

  if (current) lines.push(current);
  return lines;
}

function escapePdfText(value) {
  return String(value)
    .replace(/[^\x20-\x7E]/g, '?')
    .replace(/\\/g, '\\\\')
    .replace(/\(/g, '\\(')
    .replace(/\)/g, '\\)');
}

function createPdfBlobFromLines(lines) {
  const pageHeight = 792;
  const startY = 750;
  const lineHeight = 14;
  const linesPerPage = 48;
  const pages = [];

  for (let index = 0; index < lines.length; index += linesPerPage) {
    pages.push(lines.slice(index, index + linesPerPage));
  }

  if (pages.length === 0) pages.push(['']);

  const objects = [];
  const pageObjectNumbers = [];

  objects[1] = '<< /Type /Catalog /Pages 2 0 R >>';
  objects[2] = '';

  let nextObjectNumber = 3;
  for (const pageLines of pages) {
    const pageObjectNumber = nextObjectNumber++;
    const contentObjectNumber = nextObjectNumber++;
    pageObjectNumbers.push(pageObjectNumber);

    const streamContent = [
      'BT',
      '/F1 12 Tf',
      `50 ${startY} Td`,
      `${lineHeight} TL`,
      ...pageLines.map((line, lineIndex) => `${lineIndex === 0 ? '' : 'T* ' }(${escapePdfText(line)}) Tj`.trim()),
      'ET',
    ].join('\n');

    objects[pageObjectNumber] = `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 ${pageHeight}] /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /Contents ${contentObjectNumber} 0 R >>`;
    objects[contentObjectNumber] = `<< /Length ${streamContent.length} >>\nstream\n${streamContent}\nendstream`;
  }

  objects[2] = `<< /Type /Pages /Count ${pages.length} /Kids [${pageObjectNumbers.map((num) => `${num} 0 R`).join(' ')}] >>`;

  let pdf = '%PDF-1.4\n';
  const offsets = [0];
  for (let index = 1; index < objects.length; index += 1) {
    offsets[index] = pdf.length;
    pdf += `${index} 0 obj\n${objects[index]}\nendobj\n`;
  }

  const xrefOffset = pdf.length;
  pdf += `xref\n0 ${objects.length}\n`;
  pdf += '0000000000 65535 f \n';
  for (let index = 1; index < objects.length; index += 1) {
    pdf += `${String(offsets[index]).padStart(10, '0')} 00000 n \n`;
  }
  pdf += `trailer\n<< /Size ${objects.length} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;

  return new Blob([pdf], { type: 'application/pdf' });
}

function downloadPreviewPdf() {
  if (!previewExam.value) return;
  const blob = createPdfBlobFromLines(buildPdfLines());
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${sanitizeFilename(previewTitle.value || 'creator-exam')}.pdf`;
  link.click();
  URL.revokeObjectURL(url);
}

function sanitizeFilename(value) {
  return String(value || 'creator-exam')
    .trim()
    .replace(/[<>:"/\\|?*]+/g, '_')
    .replace(/\s+/g, ' ')
    .slice(0, 120);
}

function updateDifficultyFromSessionPreferences(preferences) {
  const split = preferences?.difficulty_distribution || {};
  const easy = clampInt(split.easy ?? 30, 0, 99);
  const medium = clampInt(split.medium ?? 50, 1, 100 - easy);
  difficultyAnchors.easyEnd = easy;
  difficultyAnchors.mediumEnd = clampInt(easy + medium, easy + 1, 100);
  normalizeDifficultyAnchors();
  syncManualDifficultyFromAnchors();
}

function difficultyDistributionForBackend() {
  return {
    easy: Number(difficultySplit.value.easy || 0),
    medium: Number(difficultySplit.value.medium || 0),
    hard: Number(difficultySplit.value.hard || 0),
  };
}

onMounted(async () => {
  try {
    await Promise.all([
      classesStore.load(),
      loadSessions(),
      loadAllUploads(),
    ]);
  } finally {
    loadingPage.value = false;
  }
});

onBeforeUnmount(() => {
  stopDifficultyDrag();
});
</script>
