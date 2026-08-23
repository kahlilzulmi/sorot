/** Memory Matrix module options (hub gear) — localStorage. */

export const MEMORY_MATRIX_SETTINGS_STORAGE_KEY = 'sorot.memoryMatrixSettings'

export interface MemoryMatrixSettings {
	/** How many yellow flashes in the first round. */
	startLength: number
	/** Number of rounds in a session. */
	rounds: number
	/** How long each cue stays yellow (ms). */
	flashMs: number
	/** Gap between yellow cues (ms). */
	gapMs: number
	/** Extra steps added after each successful round. */
	growBy: number
}

export const DEFAULT_MEMORY_MATRIX_SETTINGS: MemoryMatrixSettings = {
	startLength: 4,
	rounds: 5,
	flashMs: 700,
	gapMs: 350,
	growBy: 1
}

export const MEMORY_MATRIX_LENGTH_MIN = 2
export const MEMORY_MATRIX_LENGTH_MAX = 12
export const MEMORY_MATRIX_ROUNDS_MIN = 1
export const MEMORY_MATRIX_ROUNDS_MAX = 20
export const MEMORY_MATRIX_FLASH_MIN = 200
export const MEMORY_MATRIX_FLASH_MAX = 3000
export const MEMORY_MATRIX_GAP_MIN = 50
export const MEMORY_MATRIX_GAP_MAX = 2000
export const MEMORY_MATRIX_GROW_MIN = 0
export const MEMORY_MATRIX_GROW_MAX = 3

function clamp(value: number, min: number, max: number, fallback: number): number {
	if (!Number.isFinite(value)) return fallback
	return Math.max(min, Math.min(max, Math.round(value)))
}

export function normalizeMemoryMatrixSettings(
	parsed: Partial<MemoryMatrixSettings> | null
): MemoryMatrixSettings {
	const base = DEFAULT_MEMORY_MATRIX_SETTINGS
	if (!parsed) return { ...base }
	return {
		startLength: clamp(
			Number(parsed.startLength),
			MEMORY_MATRIX_LENGTH_MIN,
			MEMORY_MATRIX_LENGTH_MAX,
			base.startLength
		),
		rounds: clamp(
			Number(parsed.rounds),
			MEMORY_MATRIX_ROUNDS_MIN,
			MEMORY_MATRIX_ROUNDS_MAX,
			base.rounds
		),
		flashMs: clamp(
			Number(parsed.flashMs),
			MEMORY_MATRIX_FLASH_MIN,
			MEMORY_MATRIX_FLASH_MAX,
			base.flashMs
		),
		gapMs: clamp(Number(parsed.gapMs), MEMORY_MATRIX_GAP_MIN, MEMORY_MATRIX_GAP_MAX, base.gapMs),
		growBy: clamp(
			Number(parsed.growBy),
			MEMORY_MATRIX_GROW_MIN,
			MEMORY_MATRIX_GROW_MAX,
			base.growBy
		)
	}
}

export function loadMemoryMatrixSettings(): MemoryMatrixSettings {
	if (typeof window === 'undefined') return { ...DEFAULT_MEMORY_MATRIX_SETTINGS }
	try {
		const raw = window.localStorage.getItem(MEMORY_MATRIX_SETTINGS_STORAGE_KEY)
		if (!raw) return { ...DEFAULT_MEMORY_MATRIX_SETTINGS }
		return normalizeMemoryMatrixSettings(JSON.parse(raw) as Partial<MemoryMatrixSettings>)
	} catch {
		return { ...DEFAULT_MEMORY_MATRIX_SETTINGS }
	}
}

export function saveMemoryMatrixSettings(settings: MemoryMatrixSettings): MemoryMatrixSettings {
	const normalized = normalizeMemoryMatrixSettings(settings)
	if (typeof window !== 'undefined') {
		window.localStorage.setItem(MEMORY_MATRIX_SETTINGS_STORAGE_KEY, JSON.stringify(normalized))
	}
	return normalized
}

export function resetMemoryMatrixSettings(): MemoryMatrixSettings {
	if (typeof window !== 'undefined') {
		window.localStorage.removeItem(MEMORY_MATRIX_SETTINGS_STORAGE_KEY)
	}
	return { ...DEFAULT_MEMORY_MATRIX_SETTINGS }
}
