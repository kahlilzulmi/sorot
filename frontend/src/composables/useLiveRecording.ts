import { ref, type Ref } from 'vue'
import { apiPost } from './useApiClient'
import type { VideoInfo } from '../types/workspace'

interface StartRecordingResponse {
	session_dir?: string
}

interface StopRecordingResponse {
	session_dir?: string
	frames_recorded?: number
	timestamps_recorded?: number
	manual_import_required?: boolean
	obs_recording_path?: string
}

export function useLiveRecording(
	videoInfo: Ref<VideoInfo | null>,
	currentFrame: Ref<number>,
	currentTime: Ref<number>,
	emitRecordFrame: (frameNum: number, timestamp: number) => void,
	setStatus: (message: string) => void,
	setPlaying: (playing: boolean) => void
) {
	const showRecordingOverlay = ref(false)
	const recording = ref(false)
	const recordingStarted = ref(false)
	const sessionDir = ref<string | null>(null)
	const framesRecorded = ref(0)
	const lastRecordedFrame = ref(-1)
	const manualImportRequired = ref(false)
	const obsRecordingPath = ref<string | null>(null)
	let recordingAnimationId: number | null = null

	function prepareRecording(): boolean {
		if (!videoInfo.value) {
			window.alert('Please load a video first')
			return false
		}
		showRecordingOverlay.value = true
		recording.value = true
		recordingStarted.value = false
		sessionDir.value = null
		obsRecordingPath.value = null
		manualImportRequired.value = false
		framesRecorded.value = 0
		lastRecordedFrame.value = -1
		currentFrame.value = 0
		setStatus('Ready to record - press START')
		setPlaying(false)
		return true
	}

	function stopRecordingLoop(): void {
		if (recordingAnimationId !== null) {
			window.cancelAnimationFrame(recordingAnimationId)
			recordingAnimationId = null
		}
	}

	function recordingFrameLoop(onAutoStop: () => Promise<void>): void {
		if (!recording.value || !videoInfo.value) {
			recordingAnimationId = null
			return
		}

		const frame = currentFrame.value
		if (frame !== lastRecordedFrame.value) {
			lastRecordedFrame.value = frame
			framesRecorded.value++
			emitRecordFrame(frame, currentTime.value)

			if (frame >= videoInfo.value.total_frames - 1) {
				void onAutoStop()
				return
			}
		}

		recordingAnimationId = window.requestAnimationFrame(() => {
			recordingFrameLoop(onAutoStop)
		})
	}

	async function startPlaybackAndRecording(onAutoStop: () => Promise<void>): Promise<void> {
		if (!videoInfo.value) return
		try {
			const response = await apiPost<StartRecordingResponse>('/api/recording/start', {
				participant_name: 'Participant'
			})
			sessionDir.value = response.session_dir ?? null
			recordingStarted.value = true
			showRecordingOverlay.value = false
			setStatus('Recording...')
			setPlaying(true)
			document.body.classList.add('recording-cursor-hidden')
			recordingFrameLoop(onAutoStop)
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Failed to start recording'
			window.alert(`Failed to start OBS recording: ${message}`)
			recording.value = false
			showRecordingOverlay.value = false
			setStatus('Recording failed to start')
		}
	}

	async function stopRecording(): Promise<void> {
		if (!recording.value) return
		if (!recordingStarted.value) {
			recording.value = false
			showRecordingOverlay.value = false
			setPlaying(false)
			setStatus('Recording cancelled')
			return
		}
		stopRecordingLoop()
		setPlaying(false)
		document.body.classList.remove('recording-cursor-hidden')

		try {
			const response = await apiPost<StopRecordingResponse>('/api/recording/stop', {})
			sessionDir.value = response.session_dir ?? sessionDir.value
			framesRecorded.value = response.frames_recorded ?? response.timestamps_recorded ?? framesRecorded.value
			manualImportRequired.value = !!response.manual_import_required
			obsRecordingPath.value = response.obs_recording_path ?? null
			setStatus(manualImportRequired.value ? 'Recording stopped (manual import required)' : 'Recording stopped')
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Failed to stop recording'
			window.alert(`Failed to stop recording: ${message}`)
			setStatus('Recording stop failed')
		} finally {
			recordingStarted.value = false
			recording.value = false
			showRecordingOverlay.value = false
		}
	}

	async function cancelRecordingPreparation(): Promise<void> {
		if (recording.value && !sessionDir.value) {
			recording.value = false
		}
		recordingStarted.value = false
		showRecordingOverlay.value = false
		setStatus('Recording cancelled')
	}

	return {
		showRecordingOverlay,
		recording,
		sessionDir,
		framesRecorded,
		manualImportRequired,
		obsRecordingPath,
		prepareRecording,
		startPlaybackAndRecording,
		stopRecording,
		cancelRecordingPreparation
	}
}
