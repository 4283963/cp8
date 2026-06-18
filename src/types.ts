export type CameraPosition = 'front' | 'rear' | 'left' | 'right'

export interface VideoSlice {
  filename: string
  camera: CameraPosition
  timestamp: string
  size_kb: number
}

export type CameraStatus = 'ok' | 'lost'

export interface VideoSummary {
  front: number
  rear: number
  left: number
  right: number
  front_status: CameraStatus
  rear_status: CameraStatus
  left_status: CameraStatus
  right_status: CameraStatus
}

export interface VideosResponse {
  slices: VideoSlice[]
  summary: VideoSummary
}

export interface StitchResponse {
  task_id: string
  status: 'processing' | 'completed' | 'failed'
  output_file?: string
  message: string
}

export interface StitchStatusResponse {
  task_id: string
  status: 'processing' | 'completed' | 'failed'
  output_file?: string
  message: string
  progress: number
}
