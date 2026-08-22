<template>
	<SettingsView v-if="appView === 'settings'" @back="closeSettings" />

	<ModeSelector
		v-else-if="workspace.state.appMode === 'select'"
		:app-mode="workspace.state.appMode"
		:backend-ready="backendReady"
		:socket-connected="socket.connected.value"
		:gaze-source-label="gazeSourceLabel"
		:last-gaze-at="lastGazeAt"
		@select-mode="onSelectMode"
	/>

	<div v-else class="app-shell">
		<AppHeader
			:app-mode="workspace.state.appMode"
			:mode-title="modeTitle"
			:has-video="!!workspace.state.videoInfo"
			:has-scenes="workspace.state.scenes.length > 0"
			:has-imported-gaze="hasImportedGaze"
			:has-gaze-video="!!dualVideo.gazeVideoSrc.value"
			:dual-video-mode="dualVideo.videoMode.value"
			:recording-active="liveRecording.recording.value"
			:modal-blocked="postProcessing.progressBlocking()"
			:has-session="!!liveRecording.sessionDir.value"
			@back="workspace.backToModeSelect"
			@new-project="openNewVideo"
			@open-project="openWorkspacePicker"
			@save-workspace="files.saveWorkspace"
			@save-workspace-as="files.openSaveAsModal"
			@export-csv="files.quickExport('csv')"
			@export-json="files.quickExport('json')"
			@open-record="startRecordingFlow"
			@stop-record="stopRecordingFlow"
			@open-process="openProcessModal"
			@open-import="openImportModal"
			@generate-reports="onGenerateImportReports"
			@toggle-dual-video="dualVideo.toggleVideoMode()"
			@open-settings="openSettings"
		/>

		<div class="container">
			<SceneSidebar
				:scenes="workspace.state.scenes"
				:active-scene-idx="activeSceneIdx"
				:video-info="workspace.state.videoInfo"
				@select-scene="onSelectScene"
				@add-scene="scenes.addScene"
				@rename-scene="onRenameScene"
				@delete-scene="scenes.deleteScene"
			/>

			<VideoWorkspace
				:video-info="workspace.state.videoInfo"
				:video-src="videoSrc"
				:scenes="workspace.state.scenes"
				:rois="rois"
				:selected-roi-idx="selectedRoiIdx"
				:active-scene-idx="activeSceneIdx"
				:selected-scene-idx="selectedSceneIdx"
				:current-frame="workspace.state.currentFrame"
				:current-time="currentTime"
				:video-duration="videoDuration"
				:playing="playing"
				:gaze-sample="currentOverlaySample"
				:gaze-revision="gazeRevision"
				:show-recording-overlay="liveRecording.showRecordingOverlay.value"
				:roi-interaction-disabled="liveRecording.recording.value || liveRecording.showRecordingOverlay.value"
				:app-mode="workspace.state.appMode === 'import' ? 'import' : 'live'"
				:video-mode="dualVideo.videoMode.value"
				:gaze-video-src="dualVideo.gazeVideoSrc.value"
				:frame-offset="importMode.frameOffset.value"
				@select-scene="onSelectScene"
				@frame-change="video.seekFrame"
				@toggle-play="video.togglePlay"
				@jump-start="video.jumpToStart"
				@jump-end="video.jumpToEnd"
				@prev-scene="onPrevScene"
				@next-scene="onNextScene"
				@prev-frame="video.prevFrame"
				@next-frame="video.nextFrame"
				@split-scene="scenes.splitScene"
				@merge-scene="scenes.mergeWithPrevious"
				@undo="scenes.undoScenes"
				@redo="scenes.redoScenes"
				@select-roi="onSelectRoi"
				@update-roi-bounds="onUpdateRoiBounds"
				@roi-drawn="onRoiDrawn"
				@commit-rois="onCommitRois"
				@start-recording="onStartOverlayRecording"
				@cancel-recording="onCancelOverlayRecording"
				@update:frame-offset="importMode.setFrameOffset"
				@adjust-offset="onAdjustFrameOffset"
			/>

			<RoiSidebar
				:current-scene="currentScene"
				:selected-roi-idx="selectedRoiIdx ?? -1"
				@select-roi="onSelectRoi"
				@rename-roi="onRenameRoi"
				@delete-roi="onDeleteRoi"
			/>
		</div>

		<StatusBar
			:status-message="workspace.state.statusMessage"
			:current-workspace-file="workspace.state.currentWorkspaceFile"
			:last-updated="workspace.state.lastUpdated"
			:session-dir="liveRecording.sessionDir.value"
			:frames-recorded="liveRecording.framesRecorded.value"
		/>

		<NewVideoModal
			ref="newVideoModalRef"
			v-if="workspace.state.showNewVideoModal"
			@close="workspace.state.showNewVideoModal = false"
			@select-file="onNewVideoFile"
			@submit-youtube="onNewVideoYoutube"
		/>

		<SaveAsModal
			v-if="showSaveAsModal"
			:filename="saveAsFilename"
			:current-workspace-file="workspace.state.currentWorkspaceFile"
			@update:filename="saveAsFilename = $event"
			@confirm="files.confirmSaveAs"
			@cancel="showSaveAsModal = false"
		/>

		<ImportModal
			v-if="workspace.state.showImportModal"
			:import-method="importMode.importMethod.value"
			:has-video="!!workspace.state.videoInfo"
			:csv-file-name="importMode.csvFileName.value"
			:imported-video-name="importMode.importedVideoFile.value?.name ?? null"
			:imported-gaze-video-name="importMode.importedGazeVideoFile.value?.name ?? null"
			:headers="importMode.headers.value"
			:mapping="importMode.mapping.value"
			:frame-offset="importMode.frameOffset.value"
			:warnings="importMode.warnings.value"
			:errors="importMode.errors.value"
			:valid-row-count="importMode.validRowCount.value"
			:skipped-row-count="importMode.skippedRowCount.value"
			:can-apply-csv-import="importMode.canApplyCsvImport.value"
			:can-apply-auto-import="importMode.canApplyAutoImport.value"
			@update:import-method="importMode.setImportMethod"
			@csv-selected="onImportCsvSelected"
			@stimulus-selected="onImportStimulusSelected"
			@gaze-video-selected="onImportGazeVideoSelected"
			@update:mapping="onImportMappingChanged"
			@update:frame-offset="onImportFrameOffsetChanged"
			@apply-csv="applyCsvImport"
			@apply-auto="applyAutoImport"
			@close="workspace.state.showImportModal = false"
		/>

		<RecordModal
			v-if="workspace.state.showRecordModal"
			@close="workspace.state.showRecordModal = false"
			@confirm="confirmRecordModal"
		/>

		<ProcessModal
			v-if="workspace.state.showProcessModal"
			:session-dir="liveRecording.sessionDir.value"
			:manual-import-required="liveRecording.manualImportRequired.value"
			:obs-recording-path="liveRecording.obsRecordingPath.value"
			:processing="postProcessing.processing.value"
			:processing-status="postProcessing.processingStatus.value"
			:importing-obs-file="postProcessing.importingObsFile.value"
			@close="workspace.state.showProcessModal = false"
			@import-obs-file="postProcessing.openObsFilePicker"
			@generate-heatmaps="onGenerateHeatmaps"
			@generate-roi-stats="onGenerateRoiStats"
			@generate-overlay-video="onGenerateOverlayVideo"
			@generate-heatmap-overlay="onGenerateHeatmapOverlay"
			@process-all="onProcessAll"
		/>

		<RoiNameModal
			v-if="workspace.state.showROIModal"
			:label="pendingRoiLabel"
			:bounds="pendingRoiBounds"
			@update:label="pendingRoiLabel = $event"
			@confirm="confirmPendingRoi"
			@cancel="cancelPendingRoi"
		/>

		<ProgressModal
			v-if="postProcessing.showProgressModal.value"
			:progress-complete="postProcessing.progressComplete.value"
			:progress-error="postProcessing.progressError.value"
			:progress-percent="postProcessing.progressPercent.value"
			:progress-message="postProcessing.progressMessage.value"
			:progress-steps="postProcessing.progressSteps.value"
			:generated-files="postProcessing.generatedFiles.value"
			:progress-status-label="postProcessing.progressStatusLabel"
			@close="postProcessing.closeProgressModal"
		/>

		<ObsFilePickerModal
			v-if="postProcessing.showObsFilePickerModal.value"
			:loading="postProcessing.loadingObsFiles.value"
			:importing="postProcessing.importingObsFile.value"
			:files="postProcessing.availableObsFiles.value"
			@close="postProcessing.showObsFilePickerModal.value = false"
			@select-file="postProcessing.selectObsFile"
		/>

		<input
			ref="workspaceFileInputRef"
			type="file"
			accept=".json"
			class="hidden"
			@change="onWorkspaceFileSelected"
		>
	</div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, toRef, watch } from 'vue'
