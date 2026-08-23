<template>
	<div class="mm-game">
		<header class="mm-game__header">
			<button type="button" class="btn btn-secondary btn-sm" @click="$emit('back')">
				← Games hub
			</button>
			<div class="mm-game__meta">
				<span>Memory Matrix</span>
				<span class="mm-game__score">
					Round {{ roundIndex + 1 }}/{{ rounds.length }} · Skor {{ score }}
				</span>
			</div>
		</header>

		<div v-if="!finished" class="mm-game__board">
			<p class="mm-game__status">{{ statusLabel }}</p>

			<div class="mm-game__grid" role="group" aria-label="Memory matrix 3 by 3">
				<button
					v-for="tileIndex in tileIndices"
					:key="tileIndex"
					type="button"
					class="mm-game__tile"
					:class="tileClass(tileIndex)"
					:data-gaze-target="`mm-tile-${tileIndex}`"
					:disabled="phase !== 'input' || feedbackLocked"
					@click="selectTile(tileIndex)"
				/>
			</div>

			<p class="mm-game__prompt">
				{{
					phase === 'watch'
						? 'Perhatikan pola kuning'
						: phase === 'input'
							? 'Ulangi pola dengan dwell'
							: phase === 'feedback'
								? feedbackOk
									? 'Benar — lanjut'
									: 'Salah — coba lagi'
								: 'Bersiap…'
				}}
			</p>
		</div>

		<div v-else class="mm-game__summary">
			<h2>Sesi selesai</h2>
			<p>
				Skor akhir: <strong>{{ score }}</strong> / {{ rounds.length }} round benar
			</p>
			<div class="mm-game__summary-actions">
				<button type="button" class="btn btn-secondary" @click="restart">
					Main lagi
				</button>
				<button
					v-if="playlistMode"
					type="button"
					class="btn btn-primary"
					data-gaze-target="mm-next-game"
					@click="$emit('next-game')"
				>
					Game berikutnya
				</button>
				<button type="button" class="btn btn-secondary" @click="$emit('back')">
					Kembali ke hub
				</button>
			</div>
		</div>

		<p class="mm-game__hint">
			Sistem menyorot kotak kuning — ulang urutannya. Benar = hijau, salah = merah. Atur panjang
			pola & timing di pengaturan modul.
		</p>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { loadMemoryMatrixSettings } from '../../utils/memoryMatrixSettings'
import {
	MEMORY_MATRIX_GRID_SIZE,
	createMemoryMatrixSession,
	type MemoryMatrixRound
} from '../../utils/memoryMatrixTrials'

const props = defineProps<{
	playlistMode?: boolean
}>()

const emit = defineEmits<{
	(e: 'back'): void
	(e: 'next-game'): void
	(e: 'finished', payload: { score: number; totalRounds: number }): void
}>()

type Phase = 'ready' | 'watch' | 'input' | 'feedback'

const tileIndices = Array.from({ length: MEMORY_MATRIX_GRID_SIZE }, (_, i) => i)
const rounds = ref<MemoryMatrixRound[]>(createMemoryMatrixSession())
const roundIndex = ref(0)
const inputStep = ref(0)
const score = ref(0)
const finished = ref(false)
const phase = ref<Phase>('ready')
const activeCueIndex = ref<number | null>(null)
const feedbackTile = ref<number | null>(null)
const feedbackOk = ref(false)
const feedbackLocked = ref(false)

const timeouts: number[] = []

const currentRound = computed(() => rounds.value[roundIndex.value] ?? null)

const statusLabel = computed(() => {
	if (phase.value === 'watch') return 'Tonton'
	if (phase.value === 'input') return 'Giliran Anda'
	if (phase.value === 'feedback') return feedbackOk.value ? 'Benar' : 'Salah'
	return 'Siap'
})

function clearTimeouts(): void {
	while (timeouts.length > 0) {
		const id = timeouts.pop()
		if (id !== undefined) window.clearTimeout(id)
	}
}

function schedule(fn: () => void, ms: number): void {
	timeouts.push(window.setTimeout(fn, ms))
}

function tileClass(tileIndex: number): Record<string, boolean> {
	return {
		'mm-game__tile--cue': phase.value === 'watch' && activeCueIndex.value === tileIndex,
		'mm-game__tile--correct':
			feedbackTile.value === tileIndex && feedbackOk.value,
		'mm-game__tile--wrong':
			feedbackTile.value === tileIndex && !feedbackOk.value
	}
}

function restart(): void {
	clearTimeouts()
	rounds.value = createMemoryMatrixSession(loadMemoryMatrixSettings())
	roundIndex.value = 0
	inputStep.value = 0
	score.value = 0
	finished.value = false
	phase.value = 'ready'
	activeCueIndex.value = null
	feedbackTile.value = null
	feedbackOk.value = false
	feedbackLocked.value = false
	schedule(() => startWatchPhase(), 600)
}

function finishSession(): void {
	finished.value = true
	phase.value = 'ready'
	emit('finished', { score: score.value, totalRounds: rounds.value.length })
}

