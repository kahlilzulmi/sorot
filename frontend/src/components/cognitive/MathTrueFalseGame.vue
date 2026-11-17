<template>
	<div class="math-tf">
		<header class="math-tf__header" data-session-chrome>
			<button type="button" class="btn btn-secondary btn-sm" @click="$emit('back')">
				← Games hub
			</button>
			<div class="math-tf__meta">
				<span>Math · True / False</span>
				<span class="math-tf__score">Skor {{ score }} / {{ trials.length }}</span>
			</div>
		</header>

		<div v-if="!finished" class="math-tf__board">
			<ol class="math-tf__list">
				<li
					v-for="(trial, index) in trials"
					:key="trial.id"
					class="math-tf__item"
					:class="{
						'math-tf__item--active': index === currentIndex,
						'math-tf__item--correct': feedback[index] === 'correct',
						'math-tf__item--wrong': feedback[index] === 'wrong',
						'math-tf__item--done': index < currentIndex
					}"
				>
					<span class="math-tf__pointer" aria-hidden="true">
						{{ index === currentIndex ? '▸' : '' }}
					</span>
					<span class="math-tf__expr">{{ trial.expression }}</span>
				</li>
			</ol>

			<div class="math-tf__choices">
				<button
					type="button"
					class="math-tf__choice"
					data-gaze-target="math-tf-benar"
					:disabled="locked"
					@click="answer(true)"
				>
					Benar
				</button>
				<button
					type="button"
					class="math-tf__choice"
					data-gaze-target="math-tf-salah"
					:disabled="locked"
					@click="answer(false)"
				>
					Salah
				</button>
			</div>
		</div>

		<div v-else class="math-tf__summary">
			<h2>Sesi selesai</h2>
			<p>Skor akhir: <strong>{{ score }}</strong> dari {{ trials.length }}</p>
			<div class="math-tf__summary-actions">
				<button type="button" class="btn btn-secondary" @click="restart">
					Main lagi
				</button>
				<button
					v-if="playlistMode"
					type="button"
					class="btn btn-primary"
					data-gaze-target="math-tf-next-game"
					@click="$emit('next-game')"
				>
					Game berikutnya
				</button>
				<button type="button" class="btn btn-secondary" data-session-chrome @click="$emit('back')">
					Kembali ke hub
				</button>
			</div>
		</div>

		<p class="math-tf__hint" data-session-chrome>Soal persamaan matematika benar atau salah — dwell Benar / Salah.</p>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
	createMathTrueFalseSession,
	type MathTrueFalseTrial
} from '../../utils/mathTrueFalseTrials'

const props = defineProps<{
	playlistMode?: boolean
	roundCount?: number
}>()

const emit = defineEmits<{
	(e: 'back'): void
	(e: 'next-game'): void
	(e: 'finished', payload: { score: number; total: number }): void
}>()

type Feedback = 'correct' | 'wrong' | null

const trials = ref<MathTrueFalseTrial[]>(createMathTrueFalseSession(props.roundCount ?? 5))
const currentIndex = ref(0)
const score = ref(0)
const locked = ref(false)
const feedback = ref<Feedback[]>(trials.value.map(() => null))
const finished = computed(() => currentIndex.value >= trials.value.length)

watch(finished, (isFinished) => {
	if (isFinished) {
		emit('finished', { score: score.value, total: trials.value.length })
	}
})

function restart(): void {
	trials.value = createMathTrueFalseSession(props.roundCount ?? 5)
	currentIndex.value = 0
	score.value = 0
	locked.value = false
	feedback.value = trials.value.map(() => null)
}

function answer(choseTrue: boolean): void {
	if (locked.value || finished.value) return
	const trial = trials.value[currentIndex.value]
	if (!trial) return

	locked.value = true
	const correct = choseTrue === trial.isTrue
	feedback.value[currentIndex.value] = correct ? 'correct' : 'wrong'
	if (correct) score.value += 1

	window.setTimeout(() => {
		currentIndex.value += 1
		locked.value = false
	}, 650)
}

