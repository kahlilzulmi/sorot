<template>
	<section class="center-panel">
		<div class="video-section">
			<div v-if="videoInfo" class="video-container">
				<div class="video-header">
					<div class="video-title">
						<strong>{{ videoInfo.filename }}</strong>
					</div>
					<div class="video-meta">
						{{ videoInfo.width }}x{{ videoInfo.height }} @ {{ videoInfo.fps.toFixed(2) }} FPS
					</div>
				</div>

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
import PlaybackControls from './PlaybackControls.vue'

interface Roi {
	label: string
	x: number
	y: number
	width: number
	height: number
	color_tag?: string
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
	roiInteractionDisabled?: boolean
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
}>()

const canvasWrapperRef = ref<HTMLElement | null>(null)
const videoPlayerRef = ref<HTMLVideoElement | null>(null)
const roiCanvasRef = ref<HTMLCanvasElement | null>(null)
const roiInteractionDisabled = computed(() => props.roiInteractionDisabled ?? false)

const {
	onMouseDown,
	onMouseMove,
	onMouseUp,
	syncCanvasToVideoLayout
} = useRoiCanvas(roiCanvasRef, videoPlayerRef, canvasWrapperRef, roiInteractionDisabled)

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

function onVideoLoaded(): void {
	syncCanvasToVideoLayout()
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
		if (!video) return
		if (isPlaying) {
			void video.play()
		} else {
			video.pause()
		}
	}
)

function onTimeUpdate(): void {
	const video = videoPlayerRef.value
	if (!video || !props.videoInfo || props.videoInfo.fps <= 0 || !props.playing) return
	const frame = Math.round(video.currentTime * props.videoInfo.fps)
	if (frame !== props.currentFrame) {
		emit('frame-change', frame)
	}
}
</script>
