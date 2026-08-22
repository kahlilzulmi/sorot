import type { Ref } from 'vue'
import type { VideoInfo } from '../types/workspace'
import type { GazeImportSummary } from '../types/gazeImport'
import { useGazeStore } from '../stores/useGazeStore'
import type { useGazeSession } from './useGazeSession'

type GazeSessionApi = ReturnType<typeof useGazeSession>

export function useGazePersistence(
	gazeSession: GazeSessionApi,
	videoInfo: Ref<VideoInfo | null>
) {
	const gazeStore = useGazeStore()

	function hydrateGazeSessionFromStore(): void {
		if (gazeStore.gazeCoordinates.length > 0) {
			gazeSession.setImportedGaze(gazeStore.gazeCoordinates)
		}
	}

	function persistImportedGaze(
		samples: Parameters<typeof gazeStore.setGazeData>[0],
		fileName: string | null,
		summary: GazeImportSummary
	): void {
		gazeStore.setGazeData(samples, fileName, summary)
		gazeSession.setImportedGaze(samples)
		gazeStore.setVideoMetadata(videoInfo.value?.filename ?? null, videoInfo.value?.fps ?? null)
	}

	async function restoreFromIndexedDb(): Promise<boolean> {
		const restored = await gazeStore.restoreWorkspaceFromIndexedDb()
		if (restored) {
			hydrateGazeSessionFromStore()
		}
		return restored
	}

	async function clearLocalGazeSnapshot(): Promise<void> {
		await gazeStore.clearPersistedWorkspace()
		gazeStore.clearGazeData()
		gazeSession.clearImportedGaze()
	}

	return {
		hydrateGazeSessionFromStore,
		persistImportedGaze,
		restoreFromIndexedDb,
		clearLocalGazeSnapshot
	}
}
