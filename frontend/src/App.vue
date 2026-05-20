<template>
	<ModeSelector
		v-if="workspace.state.appMode === 'select'"
		:app-mode="workspace.state.appMode"
		@select-mode="onSelectMode"
	/>

	<div v-else class="app-shell">
		<AppHeader
			:app-mode="workspace.state.appMode"
			:mode-title="modeTitle"
			:has-video="!!workspace.state.videoInfo"
			:has-scenes="workspace.state.scenes.length > 0"
			@back="workspace.backToModeSelect"
			@new-project="openNewVideo"
			@open-project="openWorkspacePicker"
			@save-workspace="files.saveWorkspace"
			@save-workspace-as="files.openSaveAsModal"
			@export-csv="files.quickExport('csv')"
			@export-json="files.quickExport('json')"
			@open-record="workspace.state.showRecordModal = true"
			@open-process="workspace.state.showProcessModal = true"
			@open-import="workspace.state.showImportModal = true"
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
				:active-scene-idx="activeSceneIdx"
				:selected-scene-idx="selectedSceneIdx"
				:current-frame="workspace.state.currentFrame"
				:current-time="currentTime"
				:video-duration="videoDuration"
				:playing="playing"
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
		/>

		<NewVideoModal
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
import { onMounted, ref, toRef } from 'vue'
import ModeSelector from './components/mode/ModeSelector.vue'
import AppHeader from './components/layouts/AppHeader.vue'
import SceneSidebar from './components/scene/SceneSidebar.vue'
import VideoWorkspace from './components/video/VideoWorkspace.vue'
import RoiSidebar from './components/roi/RoiSidebar.vue'
import StatusBar from './components/layouts/StatusBar.vue'
import NewVideoModal from './components/modals/NewVideoModal.vue'
import SaveAsModal from './components/modals/SaveAsModal.vue'
import { useWorkspaceState, type AppMode } from './composables/useWorkspaceState'
import { useHistory } from './composables/useHistory'
import { useScenes } from './composables/useScenes'
import { useVideoSession } from './composables/useVideoSession'
import { useWorkspaceFiles } from './composables/useWorkspaceFiles'
import { useSocket } from './composables/useSocket'

const workspace = useWorkspaceState()
const { modeTitle } = workspace
const workspaceFileInputRef = ref<HTMLInputElement | null>(null)

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

const { showSaveAsModal, saveAsFilename } = files

const socket = useSocket()

function onSelectMode(mode: Exclude<AppMode, 'select'>): void {
	workspace.selectMode(mode)
	if (mode === 'import') {
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
	scenes.selectedRoiIdx.value = index
}

function onRenameScene(index: number): void {
	const scene = workspace.state.scenes[index]
	if (!scene) return
	const name = window.prompt('Custom scene name:', scene.custom_name ?? '')
	if (name === null) return
	scene.custom_name = name.trim()
	void scenes.saveScenes()
}

function onRenameRoi(index: number): void {
	const scene = scenes.currentScene.value
	if (!scene) return
	const roi = scene.rois[index]
	if (!roi) return
	const label = window.prompt('ROI label:', roi.label)
	if (label === null || !label.trim()) return
	roi.label = label.trim()
	void scenes.saveScenes()
}

function onDeleteRoi(index: number): void {
	const scene = scenes.currentScene.value
	if (!scene) return
	if (!window.confirm(`Delete ROI "${scene.rois[index]?.label}"?`)) return
	scene.rois.splice(index, 1)
	scenes.selectedRoiIdx.value = null
	void scenes.saveScenes()
}

onMounted(async () => {
	socket.connect()
	const loaded = await video.loadVideoInfo()
	if (loaded && workspace.state.appMode !== 'select') {
		workspace.markUpdated()
	}
})
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
