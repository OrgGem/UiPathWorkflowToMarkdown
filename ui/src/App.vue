<script setup lang="ts">
import { ref } from 'vue';
import UploadCard from './components/UploadCard.vue';
import FilesCard from './components/FilesCard.vue';
import LLMCard from './components/LLMCard.vue';
import ProcessCard from './components/ProcessCard.vue';
import type { XamlFile, LLMConfig } from './types';

const files = ref<XamlFile[]>([]);
const viewingFile = ref<XamlFile | null>(null);

const llmConfig = ref<LLMConfig>({
  enabled: false,
  apiKey: '',
  baseUrl: 'https://api.openai.com/v1',
  prompt: 'Analyze this UiPath XAML workflow and provide a concise description of its purpose and key activities.',
});

const handleFilesDiscovered = (discoveredFiles: XamlFile[]) => {
  files.value = discoveredFiles;
};

const handleFilesUpdate = (updatedFiles: XamlFile[]) => {
  files.value = updatedFiles;
};

const handleLLMConfigUpdate = (updates: Partial<LLMConfig>) => {
  llmConfig.value = { ...llmConfig.value, ...updates };
};

const handleViewFile = (file: XamlFile) => {
  viewingFile.value = file;
};

const closeFileViewer = () => {
  viewingFile.value = null;
};
</script>

<template>
  <div class="min-h-screen p-6 md:p-8">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <header class="text-center mb-10">
        <h1 class="text-4xl font-semibold mb-2 text-white">
          UiPath Workflow Analyzer
        </h1>
        <p class="text-gray-400 text-base">
          Upload, analyze, and process UiPath workflows with optional LLM enhancement
        </p>
      </header>

      <!-- Main Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <!-- Left Column -->
        <div class="space-y-5">
          <UploadCard @files-discovered="handleFilesDiscovered" />
          <LLMCard 
            :config="llmConfig"
            :files="files"
            @update-config="handleLLMConfigUpdate"
            @update-files="handleFilesUpdate"
          />
        </div>

        <!-- Right Column -->
        <div class="space-y-5">
          <FilesCard 
            :files="files"
            @update="handleFilesUpdate"
            @view-file="handleViewFile"
          />
          <ProcessCard :files="files" />
        </div>
      </div>

      <!-- Footer -->
      <footer class="text-center mt-12 text-gray-600 text-xs">
        <p>Vue 3 + Vite + TypeScript</p>
      </footer>
    </div>

    <!-- File Viewer Modal -->
    <div
      v-if="viewingFile"
      class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50"
      @click="closeFileViewer"
    >
      <div
        class="glass-card p-6 max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
        @click.stop
      >
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-xl font-bold text-white">{{ viewingFile.path }}</h3>
            <p class="text-sm text-gray-400">{{ viewingFile.checksum }}</p>
          </div>
          <button
            @click="closeFileViewer"
            class="text-gray-400 hover:text-white transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto bg-gray-900/50 rounded-lg p-4">
          <pre class="text-xs text-gray-300">{{ viewingFile.content }}</pre>
        </div>

        <div v-if="viewingFile.llmProcessed && viewingFile.llmContent" class="mt-4">
          <h4 class="text-sm font-medium text-purple-500 mb-2">LLM Processed Content:</h4>
          <div class="bg-purple-500/10 rounded-lg p-4 border border-purple-500/30">
            <pre class="text-xs text-gray-300 whitespace-pre-wrap">{{ viewingFile.llmContent }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Additional component-specific styles if needed */
</style>
