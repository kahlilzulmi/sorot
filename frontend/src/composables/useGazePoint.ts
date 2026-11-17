import { onBeforeUnmount, ref, watch, type Ref } from 'vue'
import type { GazeInputSourceId } from '../types/cognitiveGame'
import { apiPost } from './useApiClient'
import { useSocket, type GazeDetectedPayload } from './useSocket'
import { useWebGazer } from './useWebGazer'

export interface GazePoint {
	x: number
	y: number
	t: number
	source: GazeInputSourceId
}

/** One-packet delay interpolation (24–70ms). Avoids chasing a Kalman prediction then snapping back. */
const OVERLAY_SEGMENT_MIN_MS = 24
const OVERLAY_SEGMENT_MAX_MS = 70
const OVERLAY_SNAPBACK_MIN_PX = 25
const OVERLAY_SNAPBACK_MAX_PX = 140
const OVERLAY_SNAPBACK_SPEED_PX = 8

/**
 * Pluggable gaze point stream for cognitive games.
 * Mouse, WebGazer, and overlay/virtual-camera (socket) are live.
 */
export function useGazePoint(
	source: Ref<GazeInputSourceId>,
	options?: { viewport?: Ref<HTMLElement | null> }
) {
	const point = ref<GazePoint | null>(null)
	const active = ref(false)
	const webGazer = useWebGazer()
	const socket = useSocket()

	let mouseListening = false
	let webGazerUnsubscribe: (() => void) | null = null
	let webGazerStarted = false
	let overlayListening = false
	let overlayStreamStarted = false
	let sourceGeneration = 0

	let overlayRafId = 0
	let overlayFromX = 0
	let overlayFromY = 0
	let overlayToX = 0
	let overlayToY = 0
	let overlayDisplayX = 0
	let overlayDisplayY = 0
	let overlayHasTarget = false
	let overlayDisplaySeeded = false
	let overlaySegmentStart = 0
	let overlaySegmentMs = 40
	let overlayLastPacketAt = 0

	const rawPoint = ref<GazePoint | null>(null)
	const frameSample = ref<{ x: number; y: number; width: number; height: number } | null>(null)

	function pushPoint(x: number, y: number, from: GazeInputSourceId = source.value): void {
		point.value = { x, y, t: performance.now(), source: from }
		if (from === 'mouse' || from === 'webgazer') {
			rawPoint.value = { x, y, t: performance.now(), source: from }
			frameSample.value = null
		}
	}

	function mapOverlayToViewport(payload: GazeDetectedPayload): { x: number; y: number } | null {
		if (!Number.isFinite(payload.x) || !Number.isFinite(payload.y)) return null
		const frameWidth = payload.frame_width
		const frameHeight = payload.frame_height
		if (
			typeof frameWidth === 'number' &&
			typeof frameHeight === 'number' &&
			frameWidth > 0 &&
			frameHeight > 0
		) {
			const host = options?.viewport?.value
			const viewWidth = host && host.clientWidth > 0 ? host.clientWidth : window.innerWidth
			const viewHeight = host && host.clientHeight > 0 ? host.clientHeight : window.innerHeight
			return {
				x: (payload.x / frameWidth) * viewWidth,
				y: (payload.y / frameHeight) * viewHeight
			}
		}
		return { x: payload.x, y: payload.y }
	}

	function stopOverlayLerp(): void {
		if (overlayRafId !== 0 && typeof window !== 'undefined') {
			window.cancelAnimationFrame(overlayRafId)
		}
		overlayRafId = 0
		overlayHasTarget = false
		overlayDisplaySeeded = false
		overlayLastPacketAt = 0
	}

	function overlayLerpTick(): void {
		if (typeof window === 'undefined') return
		overlayRafId = window.requestAnimationFrame(overlayLerpTick)
		if (source.value !== 'tobii-overlay' && source.value !== 'socket') return
		if (!overlayHasTarget) return

		if (!overlayDisplaySeeded) {
			overlayDisplayX = overlayToX
			overlayDisplayY = overlayToY
			overlayFromX = overlayToX
			overlayFromY = overlayToY
			overlayDisplaySeeded = true
			pushPoint(overlayDisplayX, overlayDisplayY, 'tobii-overlay')
			return
		}

		const elapsed = performance.now() - overlaySegmentStart
		const u = Math.min(1, elapsed / Math.max(1, overlaySegmentMs))
		overlayDisplayX = overlayFromX + (overlayToX - overlayFromX) * u
		overlayDisplayY = overlayFromY + (overlayToY - overlayFromY) * u
		pushPoint(overlayDisplayX, overlayDisplayY, 'tobii-overlay')
	}

	function startOverlayLerp(): void {
		if (typeof window === 'undefined') return
		stopOverlayLerp()
		overlayRafId = window.requestAnimationFrame(overlayLerpTick)
	}

	function onMouseMove(event: MouseEvent): void {
		if (source.value !== 'mouse') return
		pushPoint(event.clientX, event.clientY, 'mouse')
	}

	function onOverlayGaze(payload: GazeDetectedPayload): void {
		if (source.value !== 'tobii-overlay' && source.value !== 'socket') return
		const mapped = mapOverlayToViewport(payload)
		if (!mapped) return

		const now = performance.now()
		rawPoint.value = { x: mapped.x, y: mapped.y, t: now, source: 'tobii-overlay' }
		if (
			typeof payload.frame_width === 'number' &&
			typeof payload.frame_height === 'number' &&
			payload.frame_width > 0 &&
			payload.frame_height > 0
		) {
			frameSample.value = {
				x: payload.x,
				y: payload.y,
				width: payload.frame_width,
				height: payload.frame_height
			}
		}
		if (overlayDisplaySeeded) {
			const incomingX = mapped.x - overlayDisplayX
			const incomingY = mapped.y - overlayDisplayY
			const incomingDist = Math.hypot(incomingX, incomingY)
			const velocityX = overlayToX - overlayFromX
			const velocityY = overlayToY - overlayFromY
			const speed = Math.hypot(velocityX, velocityY)
			const goingBackward = incomingX * velocityX + incomingY * velocityY < 0
			if (
				goingBackward &&
				speed > OVERLAY_SNAPBACK_SPEED_PX &&
				incomingDist > OVERLAY_SNAPBACK_MIN_PX &&
				incomingDist < OVERLAY_SNAPBACK_MAX_PX
			) {
				return
			}
		}

		overlayFromX = overlayDisplaySeeded ? overlayDisplayX : mapped.x
		overlayFromY = overlayDisplaySeeded ? overlayDisplayY : mapped.y
		overlayToX = mapped.x
		overlayToY = mapped.y
		const packetGap = overlayLastPacketAt > 0 ? now - overlayLastPacketAt : OVERLAY_SEGMENT_MIN_MS
		overlaySegmentMs = Math.min(
			OVERLAY_SEGMENT_MAX_MS,
			Math.max(OVERLAY_SEGMENT_MIN_MS, packetGap)
		)
		overlaySegmentStart = now
		overlayLastPacketAt = now
		overlayHasTarget = true
	}

	function stopMouse(): void {
		if (!mouseListening || typeof window === 'undefined') return
		window.removeEventListener('mousemove', onMouseMove)
		mouseListening = false
	}

	function stopWebGazer(): void {
		webGazerUnsubscribe?.()
		webGazerUnsubscribe = null
		if (webGazerStarted) {
			webGazer.stop()
			webGazerStarted = false
		}
	}

	async function stopOverlay(): Promise<void> {
		stopOverlayLerp()
		if (overlayListening) {
			socket.offGazeDetected(onOverlayGaze)
			overlayListening = false
		}
		if (!overlayStreamStarted) return
		overlayStreamStarted = false
		try {
			await apiPost('/api/gaze/live/stop')
		} catch {
			// Stream may already be stopped.
		}
	}

	async function startOverlay(): Promise<boolean> {
		if (typeof window === 'undefined') return false
		socket.connect()
		if (!overlayListening) {
			socket.onGazeDetected(onOverlayGaze)
			overlayListening = true
		}
		try {
			const response = await apiPost<{ success?: boolean }>('/api/gaze/live/start')
			if (!response.success) return false
			overlayStreamStarted = true
			startOverlayLerp()
			return true
		} catch {
			socket.offGazeDetected(onOverlayGaze)
			overlayListening = false
			return false
		}
	}

	async function applySource(next: GazeInputSourceId): Promise<void> {
		const generation = ++sourceGeneration
		stopMouse()
		stopWebGazer()
		await stopOverlay()
		if (generation !== sourceGeneration) return

		active.value = false
		point.value = null
		rawPoint.value = null
		frameSample.value = null

		if (next === 'mouse') {
			if (typeof window === 'undefined') return
			window.addEventListener('mousemove', onMouseMove, { passive: true })
			mouseListening = true
			active.value = true
			return
		}

		if (next === 'webgazer') {
			webGazerUnsubscribe = webGazer.onGaze((x, y) => {
				pushPoint(x, y, 'webgazer')
			})
			const ok = await webGazer.start()
			if (generation !== sourceGeneration) return
			webGazerStarted = ok
			active.value = ok
			return
		}

		if (next === 'tobii-overlay' || next === 'socket') {
			const ok = await startOverlay()
			if (generation !== sourceGeneration) return
			active.value = ok
		}
	}

	watch(source, (next) => {
		void applySource(next)
	}, { immediate: true })

	onBeforeUnmount(() => {
		sourceGeneration += 1
		stopMouse()
		stopWebGazer()
		void stopOverlay()
	})

	return {
		point,
		rawPoint,
		frameSample,
		active,
		pushPoint
	}
}
