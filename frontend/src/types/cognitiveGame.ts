export type CognitiveGameId =
	| 'math-true-false'
	| 'math-fill-blank'
	| 'face-familiarity'
	| 'visual-search'
	| 'memory-matrix'

/** Visible gaze pointer glyph (not the dwell progress indicator). */
export type GazeCursorShape = 'arrow' | 'dot' | 'transparent'

/** Progress feedback shown while dwelling on a target. */
export type DwellEffectStyle = 'ring' | 'pie' | 'transparent'

/** @deprecated Prefer GazeCursorShape. Kept for older call sites during migration. */
export type DwellCursorShape = GazeCursorShape

export type GazeInputSourceId = 'mouse' | 'socket' | 'tobii-overlay' | 'webgazer'

/** In-game chrome: focus hides hub/hints; debug shows raw vs processed gaze. */
export type CognitivePlayView = 'focus' | 'debug'

export interface CognitiveGameDefinition {
	id: CognitiveGameId
	name: string
	description: string
	/** Catalog default dwell (ms) used to seed per-game settings. */
	dwellMsOverride: number | null
}

export interface CognitiveCursorSettings {
	shape: GazeCursorShape
	dwellEffect: DwellEffectStyle
	/** Pointer glyph color (arrow / dot). */
	cursorColor: string
	/** Dwell progress indicator color (ring / pie). */
	dwellEffectColor: string
	/** Pointer glyph size in CSS pixels (arrow / dot). */
	cursorSizePx: number
	/** Dwell progress indicator size in CSS pixels (ring / pie). */
	dwellEffectSizePx: number
	dwellMs: number
	gazeSource: GazeInputSourceId
	playView: CognitivePlayView
}

export interface CognitivePlaylistSettings {
	order: CognitiveGameId[]
	/** Games included when running “Play in order”. */
	enabled: CognitiveGameId[]
}

/** Per-module settings (hub card + gear panel). Day one: dwell only. */
export interface CognitiveGameModuleSettings {
	dwellMs: number
}

export type CognitiveGameSettingsMap = Record<CognitiveGameId, CognitiveGameModuleSettings>

export const COGNITIVE_GAMES: CognitiveGameDefinition[] = [
	{
		id: 'math-true-false',
		name: 'Math · True / False',
		description: 'Benar / Salah for full equations (UFYP math shell).',
		dwellMsOverride: null
	},
	{
		id: 'math-fill-blank',
		name: 'Math · Fill Blank',
		description: 'Fill the missing number from a 2×2 answer grid.',
		dwellMsOverride: null
	},
	{
		id: 'face-familiarity',
		name: 'Face Familiarity',
		description: 'Choose the real face vs AI-generated (dwell to select).',
		dwellMsOverride: null
	},
	{
		id: 'visual-search',
		name: 'Visual Search',
		description: 'Find target characters in a dense grid (3s dwell).',
		dwellMsOverride: 3000
	},
	{
		id: 'memory-matrix',
		name: 'Memory Matrix',
		description: 'Watch the yellow sequence, then repeat it by dwell.',
		dwellMsOverride: null
	}
]

export const CURSOR_SIZE_MIN = 16
export const CURSOR_SIZE_MAX = 96

export function clampCursorSizePx(value: number): number {
	if (!Number.isFinite(value)) return 36
	return Math.max(CURSOR_SIZE_MIN, Math.min(CURSOR_SIZE_MAX, Math.round(value)))
}

export const DEFAULT_COGNITIVE_CURSOR: CognitiveCursorSettings = {
	shape: 'dot',
	dwellEffect: 'ring',
	cursorColor: '#FFFFFF',
	dwellEffectColor: '#FFFFFF',
	cursorSizePx: 36,
	dwellEffectSizePx: 36,
	dwellMs: 1000,
	gazeSource: 'mouse',
	playView: 'debug'
}

