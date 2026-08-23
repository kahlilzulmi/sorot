/** Face Familiarity image pairs — defaults + optional localStorage override. */

export const FACE_FAMILIARITY_ASSETS_STORAGE_KEY = 'sorot.faceFamiliarityAssets'

export interface FacePairAsset {
	id: string
	label: string
	/** Real / original face image (URL or data URL). */
	realSrc: string
	/** AI-generated counterpart (URL or data URL). */
	aiSrc: string
}

function placeholderSvg(label: string, background: string, accent: string): string {
	const safe = label.replace(/[<>&'"]/g, '')
	const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="512" height="512" fill="${background}"/>
  <circle cx="256" cy="200" r="88" fill="${accent}" opacity="0.85"/>
  <ellipse cx="256" cy="420" rx="150" ry="110" fill="${accent}" opacity="0.85"/>
  <text x="256" y="490" text-anchor="middle" fill="#ffffff" font-family="Segoe UI, sans-serif" font-size="28">${safe}</text>
</svg>`
	return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}

function createPlaceholderPair(n: number, stableId?: string): FacePairAsset {
	const hues = [
		{ realBg: '#1e3a5f', realAccent: '#4a90d9', aiBg: '#3a1e5f', aiAccent: '#9b59d9' },
		{ realBg: '#1e5f3a', realAccent: '#4ad98a', aiBg: '#5f3a1e', aiAccent: '#d98a4a' },
		{ realBg: '#5f1e3a', realAccent: '#d94a7a', aiBg: '#1e5f5f', aiAccent: '#4ad9d9' },
		{ realBg: '#3a3a1e', realAccent: '#d9d94a', aiBg: '#1e3a3a', aiAccent: '#4ad9c0' },
		{ realBg: '#2a2a4a', realAccent: '#7a7ad9', aiBg: '#4a2a2a', aiAccent: '#d97a7a' }
	] as const
	const palette = hues[(Math.max(1, n) - 1) % hues.length]!
	return {
		id: stableId ?? `pair-${n}-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
		label: `Tokoh ${n}`,
		realSrc: placeholderSvg(`REAL ${n}`, palette.realBg, palette.realAccent),
		aiSrc: placeholderSvg(`AI ${n}`, palette.aiBg, palette.aiAccent)
	}
}

/** Built-in starter slots (user can add/remove pairs in settings). */
export const DEFAULT_FACE_PAIRS: FacePairAsset[] = [
	createPlaceholderPair(1, 'pair-1'),
	createPlaceholderPair(2, 'pair-2'),
	createPlaceholderPair(3, 'pair-3')
]

export const MIN_FACE_PAIRS = 1
export const MAX_FACE_PAIRS = 40

/** New empty (placeholder) pair for settings “Add pair”. */
export function createEmptyFacePair(existingCount: number): FacePairAsset {
	return createPlaceholderPair(Math.max(1, existingCount + 1))
}

function isFacePairAsset(value: unknown): value is FacePairAsset {
	if (!value || typeof value !== 'object') return false
	const entry = value as Record<string, unknown>
	return (
		typeof entry.id === 'string' &&
		typeof entry.label === 'string' &&
		typeof entry.realSrc === 'string' &&
		typeof entry.aiSrc === 'string' &&
		entry.realSrc.length > 0 &&
		entry.aiSrc.length > 0
	)
}

export function normalizeFacePairs(parsed: unknown): FacePairAsset[] {
	if (!Array.isArray(parsed)) return DEFAULT_FACE_PAIRS.map((pair) => ({ ...pair }))
	const pairs = parsed.filter(isFacePairAsset).map((pair) => ({
		id: pair.id.trim() || `pair-${Date.now()}`,
		label: pair.label.trim() || 'Untitled',
		realSrc: pair.realSrc,
		aiSrc: pair.aiSrc
	}))
	if (pairs.length === 0) return DEFAULT_FACE_PAIRS.map((pair) => ({ ...pair }))
	return pairs.slice(0, MAX_FACE_PAIRS)
}

export function loadFacePairs(): FacePairAsset[] {
	if (typeof window === 'undefined') {
		return DEFAULT_FACE_PAIRS.map((pair) => ({ ...pair }))
	}
	try {
		const raw = window.localStorage.getItem(FACE_FAMILIARITY_ASSETS_STORAGE_KEY)
		if (!raw) return DEFAULT_FACE_PAIRS.map((pair) => ({ ...pair }))
		return normalizeFacePairs(JSON.parse(raw) as unknown)
	} catch {
		return DEFAULT_FACE_PAIRS.map((pair) => ({ ...pair }))
	}
}

export function saveFacePairs(pairs: FacePairAsset[]): FacePairAsset[] {
	const normalized = normalizeFacePairs(pairs)
	if (typeof window !== 'undefined') {
		window.localStorage.setItem(FACE_FAMILIARITY_ASSETS_STORAGE_KEY, JSON.stringify(normalized))
	}
	return normalized
}

export function resetFacePairsToDefaults(): FacePairAsset[] {
	if (typeof window !== 'undefined') {
		window.localStorage.removeItem(FACE_FAMILIARITY_ASSETS_STORAGE_KEY)
	}
	return DEFAULT_FACE_PAIRS.map((pair) => ({ ...pair }))
}

export function readImageFileAsDataUrl(file: File): Promise<string> {
	return new Promise((resolve, reject) => {
		const reader = new FileReader()
		reader.onload = () => {
			const result = reader.result
			if (typeof result === 'string' && result.startsWith('data:image/')) {
				resolve(result)
				return
			}
			reject(new Error('File is not a readable image'))
		}
		reader.onerror = () => reject(reader.error ?? new Error('Failed to read image'))
		reader.readAsDataURL(file)
	})
}

/** Default placeholders are SVG data URLs; uploaded photos are raster data URLs or http(s). */
export function isPlaceholderImageSrc(src: string): boolean {
	return src.startsWith('data:image/svg+xml')
}

export function isFacePairFullySupplied(pair: FacePairAsset): boolean {
	return !isPlaceholderImageSrc(pair.realSrc) && !isPlaceholderImageSrc(pair.aiSrc)
}

/** True when enough real+AI photo pairs exist to run a session (not SVG placeholders). */
export function hasSuppliedFacePhotos(minimumPairs = 1): boolean {
	const pairs = loadFacePairs().filter(isFacePairFullySupplied)
	return pairs.length >= Math.max(1, minimumPairs)
}

export function facePhotosMissingMessage(): string {
	return (
		'Face Familiarity needs real + AI photos first.\n\n' +
		"Open the game's settings (gear icon on the hub card), upload both images for each pair, then Save photos.\n\n" +
		'Play is blocked until photos are supplied.'
	)
}
