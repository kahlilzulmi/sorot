import { computed, reactive, ref, watch } from 'vue'
import {
	COGNITIVE_GAMES,
	COGNITIVE_GAME_SETTINGS_STORAGE_KEY,
	COGNITIVE_PLAYLIST_STORAGE_KEY,
	COGNITIVE_SETTINGS_STORAGE_KEY,
	DEFAULT_COGNITIVE_CURSOR,
	DEFAULT_COGNITIVE_PLAYLIST,
	normalizeCursorSettings,
	clampCursorSizePx,
	normalizeGameSettings,
	type CognitiveCursorSettings,
	type CognitiveGameId,
	type CognitiveGameSettingsMap,
	type CognitivePlaylistSettings,
	type CognitivePlayView,
	type DwellEffectStyle,
	type GazeCursorShape,
	type GazeInputSourceId
} from '../types/cognitiveGame'

function readCursorSettings(): CognitiveCursorSettings {
	if (typeof window === 'undefined') return { ...DEFAULT_COGNITIVE_CURSOR }
	try {
		const raw = window.localStorage.getItem(COGNITIVE_SETTINGS_STORAGE_KEY)
		if (!raw) return { ...DEFAULT_COGNITIVE_CURSOR }
		const parsed = JSON.parse(raw) as Partial<CognitiveCursorSettings> & { shape?: string }
		return normalizeCursorSettings(parsed)
	} catch {
		return { ...DEFAULT_COGNITIVE_CURSOR }
	}
}

function normalizePlaylist(parsed: Partial<CognitivePlaylistSettings> | null): CognitivePlaylistSettings {
	const orderRaw = parsed?.order ?? [...DEFAULT_COGNITIVE_PLAYLIST.order]
	const order = orderRaw.filter((id): id is CognitiveGameId =>
		COGNITIVE_GAMES.some((game) => game.id === id)
	)
	const missing = DEFAULT_COGNITIVE_PLAYLIST.order.filter((id) => !order.includes(id))
	const fullOrder = [...order, ...missing]

	const enabledRaw = parsed?.enabled ?? fullOrder
	const enabled = enabledRaw.filter((id): id is CognitiveGameId => fullOrder.includes(id))
	const enabledFinal = enabled.length > 0 ? enabled : [...fullOrder]

	return { order: fullOrder, enabled: enabledFinal }
}

function readPlaylist(): CognitivePlaylistSettings {
	if (typeof window === 'undefined') {
		return {
			order: [...DEFAULT_COGNITIVE_PLAYLIST.order],
			enabled: [...DEFAULT_COGNITIVE_PLAYLIST.enabled]
		}
	}
	try {
		const raw = window.localStorage.getItem(COGNITIVE_PLAYLIST_STORAGE_KEY)
		if (!raw) {
			return {
				order: [...DEFAULT_COGNITIVE_PLAYLIST.order],
				enabled: [...DEFAULT_COGNITIVE_PLAYLIST.enabled]
			}
		}
		return normalizePlaylist(JSON.parse(raw) as Partial<CognitivePlaylistSettings>)
	} catch {
		return {
			order: [...DEFAULT_COGNITIVE_PLAYLIST.order],
			enabled: [...DEFAULT_COGNITIVE_PLAYLIST.enabled]
		}
	}
}

function readGameSettings(): CognitiveGameSettingsMap {
	if (typeof window === 'undefined') return normalizeGameSettings(null)
	try {
		const raw = window.localStorage.getItem(COGNITIVE_GAME_SETTINGS_STORAGE_KEY)
		if (!raw) return normalizeGameSettings(null)
		return normalizeGameSettings(
			JSON.parse(raw) as Partial<Record<CognitiveGameId, { dwellMs?: number }>>
		)
	} catch {
		return normalizeGameSettings(null)
	}
}

const cursor = reactive<CognitiveCursorSettings>(readCursorSettings())
const playlist = reactive<CognitivePlaylistSettings>(readPlaylist())
const gameSettings = reactive<CognitiveGameSettingsMap>(readGameSettings())
const settingsOpen = ref(false)
const quitConfirmOpen = ref(false)
const gameSettingsOpenId = ref<CognitiveGameId | null>(null)

watch(
	cursor,
	() => {
		if (typeof window === 'undefined') return
		window.localStorage.setItem(COGNITIVE_SETTINGS_STORAGE_KEY, JSON.stringify({ ...cursor }))
	},
	{ deep: true }
)

watch(
	playlist,
	() => {
		if (typeof window === 'undefined') return
		window.localStorage.setItem(
			COGNITIVE_PLAYLIST_STORAGE_KEY,
			JSON.stringify({
				order: [...playlist.order],
				enabled: [...playlist.enabled]
			})
		)
	},
	{ deep: true }
)

watch(
	gameSettings,
	() => {
		if (typeof window === 'undefined') return
		window.localStorage.setItem(
			COGNITIVE_GAME_SETTINGS_STORAGE_KEY,
			JSON.stringify({ ...gameSettings })
		)
	},
	{ deep: true }
)

