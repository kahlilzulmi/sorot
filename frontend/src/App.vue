<template>
	<div id="app">
		<ModeSelector :app-mode="state.appMode" @select-mode="selectMode" />

		<div v-show="state.appMode !== 'select'">
			<AppHeader
				:app-mode="state.appMode"
				:mode-title="modeTitle"
				:has-video="Boolean(videoInfo)"
				@back="backToModeSelect"
				@new-project="openNewProjectExample"
				@open-project="triggerOpenWorkspace"
				@save-workspace="saveWorkspace"
				@save-workspace-as="openSaveAsModal"
			/>

			<input
				ref="workspaceInputRef"
				type="file"
				accept=".json,application/json"
				style="display: none"
				@change="onWorkspaceFileSelected"
			>

			<main class="container">
				<SceneSidebar
					:scenes="scenes"
					:active-scene-idx="activeSceneIdx"
					:video-info="videoInfo"
					@select-scene="selectScene"
					@add-scene="addScene"
					@rename-scene="renameScene"
					@delete-scene="deleteScene"
				/>

				<VideoWorkspace
					:video-info="videoInfo"
					:video-src="videoSrc"
					:scenes="scenes"
					:active-scene-idx="activeSceneIdx"
					:selected-scene-idx="selectedSceneIdx"
					:current-frame="currentFrame"
					:current-time="currentTime"
					:video-duration="videoDuration"
					:playing="playing"
					@select-scene="selectScene"
					@frame-change="setCurrentFrame"
					@toggle-play="togglePlayback"
					@jump-start="jumpToStart"
					@jump-end="jumpToEnd"
					@prev-scene="prevScene"
					@next-scene="nextScene"
					@prev-frame="prevFrame"
					@next-frame="nextFrame"
					@split-scene="uiOnlyMessage('Split Scene')"
					@merge-scene="uiOnlyMessage('Merge Scene')"
					@undo="uiOnlyMessage('Undo')"
					@redo="uiOnlyMessage('Redo')"
				/>

				<RoiSidebar
					:current-scene="currentScene"
					:selected-r-o-i-idx="selectedROIIdx"
					@select-roi="selectROI"
					@rename-roi="renameROI"
					@delete-roi="deleteROI"
				/>
			</main>

			<NewVideoModal
				v-if="showNewVideoModal"
				@close="showNewVideoModal = false"
				@select-file="onVideoFileSelected"
				@submit-youtube="onYoutubeSubmitted"
			/>

			<SaveAsModal
				v-if="showSaveAsModal"
				:filename="saveAsFilename"
				:current-workspace-file="state.currentWorkspaceFile"
				@update:filename="saveAsFilename = $event"
				@confirm="saveWorkspaceAs"
				@cancel="showSaveAsModal = false"
			/>

			<StatusBar
				:status-message="state.statusMessage"
				:current-workspace-file="state.currentWorkspaceFile"
				:last-updated="state.lastUpdated"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import AppHeader from './components/layouts/AppHeader.vue'
import StatusBar from './components/layouts/StatusBar.vue'
import ModeSelector from './components/mode/ModeSelector.vue'
import NewVideoModal from './components/modals/NewVideoModal.vue'
import SaveAsModal from './components/modals/SaveAsModal.vue'
import RoiSidebar from './components/roi/RoiSidebar.vue'
import SceneSidebar from './components/scene/SceneSidebar.vue'
import VideoWorkspace from './components/video/VideoWorkspace.vue'
import { useWorkspaceState } from './composables/useWorkspaceState'

interface Roi {
	label: string
	x: number
	y: number
	width: number
	height: number
	color_tag?: string
}

interface Scene {
	name: string
	custom_name?: string
	start_frame: number
	end_frame: number
	rois: Roi[]
}

interface VideoInfo {
	filename: string
	width: number
	height: number
	fps: number
	total_frames: number
	duration: number
}

const {
	state,
	modeTitle,
	selectMode,
	backToModeSelect,
	setCurrentWorkspaceFile,
	setStatus,
	markUpdated
} = useWorkspaceState()

const workspaceInputRef = ref<HTMLInputElement | null>(null)
const showNewVideoModal = ref(false)
const showSaveAsModal = ref(false)
const saveAsFilename = ref('workspace')
const selectedSceneIdx = ref(0)
const selectedROIIdx = ref(0)
const currentFrame = ref(0)
const playing = ref(false)

