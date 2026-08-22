import { computed, ref, type Ref } from 'vue'
import type { GazeCoordinate } from '../types/gaze'
import { getGazeSampleAtTime } from '../utils/gazeRoi'

export interface LiveGazeSample {
	x: number
	y: number
	timestampMs: number
}

export function useGazeSession(currentTime: Ref<number>) {
	const importedGaze = ref<GazeCoordinate[]>([])
	const liveSample = ref<LiveGazeSample | null>(null)
	const revision = ref(0)

	const currentOverlaySample = computed<Pick<GazeCoordinate, 'x' | 'y'> | null>(() => {
		if (importedGaze.value.length > 0) {
			const sample = getGazeSampleAtTime(importedGaze.value, currentTime.value)
			if (sample) {
				return { x: sample.x, y: sample.y }
			}
		}

		if (!liveSample.value) return null
		const ageMs = Date.now() - liveSample.value.timestampMs
		if (ageMs > 1200) return null
		return { x: liveSample.value.x, y: liveSample.value.y }
	})

	function setImportedGaze(samples: GazeCoordinate[]): void {
		importedGaze.value = samples
		revision.value++
	}

	function clearImportedGaze(): void {
		importedGaze.value = []
		revision.value++
	}

	function pushLiveGaze(x: number, y: number): void {
		liveSample.value = {
			x,
			y,
			timestampMs: Date.now()
		}
		revision.value++
	}

	return {
		importedGaze,
		liveSample,
		revision,
		currentOverlaySample,
		setImportedGaze,
		clearImportedGaze,
		pushLiveGaze
	}
}
