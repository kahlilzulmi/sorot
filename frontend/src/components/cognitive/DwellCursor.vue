<template>
	<div
		class="dwell-cursor"
		:class="[
			`dwell-cursor--${shape}`,
			`dwell-cursor--effect-${dwellEffect}`,
			{
				'dwell-cursor--dwelling': dwelling,
				'dwell-cursor--embedded': embedded,
				'dwell-cursor--contained': contained
			}
		]"
		:style="cursorStyle"
		aria-hidden="true"
	>
		<svg
			v-if="shape === 'arrow'"
			class="dwell-cursor__glyph"
			viewBox="0 0 24 24"
			:width="glyphPx"
			:height="glyphPx"
		>
			<path :fill="cursorColor" d="M4 3.5 19.5 12 11 14.2 8.2 21.5 4 3.5Z" />
		</svg>
		<div
			v-else-if="shape === 'dot'"
			class="dwell-cursor__dot"
			:style="dotStyle"
		/>

		<svg
			v-if="dwellEffect === 'ring'"
			class="dwell-cursor__progress"
			viewBox="0 0 36 36"
			:width="effectSize"
			:height="effectSize"
		>
			<circle class="dwell-cursor__track" cx="18" cy="18" r="15" />
			<circle
				class="dwell-cursor__arc"
				cx="18"
				cy="18"
				r="15"
				:stroke="dwellEffectColor"
				:stroke-dasharray="circumference"
				:stroke-dashoffset="arcOffset"
			/>
		</svg>
		<div
			v-else-if="dwellEffect === 'pie'"
			class="dwell-cursor__pie"
			:style="pieStyle"
		/>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
	clampCursorSizePx,
	type DwellEffectStyle,
	type GazeCursorShape
} from '../../types/cognitiveGame'

const props = withDefaults(
	defineProps<{
		x: number
		y: number
		cursorColor: string
		dwellEffectColor: string
		shape: GazeCursorShape
		dwellEffect: DwellEffectStyle
		progress: number
		dwelling: boolean
		cursorSizePx?: number
		dwellEffectSizePx?: number
		contained?: boolean
		embedded?: boolean
	}>(),
	{
		cursorSizePx: 36,
		dwellEffectSizePx: 36,
		contained: false,
		embedded: false
	}
)

const cursorSize = computed(() => clampCursorSizePx(props.cursorSizePx ?? 36))
const effectSize = computed(() => clampCursorSizePx(props.dwellEffectSizePx ?? 36))
const boxSize = computed(() => Math.max(cursorSize.value, effectSize.value))

const glyphPx = computed(() => Math.round(cursorSize.value * 0.55))
const dotPx = computed(() => Math.round(cursorSize.value * 0.34))
const piePx = computed(() => Math.round(effectSize.value * 0.5))
const strokeWidth = computed(() => Math.max(2, Math.round(effectSize.value * 0.08)))

const circumference = 2 * Math.PI * 15
const arcOffset = computed(() => circumference * (1 - Math.min(1, Math.max(0, props.progress))))

const dotStyle = computed(() => ({
	background: props.cursorColor,
	width: `${dotPx.value}px`,
	height: `${dotPx.value}px`
}))

const pieStyle = computed(() => ({
	width: `${piePx.value}px`,
	height: `${piePx.value}px`,
	background: `conic-gradient(${props.dwellEffectColor} ${props.progress * 360}deg, transparent 0)`
}))

const cursorStyle = computed(() => {
	const sizeStyle = {
		width: `${boxSize.value}px`,
		height: `${boxSize.value}px`,
		'--dwell-stroke': `${strokeWidth.value}px`
	}
	if (props.embedded) {
		return {
			...sizeStyle,
			transform: 'translate(-50%, -50%)'
		}
	}
	return {
		...sizeStyle,
		transform: `translate3d(${props.x}px, ${props.y}px, 0) translate(-50%, -50%)`
	}
})
</script>

<style scoped>
.dwell-cursor {
	position: fixed;
	top: 0;
	left: 0;
	z-index: 12000;
	pointer-events: none;
	will-change: transform;
}

.dwell-cursor--contained {
	position: absolute;
	z-index: 3;
}

.dwell-cursor--embedded {
	position: absolute;
	top: 50%;
	left: 50%;
	z-index: 1;
}

.dwell-cursor__glyph,
.dwell-cursor__dot,
.dwell-cursor__pie,
.dwell-cursor__progress {
	position: absolute;
	inset: 0;
	margin: auto;
}

.dwell-cursor__glyph {
	filter: drop-shadow(0 0 2px rgba(0, 0, 0, 0.9));
}

.dwell-cursor__dot {
	border-radius: 50%;
	box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.7);
}

.dwell-cursor__pie {
	border-radius: 50%;
	box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.35);
	opacity: 0;
	transition: opacity 0.15s ease;
}

.dwell-cursor--dwelling .dwell-cursor__pie {
	opacity: 1;
}

.dwell-cursor__progress {
	transform: rotate(-90deg);
	opacity: 0;
	transition: opacity 0.15s ease;
}

.dwell-cursor--dwelling .dwell-cursor__progress {
	opacity: 1;
}

.dwell-cursor__track {
	fill: none;
	stroke: rgba(255, 255, 255, 0.18);
	stroke-width: var(--dwell-stroke, 3px);
}

.dwell-cursor__arc {
	fill: none;
	stroke-width: var(--dwell-stroke, 3px);
	stroke-linecap: round;
	transition: stroke-dashoffset 0.05s linear;
}
</style>
