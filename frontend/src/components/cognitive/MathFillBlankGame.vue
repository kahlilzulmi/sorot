<template>
	<div class="math-fb">
		<header class="math-fb__header">
			<button type="button" class="btn btn-secondary btn-sm" @click="$emit('back')">
				← Games hub
			</button>
			<div class="math-fb__meta">
				<span>Math · Fill Blank</span>
				<span class="math-fb__score">Skor {{ score }} / {{ trials.length }}</span>
			</div>
		</header>

		<div v-if="!finished" class="math-fb__board">
			<ol class="math-fb__list">
				<li
					v-for="(trial, index) in trials"
					:key="trial.id"
					class="math-fb__item"
					:class="{
						'math-fb__item--active': index === currentIndex,
						'math-fb__item--correct': feedback[index] === 'correct',
						'math-fb__item--wrong': feedback[index] === 'wrong',
						'math-fb__item--done': index < currentIndex
					}"
				>
					<span class="math-fb__pointer" aria-hidden="true">
						{{ index === currentIndex ? '▸' : '' }}
					</span>
					<span class="math-fb__expr">{{ displayExpression(trial, index) }}</span>
				</li>
			</ol>

			<div class="math-fb__grid" role="group" aria-label="Pilihan jawaban">
				<button
					v-for="(choice, choiceIndex) in currentChoices"
					:key="`${trials[currentIndex]?.id}-${choiceIndex}`"
					type="button"
					class="math-fb__cell"
					:data-gaze-target="`math-fb-choice-${choiceIndex}`"
					:disabled="locked"
					@click="answer(choice)"
				>
					{{ choice }}
				</button>
			</div>
		</div>

		<div v-else class="math-fb__summary">
			<h2>Sesi selesai</h2>
			<p>Skor akhir: <strong>{{ score }}</strong> dari {{ trials.length }}</p>
			<div class="math-fb__summary-actions">
				<button type="button" class="btn btn-secondary" @click="restart">
					Main lagi
				</button>
				<button
					v-if="playlistMode"
					type="button"
					class="btn btn-primary"
					data-gaze-target="math-fb-next-game"
					@click="$emit('next-game')"
				>
					Game berikutnya
				</button>
				<button type="button" class="btn btn-secondary" @click="$emit('back')">
					Kembali ke hub
				</button>
			</div>
		</div>

		<p class="math-fb__hint">Soal persamaan matematika isi yang kosong — dwell kotak angka.</p>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
	correctFillBlankAnswer,
	createMathFillBlankSession,
	formatFillBlankFilled,
	formatFillBlankPrompt,
	type MathFillBlankTrial
} from '../../utils/mathFillBlankTrials'

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

const trials = ref<MathFillBlankTrial[]>(createMathFillBlankSession(props.roundCount ?? 5))
const currentIndex = ref(0)
const score = ref(0)
const locked = ref(false)
const feedback = ref<Feedback[]>(trials.value.map(() => null))
const chosenAnswers = ref<(number | null)[]>(trials.value.map(() => null))
const finished = computed(() => currentIndex.value >= trials.value.length)

const currentChoices = computed(() => {
	const trial = trials.value[currentIndex.value]
	return trial?.choices ?? [0, 0, 0, 0]
})

watch(finished, (isFinished) => {
	if (isFinished) {
		emit('finished', { score: score.value, total: trials.value.length })
	}
})

function displayExpression(trial: MathFillBlankTrial, index: number): string {
	const chosen = chosenAnswers.value[index]
	if (chosen != null) {
		return formatFillBlankFilled(trial, chosen)
	}
	return formatFillBlankPrompt(trial)
}

function restart(): void {
	trials.value = createMathFillBlankSession(props.roundCount ?? 5)
	currentIndex.value = 0
	score.value = 0
	locked.value = false
	feedback.value = trials.value.map(() => null)
	chosenAnswers.value = trials.value.map(() => null)
}

