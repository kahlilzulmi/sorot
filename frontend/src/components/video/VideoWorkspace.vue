<template>
	<section class="center-panel">
		<div class="video-section">
			<div
				v-if="videoInfo"
				class="video-container"
				:class="{ 'dual-video-mode': showDualVideoLayout }"
			>
				<div class="video-header">
					<div class="video-title">
						<strong>{{ videoInfo.filename }}</strong>
						<span v-if="showDualVideoLayout" style="margin-left: 10px; color: #17a2b8; font-size: 12px;">
							Dual Video Mode
						</span>
					</div>
					<div class="video-meta">
						{{ videoInfo.width }}x{{ videoInfo.height }} @ {{ videoInfo.fps.toFixed(2) }} FPS
					</div>
				</div>

				<div v-if="!showDualVideoLayout" ref="canvasWrapperRef" class="canvas-wrapper">
					<video
						ref="videoPlayerRef"
						:src="videoSrc"
						crossorigin="anonymous"
						style="width: 100%;"
						@loadedmetadata="onVideoLoaded"
						@timeupdate="onTimeUpdate"
					></video>
					<canvas
						ref="roiCanvasRef"
						class="roi-canvas"
						:class="{ 'roi-disabled': roiInteractionDisabled }"
						@mousedown="onMouseDown"
						@mousemove="onMouseMove"
						@mouseup="onMouseUp"
					></canvas>
					<div v-if="showRecordingOverlay" class="recording-overlay">
						<button type="button" class="btn-start-recording" @click="$emit('start-recording')">
							START
						</button>
						<button type="button" class="btn btn-secondary btn-sm" style="margin-top: 12px;" @click="$emit('cancel-recording')">
							Cancel
						</button>
					</div>
				</div>

				<div v-else class="dual-video-wrapper">
					<div class="offset-control-panel">
						<div class="offset-label">Frame Synchronization</div>
						<div class="offset-controls">
							<button type="button" class="btn-offset" title="-10 frames" @click="$emit('adjust-offset', -10)">-10</button>
							<button type="button" class="btn-offset" title="-1 frame" @click="$emit('adjust-offset', -1)">-1</button>
							<div class="offset-display">
								<label style="font-size: 11px; color: #666;">Offset:</label>
								<input
									:value="frameOffset"
									type="number"
									class="offset-input"
									style="width: 70px;"
									@input="onOffsetInput"
								>
								<span style="font-size: 11px; color: #666;">frames</span>
							</div>
							<button type="button" class="btn-offset" title="+1 frame" @click="$emit('adjust-offset', 1)">+1</button>
							<button type="button" class="btn-offset" title="+10 frames" @click="$emit('adjust-offset', 10)">+10</button>
							<button type="button" class="btn-offset-reset" title="Reset to 0" @click="$emit('update:frame-offset', 0)">Reset</button>
						</div>
						<div class="offset-hint">
							<small style="color: #666;">Positive = gaze video ahead | Negative = stimulus video ahead</small>
						</div>
					</div>

					<div class="video-panel">
						<div class="video-panel-header">Original Stimulus</div>
						<div ref="canvasWrapperRef" class="canvas-wrapper">
							<video
								ref="videoPlayerRef"
								:src="videoSrc"
								crossorigin="anonymous"
								style="width: 100%;"
								@loadedmetadata="onVideoLoaded"
								@timeupdate="onTimeUpdate"
							></video>
							<canvas
								ref="roiCanvasRef"
								class="roi-canvas"
								:class="{ 'roi-disabled': roiInteractionDisabled }"
								@mousedown="onMouseDown"
								@mousemove="onMouseMove"
								@mouseup="onMouseUp"
							></canvas>
						</div>
					</div>

					<div class="video-panel">
						<div class="video-panel-header">Eye Gaze Recording</div>
						<div class="canvas-wrapper">
							<video
								ref="gazeVideoPlayerRef"
								:src="gazeVideoSrc ?? undefined"
								crossorigin="anonymous"
								style="width: 100%;"
								muted
								@loadedmetadata="syncGazeVideoNow"
							></video>
						</div>
					</div>
				</div>

				<div class="slider-container">
					<div class="scene-boundaries">
						<div
							v-for="(scene, idx) in scenes"
							:key="`${scene.name}-${idx}`"
							:style="sceneBoundaryStyle(scene, idx)"
							:class="[
								'scene-boundary',
								{ 'active-scene': idx === activeSceneIdx, 'selected-scene': idx === selectedSceneIdx }
							]"
							@click="$emit('select-scene', idx)"
						>
							<div class="scene-label">
								<span class="scene-name">{{ scene.custom_name || scene.name }}</span>
							</div>
						</div>
						<div class="frame-position-indicator" :style="{ left: framePosition }"></div>
					</div>

					<input
						class="frame-slider"
						type="range"
						:min="0"
						:max="Math.max(videoInfo.total_frames - 1, 0)"
						:model-value="currentFrame"
						@input="onSliderInput"
					>
				</div>

				<PlaybackControls
					:current-frame="currentFrame"
					:total-frames="videoInfo.total_frames"
					:current-time="currentTime"
					:video-duration="videoDuration"
					:playing="playing"
					@toggle-play="$emit('toggle-play')"
					@jump-start="$emit('jump-start')"
					@jump-end="$emit('jump-end')"
					@prev-scene="$emit('prev-scene')"
					@next-scene="$emit('next-scene')"
					@prev-frame="$emit('prev-frame')"
					@next-frame="$emit('next-frame')"
					@split-scene="$emit('split-scene')"
					@merge-scene="$emit('merge-scene')"
					@undo="$emit('undo')"
					@redo="$emit('redo')"
				/>
			</div>

			<div v-else class="no-video">
				<p>No video loaded. Use New or Open workspace to start.</p>
			</div>
		</div>
	</section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoiCanvas } from '../../composables/useRoiCanvas'
