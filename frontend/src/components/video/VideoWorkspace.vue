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

				<div class="canvas-wrapper">
					<video :src="videoSrc" crossorigin="anonymous" controls style="width: 100%;"></video>
					<canvas class="roi-canvas"></canvas>
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

				<div class="playback-controls-new">
					<div class="frame-info-row">
						<span class="frame-info">
							Frame {{ currentFrame }} / {{ videoInfo.total_frames }}
							({{ formatTime(currentTime) }} / {{ formatTime(videoDuration) }})
						</span>
					</div>

					<div class="controls-grid">
						<div class="scene-actions">
							<button class="btn btn-icon btn-sm" type="button" @click="$emit('split-scene')">
								<SquareSplitHorizontal :size="16" />
							</button>
							<button class="btn btn-icon btn-sm" type="button" @click="$emit('merge-scene')">
								<Merge :size="16" />
							</button>
						</div>

						<div class="nav-controls-row">
							<button class="btn btn-icon" type="button" @click="$emit('jump-start')"><SkipBack :size="18" /></button>
							<button class="btn btn-icon" type="button" @click="$emit('prev-scene')"><ChevronsLeft :size="18" /></button>
							<button class="btn btn-icon" type="button" @click="$emit('prev-frame')"><ChevronLeft :size="18" /></button>
							<button class="btn btn-icon btn-play-main" type="button" @click="$emit('toggle-play')">
								<Play v-if="!playing" :size="20" />
								<Pause v-else :size="20" />
							</button>
							<button class="btn btn-icon" type="button" @click="$emit('next-frame')"><ChevronRight :size="18" /></button>
							<button class="btn btn-icon" type="button" @click="$emit('next-scene')"><ChevronsRight :size="18" /></button>
							<button class="btn btn-icon" type="button" @click="$emit('jump-end')"><SkipForward :size="18" /></button>
						</div>

						<div class="history-actions">
							<button class="btn btn-icon btn-sm" type="button" @click="$emit('undo')"><Undo2 :size="16" /></button>
							<button class="btn btn-icon btn-sm" type="button" @click="$emit('redo')"><Redo2 :size="16" /></button>
						</div>
					</div>
				</div>
			</div>

			<div v-else class="no-video">
				<p>No video loaded. Use New or Open workspace to start.</p>
			</div>
		</div>
	</section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
	ChevronLeft,
	ChevronRight,
	ChevronsLeft,
	ChevronsRight,
	Merge,
	Pause,
	Play,
	Redo2,
	SkipBack,
	SkipForward,
	SquareSplitHorizontal,
	Undo2
} from '@lucide/vue'

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

function formatTime(seconds: number): string {
	if (!Number.isFinite(seconds) || seconds < 0) return '00:00'
	const s = Math.floor(seconds % 60)
	const m = Math.floor((seconds / 60) % 60)
	const h = Math.floor(seconds / 3600)
	if (h > 0) return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
	return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
</script>
