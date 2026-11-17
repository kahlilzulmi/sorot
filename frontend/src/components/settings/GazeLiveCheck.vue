<template>
	<section class="live-check">
		<div
			ref="stageRef"
			class="live-stage"
		>
			<p v-if="!gaze.active.value" class="live-stage__status">
				Starting overlay camera…
			</p>
			<p v-else-if="!gaze.point.value" class="live-stage__status">
				Waiting for a gaze marker. Play the circle video into OBS Virtual Camera.
			</p>
			<DwellCursor
				v-if="gaze.point.value"
				contained
				:x="gaze.point.value.x"
				:y="gaze.point.value.y"
				:cursor-color="cursor.cursorColor"
				:dwell-effect-color="cursor.dwellEffectColor"
				:shape="cursor.shape"
				:dwell-effect="cursor.dwellEffect"
				:cursor-size-px="cursor.cursorSizePx"
				:dwell-effect-size-px="cursor.dwellEffectSizePx"
				:progress="0"
				:dwelling="false"
			/>
		</div>

		<aside class="live-side">
			<h2>Live check</h2>
			<p class="live-side__help">
				Black stage uses the overlay camera. Hough values apply to the live loop as you change them.
			</p>

			<p class="live-side__coords">
				<template v-if="gaze.point.value">
					{{ Math.round(gaze.point.value.x) }}, {{ Math.round(gaze.point.value.y) }}
				</template>
				<template v-else>No point yet</template>
			</p>

			<label class="live-field">
				<span>Overlay / virtual camera</span>
				<select
					v-if="captureDevices.length > 0"
					class="live-input"
					:value="String(settings.virtual_camera_index)"
					:disabled="loadingCaptureDevices"
					@change="emit('camera-change', $event)"
				>
					<option
						v-if="!captureDevices.some((device) => device.index === settings.virtual_camera_index)"
						:value="String(settings.virtual_camera_index)"
					>
						Saved index {{ settings.virtual_camera_index }} (not in list)
					</option>
					<option
						v-for="device in captureDevices"
						:key="device.index"
						:value="String(device.index)"
					>
						{{ device.name }} — index {{ device.index }}
					</option>
				</select>
				<input
					v-else
					v-model.number="settings.virtual_camera_index"
					class="live-input"
					type="number"
					min="0"
				>
			</label>
			<button
				class="btn btn-secondary btn-sm"
				type="button"
				:disabled="loadingCaptureDevices"
				@click="emit('refresh-cameras')"
			>
				{{ loadingCaptureDevices ? 'Listing…' : 'Refresh devices' }}
			</button>

			<label class="live-field">
				<span>Hough param1</span>
				<input
					v-model.number="settings.hough_param1"
					class="live-input"
					type="number"
					@input="scheduleHoughApply"
				>
			</label>
			<label class="live-field">
				<span>Hough param2</span>
				<input
					v-model.number="settings.hough_param2"
					class="live-input"
					type="number"
					@input="scheduleHoughApply"
				>
			</label>
			<div class="live-inline">
				<label class="live-field">
					<span>Min radius</span>
					<input
						v-model.number="settings.min_radius"
						class="live-input"
						type="number"
						@input="scheduleHoughApply"
					>
				</label>
				<label class="live-field">
					<span>Max radius</span>
					<input
						v-model.number="settings.max_radius"
						class="live-input"
						type="number"
						@input="scheduleHoughApply"
					>
				</label>
			</div>
			<p class="live-side__help">Radii are in original camera pixels (not the downscaled Hough copy).</p>
		</aside>
	</section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import type { AppSettings, CaptureDeviceInfo } from '../../composables/useSettings'
import { useCognitiveSettings } from '../../composables/useCognitiveSettings'
import { useGazePoint } from '../../composables/useGazePoint'
import type { GazeInputSourceId } from '../../types/cognitiveGame'
import DwellCursor from '../cognitive/DwellCursor.vue'

const props = defineProps<{
	settings: AppSettings
	captureDevices: CaptureDeviceInfo[]
	loadingCaptureDevices: boolean
}>()

const emit = defineEmits<{
	(e: 'camera-change', event: Event): void
	(e: 'refresh-cameras'): void
	(e: 'hough-change'): void
}>()

const overlaySource = ref<GazeInputSourceId>('tobii-overlay')
const stageRef = ref<HTMLElement | null>(null)
const gaze = useGazePoint(overlaySource, { viewport: stageRef })
const { cursor } = useCognitiveSettings()

let houghTimer: ReturnType<typeof setTimeout> | null = null

function scheduleHoughApply(): void {
	if (houghTimer !== null) clearTimeout(houghTimer)
	houghTimer = setTimeout(() => {
		houghTimer = null
		emit('hough-change')
	}, 250)
}

onBeforeUnmount(() => {
	if (houghTimer !== null) clearTimeout(houghTimer)
})
</script>

<style scoped>
.live-check {
	display: flex;
	min-height: 70vh;
	margin-bottom: 20px;
	border: 1px solid var(--color-border);
	border-radius: 10px;
	overflow: hidden;
	background: #000;
}

.live-stage {
	position: relative;
	flex: 1;
	min-height: 70vh;
	background: #000;
	overflow: hidden;
	cursor: none;
}

.live-stage__status {
	position: absolute;
	left: 50%;
	top: 50%;
	transform: translate(-50%, -50%);
	margin: 0;
	max-width: 28rem;
	text-align: center;
	color: rgba(255, 255, 255, 0.45);
	font-size: 14px;
	pointer-events: none;
}

.live-side {
	width: 320px;
	flex-shrink: 0;
	padding: 16px;
	overflow-y: auto;
	background: var(--color-panel);
	border-left: 1px solid var(--color-border);
	color: var(--color-text);
	cursor: default;
}

.live-side h2 {
	margin: 0 0 8px;
	font-size: 16px;
}

.live-side__help {
	margin: 0 0 14px;
	font-size: 12px;
	color: var(--color-text-dim);
}

.live-side__coords {
	margin: 0 0 16px;
	font-variant-numeric: tabular-nums;
	font-size: 15px;
	color: var(--color-accent);
}

.live-field {
	display: flex;
	flex-direction: column;
	gap: 6px;
	margin-bottom: 12px;
}

.live-field span {
	font-size: 12px;
	color: var(--color-text-dim);
}

.live-input {
	width: 100%;
	box-sizing: border-box;
	padding: 10px 12px;
	border: 1px solid var(--color-border);
	border-radius: 6px;
	background: var(--color-background);
	color: var(--color-text);
	font-size: 14px;
}

.live-inline {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 12px;
}

.live-side .btn {
	margin-bottom: 14px;
}

@media (max-width: 900px) {
	.live-check {
		flex-direction: column;
		min-height: 0;
	}

	.live-stage {
		min-height: 50vh;
	}

	.live-side {
		width: 100%;
	}
}
</style>
