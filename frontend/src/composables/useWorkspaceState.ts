import { computed, reactive, type ComputedRef } from 'vue'
import type { VideoInfo, WorkspaceScene } from '../types/workspace'

export type { VideoInfo, WorkspaceScene } from '../types/workspace'

export type AppMode = 'select' | 'live' | 'import'

type SelectableMode = Exclude<AppMode, 'select'>
const NAV_STORAGE_KEY = 'sorot:last-navigation'

interface StoredNavigation {
	mode?: AppMode
	ws?: string | null
}

export interface WorkspaceState {
	appMode: AppMode
	statusMessage: string
	videoInfo: VideoInfo | null
	scenes: WorkspaceScene[]
	currentFrame: number
	showNewVideoModal: boolean
	showRecordModal: boolean
	showProcessModal: boolean
	showImportModal: boolean
	lastUpdated: string | null
	currentWorkspaceFile: string | null
}

export interface WorkspaceStateApi {
	state: WorkspaceState
	modeTitle: ComputedRef<string>
	selectMode: (mode: SelectableMode) => void
	backToModeSelect: () => void
	setCurrentWorkspaceFile: (workspaceFile: string | null) => void
	setStatus: (message: string) => void
	markUpdated: () => void
}

function normalizeMode(mode: string | null | undefined): AppMode {
	if (mode === 'live' || mode === 'import' || mode === 'select') return mode
	return 'select'
}

function readStoredNavigation(): StoredNavigation {
	if (typeof window === 'undefined') return {}

	try {
		const raw = window.localStorage.getItem(NAV_STORAGE_KEY)
		if (!raw) return {}
		const parsed = JSON.parse(raw) as StoredNavigation
		return parsed ?? {}
	} catch {
		return {}
	}
}

function readInitialNavigation(): { mode: AppMode; workspaceFile: string | null } {
	const stored = readStoredNavigation()
	let mode = normalizeMode(stored.mode)
	let workspaceFile = stored.ws ?? null

	if (typeof window !== 'undefined') {
		const params = new URLSearchParams(window.location.search)
		mode = normalizeMode(params.get('mode') ?? mode)

		const wsParam = params.get('ws')
		if (wsParam !== null) {
			workspaceFile = wsParam.trim() || null
		}
	}

	return {
		mode,
		workspaceFile
	}
}

function persistNavigation(mode: AppMode, workspaceFile: string | null): void {
	if (typeof window === 'undefined') return

	const normalizedWorkspaceFile = workspaceFile?.trim() || null
	const params = new URLSearchParams(window.location.search)
	params.set('mode', mode)

	if (normalizedWorkspaceFile) {
		params.set('ws', normalizedWorkspaceFile)
	} else {
		params.delete('ws')
	}

	const search = params.toString()
	const nextUrl = search ? `${window.location.pathname}?${search}` : window.location.pathname
	window.history.replaceState({}, '', nextUrl)

	window.localStorage.setItem(
		NAV_STORAGE_KEY,
		JSON.stringify({ mode, ws: normalizedWorkspaceFile })
	)
}

export function useWorkspaceState(): WorkspaceStateApi {
	// Pattern: central reactive store for cross-component UI state.
	const initialNavigation = readInitialNavigation()

	const state = reactive<WorkspaceState>({
		appMode: initialNavigation.mode,
		statusMessage: 'Ready',
		videoInfo: null,
		scenes: [],
		currentFrame: 0,
		showNewVideoModal: false,
		showRecordModal: false,
		showProcessModal: false,
		showImportModal: false,
		lastUpdated: null,
		currentWorkspaceFile: initialNavigation.workspaceFile
	})

	persistNavigation(state.appMode, state.currentWorkspaceFile)

	// Derived display text stays as computed, not duplicated in components.
	const modeTitle = computed(() => {
		if (state.appMode === 'live') return 'Live Recording Mode'
		if (state.appMode === 'import') return 'Import and Analyze Mode'
		return 'Choose your workflow'
	})

	function selectMode(mode: SelectableMode): void {
		state.appMode = mode
		state.statusMessage = `Mode selected: ${mode}`
		persistNavigation(state.appMode, state.currentWorkspaceFile)
	}

	function backToModeSelect(): void {
		state.appMode = 'select'
		state.statusMessage = 'Back to mode selection'
		persistNavigation(state.appMode, state.currentWorkspaceFile)
	}

	function setCurrentWorkspaceFile(workspaceFile: string | null): void {
		state.currentWorkspaceFile = workspaceFile?.trim() || null
		persistNavigation(state.appMode, state.currentWorkspaceFile)
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
		setCurrentWorkspaceFile,
		setStatus,
		markUpdated
	}
}
