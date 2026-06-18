import { ref } from 'vue'
import type { VideosResponse } from '@/types'

export function useVideos() {
  const data = ref<VideosResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchVideos() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/videos')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      data.value = await res.json()
    } catch (e: any) {
      error.value = e.message || '获取视频列表失败'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, fetchVideos }
}