import { syncGazeVideoTime } from '../../composables/useDualVideo'
import PlaybackControls from './PlaybackControls.vue'
import type { VideoMode } from '../../composables/useDualVideo'

interface Roi {
	label: string
	x: number
	y: number
	width: number
	height: number
	color_tag?: string
}
interface RoiBounds {
	x: number
	y: number
	width: number
	height: number
}
interface GazePoint {
	x: number
	y: number
}

interface Scene {
	name: string
	custom_name?: string
	start_frame: number
	end_frame: number
	rois: Roi[]
}

interface VideoInfo {
	filename: string
	width: number
	height: number
	fps: number
	total_frames: number
	duration: number
}

const props = defineProps<{
	videoInfo: VideoInfo | null
	videoSrc: string
	scenes: Scene[]
	activeSceneIdx: number
	selectedSceneIdx: number
	currentFrame: number
	currentTime: number
	videoDuration: number
	playing: boolean
	rois: Roi[]
	selectedRoiIdx: number | null
	gazeSample: GazePoint | null
	gazeRevision: number
	showRecordingOverlay: boolean
	roiInteractionDisabled?: boolean
	appMode?: 'live' | 'import'
	videoMode?: VideoMode
	gazeVideoSrc?: string | null
	frameOffset?: number
}>()

const emit = defineEmits<{
	(e: 'select-scene', index: number): void
	(e: 'frame-change', frame: number): void
	(e: 'toggle-play'): void
	(e: 'jump-start'): void
	(e: 'jump-end'): void
	(e: 'prev-scene'): void
	(e: 'next-scene'): void
	(e: 'prev-frame'): void
	(e: 'next-frame'): void
	(e: 'split-scene'): void
	(e: 'merge-scene'): void
	(e: 'undo'): void
	(e: 'redo'): void
	(e: 'select-roi', index: number | null): void
	(e: 'update-roi-bounds', index: number, bounds: RoiBounds): void
	(e: 'roi-drawn', bounds: RoiBounds): void
	(e: 'commit-rois'): void
	(e: 'start-recording'): void
	(e: 'cancel-recording'): void
	(e: 'update:frame-offset', value: number): void
	(e: 'adjust-offset', delta: number): void
}>()

const canvasWrapperRef = ref<HTMLElement | null>(null)
const videoPlayerRef = ref<HTMLVideoElement | null>(null)
const gazeVideoPlayerRef = ref<HTMLVideoElement | null>(null)
const roiCanvasRef = ref<HTMLCanvasElement | null>(null)
const roiInteractionDisabled = computed(() => props.roiInteractionDisabled ?? false)

