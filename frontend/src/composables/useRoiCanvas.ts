import { onBeforeUnmount, onMounted, ref, watch, type Ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useGazeStore } from '../stores/useGazeStore'
import type { RegionOfInterest } from '../types/gaze'
import type { RoiBounds } from '../stores/useGazeStore'
import { MIN_ROI_DIMENSION } from '../constants/gaze'
import { findRoiIndexForGaze, getGazeSampleAtTime } from '../utils/gazeRoi'
import {
	syncCanvasToVideoLayout,
	type VideoContentLayout
} from '../utils/videoLayout'

const LABEL_HEIGHT = 24
const MIN_TOUCH_TARGET_PX = 44

type RoiResizeHandle = 'tl' | 'tr' | 'bl' | 'br' | 'body'

interface RoiHitResult {
	roiIndex: number
	handle: RoiResizeHandle
}

interface OriginalRoiBounds {
	x: number
	y: number
	width: number
	height: number
}

function hexToRgba(hex: string, alpha: number): string {
	const normalized = hex.replace('#', '')
	if (normalized.length !== 6) return `rgba(97, 175, 239, ${alpha})`
	const red = Number.parseInt(normalized.slice(0, 2), 16)
	const green = Number.parseInt(normalized.slice(2, 4), 16)
	const blue = Number.parseInt(normalized.slice(4, 6), 16)
	return `rgba(${red}, ${green}, ${blue}, ${alpha})`
}

