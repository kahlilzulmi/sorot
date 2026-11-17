<template>
	<div class="face-fam">
		<header class="face-fam__header" data-session-chrome>
			<button type="button" class="btn btn-secondary btn-sm" @click="$emit('back')">
				← Games hub
			</button>
			<div class="face-fam__meta">
				<span>Face Familiarity</span>
				<span class="face-fam__score">Skor {{ score }} / {{ trials.length }}</span>
			</div>
		</header>

		<div v-if="!finished" class="face-fam__board">
			<p class="face-fam__prompt">
				Pilih wajah yang <strong>asli</strong> (bukan AI) — soal {{ currentIndex + 1 }} /
				{{ trials.length }}
			</p>
			<p v-if="currentTrial" class="face-fam__label">{{ currentTrial.label }}</p>

			<div class="face-fam__pair" role="group" aria-label="Pilihan wajah">
				<button
					type="button"
					class="face-fam__card"
					:class="cardClass('left')"
					data-gaze-target="face-fam-left"
					:disabled="locked"
					@click="answer('left')"
				>
					<img
						v-if="currentTrial"
						:src="currentTrial.leftSrc"
						alt="Wajah kiri"
						class="face-fam__img"
						draggable="false"
					>
					<span
						v-if="feedbackMark('left')"
						class="face-fam__overlay"
						:class="`face-fam__overlay--${feedbackMark('left')}`"
						aria-hidden="true"
					>
						<span class="face-fam__mark">{{ feedbackMark('left') === 'correct' ? '✓' : '✕' }}</span>
					</span>
				</button>
				<button
					type="button"
					class="face-fam__card"
					:class="cardClass('right')"
					data-gaze-target="face-fam-right"
					:disabled="locked"
					@click="answer('right')"
				>
					<img
						v-if="currentTrial"
						:src="currentTrial.rightSrc"
						alt="Wajah kanan"
						class="face-fam__img"
						draggable="false"
					>
					<span
						v-if="feedbackMark('right')"
						class="face-fam__overlay"
						:class="`face-fam__overlay--${feedbackMark('right')}`"
						aria-hidden="true"
					>
						<span class="face-fam__mark">{{ feedbackMark('right') === 'correct' ? '✓' : '✕' }}</span>
					</span>
				</button>
			</div>
		</div>

		<div v-else class="face-fam__summary">
			<h2>Sesi selesai</h2>
			<p>Skor akhir: <strong>{{ score }}</strong> dari {{ trials.length }}</p>
			<div class="face-fam__summary-actions">
				<button type="button" class="btn btn-secondary" @click="restart">
					Main lagi
				</button>
				<button
					v-if="playlistMode"
					type="button"
					class="btn btn-primary"
					data-gaze-target="face-fam-next-game"
					@click="$emit('next-game')"
				>
					Game berikutnya
				</button>
				<button type="button" class="btn btn-secondary" data-session-chrome @click="$emit('back')">
					Kembali ke hub
				</button>
			</div>
		</div>

		<p class="face-fam__hint" data-session-chrome>
			Memilih gambar yang asli vs AI-generated — dwell salah satu wajah. Upload foto di
			pengaturan modul (ikon gear di hub).
		</p>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
	createFaceFamiliaritySession,
	type FaceFamiliaritySide,
	type FaceFamiliarityTrial
} from '../../utils/faceFamiliarityTrials'

const props = defineProps<{
	playlistMode?: boolean
}>()

const emit = defineEmits<{
	(e: 'back'): void
	(e: 'next-game'): void
	(e: 'finished', payload: { score: number; total: number }): void
}>()

type Feedback = 'correct' | 'wrong' | null

const trials = ref<FaceFamiliarityTrial[]>(createFaceFamiliaritySession())
const currentIndex = ref(0)
const score = ref(0)
const locked = ref(false)
const feedback = ref<Feedback[]>(trials.value.map(() => null))
const chosenSides = ref<(FaceFamiliaritySide | null)[]>(trials.value.map(() => null))
const finished = computed(() => currentIndex.value >= trials.value.length)
const currentTrial = computed(() => trials.value[currentIndex.value] ?? null)

watch(finished, (isFinished) => {
	if (isFinished) {
		emit('finished', { score: score.value, total: trials.value.length })
	}
})

function feedbackMark(side: FaceFamiliaritySide): Feedback {
	if (!locked.value) return null
	const trial = currentTrial.value
	const chosen = chosenSides.value[currentIndex.value]
	if (!trial || !chosen) return null
	if (side === trial.correctSide) return 'correct'
	if (side === chosen) return 'wrong'
	return null
}

function cardClass(side: FaceFamiliaritySide): Record<string, boolean> {
	const mark = feedbackMark(side)
	if (mark === 'correct') return { 'face-fam__card--correct': true }
	if (mark === 'wrong') return { 'face-fam__card--wrong': true }
	return {}
}

function restart(): void {
	trials.value = createFaceFamiliaritySession()
	currentIndex.value = 0
	score.value = 0
	locked.value = false
	feedback.value = trials.value.map(() => null)
	chosenSides.value = trials.value.map(() => null)
}

