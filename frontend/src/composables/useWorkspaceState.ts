import { computed, reactive, type ComputedRef } from 'vue'

export type AppMode = 'select' | 'live' | 'import'

type SelectableMode = Exclude<AppMode, 'select'>

export interface WorkspaceState {
	appMode: AppMode
	statusMessage: string
	videoInfo: Record<string, unknown> | null
	scenes: Array<Record<string, unknown>>
	currentFrame: number
	showNewVideoModal: boolean
	lastUpdated: string | null
	currentWorkspaceFile: string | null
}

export interface WorkspaceStateApi {
	state: WorkspaceState
	modeTitle: ComputedRef<string>
	selectMode: (mode: SelectableMode) => void
	backToModeSelect: () => void
	setStatus: (message: string) => void
	markUpdated: () => void
}

export function useWorkspaceState(): WorkspaceStateApi {
	// Pattern: central reactive store for cross-component UI state.
	const state = reactive<WorkspaceState>({
		appMode: 'select',
		statusMessage: 'Ready',
		videoInfo: null,
		scenes: [],
		currentFrame: 0,
		showNewVideoModal: false,
		lastUpdated: null,
		currentWorkspaceFile: null
	})

	// Derived display text stays as computed, not duplicated in components.
	const modeTitle = computed(() => {
		if (state.appMode === 'live') return 'Live Recording Mode'
		if (state.appMode === 'import') return 'Import and Analyze Mode'
		return 'Choose your workflow'
	})

	function selectMode(mode: SelectableMode): void {
		state.appMode = mode
		state.statusMessage = `Mode selected: ${mode}`
	}

	function backToModeSelect(): void {
		state.appMode = 'select'
		state.statusMessage = 'Back to mode selection'
	}

	function setStatus(message: string): void {
		state.statusMessage = message
	}

	function markUpdated(): void {
		state.lastUpdated = new Date().toISOString()
	}

	// Public composable API used by parent orchestrator components.
	return {
		state,
		modeTitle,
		selectMode,
		backToModeSelect,
		setStatus,
		markUpdated
	}
}