const scenes = computed<Scene[]>(() => {
	return state.scenes.map((item, idx) => {
		const source = item as Record<string, unknown>
		return {
			name: String(source.name ?? `Scene ${idx + 1}`),
			custom_name: source.custom_name ? String(source.custom_name) : '',
			start_frame: Number(source.start_frame ?? 0),
			end_frame: Number(source.end_frame ?? 0),
			rois: Array.isArray(source.rois)
				? source.rois.map((roi, roiIdx) => {
					const sourceRoi = roi as Record<string, unknown>
					return {
						label: String(sourceRoi.label ?? `ROI ${roiIdx + 1}`),
						x: Number(sourceRoi.x ?? 0),
						y: Number(sourceRoi.y ?? 0),
						width: Number(sourceRoi.width ?? 120),
						height: Number(sourceRoi.height ?? 80),
						color_tag: sourceRoi.color_tag ? String(sourceRoi.color_tag) : undefined
					}
				})
				: []
		}
	})
})

const videoInfo = computed<VideoInfo | null>(() => {
	if (!state.videoInfo) return null
	const source = state.videoInfo as Record<string, unknown>
	return {
		filename: String(source.filename ?? 'video.mp4'),
		width: Number(source.width ?? 1920),
		height: Number(source.height ?? 1080),
		fps: Number(source.fps ?? 30),
		total_frames: Number(source.total_frames ?? 1),
		duration: Number(source.duration ?? 0)
	}
})

const currentScene = computed<Scene | null>(() => scenes.value[selectedSceneIdx.value] ?? null)
const activeSceneIdx = computed(() => selectedSceneIdx.value)
const videoDuration = computed(() => videoInfo.value?.duration ?? 0)
const currentTime = computed(() => {
	if (!videoInfo.value || videoInfo.value.fps <= 0) return 0
	return currentFrame.value / videoInfo.value.fps
})
const videoSrc = computed(() => (videoInfo.value ? `/video/${videoInfo.value.filename}` : ''))

onMounted(() => {
	window.addEventListener('keydown', onGlobalKeydown)
	void restoreWorkspaceFromNavigation()
})

onBeforeUnmount(() => {
	window.removeEventListener('keydown', onGlobalKeydown)
})

function openNewProjectExample(): void {
	showNewVideoModal.value = true
}

function openSaveAsModal(): void {
	if (!videoInfo.value) {
		setStatus('Nothing to save yet. Load or create a video workspace first.')
		return
	}
	saveAsFilename.value = state.currentWorkspaceFile?.replace(/\.json$/i, '') || 'workspace'
	showSaveAsModal.value = true
}

function triggerOpenWorkspace(): void {
	workspaceInputRef.value?.click()
}

function shouldIgnoreHotkeyTarget(target: EventTarget | null): boolean {
	if (!(target instanceof HTMLElement)) return false
	const tag = target.tagName.toLowerCase()
	return tag === 'input' || tag === 'textarea' || tag === 'select' || target.isContentEditable
}

function onGlobalKeydown(event: KeyboardEvent): void {
	if (shouldIgnoreHotkeyTarget(event.target)) return

	const key = event.key.toLowerCase()

	if (event.ctrlKey && event.shiftKey && key === 's') {
		event.preventDefault()
		openSaveAsModal()
		return
	}

	if (event.ctrlKey && key === 's') {
		event.preventDefault()
		void saveWorkspace()
		return
	}

	if (event.ctrlKey && key === 'o') {
		event.preventDefault()
		triggerOpenWorkspace()
		return
	}

	if (event.ctrlKey && key === 'n') {
		event.preventDefault()
		openNewProjectExample()
		return
	}

	if (!event.ctrlKey && !event.altKey && !event.metaKey && key === 'h' && state.appMode !== 'select') {
		event.preventDefault()
		backToModeSelect()
	}
}

function setScenes(nextScenes: Scene[]): void {
	state.scenes = nextScenes as unknown as Array<Record<string, unknown>>
	markUpdated()
}

function uiOnlyMessage(feature: string): void {
	setStatus(`${feature} UI is ready. Backend behavior will be connected in the next phase.`)
}

function selectScene(index: number): void {
	if (index < 0 || index >= scenes.value.length) return
	selectedSceneIdx.value = index
	selectedROIIdx.value = 0
	currentFrame.value = scenes.value[index].start_frame
}

function addScene(): void {
	const endFrame = Math.max(currentFrame.value + 300, currentFrame.value + 1)
	const newScene: Scene = {
		name: `Scene ${scenes.value.length + 1}`,
		custom_name: '',
		start_frame: currentFrame.value,
		end_frame: endFrame,
		rois: []
	}
	setScenes([...scenes.value, newScene])
	setStatus(`${newScene.name} added`)
}

function renameScene(index: number): void {
	const original = scenes.value[index]
	if (!original) return
	const nextName = window.prompt('Rename scene', original.custom_name || original.name)
	if (nextName === null) return
	const nextScenes = [...scenes.value]
	nextScenes[index] = { ...original, custom_name: nextName.trim() }
	setScenes(nextScenes)
	setStatus(`Scene ${index + 1} renamed`)
}

