/** Visual Search module options (hub gear) — localStorage. */

export const VISUAL_SEARCH_SETTINGS_STORAGE_KEY = 'sorot.visualSearchSettings'

export interface VisualSearchSettings {
	/** Grid columns (density). */
	columns: number
	/** Grid rows (density). */
	rows: number
	/** How many target letters to place per level. */
	targetCount: number
	/** Session countdown length in seconds. */
	timerSeconds: number
}

export const DEFAULT_VISUAL_SEARCH_SETTINGS: VisualSearchSettings = {
	columns: 24,
	rows: 14,
	targetCount: 6,
	timerSeconds: 300
}

export const VISUAL_SEARCH_COLUMNS_MIN = 12
export const VISUAL_SEARCH_COLUMNS_MAX = 40
export const VISUAL_SEARCH_ROWS_MIN = 8
export const VISUAL_SEARCH_ROWS_MAX = 24
export const VISUAL_SEARCH_TARGETS_MIN = 1
export const VISUAL_SEARCH_TARGETS_MAX = 20
export const VISUAL_SEARCH_TIMER_MIN = 30
export const VISUAL_SEARCH_TIMER_MAX = 900

function clamp(value: number, min: number, max: number, fallback: number): number {
	if (!Number.isFinite(value)) return fallback
	return Math.max(min, Math.min(max, Math.round(value)))
}

export function normalizeVisualSearchSettings(
	parsed: Partial<VisualSearchSettings> | null
): VisualSearchSettings {
	const base = DEFAULT_VISUAL_SEARCH_SETTINGS
	if (!parsed) return { ...base }
	return {
		columns: clamp(
			Number(parsed.columns),
			VISUAL_SEARCH_COLUMNS_MIN,
			VISUAL_SEARCH_COLUMNS_MAX,
			base.columns
		),
		rows: clamp(Number(parsed.rows), VISUAL_SEARCH_ROWS_MIN, VISUAL_SEARCH_ROWS_MAX, base.rows),
		targetCount: clamp(
			Number(parsed.targetCount),
			VISUAL_SEARCH_TARGETS_MIN,
			VISUAL_SEARCH_TARGETS_MAX,
			base.targetCount
		),
		timerSeconds: clamp(
			Number(parsed.timerSeconds),
			VISUAL_SEARCH_TIMER_MIN,
			VISUAL_SEARCH_TIMER_MAX,
			base.timerSeconds
		)
	}
}

export function loadVisualSearchSettings(): VisualSearchSettings {
	if (typeof window === 'undefined') return { ...DEFAULT_VISUAL_SEARCH_SETTINGS }
	try {
		const raw = window.localStorage.getItem(VISUAL_SEARCH_SETTINGS_STORAGE_KEY)
		if (!raw) return { ...DEFAULT_VISUAL_SEARCH_SETTINGS }
		return normalizeVisualSearchSettings(JSON.parse(raw) as Partial<VisualSearchSettings>)
	} catch {
		return { ...DEFAULT_VISUAL_SEARCH_SETTINGS }
	}
}

export function saveVisualSearchSettings(settings: VisualSearchSettings): VisualSearchSettings {
	const normalized = normalizeVisualSearchSettings(settings)
	if (typeof window !== 'undefined') {
		window.localStorage.setItem(VISUAL_SEARCH_SETTINGS_STORAGE_KEY, JSON.stringify(normalized))
	}
	return normalized
}

export function resetVisualSearchSettings(): VisualSearchSettings {
	if (typeof window !== 'undefined') {
		window.localStorage.removeItem(VISUAL_SEARCH_SETTINGS_STORAGE_KEY)
	}
	return { ...DEFAULT_VISUAL_SEARCH_SETTINGS }
}
