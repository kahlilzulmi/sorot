import { ref } from 'vue'

export type VideoMode = 'single' | 'dual'

export function useDualVideo() {
	const videoMode = ref<VideoMode>('single')
	const gazeVideoSrc = ref<string | null>(null)
	const gazeVideoFileName = ref<string | null>(null)

	function setGazeVideo(src: string, fileName: string): void {
		gazeVideoSrc.value = src
		gazeVideoFileName.value = fileName
		videoMode.value = 'dual'
	}

	function toggleVideoMode(): void {
		if (!gazeVideoSrc.value) return
		videoMode.value = videoMode.value === 'single' ? 'dual' : 'single'
	}

	function clearGazeVideo(): void {
		gazeVideoSrc.value = null
		gazeVideoFileName.value = null
		videoMode.value = 'single'
	}

	return {
		videoMode,
		gazeVideoSrc,
		gazeVideoFileName,
		setGazeVideo,
		toggleVideoMode,
		clearGazeVideo
	}
}

export function syncGazeVideoTime(
	stimulusVideo: HTMLVideoElement,
	gazeVideo: HTMLVideoElement,
	frameOffset: number,
	fps: number
): void {
	if (fps <= 0) return
	const offsetSeconds = frameOffset / fps
	const gazeTime = stimulusVideo.currentTime + offsetSeconds
	if (Number.isFinite(gazeTime) && gazeTime >= 0 && gazeTime <= gazeVideo.duration) {
		if (Math.abs(gazeVideo.currentTime - gazeTime) > 0.03) {
			gazeVideo.currentTime = gazeTime
		}
	}
}
