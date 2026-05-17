/** Video playback state synced with the HTML video element. */
export interface VideoPlaybackState {
	isPlaying: boolean
	currentTime: number
}

/**
 * Single gaze sample (x/y in native video pixel space).
 * `timestamp` is always in **seconds** after import (synced with HTMLVideoElement.currentTime).
 */
export interface GazeCoordinate {
	x: number
	y: number
	/** Playback time in seconds (not ms or frame index once stored in Pinia). */
	timestamp: number
}

/** Axis-aligned rectangular region of interest on the video frame. */
export interface RegionOfInterest {
	id: string
	x: number
	y: number
	width: number
	height: number
	label?: string
	color_tag?: string
}