import ModeSelector from './components/mode/ModeSelector.vue'
import AppHeader from './components/layouts/AppHeader.vue'
import SceneSidebar from './components/scene/SceneSidebar.vue'
import VideoWorkspace from './components/video/VideoWorkspace.vue'
import RoiSidebar from './components/roi/RoiSidebar.vue'
import StatusBar from './components/layouts/StatusBar.vue'
import NewVideoModal from './components/modals/NewVideoModal.vue'
import SaveAsModal from './components/modals/SaveAsModal.vue'
import ImportModal from './components/modals/ImportModal.vue'
import RecordModal from './components/modals/RecordModal.vue'
import ProcessModal from './components/modals/ProcessModal.vue'
import RoiNameModal from './components/modals/RoiNameModal.vue'
import ProgressModal from './components/modals/ProgressModal.vue'
import ObsFilePickerModal from './components/modals/ObsFilePickerModal.vue'
import SettingsView from './components/settings/SettingsView.vue'
import { useWorkspaceState, type AppMode } from './composables/useWorkspaceState'
import { useHistory } from './composables/useHistory'
import { useScenes } from './composables/useScenes'
import { useVideoSession } from './composables/useVideoSession'
import { useWorkspaceFiles } from './composables/useWorkspaceFiles'
import { useSocket } from './composables/useSocket'
import { useRoiEditor, type RoiBounds } from './composables/useRoiEditor'
import { useGazeSession } from './composables/useGazeSession'
import { useLiveRecording } from './composables/useLiveRecording'
import { useImportMode, type ImportVideoUploadResult } from './composables/useImportMode'
import { usePostProcessing } from './composables/usePostProcessing'
import { useDualVideo } from './composables/useDualVideo'
import { useGazeDevices } from './composables/useGazeDevices'
import { useGazePersistence } from './composables/useGazePersistence'