export function useRoiCanvas(
	canvasRef: Ref<HTMLCanvasElement | null>,
	videoRef: Ref<HTMLVideoElement | null>,
	containerRef: Ref<HTMLElement | null>,
	disabled: Ref<boolean>,
	onAfterRender?: () => void
) {
	const gazeStore = useGazeStore()
	const { regionsOfInterest, selectedRoiIndex, gazeDataRevision, currentTime } = storeToRefs(gazeStore)

	const layout = ref<VideoContentLayout | null>(null)
	const drawing = ref(false)
	const editing = ref(false)
	const startX = ref(0)
	const startY = ref(0)
	const dragStartX = ref(0)
	const dragStartY = ref(0)
	const editRoiIndex = ref<number | null>(null)
	const resizeHandle = ref<RoiResizeHandle | null>(null)
	const originalRoi = ref<OriginalRoiBounds | null>(null)
	const hoverRoiIndex = ref<number | null>(null)
	const gazeInsideRoiIndex = ref<number | null>(null)

	let resizeObserver: ResizeObserver | null = null

	function handleHitRadiusVideoPx(): number {
		const scale = layout.value?.scale ?? 1
		return MIN_TOUCH_TARGET_PX / 2 / scale
	}

	function handleVisualSizeVideoPx(): number {
		const scale = layout.value?.scale ?? 1
		return Math.max(10, 14 / scale)
	}

	function syncCanvasToVideoLayoutHook(): void {
		const canvas = canvasRef.value
		const video = videoRef.value
		const container = containerRef.value
		if (!canvas || !video || !container) return

		layout.value = syncCanvasToVideoLayout(canvas, video, container)
		renderRois()
	}

	function canvasPointFromEvent(event: MouseEvent): { x: number; y: number } | null {
		const canvas = canvasRef.value
		if (!canvas) return null
		const rect = canvas.getBoundingClientRect()
		if (rect.width <= 0 || rect.height <= 0) return null

		const x = (event.clientX - rect.left) * (canvas.width / rect.width)
		const y = (event.clientY - rect.top) * (canvas.height / rect.height)
		if (x < 0 || y < 0 || x > canvas.width || y > canvas.height) return null
		return { x, y }
	}

	function getRoiAtPoint(x: number, y: number): RoiHitResult | null {
		const hitRadius = handleHitRadiusVideoPx()

		for (let index = regionsOfInterest.value.length - 1; index >= 0; index -= 1) {
			const roi = regionsOfInterest.value[index]
			if (selectedRoiIndex.value === index) {
				if (Math.abs(x - roi.x) <= hitRadius && Math.abs(y - roi.y) <= hitRadius) {
					return { roiIndex: index, handle: 'tl' }
				}
				if (Math.abs(x - (roi.x + roi.width)) <= hitRadius && Math.abs(y - roi.y) <= hitRadius) {
					return { roiIndex: index, handle: 'tr' }
				}
				if (Math.abs(x - roi.x) <= hitRadius && Math.abs(y - (roi.y + roi.height)) <= hitRadius) {
					return { roiIndex: index, handle: 'bl' }
				}
				if (
					Math.abs(x - (roi.x + roi.width)) <= hitRadius
					&& Math.abs(y - (roi.y + roi.height)) <= hitRadius
				) {
					return { roiIndex: index, handle: 'br' }
				}
			}

			if (x >= roi.x && x <= roi.x + roi.width && y >= roi.y && y <= roi.y + roi.height) {
				return { roiIndex: index, handle: 'body' }
			}
		}
		return null
	}

	function updateHoverState(x: number, y: number): void {
		const canvas = canvasRef.value
		if (!canvas || disabled.value) return

		const hit = getRoiAtPoint(x, y)
		if (!hit) {
			hoverRoiIndex.value = null
			canvas.style.cursor = 'crosshair'
			return
		}

		hoverRoiIndex.value = hit.roiIndex
		if (hit.handle === 'tl' || hit.handle === 'br') {
			canvas.style.cursor = 'nwse-resize'
		} else if (hit.handle === 'tr' || hit.handle === 'bl') {
			canvas.style.cursor = 'nesw-resize'
		} else {
			canvas.style.cursor = 'move'
		}
	}

	function drawRoiLabel(
		context: CanvasRenderingContext2D,
		roi: RegionOfInterest,
		label: string,
		color: string,
		canvasHeight: number
	): void {
		context.font = '14px "Segoe UI", sans-serif'
		const labelWidth = context.measureText(label).width + 16
		const fitsAbove = roi.y >= LABEL_HEIGHT
		const labelY = fitsAbove ? roi.y - LABEL_HEIGHT : roi.y
		const textY = fitsAbove ? roi.y - 7 : Math.min(roi.y + 17, canvasHeight - 4)

		context.fillStyle = color
		context.fillRect(roi.x, labelY, labelWidth, LABEL_HEIGHT)
		context.fillStyle = '#FFFFFF'
		context.fillText(label, roi.x + 8, textY)
	}

	function drawHandle(
		context: CanvasRenderingContext2D,
		x: number,
		y: number,
		color: string
	): void {
		const size = handleVisualSizeVideoPx()
		context.fillStyle = '#FFFFFF'
		context.strokeStyle = color
		context.lineWidth = 2
		context.fillRect(x - size / 2, y - size / 2, size, size)
		context.strokeRect(x - size / 2, y - size / 2, size, size)
	}

	function updateGazeInsideIndex(): void {
		const sample = getGazeSampleAtTime(gazeStore.gazeCoordinates, currentTime.value)
		if (!sample) {
			gazeInsideRoiIndex.value = null
			return
		}
		gazeInsideRoiIndex.value = findRoiIndexForGaze(sample, regionsOfInterest.value)
	}

	function renderRois(previewBounds?: RoiBounds): void {
		const canvas = canvasRef.value
		if (!canvas) return

		const context = canvas.getContext('2d')
		if (!context) return

		updateGazeInsideIndex()
		context.clearRect(0, 0, canvas.width, canvas.height)
		if (disabled.value) {
			onAfterRender?.()
			return
		}

		regionsOfInterest.value.forEach((roi: RegionOfInterest, index: number) => {
			const isSelected = index === selectedRoiIndex.value
			const isHovered = index === hoverRoiIndex.value
			const gazeInside = index === gazeInsideRoiIndex.value
			const color = roi.color_tag ?? '#61AFEF'
			const label = roi.label ?? `ROI ${index + 1}`

			context.fillStyle = hexToRgba(color, isHovered || gazeInside ? 0.32 : 0.2)
			context.fillRect(roi.x, roi.y, roi.width, roi.height)

			if (gazeInside) {
				context.strokeStyle = '#E5C07B'
				context.lineWidth = 4
				context.setLineDash([6, 4])
				context.strokeRect(roi.x, roi.y, roi.width, roi.height)
				context.setLineDash([])
			}

			context.strokeStyle = isSelected ? '#98C379' : color
			context.lineWidth = isSelected ? 3 : 2
			context.strokeRect(roi.x, roi.y, roi.width, roi.height)

			drawRoiLabel(context, roi, label, color, canvas.height)

			if (isSelected) {
				drawHandle(context, roi.x, roi.y, color)
				drawHandle(context, roi.x + roi.width, roi.y, color)
				drawHandle(context, roi.x, roi.y + roi.height, color)
				drawHandle(context, roi.x + roi.width, roi.y + roi.height, color)
			}
		})

		if (previewBounds) {
			context.strokeStyle = '#22d3ee'
			context.lineWidth = 2
			context.fillStyle = 'rgba(34, 211, 238, 0.2)'
			context.fillRect(previewBounds.x, previewBounds.y, previewBounds.width, previewBounds.height)
			context.strokeRect(previewBounds.x, previewBounds.y, previewBounds.width, previewBounds.height)
		}

		onAfterRender?.()
	}

	function applyEdit(mouseX: number, mouseY: number): void {
		if (editRoiIndex.value === null || !originalRoi.value || !resizeHandle.value) return

		const canvas = canvasRef.value
		if (!canvas) return

		const roi = regionsOfInterest.value[editRoiIndex.value]
		if (!roi) return

		const deltaX = mouseX - dragStartX.value
		const deltaY = mouseY - dragStartY.value
		const maxX = canvas.width
		const maxY = canvas.height
		const source = originalRoi.value

		let nextX = source.x
		let nextY = source.y
		let nextWidth = source.width
		let nextHeight = source.height

		if (resizeHandle.value === 'body') {
			nextX = Math.max(0, Math.min(maxX - source.width, source.x + deltaX))
			nextY = Math.max(0, Math.min(maxY - source.height, source.y + deltaY))
		} else if (resizeHandle.value === 'tl') {
			nextX = Math.max(0, Math.min(source.x + source.width - MIN_ROI_DIMENSION, source.x + deltaX))
			nextY = Math.max(0, Math.min(source.y + source.height - MIN_ROI_DIMENSION, source.y + deltaY))
			nextWidth = source.width + (source.x - nextX)
			nextHeight = source.height + (source.y - nextY)
		} else if (resizeHandle.value === 'tr') {
			nextY = Math.max(0, Math.min(source.y + source.height - MIN_ROI_DIMENSION, source.y + deltaY))
			nextWidth = Math.max(MIN_ROI_DIMENSION, Math.min(maxX - source.x, source.width + deltaX))
			nextHeight = source.height + (source.y - nextY)
		} else if (resizeHandle.value === 'bl') {
			nextX = Math.max(0, Math.min(source.x + source.width - MIN_ROI_DIMENSION, source.x + deltaX))
			nextWidth = source.width + (source.x - nextX)
			nextHeight = Math.max(MIN_ROI_DIMENSION, Math.min(maxY - source.y, source.height + deltaY))
		} else if (resizeHandle.value === 'br') {
			nextWidth = Math.max(MIN_ROI_DIMENSION, Math.min(maxX - source.x, source.width + deltaX))
			nextHeight = Math.max(MIN_ROI_DIMENSION, Math.min(maxY - source.y, source.height + deltaY))
		}

		gazeStore.updateRoiBounds(editRoiIndex.value, {
			x: nextX,
			y: nextY,
			width: nextWidth,
			height: nextHeight
		})
		renderRois()
	}

	function startEditRoi(hit: RoiHitResult, mouseX: number, mouseY: number): void {
		const roi = regionsOfInterest.value[hit.roiIndex]
		if (!roi) return

		editing.value = true
		editRoiIndex.value = hit.roiIndex
		resizeHandle.value = hit.handle
		dragStartX.value = mouseX
		dragStartY.value = mouseY
		originalRoi.value = {
			x: roi.x,
			y: roi.y,
			width: roi.width,
			height: roi.height
		}
		gazeStore.selectRoi(hit.roiIndex)
	}

	function onMouseDown(event: MouseEvent): void {
		if (disabled.value) return
		const point = canvasPointFromEvent(event)
		if (!point) return

		const hit = getRoiAtPoint(point.x, point.y)
		if (hit) {
			startEditRoi(hit, point.x, point.y)
			return
		}

		drawing.value = true
		startX.value = point.x
		startY.value = point.y
	}

	function onMouseMove(event: MouseEvent): void {
		if (disabled.value) return
		const point = canvasPointFromEvent(event)
		if (!point) {
			if (!drawing.value && !editing.value) {
				hoverRoiIndex.value = null
				const canvas = canvasRef.value
				if (canvas) canvas.style.cursor = 'default'
			}
			return
		}

		if (editing.value) {
			applyEdit(point.x, point.y)
			return
		}

		if (!drawing.value) {
			updateHoverState(point.x, point.y)
			return
		}

		const previewBounds: RoiBounds = {
			x: Math.min(startX.value, point.x),
			y: Math.min(startY.value, point.y),
			width: Math.abs(point.x - startX.value),
			height: Math.abs(point.y - startY.value)
		}
		renderRois(previewBounds)
	}

	function onMouseUp(event: MouseEvent): void {
		if (editing.value) {
			editing.value = false
			editRoiIndex.value = null
			resizeHandle.value = null
			originalRoi.value = null
			renderRois()
			return
		}

		if (!drawing.value) return
		drawing.value = false

		const point = canvasPointFromEvent(event)
		if (!point) {
			renderRois()
			return
		}

		const bounds: RoiBounds = {
			x: Math.min(startX.value, point.x),
			y: Math.min(startY.value, point.y),
			width: Math.abs(point.x - startX.value),
			height: Math.abs(point.y - startY.value)
		}
		gazeStore.addRegionOfInterest(bounds)
		renderRois()
	}

	function onDocumentMouseUp(): void {
		if (!editing.value) return
		editing.value = false
		editRoiIndex.value = null
		resizeHandle.value = null
		originalRoi.value = null
		renderRois()
	}

	onMounted(() => {
		document.addEventListener('mouseup', onDocumentMouseUp)

		const container = containerRef.value
		if (container && typeof ResizeObserver !== 'undefined') {
			resizeObserver = new ResizeObserver(() => {
				syncCanvasToVideoLayoutHook()
			})
			resizeObserver.observe(container)
			const video = videoRef.value
			if (video) resizeObserver.observe(video)
		}

		const video = videoRef.value
		if (video) {
			video.addEventListener('loadedmetadata', syncCanvasToVideoLayoutHook)
		}
		window.addEventListener('resize', syncCanvasToVideoLayoutHook)
		syncCanvasToVideoLayoutHook()
	})

	onBeforeUnmount(() => {
		document.removeEventListener('mouseup', onDocumentMouseUp)
		resizeObserver?.disconnect()
		resizeObserver = null

		const video = videoRef.value
		if (video) {
			video.removeEventListener('loadedmetadata', syncCanvasToVideoLayoutHook)
		}
		window.removeEventListener('resize', syncCanvasToVideoLayoutHook)
	})

	watch(regionsOfInterest, () => {
		renderRois()
	}, { deep: true })

	watch([selectedRoiIndex, disabled, currentTime, gazeDataRevision], () => {
		renderRois()
	})

	return {
		onMouseDown,
		onMouseMove,
		onMouseUp,
		syncCanvasToVideoLayout: syncCanvasToVideoLayoutHook,
		renderRois,
		gazeInsideRoiIndex
	}
}