const showDualVideoLayout = computed(() => {
	return props.appMode === 'import'
		&& props.videoMode === 'dual'
		&& !!props.gazeVideoSrc
})

const {
	onMouseDown,
	onMouseMove,
	onMouseUp,
	syncCanvasToVideoLayout
} = useRoiCanvas(
	roiCanvasRef,
	videoPlayerRef,
	canvasWrapperRef,
	roiInteractionDisabled,
	{
		getRois: () => props.rois,
		getSelectedRoiIndex: () => props.selectedRoiIdx,
		selectRoi: (index) => emit('select-roi', index),
		updateRoiBounds: (index, bounds) => {
			emit('update-roi-bounds', index, bounds)
		},
		onNewRoiDrawn: (bounds) => emit('roi-drawn', bounds)
	},
	{
		getCurrentGaze: () => props.gazeSample,
		getRevision: () => props.gazeRevision
	},
	() => emit('commit-rois')
)

const framePosition = computed(() => {
	if (!props.videoInfo || props.videoInfo.total_frames <= 1) return '0%'
	return `${(props.currentFrame / (props.videoInfo.total_frames - 1)) * 100}%`
})

function sceneBoundaryStyle(scene: Scene, index: number): Record<string, string> {
	if (!props.videoInfo || props.videoInfo.total_frames <= 1) {
		return { left: '0%', width: '100%', background: sceneColor(index) }
	}

	const total = props.videoInfo.total_frames - 1
	const left = (scene.start_frame / total) * 100
	const width = ((scene.end_frame - scene.start_frame + 1) / total) * 100

	return {
		left: `${Math.max(0, left)}%`,
		width: `${Math.max(1, width)}%`,
		background: sceneColor(index)
	}
}

function sceneColor(index: number): string {
	const colors = ['#56B6C2', '#98C379', '#E5C07B', '#E06C75', '#61AFEF', '#C678DD']
	return colors[index % colors.length]
}

function onSliderInput(event: Event): void {
	const target = event.target as HTMLInputElement
	emit('frame-change', Number(target.value))
}

function onOffsetInput(event: Event): void {
	const target = event.target as HTMLInputElement
	const parsed = Number(target.value)
	emit('update:frame-offset', Number.isFinite(parsed) ? parsed : 0)
	syncGazeVideoNow()
}

function onVideoLoaded(): void {
	syncCanvasToVideoLayout()
	syncGazeVideoNow()
}

function seekVideoToFrame(frame: number): void {
	const video = videoPlayerRef.value
	if (!video || !props.videoInfo || props.videoInfo.fps <= 0) return
	const targetTime = frame / props.videoInfo.fps + 0.001
	if (Math.abs(video.currentTime - targetTime) > 0.02) {
		video.currentTime = targetTime
	}
	if (!props.playing) {
		video.pause()
	}
	syncGazeVideoNow()
}

function syncGazeVideoNow(): void {
	if (!showDualVideoLayout.value) return
	const stimulus = videoPlayerRef.value
	const gaze = gazeVideoPlayerRef.value
	if (!stimulus || !gaze || !props.videoInfo) return
	syncGazeVideoTime(stimulus, gaze, props.frameOffset ?? 0, props.videoInfo.fps)
}

watch(
	() => props.currentFrame,
	(frame) => {
		seekVideoToFrame(frame)
	}
)

watch(
	() => props.playing,
	(isPlaying) => {
		const video = videoPlayerRef.value
		const gaze = gazeVideoPlayerRef.value
		if (!video) return
		if (isPlaying) {
			void video.play()
			if (gaze && showDualVideoLayout.value) {
				syncGazeVideoNow()
				void gaze.play()
			}
		} else {
			video.pause()
			gaze?.pause()
		}
	}
)

watch(
	() => [props.frameOffset, props.gazeVideoSrc],
	() => {
		syncGazeVideoNow()
	}
)

function onTimeUpdate(): void {
	const video = videoPlayerRef.value
	if (!video || !props.videoInfo || props.videoInfo.fps <= 0) return

	if (showDualVideoLayout.value) {
		syncGazeVideoNow()
	}

	if (!props.playing) return
	const frame = Math.round(video.currentTime * props.videoInfo.fps)
	if (frame !== props.currentFrame) {
		emit('frame-change', frame)
	}
}
</script>
