import { ref } from 'vue';
import { defineStore } from 'pinia';

const DB_NAME = 'digi-school';
const DB_VERSION = 1;
const STORE_NAME = 'lesson_library_assets';

let dbPromise = null;

function makeId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function openDatabase() {
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        }
      };

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('Failed to open lesson library database'));
    });
  }

  return dbPromise;
}

async function readAllAssets() {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const request = store.getAll();

    request.onsuccess = () => {
      const assets = (request.result || []).sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
      resolve(assets);
    };
    request.onerror = () => reject(request.error || new Error('Failed to read lesson library assets'));
  });
}

async function writeAssets(assetsToStore) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);

    for (const asset of assetsToStore) {
      store.put(asset);
    }

    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error || new Error('Failed to save lesson library assets'));
  });
}

async function deleteAssetById(assetId) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    store.delete(assetId);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error || new Error('Failed to delete lesson library asset'));
  });
}

export const useLessonLibraryStore = defineStore('lessonLibrary', () => {
  const assets = ref([]);
  const loading = ref(false);
  const loaded = ref(false);

  let loadPromise = null;

  async function load(force = false) {
    if (loaded.value && !force) return assets.value;
    if (loadPromise) return loadPromise;

    loadPromise = (async () => {
      loading.value = true;
      try {
        assets.value = await readAllAssets();
        loaded.value = true;
        return assets.value;
      } finally {
        loading.value = false;
        loadPromise = null;
      }
    })();

    return loadPromise;
  }

  async function addFiles(fileList) {
    const files = Array.from(fileList || []);
    if (files.length === 0) return [];

    const now = new Date().toISOString();
    const nextAssets = files.map((file) => ({
      id: makeId(),
      name: file.name,
      size: file.size,
      type: file.type || file.name.split('.').pop() || 'application/octet-stream',
      createdAt: now,
      source: 'library',
      blob: file.slice(0, file.size, file.type || undefined),
    }));

    await writeAssets(nextAssets);
    await load(true);
    return nextAssets;
  }

  async function remove(assetId) {
    await deleteAssetById(assetId);
    assets.value = assets.value.filter((asset) => asset.id !== assetId);
  }

  async function getById(assetId) {
    if (!assetId) return null;
    const found = assets.value.find((asset) => asset.id === assetId);
    if (found) return found;

    const db = await openDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const request = store.get(assetId);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error || new Error('Failed to load lesson library asset'));
    });
  }

  function reset() {
    assets.value = [];
    loaded.value = false;
    loadPromise = null;
  }

  return {
    assets,
    loading,
    loaded,
    load,
    addFiles,
    remove,
    getById,
    reset,
  };
});
