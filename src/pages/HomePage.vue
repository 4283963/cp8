<script setup lang="ts">
import { onMounted, computed } from 'vue'
import CameraPanel from '@/components/CameraPanel.vue'
import { useVideos } from '@/composables/useVideos'
import { useStitch } from '@/composables/useStitch'
import type { CameraPosition } from '@/types'

const { data, loading, fetchVideos } = useVideos()
const { stitching, status, error: stitchError, startStitch, reset } = useStitch()

const cameras: CameraPosition[] = ['front', 'rear', 'left', 'right']

const cameraLabelMap: Record<CameraPosition, string> = {
  front: '前', rear: '后', left: '左', right: '右',
}

const slicesByCamera = computed(() => {
  if (!data.value) return { front: [], rear: [], left: [], right: [] } as Record<CameraPosition, any[]>
  const grouped = { front: [], rear: [], left: [], right: [] } as Record<CameraPosition, any[]>
  for (const slice of data.value.slices) {
    grouped[slice.camera].push(slice)
  }
  return grouped
})

const totalSlices = computed(() => data.value?.slices.length ?? 0)

const isCompleted = computed(() => status.value?.status === 'completed')
const isFailed = computed(() => status.value?.status === 'failed')

async function handleStitch() {
  await startStitch(cameras)
}

onMounted(() => {
  fetchVideos()
})
</script>

<template>
  <div class="min-h-screen flex flex-col" style="background-color: var(--bg-primary);">
    <header class="border-b px-6 py-4 flex items-center justify-between" style="border-color: var(--border-color); background-color: rgba(26, 31, 46, 0.8); backdrop-filter: blur(12px);">
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full animate-blink" style="background-color: var(--accent);"></div>
          <span class="text-xs font-medium tracking-wider" style="color: var(--accent);">LIVE</span>
        </div>
        <h1 class="text-lg font-bold tracking-wide" style="color: var(--text-primary);">
          行车记录仪视频管理系统
        </h1>
        <span class="text-xs mono px-2 py-0.5 rounded" style="background-color: var(--bg-card); color: var(--text-secondary);">v1.0</span>
      </div>
      <div class="flex items-center gap-4">
        <span class="text-xs mono" style="color: var(--text-secondary);">
          切片总数: <span style="color: var(--accent);">{{ totalSlices }}</span>
        </span>
        <button
          @click="fetchVideos"
          class="text-xs px-3 py-1.5 rounded-lg transition-colors"
          style="background-color: var(--bg-card); color: var(--text-secondary); border: 1px solid var(--border-color);"
          @mouseenter="($event.target as HTMLElement).style.borderColor = 'var(--accent)'"
          @mouseleave="($event.target as HTMLElement).style.borderColor = 'var(--border-color)'"
        >
          刷新
        </button>
      </div>
    </header>

    <main class="flex-1 p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5 max-w-6xl mx-auto">
        <CameraPanel
          v-for="camera in cameras"
          :key="camera"
          :camera="camera"
          :slices="slicesByCamera[camera]"
          :loading="loading"
        />
      </div>
    </main>

    <footer class="border-t px-6 py-5" style="border-color: var(--border-color); background-color: rgba(26, 31, 46, 0.6);">
      <div class="max-w-6xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div v-if="stitching" class="flex items-center gap-3">
            <div class="w-40 h-2 rounded-full overflow-hidden" style="background-color: var(--bg-card);">
              <div
                class="progress-bar h-full rounded-full"
                :style="{ width: `${status?.progress ?? 0}%` }"
              ></div>
            </div>
            <span class="text-xs mono" style="color: var(--accent);">
              {{ status?.progress ?? 0 }}%
            </span>
            <span class="text-xs" style="color: var(--text-secondary);">
              {{ status?.message }}
            </span>
          </div>

          <div v-else-if="isCompleted" class="flex items-center gap-2 animate-slide-up">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--success);">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            <span class="text-xs" style="color: var(--success);">拼接完成</span>
            <span class="text-xs mono" style="color: var(--text-secondary);">{{ status?.output_file }}</span>
            <button
              @click="reset"
              class="text-xs px-2 py-0.5 rounded"
              style="background-color: var(--bg-card); color: var(--text-secondary); border: 1px solid var(--border-color);"
            >
              重新拼接
            </button>
          </div>

          <div v-else-if="isFailed" class="flex items-center gap-2 animate-slide-up">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: var(--danger);">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            <span class="text-xs" style="color: var(--danger);">拼接失败: {{ stitchError || status?.message }}</span>
            <button
              @click="reset"
              class="text-xs px-2 py-0.5 rounded"
              style="background-color: var(--bg-card); color: var(--text-secondary); border: 1px solid var(--border-color);"
            >
              重试
            </button>
          </div>
        </div>

        <button
          @click="handleStitch"
          :disabled="stitching || totalSlices === 0"
          class="stitch-btn px-8 py-3 rounded-xl text-sm font-bold tracking-wide"
          style="color: var(--bg-primary);"
        >
          <span v-if="stitching" class="flex items-center gap-2">
            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            拼接中...
          </span>
          <span v-else>一键全机位拼接</span>
        </button>
      </div>
    </footer>
  </div>
</template>
