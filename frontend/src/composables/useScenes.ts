import { computed, ref, type Ref } from 'vue'
import { apiGet, apiPost } from './useApiClient'
import type { VideoInfo, WorkspaceScene } from '../types/workspace'
import type { useHistory } from './useHistory'

type HistoryApi = Pick<
	ReturnType<typeof useHistory>,
	'resetHistory' | 'saveToHistory' | 'undo' | 'redo'
>

export function useScenes(
	scenes: Ref<WorkspaceScene[]>,
	videoInfo: Ref<VideoInfo | null>,
	currentFrame: Ref<number>,
	history: HistoryApi,
	setStatus: (message: string) => void
) {
	const selectedSceneIdx = ref(0)
	const selectedRoiIdx = ref<number | null>(null)

	const activeSceneIdx = computed(() => {
		for (let i = 0; i < scenes.value.length; i++) {
			const scene = scenes.value[i]
			if (
				scene.start_frame <= currentFrame.value &&
				currentFrame.value < scene.end_frame
			) {
				return i
			}
		}
		if (scenes.value.length > 0) {
			const last = scenes.value[scenes.value.length - 1]
			if (
				currentFrame.value >= last.start_frame &&
				currentFrame.value <= last.end_frame
			) {
				return scenes.value.length - 1
			}
		}
		return selectedSceneIdx.value
	})

	const currentScene = computed(() => {
		for (const scene of scenes.value) {
			if (
				scene.start_frame <= currentFrame.value &&
				currentFrame.value < scene.end_frame
			) {
				return scene
			}
		}
		if (scenes.value.length > 0) {
			const last = scenes.value[scenes.value.length - 1]
			if (
				currentFrame.value >= last.start_frame &&
				currentFrame.value <= last.end_frame
			) {
				return last
			}
		}
		return scenes.value[selectedSceneIdx.value] ?? null
	})

	async function loadScenes(): Promise<void> {
		try {
			const loaded = await apiGet<WorkspaceScene[]>('/api/scenes')
			scenes.value = loaded.map((scene) => ({
				...scene,
				custom_name: scene.custom_name ?? '',
				rois: scene.rois ?? []
			}))
			selectedSceneIdx.value = 0

			if (scenes.value.length === 1 && videoInfo.value) {
				const first = scenes.value[0]
				if (first.end_frame < videoInfo.value.total_frames - 1) {
					scenes.value.push({
						start_frame: first.end_frame + 1,
						end_frame: videoInfo.value.total_frames - 1,
						name: 'Rest of Video',
						custom_name: '',
						rois: []
					})
					await saveScenes(true)
				}
			}

			history.resetHistory(scenes.value)
		} catch (error) {
			console.error('Failed to load scenes:', error)
			setStatus('Failed to load scenes')
		}
	}

	async function saveScenes(skipHistory = false): Promise<void> {
		try {
			if (!skipHistory) {
				history.saveToHistory()
			}
			await apiPost('/api/scenes', scenes.value)
		} catch (error) {
			console.error('Failed to save scenes:', error)
			setStatus('Failed to save scenes')
		}
	}

	function selectScene(index: number): void {
		selectedSceneIdx.value = index
		selectedRoiIdx.value = null
		const scene = scenes.value[index]
		if (scene) {
			currentFrame.value = scene.start_frame
		}
	}

	async function splitScene(): Promise<void> {
		if (!videoInfo.value) return

		let sceneIdx = -1
		let scene: WorkspaceScene | null = null
		for (let i = 0; i < scenes.value.length; i++) {
			const candidate = scenes.value[i]
			if (
				candidate.start_frame <= currentFrame.value &&
				currentFrame.value <= candidate.end_frame
			) {
				sceneIdx = i
				scene = candidate
				break
			}
		}

		if (!scene) {
			window.alert('No scene found at current frame')
			return
		}

		const splitFrame = currentFrame.value
		if (splitFrame <= scene.start_frame || splitFrame >= scene.end_frame) {
			window.alert('Cannot split at this frame. Choose a frame within the scene range.')
			return
		}

		const scene1: WorkspaceScene = {
			start_frame: scene.start_frame,
			end_frame: splitFrame - 1,
			name: `Scene ${sceneIdx + 1}`,
			custom_name: scene.custom_name ?? '',
			rois: [...scene.rois]
		}
		const scene2: WorkspaceScene = {
			start_frame: splitFrame,
			end_frame: scene.end_frame,
			name: `Scene ${sceneIdx + 2}`,
			custom_name: '',
			rois: []
		}

		scenes.value.splice(sceneIdx, 1, scene1, scene2)
		for (let i = sceneIdx + 2; i < scenes.value.length; i++) {
			scenes.value[i].name = `Scene ${i + 1}`
		}
		await saveScenes()
	}

	async function addScene(): Promise<void> {
		if (!videoInfo.value) return
		const lastScene = scenes.value[scenes.value.length - 1]
		const startFrame = lastScene ? lastScene.end_frame + 1 : 0
		scenes.value.push({
			start_frame: startFrame,
			end_frame: videoInfo.value.total_frames - 1,
			name: `Scene ${scenes.value.length + 1}`,
			custom_name: '',
			rois: []
		})
		await saveScenes()
	}

	async function deleteScene(index: number): Promise<void> {
		if (!videoInfo.value) return
		if (scenes.value.length <= 1) {
			window.alert('Cannot delete the only scene')
			return
		}
		if (!window.confirm(`Delete ${scenes.value[index].name}?`)) return

		if (index > 0 && index < scenes.value.length - 1) {
			scenes.value[index - 1].end_frame = scenes.value[index + 1].start_frame - 1
		} else if (index > 0) {
			scenes.value[index - 1].end_frame = videoInfo.value.total_frames - 1
		} else if (index === 0 && scenes.value.length > 1) {
			scenes.value[1].start_frame = 0
		}

		scenes.value.splice(index, 1)
		selectedSceneIdx.value = Math.min(selectedSceneIdx.value, scenes.value.length - 1)
		await saveScenes()
	}

	async function mergeWithPrevious(): Promise<void> {
		if (selectedSceneIdx.value === 0) {
			window.alert('Cannot merge first scene')
			return
		}
		const current = scenes.value[selectedSceneIdx.value]
		const previous = scenes.value[selectedSceneIdx.value - 1]
		if (!window.confirm(`Merge "${current.name}" into "${previous.name}"?`)) return

		previous.end_frame = current.end_frame
		previous.rois.push(...current.rois)
		scenes.value.splice(selectedSceneIdx.value, 1)
		selectedSceneIdx.value--
		await saveScenes()
	}

	function prevScene(): number | null {
		for (let i = scenes.value.length - 1; i >= 0; i--) {
			if (scenes.value[i].start_frame < currentFrame.value) {
				return i
			}
		}
		return null
	}

	function nextScene(): number | null {
		for (let i = 0; i < scenes.value.length; i++) {
			if (scenes.value[i].start_frame > currentFrame.value) {
				return i
			}
		}
		return null
	}

	async function undoScenes(): Promise<void> {
		if (history.undo()) {
			await saveScenes(true)
		}
	}

	async function redoScenes(): Promise<void> {
		if (history.redo()) {
			await saveScenes(true)
		}
	}

	return {
		selectedSceneIdx,
		selectedRoiIdx,
		activeSceneIdx,
		currentScene,
		loadScenes,
		saveScenes,
		selectScene,
		splitScene,
		addScene,
		deleteScene,
		mergeWithPrevious,
		prevScene,
		nextScene,
		undoScenes,
		redoScenes
	}
}
