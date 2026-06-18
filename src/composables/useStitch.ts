import { ref } from 'vue'
import type { CameraPosition, StitchResponse, StitchStatusResponse } from '@/types'

export function useStitch() {
  const stitching = ref(false)
  const taskId = ref<string | null>(null)
  const status = ref<StitchStatusResponse | null>(null)
  const error = ref<string | null>(null)

  let pollTimer: ReturnType<typeof setInterval> | null = null

  async function startStitch(cameras: CameraPosition[]) {
    stitching.value = true
    error.value = null
    taskId.value = null
    status.value = null

    try {
      const res = await fetch('/api/stitch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cameras }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const result: StitchResponse = await res.json()
      taskId.value = result.task_id
      status.value = {
        task_id: result.task_id,
        status: result.status,
        output_file: result.output_file,
        message: result.message,
        progress: 0,
      }

      pollStatus()
    } catch (e: any) {
      error.value = e.message || '启动拼接失败'
      stitching.value = false
    }
  }

  function pollStatus() {
    if (pollTimer) clearInterval(pollTimer)

    pollTimer = setInterval(async () => {
      if (!taskId.value) return

      try {
        const res = await fetch(`/api/stitch/${taskId.value}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const result: StitchStatusResponse = await res.json()
        status.value = result

        if (result.status === 'completed' || result.status === 'failed') {
          if (pollTimer) clearInterval(pollTimer)
          pollTimer = null
          stitching.value = false
        }
      } catch (e: any) {
        error.value = e.message || '查询状态失败'
        if (pollTimer) clearInterval(pollTimer)
        pollTimer = null
        stitching.value = false
      }
    }, 1000)
  }

  function reset() {
    if (pollTimer) clearInterval(pollTimer)
    pollTimer = null
    stitching.value = false
    taskId.value = null
    status.value = null
    error.value = null
  }

  return { stitching, taskId, status, error, startStitch, reset }
}
