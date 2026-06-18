<script setup lang="ts">
import type { VideoSlice, CameraPosition, CameraStatus } from '@/types'
import { computed } from 'vue'

const props = defineProps<{
  camera: CameraPosition
  slices: VideoSlice[]
  loading: boolean
  status: CameraStatus
}>()

const cameraLabel: Record<CameraPosition, string> = {
  front: '前',
  rear: '后',
  left: '左',
  right: '右',
}

const cameraIcon: Record<CameraPosition, string> = {
  front: '▲',
  rear: '▼',
  left: '◄',
  right: '►',
}

const isLost = computed(() => props.status === 'lost')

const sortedSlices = computed(() =>
  [...props.slices].sort((a, b) => a.timestamp.localeCompare(b.timestamp))
)

const totalSize = computed(() => {
  const kb = props.slices.reduce((sum, s) => sum + s.size_kb, 0)
  if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`
  return `${kb} KB`
})

function formatTime(ts: string) {
  return ts.replace(/^\d{4}-\d{2}-\d{2} /, '')
}
</script>

<template>
  <div
    class="camera-panel rounded-xl p-5 relative overflow-hidden"
    :style="{
      backgroundColor: isLost ? '#0a0000' : 'var(--bg-card)',
      borderColor: isLost ? '#7f1d1d' : 'var(--border-color)',
    }"
  >
    <div v-if="!isLost" class="scan-line absolute inset-0 pointer-events-none overflow-hidden"></div>

    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold"
          :style="isLost ? 'background-color: #370000; color: #ef4444;' : 'background: linear-gradient(135deg, var(--accent), var(--accent-blue)); color: var(--bg-primary);'"
        >
          {{ cameraIcon[camera] }}
        </div>
        <div>
          <h3 class="text-base font-semibold" :style="isLost ? 'color: #ef4444;' : 'color: var(--text-primary);'">
            {{ cameraLabel[camera] }}方摄像头
          </h3>
          <p class="text-xs mono" :style="isLost ? 'color: #991b1b;' : 'color: var(--text-secondary);'">
            {{ camera.toUpperCase() }} CAM
          </p>
        </div>
      </div>
      <div class="text-right">
        <div v-if="isLost" class="text-sm font-bold" style="color: #ef4444;">
          信号丢失
        </div>
        <div v-else class="text-sm font-medium" style="color: var(--accent);">
          {{ slices.length }} <span class="text-xs" style="color: var(--text-secondary);">个切片</span>
        </div>
        <div v-if="!isLost" class="text-xs mono" style="color: var(--text-secondary);">
          {{ totalSize }}
        </div>
        <div v-else class="text-xs" style="color: #991b1b;">
          NO SIGNAL
        </div>
      </div>
    </div>

    <div v-if="loading" class="space-y-2">
      <div v-for="i in 3" :key="i" class="h-8 rounded-lg animate-pulse" style="background-color: var(--bg-card-hover);"></div>
    </div>

    <div v-else-if="isLost" class="relative flex items-center justify-center" style="height: 192px; background-color: #000;">
      <div class="text-center z-10">
        <svg class="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: #ef4444;">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
        </svg>
        <p class="text-lg font-bold tracking-wider" style="color: #ef4444;">摄像头暂无信号</p>
        <p class="text-xs mt-1" style="color: #7f1d1d;">CAMERA OFFLINE</p>
      </div>
      <div class="absolute inset-0 flex items-center justify-center opacity-20">
        <div class="text-6xl font-bold" style="color: #ef4444;">NO SIGNAL</div>
      </div>
    </div>

    <div v-else-if="slices.length === 0" class="py-6 text-center">
      <p class="text-sm" style="color: var(--text-secondary);">暂无视频切片</p>
    </div>

    <div v-else class="space-y-1 max-h-48 overflow-y-auto pr-1" style="scrollbar-width: thin; scrollbar-color: var(--border-color) transparent;">
      <div
        v-for="slice in sortedSlices"
        :key="slice.filename"
        class="slice-item flex items-center justify-between px-3 py-2 rounded-lg"
      >
        <div class="flex items-center gap-2 min-w-0">
          <div class="w-1.5 h-1.5 rounded-full flex-shrink-0" style="background-color: var(--accent);"></div>
          <span class="mono text-xs truncate" style="color: var(--text-primary);">{{ slice.filename }}</span>
        </div>
        <div class="flex items-center gap-3 flex-shrink-0 ml-2">
          <span class="mono text-xs" style="color: var(--text-secondary);">{{ formatTime(slice.timestamp) }}</span>
          <span class="text-xs" style="color: var(--text-secondary);">{{ slice.size_kb >= 1024 ? (slice.size_kb / 1024).toFixed(1) + 'M' : slice.size_kb + 'K' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