function handleGazeTarget(targetId: string): boolean {
	if (targetId === 'math-tf-benar') {
		answer(true)
		return true
	}
	if (targetId === 'math-tf-salah') {
		answer(false)
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
.math-tf {
	flex: 1;
	display: flex;
	flex-direction: column;
	width: 100%;
	height: 100%;
	min-height: 0;
	max-width: none;
	margin: 0;
	padding: clamp(0.5rem, 1.5vh, 1rem) clamp(2vw, 5vw, 4rem) clamp(0.75rem, 2vh, 1.25rem);
	box-sizing: border-box;
	color: #fff;
	background: #000;
}

.math-tf__header {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	flex-shrink: 0;
	margin-bottom: clamp(0.25rem, 1vh, 0.75rem);
}

.math-tf__meta {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 2px;
	font-size: clamp(0.75rem, 1.5vh, 0.95rem);
	color: rgba(255, 255, 255, 0.55);
}

.math-tf__score {
	color: rgba(255, 255, 255, 0.4);
	font-size: 0.9em;
}

.math-tf__board {
	flex: 1;
	display: grid;
	grid-template-columns: minmax(0, 1fr) auto;
	column-gap: clamp(4rem, 12vw, 14rem);
	align-items: center;
	min-height: 0;
	width: 100%;
	padding: 0 clamp(1vw, 4vw, 5rem);
	background: transparent;
	border: none;
}

.math-tf__list {
	list-style: none;
	margin: 0;
	padding: 0;
	display: flex;
	flex-direction: column;
	justify-content: center;
	gap: clamp(1.25rem, 4vh, 2.75rem);
}

.math-tf__item {
	display: grid;
	grid-template-columns: clamp(2rem, 4vh, 3rem) 1fr;
	gap: clamp(0.75rem, 2vw, 1.5rem);
	align-items: baseline;
	font-size: clamp(2.75rem, 8.5vh, 5rem);
	line-height: 1.15;
	font-weight: 500;
	font-variant-numeric: tabular-nums;
	letter-spacing: 0.03em;
	color: #fff;
	transition: color 0.2s ease;
}

.math-tf__item--active {
	font-weight: 600;
}

.math-tf__item--correct {
	color: #4ade80;
}

.math-tf__item--wrong {
	color: #f87171;
}

.math-tf__pointer {
	color: #fff;
	font-size: 0.9em;
	line-height: 1.15;
}

.math-tf__choices {
	justify-self: end;
	display: flex;
	flex-direction: column;
	gap: clamp(1rem, 3vh, 1.75rem);
	min-width: clamp(12rem, 28vmin, 18rem);
}

.math-tf__choice {
	min-height: clamp(5.5rem, 16vmin, 9rem);
	padding: clamp(0.85rem, 2vh, 1.4rem) clamp(1.25rem, 3vw, 2rem);
	border: 2px solid #fff;
	background: transparent;
	color: #fff;
	font-size: clamp(2rem, 6vmin, 3.25rem);
	font-weight: 600;
	cursor: pointer;
	transition: background 0.15s ease;
}

.math-tf__choice:hover:not(:disabled),
.math-tf__choice:focus-visible:not(:disabled) {
	background: rgba(255, 255, 255, 0.14);
}

.math-tf__choice:disabled {
	opacity: 0.45;
	cursor: default;
}

.math-tf__summary {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: clamp(1.5rem, 4vh, 3rem);
	text-align: center;
}

.math-tf__summary h2 {
	margin: 0 0 10px;
	font-size: clamp(1.75rem, 4.5vh, 2.5rem);
	color: #fff;
}

.math-tf__summary p {
	margin: 0 0 20px;
	font-size: clamp(1.1rem, 2.8vh, 1.4rem);
	color: rgba(255, 255, 255, 0.65);
}

.math-tf__summary-actions {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	justify-content: center;
}

.math-tf__hint {
	flex-shrink: 0;
	margin: clamp(0.5rem, 1.5vh, 1rem) 0 0;
	font-size: clamp(0.7rem, 1.5vh, 0.9rem);
	color: rgba(255, 255, 255, 0.4);
}

@media (max-width: 900px) {
	.math-tf__board {
		grid-template-columns: 1fr;
		justify-items: center;
		row-gap: clamp(1.5rem, 4vh, 2.5rem);
	}

	.math-tf__choices {
		justify-self: center;
		flex-direction: row;
		min-width: 0;
		width: min(100%, 32rem);
	}

	.math-tf__choice {
		flex: 1;
	}
}
</style>

