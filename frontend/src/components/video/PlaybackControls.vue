<template>
	<div class="playback-controls-new">
		<div class="frame-info-row">
			<span class="frame-info">
				Frame {{ currentFrame }} / {{ totalFrames }}
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
</template>

<script setup lang="ts">
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

// Pattern: presentational playback control bar; parent owns playback logic.
defineProps<{
	currentFrame: number
	totalFrames: number
	currentTime: number
	videoDuration: number
	playing: boolean
}>()

defineEmits<{
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

function formatTime(seconds: number): string {
	if (!Number.isFinite(seconds) || seconds < 0) return '00:00'
	const s = Math.floor(seconds % 60)
	const m = Math.floor((seconds / 60) % 60)
	const h = Math.floor(seconds / 3600)
	if (h > 0) return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
	return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
</script>