function startWatchPhase(): void {
	const round = currentRound.value
	if (!round || finished.value) return
	clearTimeouts()
	phase.value = 'watch'
	inputStep.value = 0
	activeCueIndex.value = null
	feedbackTile.value = null
	feedbackLocked.value = true

	const settings = loadMemoryMatrixSettings()
	let delay = 400
	round.sequence.forEach((tileIndex, step) => {
		schedule(() => {
			activeCueIndex.value = tileIndex
		}, delay)
		delay += settings.flashMs
		schedule(() => {
			activeCueIndex.value = null
		}, delay)
		delay += settings.gapMs
		if (step === round.sequence.length - 1) {
			schedule(() => {
				phase.value = 'input'
				feedbackLocked.value = false
			}, delay + 150)
		}
	})
}

function advanceAfterFeedback(ok: boolean): void {
	feedbackLocked.value = true
	schedule(() => {
		feedbackTile.value = null
		if (!ok) {
			// Retry same round after a miss.
			startWatchPhase()
			return
		}
		const next = roundIndex.value + 1
		if (next >= rounds.value.length) {
			finishSession()
			return
		}
		roundIndex.value = next
		startWatchPhase()
	}, 850)
}

function selectTile(tileIndex: number): void {
	if (finished.value || phase.value !== 'input' || feedbackLocked.value) return
	const round = currentRound.value
	if (!round) return
	const expected = round.sequence[inputStep.value]
	if (expected === undefined) return

	feedbackLocked.value = true
	feedbackTile.value = tileIndex
	const ok = tileIndex === expected
	feedbackOk.value = ok
	phase.value = 'feedback'

	if (ok) {
		inputStep.value += 1
		if (inputStep.value >= round.sequence.length) {
			score.value += 1
			advanceAfterFeedback(true)
			return
		}
		schedule(() => {
			feedbackTile.value = null
			phase.value = 'input'
			feedbackLocked.value = false
		}, 450)
		return
	}

	advanceAfterFeedback(false)
}

function handleGazeTarget(targetId: string): boolean {
	if (targetId === 'mm-next-game') {
		emit('next-game')
		return true
	}
	if (!targetId.startsWith('mm-tile-')) return false
	const tileIndex = Number(targetId.slice('mm-tile-'.length))
	if (!Number.isFinite(tileIndex)) return false
	selectTile(tileIndex)
	return true
}

onMounted(() => {
	schedule(() => startWatchPhase(), 700)
})

onUnmounted(() => {
	clearTimeouts()
})

defineExpose({
	handleGazeTarget,
	finished,
	score,
	restart
})
</script>

<style scoped>
.mm-game {
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

.mm-game__header {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	flex-shrink: 0;
	margin-bottom: clamp(0.35rem, 1vh, 0.75rem);
}

.mm-game__meta {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 2px;
	font-size: clamp(0.8rem, 1.6vh, 1rem);
	color: rgba(255, 255, 255, 0.7);
}

.mm-game__score {
	color: rgba(255, 255, 255, 0.45);
	font-size: 0.9em;
}

.mm-game__board {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: clamp(0.75rem, 2vh, 1.25rem);
	min-height: 0;
}

.mm-game__status {
	margin: 0;
	font-size: clamp(1.1rem, 2.8vh, 1.6rem);
	letter-spacing: 0.04em;
	text-transform: uppercase;
	color: rgba(255, 255, 255, 0.85);
}

.mm-game__grid {
	display: grid;
	grid-template-columns: repeat(3, minmax(0, 1fr));
	gap: clamp(0.65rem, 1.8vmin, 1.1rem);
	width: min(72vmin, 420px);
	aspect-ratio: 1;
}

.mm-game__tile {
	width: 100%;
	height: 100%;
	padding: 0;
	border: 2px solid rgba(255, 255, 255, 0.2);
	border-radius: 4px;
	background: #6b6b6b;
	cursor: pointer;
	transition: background 0.12s ease, border-color 0.12s ease;
}

.mm-game__tile:hover:not(:disabled),
.mm-game__tile:focus-visible:not(:disabled) {
	border-color: #fff;
	outline: none;
}

.mm-game__tile:disabled {
	cursor: default;
}

.mm-game__tile--cue {
	background: #facc15;
	border-color: #fde047;
}

.mm-game__tile--correct {
	background: #22c55e;
	border-color: #4ade80;
}

.mm-game__tile--wrong {
	background: #ef4444;
	border-color: #f87171;
}

.mm-game__prompt {
	margin: 0;
	font-size: clamp(0.95rem, 2.2vh, 1.25rem);
	color: rgba(255, 255, 255, 0.7);
	text-align: center;
}

.mm-game__summary {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 12px;
	text-align: center;
}

.mm-game__summary h2 {
	margin: 0;
	font-size: clamp(1.5rem, 4vh, 2.25rem);
}

.mm-game__summary p {
	margin: 0;
	color: rgba(255, 255, 255, 0.65);
}

.mm-game__summary-actions {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	justify-content: center;
	margin-top: 8px;
}

.mm-game__hint {
	flex-shrink: 0;
	margin: clamp(0.5rem, 1.5vh, 1rem) 0 0;
	font-size: clamp(0.7rem, 1.5vh, 0.9rem);
	color: rgba(255, 255, 255, 0.4);
}
</style>
