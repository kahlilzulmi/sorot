<template>
	<div class="gaze-debug" aria-hidden="true">
		<div
			v-if="raw"
			class="gaze-debug__raw"
			:style="{ transform: `translate3d(${raw.x}px, ${raw.y}px, 0) translate(-50%, -50%)` }"
		/>
		<pre class="gaze-debug__hud">{{ hudText }}</pre>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { GazePoint } from '../../composables/useGazePoint'

const props = defineProps<{
	processed: GazePoint | null
	raw: GazePoint | null
	frame: { x: number; y: number; width: number; height: number } | null
}>()

const hudText = computed(() => {
	const processed = props.processed
	const raw = props.raw
	const frame = props.frame
	const lines = [
		'debug view',
		processed
			? `processed  ${Math.round(processed.x)}, ${Math.round(processed.y)}`
			: 'processed  —',
		raw && (raw.x !== processed?.x || raw.y !== processed?.y)
			? `raw        ${Math.round(raw.x)}, ${Math.round(raw.y)}`
			: raw
				? 'raw        (same as processed)'
				: 'raw        —'
	]
	if (frame) {
		lines.push(`camera     ${Math.round(frame.x)}, ${Math.round(frame.y)}  (${frame.width}×${frame.height})`)
	}
	return lines.join('\n')
})
</script>

<style scoped>
.gaze-debug {
	pointer-events: none;
}

.gaze-debug__raw {
	position: fixed;
	top: 0;
	left: 0;
	z-index: 11990;
	width: 16px;
	height: 16px;
	border: 2px solid #5ce1e6;
	border-radius: 50%;
	opacity: 0.75;
	box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.6);
}

.gaze-debug__hud {
	position: fixed;
	top: 12px;
	left: 12px;
	z-index: 12100;
	margin: 0;
	padding: 8px 10px;
	border-radius: 6px;
	background: rgba(0, 0, 0, 0.62);
	color: #b8f4f6;
	font: 12px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
	white-space: pre;
}
</style>
