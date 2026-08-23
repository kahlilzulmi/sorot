import {
	loadVisualSearchSettings,
	type VisualSearchSettings
} from './visualSearchSettings'

export interface VisualSearchLevelDef {
	id: string
	distractor: string
	target: string
	prompt: string
}

/** Levels matching the UFYP visual-search reference strip. */
export const VISUAL_SEARCH_LEVELS: VisualSearchLevelDef[] = [
	{
		id: 'c-o',
		distractor: 'C',
		target: 'O',
		prompt: 'Temukan semua huruf O'
	},
	{
		id: 'o-q',
		distractor: 'O',
		target: 'Q',
		prompt: 'Temukan semua huruf Q'
	},
	{
		id: 'bar-i',
		distractor: '|',
		target: 'I',
		prompt: 'Temukan semua huruf I (i kapital)'
	}
]

export interface VisualSearchCell {
	/** Stable cell id for gaze targets (`vs-cell-${id}`). */
	id: string
	char: string
	isTarget: boolean
}

export interface VisualSearchLevel {
	def: VisualSearchLevelDef
	columns: number
	rows: number
	cells: VisualSearchCell[]
	targetIds: string[]
}

function randInt(min: number, max: number): number {
	return Math.floor(Math.random() * (max - min + 1)) + min
}

function shuffleInPlace<T>(items: T[]): T[] {
	for (let i = items.length - 1; i > 0; i -= 1) {
		const j = randInt(0, i)
		const tmp = items[i]!
		items[i] = items[j]!
		items[j] = tmp
	}
	return items
}

export function buildVisualSearchLevel(
	def: VisualSearchLevelDef,
	settings: VisualSearchSettings
): VisualSearchLevel {
	const columns = settings.columns
	const rows = settings.rows
	const total = columns * rows
	const targetCount = Math.min(settings.targetCount, Math.max(1, total - 1))
	const indices = shuffleInPlace([...Array.from({ length: total }, (_, i) => i)]).slice(
		0,
		targetCount
	)
	const targetSet = new Set(indices)
	const cells: VisualSearchCell[] = []
	const targetIds: string[] = []

	for (let i = 0; i < total; i += 1) {
		const id = String(i)
		const isTarget = targetSet.has(i)
		cells.push({
			id,
			char: isTarget ? def.target : def.distractor,
			isTarget
		})
		if (isTarget) targetIds.push(id)
	}

	return { def, columns, rows, cells, targetIds }
}

export function createVisualSearchSession(
	settings: VisualSearchSettings = loadVisualSearchSettings()
): VisualSearchLevel[] {
	return VISUAL_SEARCH_LEVELS.map((def) => buildVisualSearchLevel(def, settings))
}

export function formatVisualSearchTimer(totalSeconds: number): string {
	const safe = Math.max(0, Math.floor(totalSeconds))
	const minutes = Math.floor(safe / 60)
	const seconds = safe % 60
	return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}
