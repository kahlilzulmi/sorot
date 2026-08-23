import { loadFacePairs, isFacePairFullySupplied, type FacePairAsset } from './faceFamiliarityAssets'

export type FaceFamiliaritySide = 'left' | 'right'

export interface FaceFamiliarityTrial {
	id: string
	pairId: string
	label: string
	leftSrc: string
	rightSrc: string
	/** Side that shows the real (non-AI) face. */
	correctSide: FaceFamiliaritySide
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

function toTrial(pair: FacePairAsset, index: number): FaceFamiliarityTrial {
	const realOnLeft = Math.random() < 0.5
	return {
		id: `face-fam-${pair.id}-${index}-${Date.now()}-${randInt(100, 999)}`,
		pairId: pair.id,
		label: pair.label,
		leftSrc: realOnLeft ? pair.realSrc : pair.aiSrc,
		rightSrc: realOnLeft ? pair.aiSrc : pair.realSrc,
		correctSide: realOnLeft ? 'left' : 'right'
	}
}

/**
 * One trial per fully supplied pair (user-defined count via settings).
 * Play is gated so at least one supplied pair exists before this runs.
 */
export function createFaceFamiliaritySession(): FaceFamiliarityTrial[] {
	const supplied = loadFacePairs().filter(isFacePairFullySupplied)
	const pool = shuffleInPlace([...supplied])
	return pool.map((pair, index) => toTrial(pair, index))
}
