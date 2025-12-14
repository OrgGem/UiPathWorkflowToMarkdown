<template>
  <div class="glass-card p-6">
    <h2 class="text-2xl font-bold mb-4 bg-gradient-to-r from-purple-500 to-blue-500 bg-clip-text text-transparent">
      Discovered Files
    </h2>
    
    <div v-if="files.length === 0" class="text-center py-8 text-gray-500">
      No files discovered yet. Upload an archive to get started.
    </div>

    <div v-else>
      <div class="flex items-center justify-between mb-4">
        <p class="text-gray-400">
          {{ files.length }} XAML file(s) found, {{ selectedCount }} selected
        </p>
        <div class="flex gap-2">
          <button @click="selectAll" class="glass-button-secondary px-4 py-2 text-sm">
            Select All
          </button>
          <button @click="selectNone" class="glass-button-secondary px-4 py-2 text-sm">
            Select None
          </button>
        </div>
      </div>

      <div class="space-y-2 max-h-96 overflow-y-auto">
        <div
          v-for="(file, index) in files"
          :key="file.checksum"
          class="flex items-center gap-3 p-4 rounded-lg transition-all cursor-pointer"
          :class="file.selected ? 'bg-purple-500/20 border border-purple-500/50' : 'bg-glass/30 border border-white/10 hover:bg-glass/50'"
          @click="toggleSelection(index)"
        >
          <input
            type="checkbox"
            :checked="file.selected"
            @change.stop="toggleSelection(index)"
            class="w-5 h-5 rounded border-gray-600 bg-glass text-purple-500 focus:ring-purple-500 focus:ring-offset-0"
          />
          
          <div class="flex-1 min-w-0">
            <p class="text-white font-medium truncate">{{ file.path }}</p>
            <div class="flex items-center gap-4 text-xs text-gray-400 mt-1">
              <span>{{ formatBytes(file.size) }}</span>
              <span class="font-mono">{{ file.checksum.slice(0, 8) }}...</span>
              <span v-if="file.llmProcessed" class="text-purple-500">✓ LLM Processed</span>
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
