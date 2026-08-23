import { onMounted, onUnmounted, ref, watch, type Ref } from 'vue'
import type { GazeInputSourceId } from '../types/cognitiveGame'

export interface GazePoint {
	x: number
	y: number
	t: number
	source: GazeInputSourceId
}

/**
 * Pluggable gaze point stream for cognitive games.
 * Phase 1: mouse is live; other sources accept external pushes later.
 */
export function useGazePoint(source: Ref<GazeInputSourceId>) {
	const point = ref<GazePoint | null>(null)
	const active = ref(false)

	function pushPoint(x: number, y: number, from: GazeInputSourceId = source.value): void {
		point.value = { x, y, t: performance.now(), source: from }
	}

	function onMouseMove(event: MouseEvent): void {
		if (source.value !== 'mouse') return
		pushPoint(event.clientX, event.clientY, 'mouse')
	}

	function start(): void {
		if (active.value || typeof window === 'undefined') return
		active.value = true
		window.addEventListener('mousemove', onMouseMove, { passive: true })
	}

	function stop(): void {
		if (!active.value || typeof window === 'undefined') return
		active.value = false
		window.removeEventListener('mousemove', onMouseMove)
	}

	watch(source, () => {
		// Future: swap socket / tobii / webgazer adapters here.
	})

	onMounted(start)
	onUnmounted(stop)

	return {
		point,
		active,
		start,
		stop,
		pushPoint
	}
}
