<template>
  <div class="glass-card p-5">
    <h2 class="text-xl font-semibold mb-4 text-white">
      Process & Send to Backend
    </h2>

    <div class="space-y-4">
      <div class="bg-glass/30 rounded-lg p-4 border border-white/10">
        <h3 class="font-medium text-white mb-2">Summary</h3>
        <div class="space-y-1 text-sm text-gray-400">
          <p>Total files: {{ files.length }}</p>
          <p>Selected files: {{ selectedFiles.length }}</p>
          <p>LLM processed: {{ llmProcessedCount }}</p>
        </div>
      </div>

      <div>
        <label class="flex items-center gap-3 cursor-pointer mb-2">
          <input
            type="checkbox"
            v-model="sendLLMContent"
            class="w-5 h-5 rounded border-gray-600 bg-glass text-purple-500 focus:ring-purple-500 focus:ring-offset-0"
          />
          <span class="text-white font-medium">Send LLM-processed content to backend</span>
        </label>
        <p class="text-sm text-gray-400 ml-8">
          If enabled, sends LLM-processed content instead of raw XAML
        </p>
      </div>

      <button
        @click="sendToBackend"
        :disabled="selectedFiles.length === 0 || processing"
        class="glass-button w-full"
        :class="{ 'opacity-50 cursor-not-allowed': selectedFiles.length === 0 || processing }"
      >
        {{ processing ? 'Sending...' : 'Send to Backend' }}
      </button>

      <div v-if="processing" class="text-center py-4">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
        <p class="text-gray-400 mt-2">{{ status }}</p>
      </div>

      <div v-if="error" class="p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
        {{ error }}
      </div>

      <div v-if="success" class="p-4 bg-green-500/10 border border-green-500/50 rounded-lg text-green-400 text-sm">
        Successfully sent {{ selectedFiles.length }} file(s) to backend
      </div>

      <div v-if="previewContent" class="mt-6">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-medium text-white">Preview</h3>
          <button
            @click="downloadMarkdown"
            class="glass-button-secondary px-4 py-2 text-sm"
          >
            Download Markdown
          </button>
        </div>
        <div class="bg-gray-900/50 rounded-lg p-4 border border-white/10 max-h-96 overflow-y-auto">
          <pre class="text-sm text-gray-300 whitespace-pre-wrap">{{ previewContent }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { BackendConfig, LLMConfig, XamlFile } from '../types';

const props = defineProps<{
  files: XamlFile[];
  apiUrl?: string;
  llmConfig?: LLMConfig;
}>();

const processing = ref(false);
const status = ref('');
const error = ref('');
const success = ref(false);
const sendLLMContent = ref(false);
const previewContent = ref('');

const selectedFiles = computed(() => {
  return props.files.filter(f => f.selected);
});

const llmProcessedCount = computed(() => {
  return props.files.filter(f => f.llmProcessed).length;
});

const backendConfig = computed<BackendConfig | undefined>(() => {
  if (!props.llmConfig || !props.llmConfig.enabled || !props.llmConfig.apiKey) {
    return undefined;
  }

  return {
    use_llm: true,
    api_key: props.llmConfig.apiKey,
    base_url: props.llmConfig.baseUrl,
    model: props.llmConfig.model,
    prompt: props.llmConfig.prompt,
    use_source: true,
  };
});

const sendToBackend = async () => {
  if (selectedFiles.value.length === 0) return;

  processing.value = true;
  error.value = '';
  success.value = false;
  previewContent.value = '';
  status.value = 'Preparing payload...';

  try {
    // Determine the API endpoint
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
    const baseUrl = props.apiUrl || apiBaseUrl || window.location.origin;
    const endpoint = `${baseUrl}/api/workflows/ingest`;

    // Prepare the payload
    const payload = {
      files: selectedFiles.value.map(file => ({
        path: file.path,
        size: file.size,
        checksum: file.checksum,
        content: sendLLMContent.value && file.llmContent ? file.llmContent : file.content,
        llmProcessed: sendLLMContent.value && file.llmProcessed,
      })),
      ...(backendConfig.value ? { config: backendConfig.value } : {}),
    };

    status.value = 'Sending to backend...';

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Backend request failed: ${response.status} ${text}`);
    }

    // Check if response is markdown
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('text/markdown') || contentType?.includes('text/plain')) {
      previewContent.value = await response.text();
    } else {
      const data = await response.json();
      previewContent.value = JSON.stringify(data, null, 2);
    }

    success.value = true;
    status.value = 'Complete';
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unknown error occurred';
    console.error('Backend send error:', err);
  } finally {
    processing.value = false;
  }
};

const downloadMarkdown = () => {
  if (!previewContent.value) return;

  const blob = new Blob([previewContent.value], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'workflow-analysis.md';
  link.click();
  URL.revokeObjectURL(url);
};
</script>
