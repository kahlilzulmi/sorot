<template>
	<div class="vs-game">
		<header class="vs-game__header">
			<button type="button" class="btn btn-secondary btn-sm" @click="$emit('back')">
				← Games hub
			</button>
			<div class="vs-game__meta">
				<span>Visual Search</span>
				<span class="vs-game__score">
					Level {{ levelIndex + 1 }}/{{ levels.length }} · Ditemukan {{ foundCount }} /
					{{ currentLevel?.targetIds.length ?? 0 }}
				</span>
			</div>
		</header>

		<div v-if="!finished" class="vs-game__board">
			<p class="vs-game__timer" :class="{ 'vs-game__timer--low': remainingSeconds <= 30 }">
				{{ timerLabel }}
			</p>

			<div
				v-if="currentLevel"
				class="vs-game__grid"
				:style="gridStyle"
				role="group"
				:aria-label="currentLevel.def.prompt"
			>
				<button
					v-for="cell in currentLevel.cells"
					:key="cell.id"
					type="button"
					class="vs-game__cell"
					:class="{ 'vs-game__cell--found': foundIds.has(cell.id) }"
					:data-gaze-target="`vs-cell-${cell.id}`"
					:disabled="finished || foundIds.has(cell.id)"
					@click="selectCell(cell.id)"
				>
					{{ cell.char }}
				</button>
			</div>

			<p v-if="currentLevel" class="vs-game__prompt">{{ currentLevel.def.prompt }}</p>
		</div>

		<div v-else class="vs-game__summary">
			<h2>Sesi selesai</h2>
			<p>
				Skor: <strong>{{ score }}</strong> target ditemukan ·
				{{ levelsCompleted }} / {{ levels.length }} level selesai
			</p>
			<div class="vs-game__summary-actions">
				<button type="button" class="btn btn-secondary" @click="restart">
					Main lagi
				</button>
				<button
					v-if="playlistMode"
					type="button"
					class="btn btn-primary"
					data-gaze-target="vs-next-game"
					@click="$emit('next-game')"
				>
					Game berikutnya
				</button>
				<button type="button" class="btn btn-secondary" @click="$emit('back')">
					Kembali ke hub
				</button>
			</div>
		</div>

		<p class="vs-game__hint">
			Temukan huruf berbeda di kerumunan — dwell (default 3s) pada huruf target sampai berwarna
			hijau. Atur kepadatan grid & jumlah target di pengaturan modul.
		</p>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { loadVisualSearchSettings } from '../../utils/visualSearchSettings'
import {
	createVisualSearchSession,
	formatVisualSearchTimer,
	type VisualSearchLevel
} from '../../utils/visualSearchTrials'

const props = defineProps<{
	playlistMode?: boolean
}>()

const emit = defineEmits<{
	(e: 'back'): void
	(e: 'next-game'): void
	(e: 'finished', payload: { score: number; levelsCompleted: number; totalLevels: number }): void
}>()

const levels = ref<VisualSearchLevel[]>(createVisualSearchSession())
const levelIndex = ref(0)
const foundIds = ref<Set<string>>(new Set())
const score = ref(0)
const levelsCompleted = ref(0)
const finished = ref(false)
const remainingSeconds = ref(loadVisualSearchSettings().timerSeconds)

let timerId: number | null = null

const currentLevel = computed(() => levels.value[levelIndex.value] ?? null)
const foundCount = computed(() => foundIds.value.size)
const timerLabel = computed(() => formatVisualSearchTimer(remainingSeconds.value))
const gridStyle = computed(() => {
	const level = currentLevel.value
	if (!level) return {}
	return {
		gridTemplateColumns: `repeat(${level.columns}, minmax(0, 1fr))`
	}
})

watch(finished, (isFinished) => {
	if (isFinished) {
		stopTimer()
		emit('finished', {
			score: score.value,
			levelsCompleted: levelsCompleted.value,
			totalLevels: levels.value.length
		})
	}
})

function startTimer(): void {
	stopTimer()
	timerId = window.setInterval(() => {
		if (finished.value) return
		remainingSeconds.value -= 1
		if (remainingSeconds.value <= 0) {
			remainingSeconds.value = 0
			finished.value = true
		}
	}, 1000)
}

function stopTimer(): void {
	if (timerId !== null) {
		window.clearInterval(timerId)
		timerId = null
	}
}

