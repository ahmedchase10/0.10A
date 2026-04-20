import { ref } from 'vue';
import { defineStore } from 'pinia';
import api from '@/services/api';

/**
 * classesStore — single source of truth for the teacher's class list.
 *
 * Both the sidebar (appLayout) and the Dashboard read from here, so any
 * create / delete / update on the Dashboard is immediately reflected in
 * the sidebar without a page reload.
 *
 * Usage:
 *   const classesStore = useClassesStore();
 *   await classesStore.load();          // fetch from API (idempotent)
 *   classesStore.add(newClass);         // after POST /classes
 *   classesStore.update(id, patch);     // after PUT /classes/:id
 *   classesStore.remove(id);            // after DELETE /classes/:id
 *   classesStore.classes                // reactive array
 *   classesStore.loading                // bool
 */
export const useClassesStore = defineStore('classes', () => {
    const classes = ref([]);
    const loading = ref(false);
    const loaded = ref(false); // avoid redundant API calls

    // ── Load ──────────────────────────────────────────────────────────────────

    async function load(force = false) {
        if (loaded.value && !force) return;
        loading.value = true;
        try {
            const res = await api.getClasses();
            if (res.success) {
                classes.value = res.classes || [];
                loaded.value = true;
            }
        } catch (err) {
            console.error('[classesStore] load failed:', err);
        } finally {
            loading.value = false;
        }
    }

    // ── Mutations (call these after a successful API call) ────────────────────

    function add(cls) {
        classes.value.unshift(cls);
    }

    function update(classId, patch) {
        const idx = classes.value.findIndex(c => c.id === classId);
        if (idx !== -1) classes.value[idx] = { ...classes.value[idx], ...patch };
    }

    function remove(classId) {
        classes.value = classes.value.filter(c => c.id !== classId);
    }

    // ── Reset (call on logout) ────────────────────────────────────────────────

    function reset() {
        classes.value = [];
        loaded.value = false;
    }

    return { classes, loading, loaded, load, add, update, remove, reset };
});