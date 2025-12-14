<template>
  <div class="glass-card p-5">
    <h2 class="text-xl font-semibold mb-4 text-white">
      LLM Preprocessing
    </h2>
    
    <div class="mb-6">
      <label class="flex items-center gap-3 cursor-pointer">
        <input
          type="checkbox"
          :checked="config.enabled"
          @change="updateEnabled"
          class="w-5 h-5 rounded border-gray-600 bg-glass text-purple-500 focus:ring-purple-500 focus:ring-offset-0"
        />
        <span class="text-white font-medium">Enable LLM Preprocessing</span>
      </label>
      <p class="text-sm text-gray-400 mt-2">
        Process XAML files with an OpenAI-compatible LLM before sending to backend.
        Your API key stays in the browser.
      </p>
    </div>

    <div v-if="config.enabled" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          API Key
        </label>
        <input
          type="password"
          :value="config.apiKey"
          @input="updateApiKey"
          placeholder="sk-..."
          class="glass-input"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          Base URL
        </label>
        <input
          type="text"
          :value="config.baseUrl"
          @input="updateBaseUrl"
          placeholder="https://api.openai.com/v1"
          class="glass-input"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          System Prompt
        </label>
        <textarea
          :value="config.prompt"
          @input="updatePrompt"
          rows="4"
          placeholder="Enter instructions for the LLM..."
          class="glass-input resize-none"
        ></textarea>
      </div>

      <button
        v-if="hasSelectedFiles"
        @click="runLLMProcessing"
        :disabled="!config.apiKey || processing"
        class="glass-button w-full"
        :class="{ 'opacity-50 cursor-not-allowed': !config.apiKey || processing }"
      >
        {{ processing ? 'Processing...' : `Process ${selectedFilesCount} Selected File(s)` }}
      </button>

      <div v-if="processing" class="mt-4">
        <div class="flex items-center justify-between text-sm text-gray-400 mb-2">
          <span>{{ status }}</span>
          <span>{{ processedCount }} / {{ selectedFilesCount }}</span>
        </div>
        <div class="w-full bg-glass rounded-full h-2">
          <div
            class="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-300"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
      </div>

      <div v-if="error" class="mt-4 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
        {{ error }}
      </div>

      <div v-if="successCount > 0" class="mt-4 p-4 bg-green-500/10 border border-green-500/50 rounded-lg text-green-400 text-sm">
        Successfully processed {{ successCount }} file(s)
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { LLMConfig, XamlFile, ChatCompletionRequest, ChatCompletionResponse } from '../types';

const props = defineProps<{
  config: LLMConfig;
  files: XamlFile[];
}>();

const emit = defineEmits<{
  updateConfig: [config: Partial<LLMConfig>];
  updateFiles: [files: XamlFile[]];
}>();

const processing = ref(false);
const status = ref('');
const error = ref('');
const processedCount = ref(0);
const successCount = ref(0);

const hasSelectedFiles = computed(() => {
  return props.files.some(f => f.selected);
});

const selectedFilesCount = computed(() => {
  return props.files.filter(f => f.selected).length;
});

const progress = computed(() => {
  if (selectedFilesCount.value === 0) return 0;
  return (processedCount.value / selectedFilesCount.value) * 100;
});

const updateEnabled = (e: Event) => {
  const target = e.target as HTMLInputElement;
  emit('updateConfig', { enabled: target.checked });
};

const updateApiKey = (e: Event) => {
  const target = e.target as HTMLInputElement;
  emit('updateConfig', { apiKey: target.value });
};

const updateBaseUrl = (e: Event) => {
  const target = e.target as HTMLInputElement;
  emit('updateConfig', { baseUrl: target.value });
};

const updatePrompt = (e: Event) => {
  const target = e.target as HTMLTextAreaElement;
  emit('updateConfig', { prompt: target.value });
};

const runLLMProcessing = async () => {
  if (!props.config.apiKey) return;

  processing.value = true;
  error.value = '';
  processedCount.value = 0;
  successCount.value = 0;

  const selectedFiles = props.files.filter(f => f.selected);
  const updatedFiles = [...props.files];

  for (const file of selectedFiles) {
    const fileIndex = props.files.findIndex(f => f.checksum === file.checksum);
    status.value = `Processing ${file.path}...`;

    try {
      const request: ChatCompletionRequest = {
        model: 'gpt-4',
        messages: [
          {
            role: 'system',
            content: props.config.prompt || 'You are a helpful assistant that processes UiPath XAML workflow files.',
          },
          {
            role: 'user',
            content: `Process this XAML file:\n\n${file.content}`,
          },
        ],
        temperature: 0.7,
      };

      const response = await fetch(`${props.config.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${props.config.apiKey}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      const data: ChatCompletionResponse = await response.json();
      const llmContent = data.choices[0]?.message?.content || '';

      if (fileIndex >= 0 && fileIndex < updatedFiles.length) {
        const existingFile = updatedFiles[fileIndex];
        if (existingFile) {
          updatedFiles[fileIndex] = {
            ...existingFile,
            llmProcessed: true,
            llmContent,
          };
        }
      }

      successCount.value++;
    } catch (err) {
      error.value = `Failed to process ${file.path}: ${err instanceof Error ? err.message : 'Unknown error'}`;
      console.error('LLM processing error:', err);
    }

    processedCount.value++;
  }

  emit('updateFiles', updatedFiles);
  processing.value = false;
  status.value = 'Complete';
};
</script>