export function useCognitiveSettings() {
	const games = computed(() =>
		playlist.order
			.map((id) => COGNITIVE_GAMES.find((game) => game.id === id))
			.filter((game): game is (typeof COGNITIVE_GAMES)[number] => Boolean(game))
	)

	const enabledGames = computed(() =>
		playlist.order
			.filter((id) => playlist.enabled.includes(id))
			.map((id) => COGNITIVE_GAMES.find((game) => game.id === id))
			.filter((game): game is (typeof COGNITIVE_GAMES)[number] => Boolean(game))
	)

	const enabledCount = computed(() => playlist.enabled.length)

	const gameSettingsTarget = computed(() => {
		const id = gameSettingsOpenId.value
		if (!id) return null
		return COGNITIVE_GAMES.find((game) => game.id === id) ?? null
	})

	function setCursorShape(shape: GazeCursorShape): void {
		cursor.shape = shape
	}

	function setDwellEffect(effect: DwellEffectStyle): void {
		cursor.dwellEffect = effect
	}

	function setCursorColor(color: string): void {
		cursor.cursorColor = color
	}

	function setDwellEffectColor(color: string): void {
		cursor.dwellEffectColor = color
	}

	function setCursorSizePx(sizePx: number): void {
		cursor.cursorSizePx = clampCursorSizePx(sizePx)
	}

	function setDwellEffectSizePx(sizePx: number): void {
		cursor.dwellEffectSizePx = clampCursorSizePx(sizePx)
	}

	function setDwellMs(ms: number): void {
		cursor.dwellMs = Math.max(200, Math.round(ms))
	}

	function setGazeSource(source: GazeInputSourceId): void {
		cursor.gazeSource = source
	}

	function setPlayView(view: CognitivePlayView): void {
		cursor.playView = view
	}

	function dwellMsForGame(gameId: CognitiveGameId | null): number {
		if (!gameId) return cursor.dwellMs
		return gameSettings[gameId]?.dwellMs ?? cursor.dwellMs
	}

	function setGameDwellMs(gameId: CognitiveGameId, ms: number): void {
		gameSettings[gameId] = {
			...gameSettings[gameId],
			dwellMs: Math.max(200, Math.round(ms))
		}
	}

	function openGameSettings(gameId: CognitiveGameId): void {
		gameSettingsOpenId.value = gameId
		settingsOpen.value = false
		quitConfirmOpen.value = false
	}

	function closeGameSettings(): void {
		gameSettingsOpenId.value = null
	}

	function isGameEnabled(id: CognitiveGameId): boolean {
		return playlist.enabled.includes(id)
	}

	function toggleGameEnabled(id: CognitiveGameId): void {
		if (playlist.enabled.includes(id)) {
			if (playlist.enabled.length <= 1) return
			playlist.enabled = playlist.enabled.filter((entry) => entry !== id)
			return
		}
		playlist.enabled = [...playlist.enabled, id]
	}

	function moveGame(id: CognitiveGameId, direction: -1 | 1): void {
		const index = playlist.order.indexOf(id)
		if (index < 0) return
		const next = index + direction
		if (next < 0 || next >= playlist.order.length) return
		const copy = [...playlist.order]
		const [item] = copy.splice(index, 1)
		copy.splice(next, 0, item)
		playlist.order = copy
	}

	function reorderGame(fromId: CognitiveGameId, toId: CognitiveGameId): void {
		if (fromId === toId) return
		const fromIndex = playlist.order.indexOf(fromId)
		const toIndex = playlist.order.indexOf(toId)
		if (fromIndex < 0 || toIndex < 0) return
		const copy = [...playlist.order]
		const [item] = copy.splice(fromIndex, 1)
		copy.splice(toIndex, 0, item)
		playlist.order = copy
	}

	function moveGameToIndex(id: CognitiveGameId, toIndex: number): void {
		const fromIndex = playlist.order.indexOf(id)
		if (fromIndex < 0) return
		const clamped = Math.max(0, Math.min(playlist.order.length - 1, Math.round(toIndex)))
		if (fromIndex === clamped) return
		const copy = [...playlist.order]
		const [item] = copy.splice(fromIndex, 1)
		copy.splice(clamped, 0, item)
		playlist.order = copy
	}

	function toggleSettings(): void {
		settingsOpen.value = !settingsOpen.value
		if (settingsOpen.value) {
			quitConfirmOpen.value = false
			gameSettingsOpenId.value = null
		}
	}

	function openQuitConfirm(): void {
		quitConfirmOpen.value = true
		settingsOpen.value = false
		gameSettingsOpenId.value = null
	}

	function closeQuitConfirm(): void {
		quitConfirmOpen.value = false
	}

	function closeOverlays(): void {
		settingsOpen.value = false
		quitConfirmOpen.value = false
		gameSettingsOpenId.value = null
	}

	return {
		cursor,
		playlist,
		gameSettings,
		games,
		enabledGames,
		enabledCount,
		settingsOpen,
		quitConfirmOpen,
		gameSettingsOpenId,
		gameSettingsTarget,
		setCursorShape,
		setDwellEffect,
		setCursorColor,
		setDwellEffectColor,
		setCursorSizePx,
		setDwellEffectSizePx,
		setDwellMs,
		setGazeSource,
		setPlayView,
		dwellMsForGame,
		setGameDwellMs,
		openGameSettings,
		closeGameSettings,
		isGameEnabled,
		toggleGameEnabled,
		moveGame,
		reorderGame,
		moveGameToIndex,
		toggleSettings,
		openQuitConfirm,
		closeQuitConfirm,
		closeOverlays
	}
}
