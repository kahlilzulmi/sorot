import { computed, ref, type Ref } from 'vue'
import type { WorkspaceScene } from '../types/workspace'

function cloneScenes(scenes: WorkspaceScene[]): WorkspaceScene[] {
	return JSON.parse(JSON.stringify(scenes)) as WorkspaceScene[]
}

export function useHistory(scenes: Ref<WorkspaceScene[]>) {
	const history = ref<WorkspaceScene[][]>([])
	const historyIndex = ref(-1)

	const canUndo = computed(() => historyIndex.value > 0)
	const canRedo = computed(() => historyIndex.value < history.value.length - 1)

	function resetHistory(snapshot: WorkspaceScene[]): void {
		history.value = [cloneScenes(snapshot)]
		historyIndex.value = 0
	}

	function saveToHistory(): void {
		if (historyIndex.value < history.value.length - 1) {
			history.value = history.value.slice(0, historyIndex.value + 1)
		}
		history.value.push(cloneScenes(scenes.value))
		historyIndex.value++

		if (history.value.length > 50) {
			history.value.shift()
			historyIndex.value--
		}
	}

	function applyHistoryIndex(index: number): void {
		const snapshot = history.value[index]
		if (!snapshot) return
		scenes.value = cloneScenes(snapshot)
	}

	function undo(): boolean {
		if (!canUndo.value) return false
		historyIndex.value--
		applyHistoryIndex(historyIndex.value)
		return true
	}

	function redo(): boolean {
		if (!canRedo.value) return false
		historyIndex.value++
		applyHistoryIndex(historyIndex.value)
		return true
	}

	return {
		canUndo,
		canRedo,
		resetHistory,
		saveToHistory,
		undo,
		redo
	}
}
