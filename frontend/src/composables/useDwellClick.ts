import { onMounted, onUnmounted, ref, watch, type Ref } from 'vue'
import { GAZE_TARGET_ATTR } from '../types/cognitiveGame'
import type { GazePoint } from './useGazePoint'

export interface GazeHitTarget {
	id: string
	element: HTMLElement
}

/**
 * Dwell-to-click: accumulates progress while gaze stays on `[data-gaze-target]`.
 * Mouse click is a debug fallback that fires the same callback.
 */
export function useDwellClick(options: {
	point: Ref<GazePoint | null>
	dwellMs: Ref<number>
	paused: Ref<boolean>
	onGazeClick: (targetId: string, element: HTMLElement) => void
	root?: Ref<HTMLElement | null>
}) {
	const progress = ref(0)
	const activeTargetId = ref<string | null>(null)
	const dwelling = ref(false)

	let dwellStartedAt: number | null = null
	let lastTargetId: string | null = null
	let firedForTarget: string | null = null
	let rafId = 0

	function hitTest(x: number, y: number): GazeHitTarget | null {
		if (typeof document === 'undefined') return null
		const stack = document.elementsFromPoint(x, y)
		for (const node of stack) {
			if (!(node instanceof HTMLElement)) continue
			const host = node.closest(`[${GAZE_TARGET_ATTR}]`)
			if (!(host instanceof HTMLElement)) continue
			if (options.root?.value && !options.root.value.contains(host)) continue
			const id = host.getAttribute(GAZE_TARGET_ATTR)
			if (!id) continue
			return { id, element: host }
		}
		return null
	}

	function resetDwell(): void {
		dwellStartedAt = null
		firedForTarget = null
		progress.value = 0
		dwelling.value = false
	}

	function tick(): void {
		rafId = window.requestAnimationFrame(tick)
		if (options.paused.value) {
			resetDwell()
			activeTargetId.value = null
			return
		}

		const gaze = options.point.value
		if (!gaze) {
			resetDwell()
			activeTargetId.value = null
			return
		}

		const hit = hitTest(gaze.x, gaze.y)
		const nextId = hit?.id ?? null
		activeTargetId.value = nextId

		if (!hit) {
			resetDwell()
			lastTargetId = null
			return
		}

		if (nextId !== lastTargetId) {
			lastTargetId = nextId
			dwellStartedAt = performance.now()
			firedForTarget = null
			progress.value = 0
			dwelling.value = true
			return
		}

		if (firedForTarget === nextId || dwellStartedAt === null) {
			progress.value = firedForTarget === nextId ? 1 : progress.value
			return
		}

		const elapsed = performance.now() - dwellStartedAt
		const ratio = Math.min(1, elapsed / Math.max(1, options.dwellMs.value))
		progress.value = ratio
		dwelling.value = true

		if (ratio >= 1) {
			firedForTarget = nextId
			options.onGazeClick(hit.id, hit.element)
		}
	}

	function onMouseClick(event: MouseEvent): void {
		if (options.paused.value) return
		const hit = hitTest(event.clientX, event.clientY)
		if (!hit) return
		progress.value = 1
		activeTargetId.value = hit.id
		options.onGazeClick(hit.id, hit.element)
	}

	onMounted(() => {
		rafId = window.requestAnimationFrame(tick)
		window.addEventListener('click', onMouseClick, true)
	})

	onUnmounted(() => {
		window.cancelAnimationFrame(rafId)
		window.removeEventListener('click', onMouseClick, true)
	})

	watch(
		() => options.dwellMs.value,
		() => {
			resetDwell()
			lastTargetId = null
		}
	)

	return {
		progress,
		activeTargetId,
		dwelling,
		resetDwell
	}
}