function deleteScene(index: number): void {
	if (scenes.value.length <= 1) {
		setStatus('At least one scene is required')
		return
	}
	const nextScenes = scenes.value.filter((_, i) => i !== index)
	setScenes(nextScenes)
	if (selectedSceneIdx.value >= nextScenes.length) {
		selectedSceneIdx.value = nextScenes.length - 1
	}
	setStatus(`Scene ${index + 1} deleted`)
}

function selectROI(index: number): void {
	selectedROIIdx.value = index
}

function renameROI(index: number): void {
	if (!currentScene.value) return
	const roi = currentScene.value.rois[index]
	if (!roi) return
	const nextName = window.prompt('Rename ROI', roi.label)
	if (nextName === null) return

	const nextScenes = [...scenes.value]
	const targetScene = { ...nextScenes[selectedSceneIdx.value] }
	targetScene.rois = targetScene.rois.map((item, itemIndex) => {
		if (itemIndex !== index) return item
		return { ...item, label: nextName.trim() || item.label }
	})
	nextScenes[selectedSceneIdx.value] = targetScene
	setScenes(nextScenes)
	setStatus(`ROI ${index + 1} renamed`)
}

function deleteROI(index: number): void {
	if (!currentScene.value) return
	const nextScenes = [...scenes.value]
	const targetScene = { ...nextScenes[selectedSceneIdx.value] }
	targetScene.rois = targetScene.rois.filter((_, itemIndex) => itemIndex !== index)
	nextScenes[selectedSceneIdx.value] = targetScene
	setScenes(nextScenes)
	selectedROIIdx.value = Math.max(0, selectedROIIdx.value - 1)
	setStatus(`ROI ${index + 1} deleted`)
}

function setCurrentFrame(frame: number): void {
	if (!videoInfo.value) return
	const max = Math.max(videoInfo.value.total_frames - 1, 0)
	currentFrame.value = Math.min(Math.max(frame, 0), max)
}

function jumpToStart(): void {
	setCurrentFrame(0)
}

function jumpToEnd(): void {
	if (!videoInfo.value) return
	setCurrentFrame(videoInfo.value.total_frames - 1)
}

function prevFrame(): void {
	setCurrentFrame(currentFrame.value - 1)
}

function nextFrame(): void {
	setCurrentFrame(currentFrame.value + 1)
}

function prevScene(): void {
	if (selectedSceneIdx.value <= 0) return
	selectScene(selectedSceneIdx.value - 1)
}

function nextScene(): void {
	if (selectedSceneIdx.value >= scenes.value.length - 1) return
	selectScene(selectedSceneIdx.value + 1)
}

function togglePlayback(): void {
	playing.value = !playing.value
	setStatus(playing.value ? 'Playback started (UI preview)' : 'Playback paused (UI preview)')
}

function onVideoFileSelected(file: File): void {
	state.videoInfo = {
		filename: file.name,
		width: 1920,
		height: 1080,
		fps: 30,
		total_frames: 9000,
		duration: 300
	}

	if (scenes.value.length === 0) {
		setScenes([
			{ name: 'Scene 1', custom_name: '', start_frame: 0, end_frame: 2999, rois: [] },
			{ name: 'Scene 2', custom_name: '', start_frame: 3000, end_frame: 5999, rois: [] },
			{ name: 'Scene 3', custom_name: '', start_frame: 6000, end_frame: 8999, rois: [] }
		])
	}

	showNewVideoModal.value = false
	setStatus(`UI workspace created for ${file.name}`)
	markUpdated()
}

function onYoutubeSubmitted(url: string): void {
	showNewVideoModal.value = false
	setStatus(`YouTube URL captured in UI: ${url}. Backend download wiring comes next.`)
}

async function onWorkspaceFileSelected(event: Event): Promise<void> {
	const input = event.target as HTMLInputElement
	const file = input.files?.[0]
	if (!file) return

	try {
		setStatus(`Loading workspace: ${file.name}...`)
		const text = await file.text()
		const workspace = JSON.parse(text) as Record<string, unknown>

		if (!workspace.video_info || !workspace.scenes) {
			throw new Error('Invalid workspace file format')
		}

		const response = await fetch('/api/import-workspace', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				...workspace,
				workspace_file: file.name
			})
		})

		const payload = (await response.json()) as {
			success?: boolean
			error?: string
			video_info?: Record<string, unknown>
			scenes?: Array<Record<string, unknown>>
			workspace_file?: string
		}

		if (!response.ok || !payload.success) {
			throw new Error(payload.error || 'Failed to import workspace')
		}

		state.videoInfo = payload.video_info || (workspace.video_info as Record<string, unknown>) || null
		state.scenes = payload.scenes || (workspace.scenes as Array<Record<string, unknown>>) || []
		selectedSceneIdx.value = 0
		selectedROIIdx.value = 0
		currentFrame.value = 0
		setCurrentWorkspaceFile(payload.workspace_file || file.name)

		if (state.appMode === 'select') {
			selectMode('import')
		}

		setStatus(`Workspace loaded: ${state.currentWorkspaceFile}`)
		markUpdated()
	} catch (error) {
		setStatus(`Open workspace failed: ${getErrorMessage(error)}`)
	} finally {
		input.value = ''
	}
}

