import {
	loadMemoryMatrixSettings,
	type MemoryMatrixSettings
} from './memoryMatrixSettings'

export const MEMORY_MATRIX_GRID_SIZE = 9

export interface MemoryMatrixRound {
	id: string
	/** Tile indices 0–8 in playback order. */
	sequence: number[]
}

function randInt(min: number, max: number): number {
	return Math.floor(Math.random() * (max - min + 1)) + min
}

export function buildMemoryMatrixSequence(length: number): number[] {
	const safeLength = Math.max(1, Math.min(MEMORY_MATRIX_GRID_SIZE * 2, Math.round(length)))
	const sequence: number[] = []
	let previous = -1
	for (let i = 0; i < safeLength; i += 1) {
		let next = randInt(0, MEMORY_MATRIX_GRID_SIZE - 1)
		// Avoid immediate repeats so cues are easier to perceive.
		if (next === previous && MEMORY_MATRIX_GRID_SIZE > 1) {
			next = (next + 1 + randInt(0, MEMORY_MATRIX_GRID_SIZE - 2)) % MEMORY_MATRIX_GRID_SIZE
		}
		sequence.push(next)
		previous = next
	}
	return sequence
}

export function createMemoryMatrixSession(
	settings: MemoryMatrixSettings = loadMemoryMatrixSettings()
): MemoryMatrixRound[] {
	const rounds: MemoryMatrixRound[] = []
	for (let i = 0; i < settings.rounds; i += 1) {
		const length = settings.startLength + i * settings.growBy
		rounds.push({
			id: `mm-round-${i}-${Date.now()}-${randInt(100, 999)}`,
			sequence: buildMemoryMatrixSequence(length)
		})
	}
	return rounds
}
