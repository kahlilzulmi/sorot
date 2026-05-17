import type { GazeCoordinate, RegionOfInterest } from '../types/gaze'
import type { RoiTimeMetric } from '../types/metrics'
import { findGazeAtTime } from './findGazeAtTime'

/** Default gaze-to-ROI tolerance per Sorot accuracy constraint (~15px). */
export const GAZE_POSITION_MARGIN_PX = 15

/** @deprecated Use GAZE_POSITION_MARGIN_PX */
export const GAZE_ROI_MARGIN_PX = GAZE_POSITION_MARGIN_PX

export const DEFAULT_SCENE_NAME = 'Session'

/**
 * Whether a gaze point falls inside an axis-aligned ROI, expanded by margin on all sides.
 * Unlike strict Python bounds tests, margin absorbs ~15px tracking error.
 */
export function isGazeInRoi(
	gaze: Pick<GazeCoordinate, 'x' | 'y'>,
	roi: RegionOfInterest,
	marginPx: number = GAZE_POSITION_MARGIN_PX
): boolean {
	return (
		gaze.x >= roi.x - marginPx
		&& gaze.x <= roi.x + roi.width + marginPx
		&& gaze.y >= roi.y - marginPx
		&& gaze.y <= roi.y + roi.height + marginPx
	)
}

/**
 * Index of the topmost ROI containing the gaze point, or null when outside all ROIs.
 */
export function findRoiIndexForGaze(
	gaze: Pick<GazeCoordinate, 'x' | 'y'>,
	regions: RegionOfInterest[],
	marginPx: number = GAZE_POSITION_MARGIN_PX
): number | null {
	for (let index = regions.length - 1; index >= 0; index -= 1) {
		if (isGazeInRoi(gaze, regions[index], marginPx)) {
			return index
		}
	}
	return null
}

/**
 * Gaze sample closest to playback time within a sync window (seconds).
 * Uses binary search when coordinates are sorted by timestamp.
 */
export function getGazeSampleAtTime(
	coordinates: readonly GazeCoordinate[],
	currentTime: number,
	windowSeconds = 0.05
): GazeCoordinate | null {
	return findGazeAtTime(coordinates, currentTime, windowSeconds)
}

/**
 * Single-pass ROI attribution and metrics.
 *
 * - Each sample is assigned to at most one ROI (topmost when overlapping).
 * - Samples outside all ROIs are excluded from percentage denominators.
 * - `percentage` = share of attributed hits for that ROI (0–100).
 * - `totalSamples` = all gaze rows in the scene (including outside ROI).
 */
export function computeRoiMetrics(
	samples: readonly GazeCoordinate[],
	rois: readonly RegionOfInterest[],
	sceneName: string = DEFAULT_SCENE_NAME,
	marginPx: number = GAZE_POSITION_MARGIN_PX
): RoiTimeMetric[] {
	if (rois.length === 0) {
		return []
	}

	const gazeCounts = new Array<number>(rois.length).fill(0)
	let attributedHits = 0
	const totalSamples = samples.length

	for (const sample of samples) {
		const roiIndex = findRoiIndexForGaze(sample, rois as RegionOfInterest[], marginPx)
		if (roiIndex === null) {
			continue
		}
		gazeCounts[roiIndex] += 1
		attributedHits += 1
	}

	if (attributedHits === 0) {
		return rois.map((roi) => ({
			scene: sceneName,
			roiLabel: roi.label ?? 'ROI',
			gazeCount: 0,
			percentage: 0,
			totalSamples,
			displayName: sceneName
		}))
	}

	return rois.map((roi, index) => {
		const gazeCount = gazeCounts[index]
		const percentage = (gazeCount / attributedHits) * 100
		return {
			scene: sceneName,
			roiLabel: roi.label ?? `ROI ${index + 1}`,
			gazeCount,
			percentage: Math.round(percentage * 100) / 100,
			totalSamples,
			displayName: sceneName
		}
	})
}

/*
 * QA fixture (manual / future vitest):
 *
 * ROIs: A (0,0,100,100), B (200,0,100,100), C (400,0,100,100)
 * Margin: 0 for deterministic counts
 *
 * 1000 samples:
 *   400 at (50,50)   -> A
 *   300 at (250,50)  -> B
 *   200 at (450,50)  -> C
 *   100 at (900,900) -> outside
 *
 * Expected attributedHits = 900
 *   A: gazeCount 400, percentage 44.44
 *   B: gazeCount 300, percentage 33.33
 *   C: gazeCount 200, percentage 22.22
 *   totalSamples = 1000 for each row
 */
