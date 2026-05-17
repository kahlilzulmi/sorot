/** Layout of the visible video frame inside its element (object-contain letterboxing). */
export interface VideoContentLayout {
	/** Offset from container top-left, CSS px */
	offsetX: number
	offsetY: number
	/** Visible video frame size on screen, CSS px */
	displayWidth: number
	displayHeight: number
	/** Native video resolution (canvas bitmap size) */
	pixelWidth: number
	pixelHeight: number
	/** CSS pixels per native video pixel */
	scale: number
}

/**
 * Computes where the video pixels are actually drawn inside the &lt;video&gt; box
 * when `object-fit: contain` is used.
 */
export function getVideoContentLayout(
	video: HTMLVideoElement,
	container: HTMLElement
): VideoContentLayout | null {
	const pixelWidth = video.videoWidth
	const pixelHeight = video.videoHeight
	if (pixelWidth <= 0 || pixelHeight <= 0) return null

	const containerRect = container.getBoundingClientRect()
	const videoRect = video.getBoundingClientRect()
	const scale = Math.min(videoRect.width / pixelWidth, videoRect.height / pixelHeight)
	const displayWidth = pixelWidth * scale
	const displayHeight = pixelHeight * scale
	const offsetX = videoRect.left - containerRect.left + (videoRect.width - displayWidth) / 2
	const offsetY = videoRect.top - containerRect.top + (videoRect.height - displayHeight) / 2

	return {
		offsetX,
		offsetY,
		displayWidth,
		displayHeight,
		pixelWidth,
		pixelHeight,
		scale
	}
}

/**
 * Sizes and positions the ROI canvas over the rendered video frame (not the container).
 * Canvas bitmap uses native video resolution; CSS box matches the visible frame.
 */
export function syncCanvasToVideoLayout(
	canvas: HTMLCanvasElement,
	video: HTMLVideoElement,
	container: HTMLElement
): VideoContentLayout | null {
	const layout = getVideoContentLayout(video, container)
	if (!layout) return null

	canvas.width = layout.pixelWidth
	canvas.height = layout.pixelHeight
	canvas.style.position = 'absolute'
	canvas.style.left = `${layout.offsetX}px`
	canvas.style.top = `${layout.offsetY}px`
	canvas.style.width = `${layout.displayWidth}px`
	canvas.style.height = `${layout.displayHeight}px`
	canvas.style.pointerEvents = 'auto'

	return layout
}