const workspace = useWorkspaceState()
const { modeTitle } = workspace
const workspaceFileInputRef = ref<HTMLInputElement | null>(null)
const newVideoModalRef = ref<InstanceType<typeof NewVideoModal> | null>(null)
const appView = ref<'editor' | 'settings'>(readInitialAppView())

function readInitialAppView(): 'editor' | 'settings' {
	if (typeof window === 'undefined') return 'editor'
	return window.location.pathname === '/settings' ? 'settings' : 'editor'
}

function openSettings(): void {
	appView.value = 'settings'
	if (typeof window !== 'undefined') {
		window.history.pushState({}, '', '/settings')
	}
}

function closeSettings(): void {
	appView.value = 'editor'
	if (typeof window === 'undefined') return
	const params = new URLSearchParams(window.location.search)
	const mode = params.get('mode')
	const ws = params.get('ws')
	let path = '/'
	if (mode === 'live' || mode === 'import') {
		path = ws ? `/?mode=${mode}&ws=${encodeURIComponent(ws)}` : `/?mode=${mode}`
	}
	window.history.pushState({}, '', path)
}

const scenesRef = toRef(workspace.state, 'scenes')
const videoInfoRef = toRef(workspace.state, 'videoInfo')
const currentFrameRef = toRef(workspace.state, 'currentFrame')
const currentWorkspaceFileRef = toRef(workspace.state, 'currentWorkspaceFile')
const lastUpdatedRef = toRef(workspace.state, 'lastUpdated')

