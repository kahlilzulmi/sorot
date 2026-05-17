import type { GazeCoordinate } from '../types/gaze'

/**
 * Nearest gaze sample to `currentTime` within `windowSeconds`, using binary search.
 * Expects `coordinates` sorted ascending by `timestamp`.
 */
export function findGazeAtTime(
	coordinates: readonly GazeCoordinate[],
	currentTime: number,
	windowSeconds = 0.05
): GazeCoordinate | null {
	if (coordinates.length === 0) {
		return null
	}

	let left = 0
	let right = coordinates.length - 1

	while (left < right) {
		const mid = Math.floor((left + right) / 2)
		if (coordinates[mid].timestamp < currentTime) {
			left = mid + 1
		} else {
			right = mid
		}
	}

	const candidates: GazeCoordinate[] = []
	if (left > 0) {
		candidates.push(coordinates[left - 1])
	}
	if (left < coordinates.length) {
		candidates.push(coordinates[left])
	}

	let closest: GazeCoordinate | null = null
	let closestDelta = windowSeconds

	for (const sample of candidates) {
		const delta = Math.abs(sample.timestamp - currentTime)
		if (delta <= closestDelta) {
			closest = sample
			closestDelta = delta
		}
	}

	return closest
}

/** Sort gaze rows by timestamp (seconds) for binary lookup. */
export function sortGazeByTimestamp(coordinates: GazeCoordinate[]): GazeCoordinate[] {
	return [...coordinates].sort((a, b) => a.timestamp - b.timestamp)
}
