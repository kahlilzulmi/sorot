import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { MIN_ROI_DIMENSION } from '../constants/gaze'
import type { GazeCoordinate, RegionOfInterest } from '../types/gaze'
import type { GazeTimestampUnit } from '../utils/gazeTimestamp'
import { sortGazeByTimestamp } from '../utils/findGazeAtTime'
import {
	clearWorkspaceSnapshot,
	loadWorkspaceSnapshot,
	saveWorkspaceSnapshot,
	type PersistedWorkspace
} from '../utils/gazePersistence'

export interface GazeImportSummary {
	validRowCount: number
	skippedRowCount: number
	columnMapping: {
		x: string
		y: string
		timestamp: string
	}
	/** Unit detected in CSV before normalization. */
	timestampUnit: GazeTimestampUnit
	/** FPS used when converting frame indices to seconds. */
	assumedVideoFps: number | null
	warnings: string[]
}

export interface RoiBounds {
	x: number
	y: number
	width: number
	height: number
}

const ROI_COLOR_PALETTE = [
	'#61AFEF',
	'#98C379',
	'#E5C07B',
	'#E06C75',
	'#C678DD',
	'#56B6C2',
	'#D19A66',
	'#BE5046'
] as const

function createRegionId(): string {
	return crypto.randomUUID()
}

function ensureRegionId(region: RegionOfInterest): RegionOfInterest {
	if (region.id) {
		return region
	}
	return { ...region, id: createRegionId() }
}

export const useGazeStore = defineStore('gaze', () => {
	const isPlaying = ref(false)
	const currentTime = ref(0)

	const gazeCoordinates = ref<GazeCoordinate[]>([])
	const gazeDataRevision = ref(0)
	const sourceFileName = ref<string | null>(null)
	const importSummary = ref<GazeImportSummary | null>(null)
	const videoFileName = ref<string | null>(null)
	const videoFps = ref<number | null>(null)

	const regionsOfInterest = ref<RegionOfInterest[]>([])
	const selectedRoiIndex = ref<number | null>(null)
	let nextColorIndex = 0

	const gazeSampleCount = computed(() => gazeCoordinates.value.length)
	const roiCount = computed(() => regionsOfInterest.value.length)

	const activeRoi = computed<RegionOfInterest | null>(() => {
		if (selectedRoiIndex.value === null) return null
		return regionsOfInterest.value[selectedRoiIndex.value] ?? null
	})

	function setPlaying(playing: boolean): void {
		isPlaying.value = playing
	}

	function setCurrentTime(time: number): void {
		currentTime.value = Math.max(0, time)
	}

	function togglePlayback(): void {
		isPlaying.value = !isPlaying.value
	}

	function buildPersistenceSnapshot(): PersistedWorkspace {
		return {
			gazeCoordinates: gazeCoordinates.value,
			regionsOfInterest: regionsOfInterest.value,
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
		regionsOfInterest.value = snapshot.regionsOfInterest.map((region) =>
			ensureRegionId({ ...region })
		)
		sourceFileName.value = snapshot.sourceFileName
		videoFileName.value = snapshot.videoFileName
		videoFps.value = snapshot.videoFps
		importSummary.value = snapshot.importSummary
		selectedRoiIndex.value =
			regionsOfInterest.value.length > 0 ? Math.min(selectedRoiIndex.value ?? 0, regionsOfInterest.value.length - 1) : null
		return gazeCoordinates.value.length > 0 || regionsOfInterest.value.length > 0
	}

	async function clearPersistedWorkspace(): Promise<void> {
		await clearWorkspaceSnapshot()
	}

	function clearGazeCoordinates(): void {
		clearGazeData()
	}

	function setRegionsOfInterest(
		nextRegions: RegionOfInterest[],
		selectedIndex: number | null = 0
	): void {
		regionsOfInterest.value = nextRegions.map((region) => ensureRegionId({ ...region }))
		persistWorkspace()
		if (regionsOfInterest.value.length === 0) {
			selectedRoiIndex.value = null
			return
		}
		if (selectedIndex !== null && selectedIndex >= 0 && selectedIndex < regionsOfInterest.value.length) {
			selectedRoiIndex.value = selectedIndex
			return
		}
		selectedRoiIndex.value = 0
	}

	function selectRoi(index: number): void {
		if (index < 0 || index >= regionsOfInterest.value.length) return
		selectedRoiIndex.value = index
	}

	function updateRoiBounds(index: number, bounds: RoiBounds): void {
		const region = regionsOfInterest.value[index]
		if (!region) return
		region.x = Math.round(bounds.x)
		region.y = Math.round(bounds.y)
		region.width = Math.round(bounds.width)
		region.height = Math.round(bounds.height)
		persistWorkspace()
	}

	function addRegionOfInterest(bounds: RoiBounds): RegionOfInterest | null {
		if (bounds.width < MIN_ROI_DIMENSION || bounds.height < MIN_ROI_DIMENSION) return null

		const region: RegionOfInterest = {
			id: createRegionId(),
			x: Math.round(bounds.x),
			y: Math.round(bounds.y),
			width: Math.round(bounds.width),
			height: Math.round(bounds.height),
			label: `ROI ${regionsOfInterest.value.length + 1}`,
			color_tag: ROI_COLOR_PALETTE[nextColorIndex % ROI_COLOR_PALETTE.length]
		}
		nextColorIndex += 1
		regionsOfInterest.value.push(region)
		selectedRoiIndex.value = regionsOfInterest.value.length - 1
		persistWorkspace()
		return region
	}

	function removeRegionOfInterest(index: number): boolean {
		if (index < 0 || index >= regionsOfInterest.value.length) return false
		regionsOfInterest.value.splice(index, 1)
		if (regionsOfInterest.value.length === 0) {
			selectedRoiIndex.value = null
			return true
		}
		if (selectedRoiIndex.value === null) {
			selectedRoiIndex.value = 0
			return true
		}
		if (selectedRoiIndex.value >= regionsOfInterest.value.length) {
			selectedRoiIndex.value = regionsOfInterest.value.length - 1
		}
		persistWorkspace()
		return true
	}

	function deleteActiveRoi(): boolean {
		if (selectedRoiIndex.value === null) return false
		return removeRegionOfInterest(selectedRoiIndex.value)
	}

	return {
		isPlaying,
		currentTime,
		gazeCoordinates,
		gazeDataRevision,
		sourceFileName,
		importSummary,
		videoFileName,
		videoFps,
		regionsOfInterest,
		selectedRoiIndex,
		gazeSampleCount,
		roiCount,
		activeRoi,
		setPlaying,
		setCurrentTime,
		togglePlayback,
		setGazeData,
		setGazeCoordinates,
		setVideoMetadata,
		clearGazeData,
		clearGazeCoordinates,
		restoreWorkspaceFromIndexedDb,
		clearPersistedWorkspace,
		setRegionsOfInterest,
		selectRoi,
		updateRoiBounds,
		addRegionOfInterest,
		removeRegionOfInterest,
		deleteActiveRoi
	}
})