function restart(): void {
	const settings = loadVisualSearchSettings()
	levels.value = createVisualSearchSession(settings)
	levelIndex.value = 0
	foundIds.value = new Set()
	score.value = 0
	levelsCompleted.value = 0
	finished.value = false
	remainingSeconds.value = settings.timerSeconds
	startTimer()
}

function selectCell(cellId: string): void {
	if (finished.value) return
	const level = currentLevel.value
	if (!level) return
	const cell = level.cells.find((entry) => entry.id === cellId)
	if (!cell || !cell.isTarget) return
	if (foundIds.value.has(cellId)) return

	const next = new Set(foundIds.value)
	next.add(cellId)
	foundIds.value = next
	score.value += 1

	if (next.size >= level.targetIds.length) {
		levelsCompleted.value += 1
		const nextLevel = levelIndex.value + 1
		if (nextLevel >= levels.value.length) {
			finished.value = true
			return
		}
		levelIndex.value = nextLevel
		foundIds.value = new Set()
	}
}

function handleGazeTarget(targetId: string): boolean {
	if (targetId === 'vs-next-game') {
		emit('next-game')
		return true
	}
	if (!targetId.startsWith('vs-cell-')) return false
	const cellId = targetId.slice('vs-cell-'.length)
	selectCell(cellId)
	return true
}

onMounted(() => {
	startTimer()
})

onUnmounted(() => {
	stopTimer()
})

defineExpose({
	handleGazeTarget,
	finished,
	score,
	restart
})
</script>

<style scoped>
.vs-game {
	flex: 1;
	display: flex;
	flex-direction: column;
	width: 100%;
	height: 100%;
	min-height: 0;
	padding: clamp(0.5rem, 1.5vh, 1rem) clamp(1rem, 3vw, 2.5rem)
		clamp(0.5rem, 1.5vh, 1rem);
	box-sizing: border-box;
	color: #fff;
	background: #000;
}

.vs-game__header {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	flex-shrink: 0;
	margin-bottom: clamp(0.35rem, 1vh, 0.75rem);
}

.vs-game__meta {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 2px;
	font-size: clamp(0.8rem, 1.6vh, 1rem);
	color: rgba(255, 255, 255, 0.7);
}

.vs-game__score {
	color: rgba(255, 255, 255, 0.45);
	font-size: 0.9em;
}

.vs-game__board {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: clamp(0.5rem, 1.5vh, 1rem);
	min-height: 0;
}

.vs-game__timer {
	margin: 0;
	font-variant-numeric: tabular-nums;
	font-size: clamp(1.5rem, 4vh, 2.5rem);
	letter-spacing: 0.06em;
	color: #fff;
}

.vs-game__timer--low {
	color: #f87171;
}

.vs-game__grid {
	display: grid;
	width: min(100%, 1100px);
	max-height: min(72vh, 820px);
	overflow: auto;
	padding: clamp(0.75rem, 2vh, 1.25rem);
	border: 1px solid rgba(255, 255, 255, 0.85);
	background: #000;
	gap: 0;
}

.vs-game__cell {
	aspect-ratio: 1;
	min-width: 0;
	min-height: 0;
	padding: 0;
	border: none;
	background: transparent;
	color: #fff;
	font-family: 'Consolas', 'Courier New', monospace;
	font-size: clamp(0.55rem, 1.6vmin, 1.05rem);
	font-weight: 600;
	line-height: 1;
	cursor: pointer;
}

.vs-game__cell:hover:not(:disabled),
.vs-game__cell:focus-visible:not(:disabled) {
	color: #e5e5e5;
	outline: none;
}

.vs-game__cell:disabled {
	cursor: default;
}

/* Found = letter color only (no bounding box), brighter than the reference glow. */
.vs-game__cell--found {
	color: #4ade80;
}

.vs-game__prompt {
	margin: 0;
	font-size: clamp(0.95rem, 2.2vh, 1.25rem);
	color: rgba(255, 255, 255, 0.75);
	text-align: center;
}

.vs-game__summary {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 12px;
	text-align: center;
}

.vs-game__summary h2 {
	margin: 0;
	font-size: clamp(1.5rem, 4vh, 2.25rem);
}

.vs-game__summary p {
	margin: 0;
	color: rgba(255, 255, 255, 0.65);
}

.vs-game__summary-actions {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	justify-content: center;
	margin-top: 8px;
}

.vs-game__hint {
	flex-shrink: 0;
	margin: clamp(0.5rem, 1.5vh, 1rem) 0 0;
	font-size: clamp(0.7rem, 1.5vh, 0.9rem);
	color: rgba(255, 255, 255, 0.4);
}
</style>
