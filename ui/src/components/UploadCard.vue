<template>
  <div class="glass-card p-5">
    <h2 class="text-xl font-semibold mb-4 text-white">
      Upload Archive
    </h2>
    <p class="text-gray-400 mb-4 text-sm">
      Select a UiPath project archive (.zip or .nupkg) to analyze
    </p>
    
    <div 
      class="border-2 border-dashed rounded-md p-6 text-center transition-colors"
      :class="dragActive ? 'border-purple-500 bg-purple-500/5' : 'border-gray-700'"
      @dragover.prevent="dragActive = true"
      @dragleave.prevent="dragActive = false"
      @drop.prevent="handleDrop"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".zip,.nupkg"
        @change="handleFileSelect"
        class="hidden"
      />
      
      <div v-if="!file" class="cursor-pointer" @click="() => fileInput?.click()">
        <svg class="w-12 h-12 mx-auto mb-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p class="text-gray-300 mb-1 text-sm">Click to browse or drag and drop</p>
        <p class="text-xs text-gray-500">.zip or .nupkg files</p>
      </div>
      
      <div v-else class="text-left">
        <div class="flex items-center justify-between bg-gray-800/50 rounded-md p-3">
          <div class="flex items-center space-x-3">
            <svg class="w-7 h-7 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div>
              <p class="font-medium text-white text-sm">{{ file.name }}</p>
              <p class="text-xs text-gray-400">{{ formatBytes(file.size) }}</p>
            </div>
          </div>
          <button
            @click="clearFile"
            class="text-gray-400 hover:text-red-400 transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <button
      v-if="file && !processing"
      @click="processArchive"
      class="glass-button w-full mt-4"
    >
      Process Archive
    </button>

    <div v-if="processing" class="mt-4 text-center">
      <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500"></div>
      <p class="text-gray-400 mt-2 text-sm">{{ status }}</p>
    </div>

    <div v-if="error" class="mt-4 p-3 bg-red-900/20 border border-red-800 rounded-md text-red-400 text-sm">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import JSZip from 'jszip';
import { computeChecksum, formatBytes } from '../utils/checksum';
import type { XamlFile } from '../types';

const emit = defineEmits<{
  filesDiscovered: [files: XamlFile[]];
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const file = ref<File | null>(null);
const dragActive = ref(false);
const processing = ref(false);
const status = ref('');
const error = ref('');

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    file.value = target.files[0];
    error.value = '';
  }
};

const handleDrop = (event: DragEvent) => {
  dragActive.value = false;
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile.name.match(/\.(zip|nupkg)$/i)) {
      file.value = droppedFile;
      error.value = '';
    } else {
      error.value = 'Please select a .zip or .nupkg file';
    }
  }
};

const clearFile = () => {
  file.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const processArchive = async () => {
  if (!file.value) return;

  processing.value = true;
  status.value = 'Extracting archive...';
  error.value = '';

  try {
    const zip = new JSZip();
    const contents = await zip.loadAsync(file.value);
    
    status.value = 'Searching for XAML files...';
    const xamlFiles: XamlFile[] = [];
    
    for (const [path, zipEntry] of Object.entries(contents.files)) {
      if (path.toLowerCase().endsWith('.xaml') && !zipEntry.dir) {
        status.value = `Processing ${path}...`;
        const content = await zipEntry.async('text');
        const checksum = await computeChecksum(content);
        
        xamlFiles.push({
          path,
          size: content.length,
          checksum,
          content,
          selected: true,
        });
      }
    }

    if (xamlFiles.length === 0) {
      error.value = 'No XAML files found in the archive';
    } else {
      status.value = `Found ${xamlFiles.length} XAML file(s)`;
      emit('filesDiscovered', xamlFiles);
    }
  } catch (err) {
    error.value = `Failed to process archive: ${err instanceof Error ? err.message : 'Unknown error'}`;
  } finally {
    processing.value = false;
  }
};
</script>
