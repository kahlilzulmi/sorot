import { computed, ref, type Ref } from 'vue'
import { apiGet, apiPost, apiPostForm } from './useApiClient'
import type { VideoInfo } from '../types/workspace'

interface YoutubeDownloadResponse extends VideoInfo {
	filename: string
}

export function useVideoSession(
	videoInfo: Ref<VideoInfo | null>,
	currentFrame: Ref<number>,
	setStatus: (message: string) => void,
	onVideoReady: () => Promise<void>
) {
	const videoSrc = ref('')
	const playing = ref(false)
	const lastYoutubeUrl = ref('')

	const currentTime = computed(() => {
		if (!videoInfo.value || videoInfo.value.fps <= 0) return 0
		return currentFrame.value / videoInfo.value.fps
	})

	const videoDuration = computed(() => videoInfo.value?.duration ?? 0)

	function setVideoFromInfo(info: VideoInfo): void {
		videoInfo.value = info
		videoSrc.value = `/video/${info.filename}`
		currentFrame.value = 0
		playing.value = false
	}

	async function loadVideoInfo(): Promise<boolean> {
		try {
			const info = await apiGet<VideoInfo>('/api/video-info')
			setVideoFromInfo(info)
			await onVideoReady()
			setStatus('Video loaded')
			return true
		} catch {
			return false
		}
	}

	async function uploadVideo(file: File): Promise<boolean> {
		setStatus('Uploading video...')
		const formData = new FormData()
		formData.append('video', file)
		try {
			const info = await apiPostForm<VideoInfo>('/api/upload-video', formData)
			setVideoFromInfo(info)
			await onVideoReady()
			setStatus('Video loaded')
			return true
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Upload failed'
			window.alert(`Failed to upload video: ${message}`)
			setStatus('Upload failed')
			return false
		}
	}

	async function downloadYoutube(url: string): Promise<boolean> {
		if (!url.trim()) {
			window.alert('Please enter a YouTube URL')
			return false
		}
		setStatus('Downloading from YouTube...')
		try {
			const info = await apiPost<YoutubeDownloadResponse>('/api/download-youtube', { url })
			setVideoFromInfo(info)
			lastYoutubeUrl.value = url
			await onVideoReady()
			setStatus('Video downloaded')
			return true
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Download failed'
			window.alert(`Failed to download video: ${message}`)
			setStatus('Download failed')
			return false
		}
	}

	function seekFrame(frame: number): void {
		if (!videoInfo.value) return
		const max = Math.max(0, videoInfo.value.total_frames - 1)
		currentFrame.value = Math.max(0, Math.min(frame, max))
	}

	function togglePlay(): void {
		playing.value = !playing.value
	}

	function pause(): void {
		playing.value = false
	}

	function nextFrame(): void {
		if (!videoInfo.value) return
		if (currentFrame.value < videoInfo.value.total_frames - 1) {
			pause()
			seekFrame(currentFrame.value + 1)
		}
	}

	function prevFrame(): void {
		if (currentFrame.value > 0) {
			pause()
			seekFrame(currentFrame.value - 1)
		}
	}

	function jumpToStart(): void {
		pause()
		seekFrame(0)
	}

	function jumpToEnd(): void {
		if (!videoInfo.value) return
		pause()
		seekFrame(videoInfo.value.total_frames - 1)
	}

	return {
		videoSrc,
		playing,
		lastYoutubeUrl,
		currentTime,
		videoDuration,
		loadVideoInfo,
		uploadVideo,
		downloadYoutube,
		seekFrame,
		togglePlay,
		pause,
		nextFrame,
		prevFrame,
		jumpToStart,
		jumpToEnd
	}
}
