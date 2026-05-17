/**
 * Acceptable gaze position error (px) for ROI hit tests and export validation.
 * Downstream ROI math should expand bounds by this margin — not used in marker CV.
 */
export const GAZE_POSITION_MARGIN_PX = 15

/** Minimum width/height (px) when creating or resizing ROIs on the canvas. */
export const MIN_ROI_DIMENSION = 20
