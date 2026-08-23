<template>
	<div
		class="dwell-cursor"
		:class="[
			`dwell-cursor--${shape}`,
			`dwell-cursor--effect-${dwellEffect}`,
			{
				'dwell-cursor--dwelling': dwelling,
				'dwell-cursor--embedded': embedded
			}
		]"
		:style="cursorStyle"
		aria-hidden="true"
	>
		<svg v-if="shape === 'arrow'" class="dwell-cursor__glyph" viewBox="0 0 24 24" width="22" height="22">
			<path :fill="cursorColor" d="M4 3.5 19.5 12 11 14.2 8.2 21.5 4 3.5Z" />
		</svg>
		<div v-else-if="shape === 'dot'" class="dwell-cursor__dot" :style="{ background: cursorColor }" />
		<!-- transparent shape: no glyph -->

		<svg
			v-if="dwellEffect === 'ring'"
			class="dwell-cursor__progress"
			viewBox="0 0 36 36"
			width="36"
			height="36"
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
			:style="{
				background: `conic-gradient(${dwellEffectColor} ${progress * 360}deg, transparent 0)`
			}"
		/>
		<!-- transparent effect: no dwell progress UI -->
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DwellEffectStyle, GazeCursorShape } from '../../types/cognitiveGame'

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
		/** When true, centers inside a relative parent instead of fixed viewport coords. */
		embedded?: boolean
	}>(),
	{
		embedded: false
	}
)

const circumference = 2 * Math.PI * 15

const arcOffset = computed(() => circumference * (1 - Math.min(1, Math.max(0, props.progress))))

const cursorStyle = computed(() => {
	if (props.embedded) {
		return {
			transform: 'translate(-50%, -50%)'
		}
	}
	return {
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
	width: 36px;
	height: 36px;
	pointer-events: none;
	will-change: transform;
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
	width: 18px;
	height: 18px;
	filter: drop-shadow(0 0 2px rgba(0, 0, 0, 0.9));
}

.dwell-cursor__dot {
	width: 12px;
	height: 12px;
	border-radius: 50%;
	box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.7);
}

.dwell-cursor__pie {
	width: 18px;
	height: 18px;
	border-radius: 50%;
	box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.35);
	opacity: 0;
	transition: opacity 0.15s ease;
}

.dwell-cursor--dwelling .dwell-cursor__pie {
	opacity: 1;
}

.dwell-cursor__progress {
	width: 36px;
	height: 36px;
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
	stroke-width: 3;
}

.dwell-cursor__arc {
	fill: none;
	stroke-width: 3;
	stroke-linecap: round;
	transition: stroke-dashoffset 0.05s linear;
}
</style>