const history = useHistory(scenesRef)

const scenes = useScenes(
	scenesRef,
	videoInfoRef,
	currentFrameRef,
	history,
	workspace.setStatus
)

const video = useVideoSession(
	videoInfoRef,
	currentFrameRef,
	workspace.setStatus,
	async () => {
		await scenes.loadScenes()
	}
)

const files = useWorkspaceFiles(
	videoInfoRef,
	scenesRef,
	currentWorkspaceFileRef,
	lastUpdatedRef,
	video.lastYoutubeUrl,
	workspace.setStatus,
	(importedScenes) => {
		history.resetHistory(importedScenes)
		if (videoInfoRef.value) {
			video.videoSrc.value = `/video/${videoInfoRef.value.filename}`
		}
	}
)

const {
	activeSceneIdx,
	selectedSceneIdx,
	currentScene,
	selectedRoiIdx
} = scenes

const { videoSrc, playing, currentTime, videoDuration } = video
const roiEditor = useRoiEditor(scenesRef, currentScene, selectedRoiIdx)
const { rois } = roiEditor
const gazeSession = useGazeSession(currentTime)
const { currentOverlaySample, revision: gazeRevision } = gazeSession
const gazeDevices = useGazeDevices()
const gazePersistence = useGazePersistence(gazeSession, videoInfoRef)
const importMode = useImportMode(
	videoInfoRef,
	(payload) => {
		gazePersistence.persistImportedGaze(payload.samples, payload.fileName, payload.summary)
	},
	workspace.setStatus
)

const { showSaveAsModal, saveAsFilename } = files

const socket = useSocket()
const liveRecording = useLiveRecording(
	videoInfoRef,
	currentFrameRef,
	currentTime,
	socket.emitRecordFrame,
	workspace.setStatus,
	video.setPlaying
)
const dualVideo = useDualVideo()
const postProcessing = usePostProcessing(
	liveRecording.sessionDir,
	liveRecording.manualImportRequired,
	liveRecording.obsRecordingPath,
	workspace.setStatus
)
const pendingRoiBounds = ref<RoiBounds | null>(null)
const pendingRoiLabel = ref('')
const lastGazeAt = ref<string | null>(null)
const hasImportedGaze = computed(() => gazeSession.importedGaze.value.length > 0)
const hasAnyRoi = computed(() => workspace.state.scenes.some((scene) => scene.rois.length > 0))
const backendReady = computed(() => !!videoInfoRef.value || workspace.state.statusMessage !== 'Ready')
const gazeSourceLabel = computed(() => {
	const deviceName = gazeDevices.selectedDevice.value.name
	if (gazeSession.importedGaze.value.length > 0) return 'Imported gaze loaded'
	if (socket.connected.value) return `Live gaze · ${deviceName}`
	return `${deviceName} (standby)`
})

function handleGazeDetected(payload: { x: number; y: number }): void {
	gazeSession.pushLiveGaze(payload.x, payload.y)
	lastGazeAt.value = new Date().toLocaleTimeString()
}

function onSelectMode(mode: Exclude<AppMode, 'select'>): void {
	workspace.selectMode(mode)
	if (mode === 'import') {
		importMode.resetImportState()
		workspace.state.showImportModal = true
	}
}

function openNewVideo(): void {
	workspace.state.showNewVideoModal = true
}

function openWorkspacePicker(): void {
	workspaceFileInputRef.value?.click()
}

