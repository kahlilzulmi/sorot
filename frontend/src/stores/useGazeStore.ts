import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { GazeCoordinate } from '../types/gaze'
import type { GazeImportSummary } from '../types/gazeImport'
import { sortGazeByTimestamp } from '../utils/findGazeAtTime'
import {
	clearWorkspaceSnapshot,
	loadWorkspaceSnapshot,
	saveWorkspaceSnapshot,
	type PersistedGazeSnapshot
} from '../utils/gazePersistence'

export type { GazeImportSummary } from '../types/gazeImport'

/** Pinia store for imported gaze samples + IndexedDB persistence (ROIs live in `scenes[].rois[]`). */
export const useGazeStore = defineStore('gaze', () => {
	const gazeCoordinates = ref<GazeCoordinate[]>([])
	const gazeDataRevision = ref(0)
	const sourceFileName = ref<string | null>(null)
	const importSummary = ref<GazeImportSummary | null>(null)
	const videoFileName = ref<string | null>(null)
	const videoFps = ref<number | null>(null)

	const gazeSampleCount = computed(() => gazeCoordinates.value.length)

	function buildPersistenceSnapshot(): PersistedGazeSnapshot {
		return {
			gazeCoordinates: gazeCoordinates.value,
			sourceFileName: sourceFileName.value,
			videoFileName: videoFileName.value,
			videoFps: videoFps.value,
			importSummary: importSummary.value,
			savedAt: new Date().toISOString()
		}
	}

	function persistWorkspace(): void {
		void saveWorkspaceSnapshot(buildPersistenceSnapshot())
	}

	function setGazeData(
		coordinates: GazeCoordinate[],
		fileName: string | null,
		summary: GazeImportSummary
	): void {
		gazeCoordinates.value = sortGazeByTimestamp(coordinates)
		gazeDataRevision.value += 1
		sourceFileName.value = fileName
		importSummary.value = summary
		persistWorkspace()
	}

	function setVideoMetadata(fileName: string | null, fps: number | null): void {
		videoFileName.value = fileName
		videoFps.value = fps && fps > 0 ? fps : null
		persistWorkspace()
	}

	function setGazeCoordinates(coordinates: GazeCoordinate[]): void {
		gazeCoordinates.value = sortGazeByTimestamp(coordinates)
		gazeDataRevision.value += 1
		sourceFileName.value = null
		importSummary.value = null
	}

	function clearGazeData(): void {
		gazeCoordinates.value = []
		gazeDataRevision.value += 1
		sourceFileName.value = null
		importSummary.value = null
		persistWorkspace()
	}

	async function restoreWorkspaceFromIndexedDb(): Promise<boolean> {
		const snapshot = await loadWorkspaceSnapshot()
		if (!snapshot) {
			return false
		}

		gazeCoordinates.value = sortGazeByTimestamp(snapshot.gazeCoordinates)
		gazeDataRevision.value += 1
		sourceFileName.value = snapshot.sourceFileName
		videoFileName.value = snapshot.videoFileName
		videoFps.value = snapshot.videoFps
		importSummary.value = snapshot.importSummary
		return gazeCoordinates.value.length > 0
	}

	async function clearPersistedWorkspace(): Promise<void> {
		await clearWorkspaceSnapshot()
	}

	return {
		gazeCoordinates,
		gazeDataRevision,
		sourceFileName,
		importSummary,
		videoFileName,
		videoFps,
		gazeSampleCount,
		setGazeData,
		setGazeCoordinates,
		setVideoMetadata,
		clearGazeData,
		restoreWorkspaceFromIndexedDb,
		clearPersistedWorkspace
	}
})
