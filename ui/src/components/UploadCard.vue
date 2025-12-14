<template>
  <div class="glass-card p-6">
    <h2 class="text-2xl font-bold mb-4 bg-gradient-to-r from-purple-500 to-blue-500 bg-clip-text text-transparent">
      Upload Archive
    </h2>
    <p class="text-gray-400 mb-4">
      Select a UiPath project archive (.zip or .nupkg) to analyze
    </p>
    
    <div 
      class="border-2 border-dashed rounded-lg p-8 text-center transition-colors"
      :class="dragActive ? 'border-purple-500 bg-purple-500/10' : 'border-white/10'"
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
        <svg class="w-16 h-16 mx-auto mb-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p class="text-gray-300 mb-2">Click to browse or drag and drop</p>
        <p class="text-sm text-gray-500">.zip or .nupkg files</p>
      </div>
      
      <div v-else class="text-left">
        <div class="flex items-center justify-between bg-glass/50 rounded-lg p-4">
          <div class="flex items-center space-x-3">
            <svg class="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div>
              <p class="font-medium text-white">{{ file.name }}</p>
              <p class="text-sm text-gray-400">{{ formatBytes(file.size) }}</p>
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
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      <p class="text-gray-400 mt-2">{{ status }}</p>
    </div>

    <div v-if="error" class="mt-4 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
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
