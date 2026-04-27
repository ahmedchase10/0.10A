import { ref } from 'vue';
import { defineStore } from 'pinia';
import api from '@/services/api';

/**
 * classesStore — single source of truth for the teacher's class list.
 *
 * BUG-09 fix: added _loadPromise in-flight guard so simultaneous calls to
 * load() (from appLayout + classpage mounting at the same time) only fire
 * ONE network request. The second caller simply awaits the same promise.
 */
export const useClassesStore = defineStore('classes', () => {
    const classes = ref([]);
    const loading = ref(false);
    const loaded = ref(false);

    // BUG-09: in-flight guard
    let _loadPromise = null;

    async function _doLoad() {
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

    async function load(force = false) {
        if (loaded.value && !force) return;
        if (_loadPromise) return _loadPromise;         // BUG-09: reuse in-flight request
        _loadPromise = _doLoad().finally(() => {
            _loadPromise = null;
        });
        return _loadPromise;
    }

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

    function reset() {
        classes.value = [];
        loaded.value = false;
        _loadPromise = null;
    }

    return { classes, loading, loaded, load, add, update, remove, reset };
});