async function onWorkspaceFileSelected(event: Event): void {
	const input = event.target as HTMLInputElement
	const file = input.files?.[0]
	input.value = ''
	if (!file) return
	const ok = await files.importWorkspaceFile(file)
	if (ok && videoInfoRef.value) {
		video.videoSrc.value = `/video/${videoInfoRef.value.filename}`
	}
}

async function onNewVideoFile(file: File): Promise<void> {
	const ok = await video.uploadVideo(file)
	if (ok) workspace.state.showNewVideoModal = false
}

async function onNewVideoYoutube(url: string): Promise<void> {
	const ok = await video.downloadYoutube(url)
	if (ok) workspace.state.showNewVideoModal = false
	else newVideoModalRef.value?.resetYoutubeAttempt()
}

function onSelectScene(index: number): void {
	scenes.selectScene(index)
}

function onPrevScene(): void {
	const idx = scenes.prevScene()
	if (idx !== null) scenes.selectScene(idx)
}

function onNextScene(): void {
	const idx = scenes.nextScene()
	if (idx !== null) scenes.selectScene(idx)
}

function onSelectRoi(index: number): void {
	roiEditor.selectRoi(index)
}

function onRenameScene(index: number, customName: string): void {
	const scene = workspace.state.scenes[index]
	if (!scene) return
	scene.custom_name = customName
	void scenes.saveScenes()
}

function onRenameRoi(index: number): void {
	const scene = currentScene.value
	if (!scene) return
	const roi = scene.rois[index]
	if (!roi) return
	const label = window.prompt('ROI label:', roi.label)
	if (label === null || !label.trim()) return
	roiEditor.renameRoi(index, label.trim())
	void scenes.saveScenes()
}

function onDeleteRoi(index: number): void {
	const scene = currentScene.value
	if (!scene) return
	if (!window.confirm(`Delete ROI "${scene.rois[index]?.label}"?`)) return
	roiEditor.deleteRoi(index)
	void scenes.saveScenes()
}

function onUpdateRoiBounds(index: number, bounds: RoiBounds): void {
	roiEditor.updateRoiBounds(index, bounds)
}

function onRoiDrawn(bounds: RoiBounds): void {
	const scene = currentScene.value
	if (!scene) return
	pendingRoiBounds.value = bounds
	pendingRoiLabel.value = `ROI ${scene.rois.length + 1}`
	workspace.state.showROIModal = true
}

function confirmPendingRoi(): void {
	if (!pendingRoiBounds.value) {
		cancelPendingRoi()
		return
	}
	const label = pendingRoiLabel.value.trim() || `ROI ${(currentScene.value?.rois.length ?? 0) + 1}`
	roiEditor.addRegionOfInterest(pendingRoiBounds.value, label)
	pendingRoiBounds.value = null
	pendingRoiLabel.value = ''
	workspace.state.showROIModal = false
	void scenes.saveScenes()
}

function cancelPendingRoi(): void {
	pendingRoiBounds.value = null
	pendingRoiLabel.value = ''
	workspace.state.showROIModal = false
}

function openProcessModal(): void {
	if (!postProcessing.canOpenModal()) return
	workspace.state.showProcessModal = true
}

function closeProcessModal(): void {
	workspace.state.showProcessModal = false
}

async function onGenerateHeatmaps(): Promise<void> {
	await postProcessing.generateHeatmaps(closeProcessModal)
}

async function onGenerateRoiStats(): Promise<void> {
	await postProcessing.generateRoiStats(closeProcessModal)
}

async function onGenerateOverlayVideo(): Promise<void> {
	await postProcessing.generateOverlayVideo(closeProcessModal)
}

async function onGenerateHeatmapOverlay(): Promise<void> {
	await postProcessing.generateHeatmapOverlayVideo(closeProcessModal)
}

async function onProcessAll(): Promise<void> {
	await postProcessing.processAll(closeProcessModal)
}

function onCommitRois(): void {
	void scenes.saveScenes()
}

