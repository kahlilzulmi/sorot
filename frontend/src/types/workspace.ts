/** ROI entry in a saved workspace / scene (legacy JSON shape). */
export interface WorkspaceRoi {
	label: string
	x: number
	y: number
	width: number
	height: number
	color_tag?: string
}

/** Scene segment with frame bounds and nested ROIs. */
export interface WorkspaceScene {
	name: string
	custom_name?: string
	start_frame: number
	end_frame: number
	rois: WorkspaceRoi[]
}

/** Video metadata attached to a workspace session. */
export interface VideoInfo {
	filename: string
	width: number
	height: number
	fps: number
	total_frames: number
	duration: number
}