function answer(side: FaceFamiliaritySide): void {
	if (locked.value || finished.value) return
	const trial = currentTrial.value
	if (!trial) return

	locked.value = true
	chosenSides.value[currentIndex.value] = side
	const correct = side === trial.correctSide
	feedback.value[currentIndex.value] = correct ? 'correct' : 'wrong'
	if (correct) score.value += 1

	window.setTimeout(() => {
		currentIndex.value += 1
		locked.value = false
	}, 750)
}

function handleGazeTarget(targetId: string): boolean {
	if (targetId === 'face-fam-left') {
		answer('left')
		return true
	}
	if (targetId === 'face-fam-right') {
		answer('right')
		return true
	}
	return false
}

defineExpose({
	handleGazeTarget,
	finished,
	score,
	restart
})
</script>

<style scoped>
.face-fam {
	flex: 1;
	display: flex;
	flex-direction: column;
	width: 100%;
	height: 100%;
	min-height: 0;
	padding: clamp(0.5rem, 1.5vh, 1rem) clamp(1.25rem, 4vw, 3rem)
		clamp(0.75rem, 2vh, 1.25rem);
	box-sizing: border-box;
	color: #fff;
	background: #000;
}

.face-fam__header {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	flex-shrink: 0;
	margin-bottom: clamp(0.5rem, 1.5vh, 1rem);
}

.face-fam__meta {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 2px;
	font-size: clamp(0.8rem, 1.6vh, 1rem);
	color: rgba(255, 255, 255, 0.7);
}

.face-fam__score {
	color: rgba(255, 255, 255, 0.45);
	font-size: 0.9em;
}

.face-fam__board {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: clamp(0.75rem, 2vh, 1.25rem);
	min-height: 0;
}

.face-fam__prompt {
	margin: 0;
	font-size: clamp(1rem, 2.4vh, 1.35rem);
	color: rgba(255, 255, 255, 0.75);
	text-align: center;
}

.face-fam__label {
	margin: 0;
	font-size: clamp(0.85rem, 2vh, 1.1rem);
	color: rgba(255, 255, 255, 0.45);
}

.face-fam__pair {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: clamp(1rem, 3vw, 2.5rem);
	width: min(100%, 920px);
}

.face-fam__card {
	position: relative;
	aspect-ratio: 1;
	padding: 0;
	border: 3px solid rgba(255, 255, 255, 0.35);
	background: #0a0a0a;
	cursor: pointer;
	overflow: hidden;
	transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

.face-fam__card:hover:not(:disabled),
.face-fam__card:focus-visible:not(:disabled) {
	border-color: #fff;
	background: rgba(255, 255, 255, 0.04);
}

.face-fam__card:disabled {
	cursor: default;
}

.face-fam__card--correct {
	border-color: #4ade80;
	box-shadow: 0 0 0 2px rgba(74, 222, 128, 0.35);
}

.face-fam__card--wrong {
	border-color: #f87171;
	box-shadow: 0 0 0 2px rgba(248, 113, 113, 0.35);
}

.face-fam__img {
	display: block;
	width: 100%;
	height: 100%;
	object-fit: cover;
	pointer-events: none;
	user-select: none;
}

.face-fam__overlay {
	position: absolute;
	inset: 0;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(0, 0, 0, 0.42);
	pointer-events: none;
}

.face-fam__overlay--correct {
	background: rgba(0, 0, 0, 0.38);
}

.face-fam__overlay--wrong {
	background: rgba(0, 0, 0, 0.48);
}

.face-fam__mark {
	display: flex;
	align-items: center;
	justify-content: center;
	width: clamp(3.25rem, 12vmin, 5.5rem);
	height: clamp(3.25rem, 12vmin, 5.5rem);
	border-radius: 50%;
	font-size: clamp(2rem, 8vmin, 3.5rem);
	font-weight: 700;
	line-height: 1;
	color: #fff;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.45);
}

.face-fam__overlay--correct .face-fam__mark {
	background: rgba(34, 197, 94, 0.92);
}

.face-fam__overlay--wrong .face-fam__mark {
	background: rgba(239, 68, 68, 0.92);
}

.face-fam__summary {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 12px;
	text-align: center;
}

.face-fam__summary h2 {
	margin: 0;
	font-size: clamp(1.5rem, 4vh, 2.25rem);
}

.face-fam__summary p {
	margin: 0;
	color: rgba(255, 255, 255, 0.65);
}

.face-fam__summary-actions {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	justify-content: center;
	margin-top: 8px;
}

.face-fam__hint {
	flex-shrink: 0;
	margin: clamp(0.5rem, 1.5vh, 1rem) 0 0;
	font-size: clamp(0.7rem, 1.5vh, 0.9rem);
	color: rgba(255, 255, 255, 0.4);
}

@media (max-width: 720px) {
	.face-fam__pair {
		width: 100%;
		gap: 12px;
	}
}
</style>