export const DEFAULT_COGNITIVE_PLAYLIST: CognitivePlaylistSettings = {
	order: [
		'math-true-false',
		'math-fill-blank',
		'face-familiarity',
		'visual-search',
		'memory-matrix'
	],
	enabled: [
		'math-true-false',
		'math-fill-blank',
		'face-familiarity',
		'visual-search',
		'memory-matrix'
	]
}

export const COGNITIVE_SETTINGS_STORAGE_KEY = 'sorot.cognitiveSettings'
export const COGNITIVE_PLAYLIST_STORAGE_KEY = 'sorot.cognitivePlaylist'
export const COGNITIVE_GAME_SETTINGS_STORAGE_KEY = 'sorot.cognitiveGameSettings'

/** Hit-test attribute for dwell targets. */
export const GAZE_TARGET_ATTR = 'data-gaze-target'

export function buildDefaultGameSettings(): CognitiveGameSettingsMap {
	const map = {} as CognitiveGameSettingsMap
	for (const game of COGNITIVE_GAMES) {
		map[game.id] = {
			dwellMs: game.dwellMsOverride ?? DEFAULT_COGNITIVE_CURSOR.dwellMs
		}
	}
	return map
}

export function normalizeGameSettings(
	parsed: Partial<Record<CognitiveGameId, Partial<CognitiveGameModuleSettings>>> | null
): CognitiveGameSettingsMap {
	const defaults = buildDefaultGameSettings()
	if (!parsed) return defaults
	for (const game of COGNITIVE_GAMES) {
		const entry = parsed[game.id]
		if (!entry) continue
		const dwellMs = Number(entry.dwellMs)
		if (Number.isFinite(dwellMs)) {
			defaults[game.id] = { dwellMs: Math.max(200, Math.round(dwellMs)) }
		}
	}
	return defaults
}

export function normalizeCursorSettings(
	parsed: Partial<CognitiveCursorSettings> & { shape?: string; color?: string }
): CognitiveCursorSettings {
	let shape: GazeCursorShape = DEFAULT_COGNITIVE_CURSOR.shape
	let dwellEffect: DwellEffectStyle = DEFAULT_COGNITIVE_CURSOR.dwellEffect

	const rawShape = parsed.shape
	if (rawShape === 'arrow' || rawShape === 'dot' || rawShape === 'transparent') {
		shape = rawShape
	} else if (rawShape === 'ring' || rawShape === 'pie') {
		dwellEffect = rawShape
		shape = 'dot'
	}

	if (parsed.dwellEffect === 'ring' || parsed.dwellEffect === 'pie' || parsed.dwellEffect === 'transparent') {
		dwellEffect = parsed.dwellEffect
	}

	const legacyColor =
		typeof parsed.color === 'string' && parsed.color.trim() ? parsed.color : null
	const cursorColor =
		(typeof parsed.cursorColor === 'string' && parsed.cursorColor.trim()
			? parsed.cursorColor
			: null) ??
		legacyColor ??
		DEFAULT_COGNITIVE_CURSOR.cursorColor
	const dwellEffectColor =
		(typeof parsed.dwellEffectColor === 'string' && parsed.dwellEffectColor.trim()
			? parsed.dwellEffectColor
			: null) ??
		legacyColor ??
		DEFAULT_COGNITIVE_CURSOR.dwellEffectColor

	const { color: _legacyColor, ...rest } = parsed as Partial<CognitiveCursorSettings> & {
		color?: string
	}

	return {
		...DEFAULT_COGNITIVE_CURSOR,
		...rest,
		shape,
		dwellEffect,
		cursorColor,
		dwellEffectColor,
		cursorSizePx: clampCursorSizePx(
			Number(parsed.cursorSizePx) || DEFAULT_COGNITIVE_CURSOR.cursorSizePx
		),
		dwellEffectSizePx: clampCursorSizePx(
			Number(parsed.dwellEffectSizePx) || DEFAULT_COGNITIVE_CURSOR.dwellEffectSizePx
		),
		dwellMs: Math.max(200, Number(parsed.dwellMs) || DEFAULT_COGNITIVE_CURSOR.dwellMs),
		playView: parsed.playView === 'focus' ? 'focus' : 'debug'
	}
}