function startRecordingFlow(): void {
	if (workspace.state.appMode !== 'live') return
	if (liveRecording.recording.value) return
	if (!postProcessing.canOpenModal()) return
	workspace.state.showRecordModal = true
}

async function confirmRecordModal(): Promise<void> {
	workspace.state.showRecordModal = false
	video.jumpToStart()
	if (!liveRecording.prepareRecording()) return
	try {
		await document.documentElement.requestFullscreen()
	} catch {
		// Fullscreen is optional
	}
}

async function onStartOverlayRecording(): Promise<void> {
	await liveRecording.startPlaybackAndRecording(stopRecordingFlow)
}

async function stopRecordingFlow(): Promise<void> {
	await liveRecording.stopRecording()
	if (
		liveRecording.sessionDir.value &&
		!liveRecording.manualImportRequired.value &&
		workspace.state.appMode === 'live'
	) {
		await postProcessing.runPostProcessingPipeline()
	}
}

async function onCancelOverlayRecording(): Promise<void> {
	await liveRecording.cancelRecordingPreparation()
}

function openImportModal(): void {
	if (!postProcessing.canOpenModal()) return
	workspace.state.showImportModal = true
}

function handleImportVideoResult(result: ImportVideoUploadResult | null): void {
	if (result?.gazeVideoPath && result.gazeVideoFilename) {
		dualVideo.setGazeVideo(result.gazeVideoPath, result.gazeVideoFilename)
	}
}

async function onGenerateImportReports(): Promise<void> {
	if (!postProcessing.canOpenModal()) return
	await postProcessing.generateReportsFromImport(
		hasImportedGaze.value,
		workspace.state.scenes.length > 0,
		hasAnyRoi.value
	)
}

function onAdjustFrameOffset(delta: number): void {
	importMode.setFrameOffset(importMode.frameOffset.value + delta)
}

async function onImportStimulusSelected(file: File): Promise<void> {
	importMode.setImportedVideoFile(file)
}

async function onImportGazeVideoSelected(file: File): Promise<void> {
	importMode.setImportedGazeVideoFile(file)
}

async function onImportCsvSelected(file: File): Promise<void> {
	await importMode.parseCsvFile(file)
}

function onImportMappingChanged(field: 'x' | 'y' | 'timestamp', value: string): void {
	importMode.setMappingField(field, value)
}

function onImportFrameOffsetChanged(value: number): void {
	importMode.setFrameOffset(value)
}

async function applyCsvImport(): Promise<void> {
	const ok = await importMode.applyImport(video.uploadVideo, (result) => {
		handleImportVideoResult(result)
	})
	if (ok) {
		workspace.state.showImportModal = false
	}
}

async function applyAutoImport(): Promise<void> {
	const ok = await importMode.processAutoDetect(video.uploadVideo, (result) => {
		handleImportVideoResult(result)
		if (workspace.state.scenes.length === 0) {
			void scenes.addScene()
		}
	})
	if (ok) {
		workspace.state.showImportModal = false
	}
}

onMounted(async () => {
	if (typeof window !== 'undefined') {
		window.addEventListener('popstate', onPopState)
	}
	socket.connect()
	socket.onGazeDetected(handleGazeDetected)
	await gazePersistence.restoreFromIndexedDb()
	const loaded = await video.loadVideoInfo()
	if (loaded && workspace.state.appMode !== 'select') {
		workspace.markUpdated()
	}
})

onBeforeUnmount(() => {
	if (typeof window !== 'undefined') {
		window.removeEventListener('popstate', onPopState)
	}
	socket.offGazeDetected(handleGazeDetected)
})

function onPopState(): void {
	appView.value = readInitialAppView()
}

watch(
	() => workspace.state.appMode,
	(mode) => {
		if (mode === 'select') {
			importMode.resetImportState()
			gazeSession.clearImportedGaze()
			dualVideo.clearGazeVideo()
		}
	}
)
</script>

<style scoped>
.app-shell {
	display: flex;
	flex-direction: column;
	min-height: 100vh;
}

.hidden {
	display: none;
}
</style>
