<template>
  <div class="glass-card p-5">
    <h2 class="text-xl font-semibold mb-4 text-white">
      Discovered Files
    </h2>
    
    <div v-if="files.length === 0" class="text-center py-8 text-gray-500 text-sm">
      No files discovered yet. Upload an archive to get started.
    </div>

    <div v-else>
      <div class="flex items-center justify-between mb-3">
        <p class="text-gray-400 text-sm">
          {{ files.length }} XAML file(s) found, {{ selectedCount }} selected
        </p>
        <div class="flex gap-2">
          <button @click="selectAll" class="glass-button-secondary px-3 py-1.5 text-xs">
            Select All
          </button>
          <button @click="selectNone" class="glass-button-secondary px-3 py-1.5 text-xs">
            Select None
          </button>
        </div>
      </div>

      <div class="space-y-2 max-h-96 overflow-y-auto">
        <div
          v-for="(file, index) in files"
          :key="file.checksum"
          class="flex items-center gap-3 p-3 rounded-md transition-colors cursor-pointer"
          :class="file.selected ? 'bg-purple-500/10 border border-purple-600' : 'bg-gray-800/30 border border-gray-700 hover:bg-gray-800/50'"
          @click="toggleSelection(index)"
        >
          <input
            type="checkbox"
            :checked="file.selected"
            @change.stop="toggleSelection(index)"
            class="w-4 h-4 rounded border-gray-600 bg-gray-900 text-purple-600 focus:ring-purple-600 focus:ring-offset-0"
          />
          
          <div class="flex-1 min-w-0">
            <p class="text-white text-sm font-medium truncate">{{ file.path }}</p>
            <div class="flex items-center gap-3 text-xs text-gray-400 mt-0.5">
              <span>{{ formatBytes(file.size) }}</span>
              <span class="font-mono">{{ file.checksum.slice(0, 8) }}...</span>
              <span v-if="file.llmProcessed" class="text-purple-400">✓ LLM Processed</span>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button
              @click.stop="$emit('viewFile', file)"
              class="p-2 rounded hover:bg-white/10 transition-colors"
              title="View content"
            >
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatBytes } from '../utils/checksum';
import type { XamlFile } from '../types';

const props = defineProps<{
  files: XamlFile[];
}>();

const emit = defineEmits<{
  update: [files: XamlFile[]];
  viewFile: [file: XamlFile];
}>();

const selectedCount = computed(() => {
  return props.files.filter(f => f.selected).length;
});

const toggleSelection = (index: number) => {
  if (index < 0 || index >= props.files.length) return;
  const updated = [...props.files];
  const file = updated[index];
  if (file) {
    file.selected = !file.selected;
  }
  emit('update', updated);
};

const selectAll = () => {
  const updated = props.files.map(f => ({ ...f, selected: true }));
  emit('update', updated);
};

const selectNone = () => {
  const updated = props.files.map(f => ({ ...f, selected: false }));
  emit('update', updated);
};
</script>