async function saveWorkspace(): Promise<void> {
	if (!state.videoInfo) {
		setStatus('Nothing to save yet. Load or create a video workspace first.')
		return
	}

	try {
		setStatus('Saving workspace...')
		const response = await fetch('/api/save-workspace', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				video_info: state.videoInfo,
				scenes: state.scenes,
				workspace_file: state.currentWorkspaceFile
			})
		})

		const payload = (await response.json()) as {
			success?: boolean
			error?: string
			workspace_file?: string
		}

		if (!response.ok || !payload.success) {
			throw new Error(payload.error || 'Failed to save workspace')
		}

		setCurrentWorkspaceFile(payload.workspace_file || state.currentWorkspaceFile)
		setStatus(`Saved to ${state.currentWorkspaceFile}`)
		markUpdated()
	} catch (error) {
		setStatus(`Save failed: ${getErrorMessage(error)}`)
	}
}

async function saveWorkspaceAs(): Promise<void> {
	if (!state.videoInfo) {
		setStatus('Nothing to save yet. Load or create a video workspace first.')
		return
	}

	const requested = saveAsFilename.value.trim()
	if (!requested) {
		setStatus('Please enter a filename for Save As')
		return
	}

	try {
		setStatus('Saving workspace as...')
		const response = await fetch('/api/save-workspace-as', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				video_info: state.videoInfo,
				scenes: state.scenes,
				filename: requested
			})
		})

		const payload = (await response.json()) as {
			success?: boolean
			error?: string
			workspace_file?: string
		}

		if (!response.ok || !payload.success) {
			throw new Error(payload.error || 'Failed to save workspace as')
		}

		setCurrentWorkspaceFile(payload.workspace_file || requested)
		showSaveAsModal.value = false
		setStatus(`Saved as ${state.currentWorkspaceFile}`)
		markUpdated()
	} catch (error) {
		setStatus(`Save As failed: ${getErrorMessage(error)}`)
	}
}

function getErrorMessage(error: unknown): string {
	if (error instanceof Error) return error.message
	if (typeof error === 'string') return error
	return 'Unknown error'
}

async function restoreWorkspaceFromNavigation(): Promise<void> {
	const workspaceFile = state.currentWorkspaceFile
	if (!workspaceFile) return

	try {
		setStatus(`Restoring workspace: ${workspaceFile}...`)

		const workspaceResponse = await fetch(`/api/workspace/${encodeURIComponent(workspaceFile)}`)
		const workspacePayload = (await workspaceResponse.json()) as {
			success?: boolean
			error?: string
			workspace?: Record<string, unknown>
			workspace_file?: string
		}

		if (!workspaceResponse.ok || !workspacePayload.success || !workspacePayload.workspace) {
			throw new Error(workspacePayload.error || 'Could not load workspace file')
		}

		const importResponse = await fetch('/api/import-workspace', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				...workspacePayload.workspace,
				workspace_file: workspacePayload.workspace_file || workspaceFile
			})
		})

		const importPayload = (await importResponse.json()) as {
			success?: boolean
			error?: string
			video_info?: Record<string, unknown>
			scenes?: Array<Record<string, unknown>>
			workspace_file?: string
		}

		if (!importResponse.ok || !importPayload.success) {
			throw new Error(importPayload.error || 'Could not import workspace data')
		}

		state.videoInfo = importPayload.video_info || (workspacePayload.workspace.video_info as Record<string, unknown>) || null
		state.scenes = importPayload.scenes || (workspacePayload.workspace.scenes as Array<Record<string, unknown>>) || []
		selectedSceneIdx.value = 0
		selectedROIIdx.value = 0
		currentFrame.value = 0
		setCurrentWorkspaceFile(importPayload.workspace_file || workspacePayload.workspace_file || workspaceFile)

		if (state.appMode === 'select') {
			selectMode('import')
		} else {
			setStatus(`Workspace restored: ${state.currentWorkspaceFile}`)
		}

		markUpdated()
	} catch (error) {
		setStatus(`Workspace restore failed: ${getErrorMessage(error)}`)
	}
}
</script>