function answer(chosen: number): void {
	if (locked.value || finished.value) return
	const trial = trials.value[currentIndex.value]
	if (!trial) return

	locked.value = true
	chosenAnswers.value[currentIndex.value] = chosen
	const correct = chosen === correctFillBlankAnswer(trial)
	feedback.value[currentIndex.value] = correct ? 'correct' : 'wrong'
	if (correct) score.value += 1

	window.setTimeout(() => {
		currentIndex.value += 1
		locked.value = false
	}, 650)
}

function handleGazeTarget(targetId: string): boolean {
	const match = /^math-fb-choice-(\d)$/.exec(targetId)
	if (!match) return false
	const index = Number(match[1])
	const choice = currentChoices.value[index]
	if (choice == null) return false
	answer(choice)
	return true
}

defineExpose({
	handleGazeTarget,
	finished,
	score,
	restart
})
</script>

<style scoped>
.math-fb {
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

.math-fb__header {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	flex-shrink: 0;
	margin-bottom: clamp(0.25rem, 1vh, 0.75rem);
}

.math-fb__meta {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 2px;
	font-size: clamp(0.75rem, 1.5vh, 0.95rem);
	color: rgba(255, 255, 255, 0.55);
}

.math-fb__score {
	color: rgba(255, 255, 255, 0.4);
	font-size: 0.9em;
}

.math-fb__board {
	flex: 1;
	display: grid;
	grid-template-columns: minmax(0, 1fr) auto;
	column-gap: clamp(4rem, 12vw, 14rem);
	align-items: center;
	justify-content: space-between;
	min-height: 0;
	width: 100%;
	padding: 0 clamp(1vw, 4vw, 5rem);
	background: transparent;
	border: none;
}

.math-fb__list {
	list-style: none;
	margin: 0;
	padding: 0;
	display: flex;
	flex-direction: column;
	justify-content: center;
	gap: clamp(1.25rem, 4vh, 2.75rem);
}

.math-fb__item {
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

.math-fb__item--active {
	font-weight: 600;
}

.math-fb__item--correct {
	color: #4ade80;
}

.math-fb__item--wrong {
	color: #f87171;
}

.math-fb__pointer {
	color: #fff;
	font-size: 0.9em;
	line-height: 1.15;
}

.math-fb__grid {
	justify-self: end;
	display: grid;
	grid-template-columns: repeat(2, clamp(9rem, 26vmin, 15rem));
	grid-template-rows: repeat(2, clamp(9rem, 26vmin, 15rem));
	gap: clamp(1.1rem, 2.8vmin, 1.75rem);
}

.math-fb__cell {
	display: flex;
	align-items: center;
	justify-content: center;
	border: 2px solid #fff;
	background: transparent;
	color: #fff;
	font-size: clamp(3rem, 9vmin, 5rem);
	font-weight: 600;
	font-variant-numeric: tabular-nums;
	cursor: pointer;
	transition: background 0.15s ease;
}

.math-fb__cell:hover:not(:disabled),
.math-fb__cell:focus-visible:not(:disabled) {
	background: rgba(255, 255, 255, 0.14);
}

.math-fb__cell:disabled {
	opacity: 0.45;
	cursor: default;
}

.math-fb__summary {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: clamp(1.5rem, 4vh, 3rem);
	text-align: center;
}

.math-fb__summary h2 {
	margin: 0 0 10px;
	font-size: clamp(1.75rem, 4.5vh, 2.5rem);
	color: #fff;
}

.math-fb__summary p {
	margin: 0 0 20px;
	font-size: clamp(1.1rem, 2.8vh, 1.4rem);
	color: rgba(255, 255, 255, 0.65);
}

.math-fb__summary-actions {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	justify-content: center;
}

.math-fb__hint {
	flex-shrink: 0;
	margin: clamp(0.5rem, 1.5vh, 1rem) 0 0;
	font-size: clamp(0.7rem, 1.5vh, 0.9rem);
	color: rgba(255, 255, 255, 0.4);
}

@media (max-width: 900px) {
	.math-fb__board {
		grid-template-columns: 1fr;
		justify-items: center;
		row-gap: clamp(1.5rem, 4vh, 2.5rem);
	}

	.math-fb__grid {
		justify-self: center;
	}
}
</style>

