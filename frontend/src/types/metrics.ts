/** Per-ROI gaze metrics aligned with Sorot report / statistics exports. */
export interface RoiTimeMetric {
	scene: string
	roiLabel: string
	gazeCount: number
	/** Share of gaze samples in the scene attributed to this ROI (0–100). */
	percentage: number
	totalSamples?: number
	customName?: string
	displayName?: string
}
