<template>
	<div
		class="cog-game-settings"
		role="dialog"
		aria-modal="true"
		:aria-label="`${gameName} settings`"
		@click.self="closeGameSettings"
	>
		<div
			class="cog-game-settings__panel"
			:class="{
				'cog-game-settings__panel--wide':
					gameId === 'face-familiarity' ||
					gameId === 'visual-search' ||
					gameId === 'memory-matrix'
			}"
		>
			<header class="cog-game-settings__header">
				<h2>{{ gameName }}</h2>
				<p>
					{{
						gameId === 'face-familiarity'
							? 'Dwell time and face photo pairs for this module.'
							: gameId === 'visual-search'
								? 'Dwell time, grid density, targets, and session timer.'
								: gameId === 'memory-matrix'
									? 'Dwell time, sequence length, rounds, and flash timing.'
									: 'Module settings. Day one: dwell time only.'
					}}
				</p>
			</header>

			<section v-if="gameId" class="cog-game-settings__section">
				<label class="cog-game-settings__field">
					<span>Dwell time (ms)</span>
					<input
						:value="dwellMsForGame(gameId)"
						class="cog-game-settings__input"
						type="number"
						min="200"
						step="100"
						@change="onDwellChange"
					>
				</label>
				<p class="cog-game-settings__hint">
					How long gaze must stay on a target before it clicks in this module.
				</p>
			</section>

			<section v-if="gameId === 'face-familiarity'" class="cog-game-settings__section">
				<h3 class="cog-game-settings__subheader">Face photos</h3>
				<p class="cog-game-settings__hint">
					Upload a <strong>real</strong> and an <strong>AI</strong> image for each pair.
					Use <strong>Add pair</strong> / remove to set how many faces you need.
					A session plays every ready pair (order shuffled). Saved in localStorage
					(<code>{{ faceStorageKey }}</code>). Play needs at least one complete pair.
				</p>

				<div
					v-for="(pair, index) in facePairs"
					:key="pair.id"
					class="cog-face-row"
				>
					<input
						v-model="pair.label"
						class="cog-face-row__label"
						type="text"
						:aria-label="`Pair ${index + 1} label`"
					>
					<label class="cog-face-row__upload">
						<span>Real</span>
						<img :src="pair.realSrc" alt="" class="cog-face-row__thumb">
						<input
							type="file"
							accept="image/*"
							@change="onFaceFile(index, 'realSrc', $event)"
						>
						<span
							class="cog-face-row__badge"
							:class="{ 'cog-face-row__badge--ok': !isPlaceholderImageSrc(pair.realSrc) }"
						>
							{{ isPlaceholderImageSrc(pair.realSrc) ? 'Missing' : 'OK' }}
						</span>
					</label>
					<label class="cog-face-row__upload">
						<span>AI</span>
						<img :src="pair.aiSrc" alt="" class="cog-face-row__thumb">
						<input
							type="file"
							accept="image/*"
							@change="onFaceFile(index, 'aiSrc', $event)"
						>
						<span
							class="cog-face-row__badge"
							:class="{ 'cog-face-row__badge--ok': !isPlaceholderImageSrc(pair.aiSrc) }"
						>
							{{ isPlaceholderImageSrc(pair.aiSrc) ? 'Missing' : 'OK' }}
						</span>
					</label>
					<button
						type="button"
						class="cog-face-row__remove"
						:disabled="facePairs.length <= minFacePairs"
						:aria-label="`Remove pair ${index + 1}`"
						@click="removeFacePair(index)"
					>
						Remove
					</button>
				</div>

				<div class="cog-face-actions">
					<button
						type="button"
						class="cog-game-settings__btn"
						:disabled="facePairs.length >= maxFacePairs"
						@click="addFacePair"
					>
						Add pair
					</button>
					<button
						type="button"
						class="cog-game-settings__btn cog-game-settings__btn--primary"
						@click="saveFaceAssets"
					>
						Save photos
					</button>
					<button type="button" class="cog-game-settings__btn" @click="resetFaceAssets">
						Reset placeholders
					</button>
				</div>
				<p v-if="faceMessage" class="cog-face-msg" :class="{ 'cog-face-msg--warn': faceWarn }">
					{{ faceMessage }}
				</p>
				<p class="cog-game-settings__hint">
					Ready pairs (session length): {{ suppliedPairCount }} / {{ facePairs.length }}
					slots
				</p>
			</section>
			<section v-if="gameId === 'visual-search'" class="cog-game-settings__section">
				<h3 class="cog-game-settings__subheader">Visual Search</h3>
				<p class="cog-game-settings__hint">
					Found targets only change <strong>letter color</strong> to green (no bounding box).
					Saved in localStorage (<code>{{ vsStorageKey }}</code>).
				</p>
				<label class="cog-game-settings__field">
					<span>Columns (density)</span>
					<input v-model.number="vsDraft.columns" class="cog-game-settings__input" type="number" :min="vsColsMin" :max="vsColsMax" step="1">
				</label>
				<label class="cog-game-settings__field">
					<span>Rows (density)</span>
					<input v-model.number="vsDraft.rows" class="cog-game-settings__input" type="number" :min="vsRowsMin" :max="vsRowsMax" step="1">
				</label>
				<label class="cog-game-settings__field">
					<span>Targets per level</span>
					<input v-model.number="vsDraft.targetCount" class="cog-game-settings__input" type="number" :min="vsTargetsMin" :max="vsTargetsMax" step="1">
				</label>
				<label class="cog-game-settings__field">
					<span>Session timer (seconds)</span>
					<input v-model.number="vsDraft.timerSeconds" class="cog-game-settings__input" type="number" :min="vsTimerMin" :max="vsTimerMax" step="30">
				</label>
				<div class="cog-face-actions">
					<button type="button" class="cog-game-settings__btn cog-game-settings__btn--primary" @click="saveVsSettings">
						Save Visual Search settings
					</button>
					<button type="button" class="cog-game-settings__btn" @click="resetVsSettings">
						Reset defaults
					</button>
				</div>
				<p v-if="vsMessage" class="cog-face-msg" :class="{ 'cog-face-msg--warn': vsWarn }">
					{{ vsMessage }}
				</p>
			</section>

			<section v-if="gameId === 'memory-matrix'" class="cog-game-settings__section">
				<h3 class="cog-game-settings__subheader">Memory Matrix</h3>
				<p class="cog-game-settings__hint">
					Yellow = system cue, green = correct dwell, red = wrong. Saved in localStorage
					(<code>{{ mmStorageKey }}</code>).
				</p>
				<label class="cog-game-settings__field">
					<span>Starting sequence length</span>
					<input
						v-model.number="mmDraft.startLength"
						class="cog-game-settings__input"
						type="number"
						:min="mmLengthMin"
						:max="mmLengthMax"
						step="1"
					>
				</label>
				<label class="cog-game-settings__field">
					<span>Rounds</span>
					<input
						v-model.number="mmDraft.rounds"
						class="cog-game-settings__input"
						type="number"
						:min="mmRoundsMin"
						:max="mmRoundsMax"
						step="1"
					>
				</label>
				<label class="cog-game-settings__field">
					<span>Grow by (after each success)</span>
					<input
						v-model.number="mmDraft.growBy"
						class="cog-game-settings__input"
						type="number"
						:min="mmGrowMin"
						:max="mmGrowMax"
						step="1"
					>
				</label>
				<label class="cog-game-settings__field">
					<span>Flash duration (ms)</span>
					<input
						v-model.number="mmDraft.flashMs"
						class="cog-game-settings__input"
						type="number"
						:min="mmFlashMin"
						:max="mmFlashMax"
						step="50"
					>
				</label>
				<label class="cog-game-settings__field">
					<span>Gap between flashes (ms)</span>
					<input
						v-model.number="mmDraft.gapMs"
						class="cog-game-settings__input"
						type="number"
						:min="mmGapMin"
						:max="mmGapMax"
						step="50"
					>
				</label>
				<div class="cog-face-actions">
					<button
						type="button"
						class="cog-game-settings__btn cog-game-settings__btn--primary"
						@click="saveMmSettings"
					>
						Save Memory Matrix settings
					</button>
					<button type="button" class="cog-game-settings__btn" @click="resetMmSettings">
						Reset defaults
					</button>
				</div>
				<p v-if="mmMessage" class="cog-face-msg" :class="{ 'cog-face-msg--warn': mmWarn }">
					{{ mmMessage }}
				</p>
			</section>

			<footer class="cog-game-settings__footer">
				<button type="button" class="cog-game-settings__btn" @click="closeGameSettings">
					Close
				</button>
			</footer>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useCognitiveSettings } from '../../composables/useCognitiveSettings'
import type { CognitiveGameId } from '../../types/cognitiveGame'
import {
	FACE_FAMILIARITY_ASSETS_STORAGE_KEY,
	MAX_FACE_PAIRS,
	MIN_FACE_PAIRS,
	createEmptyFacePair,
	isFacePairFullySupplied,
	isPlaceholderImageSrc,
	loadFacePairs,
	readImageFileAsDataUrl,
	resetFacePairsToDefaults,
	saveFacePairs,
	type FacePairAsset
} from '../../utils/faceFamiliarityAssets'
import {
	VISUAL_SEARCH_COLUMNS_MAX,
	VISUAL_SEARCH_COLUMNS_MIN,
	VISUAL_SEARCH_ROWS_MAX,
	VISUAL_SEARCH_ROWS_MIN,
	VISUAL_SEARCH_SETTINGS_STORAGE_KEY,
	VISUAL_SEARCH_TARGETS_MAX,
	VISUAL_SEARCH_TARGETS_MIN,
	VISUAL_SEARCH_TIMER_MAX,
	VISUAL_SEARCH_TIMER_MIN,
	loadVisualSearchSettings,
	resetVisualSearchSettings,
	saveVisualSearchSettings,
	type VisualSearchSettings
} from '../../utils/visualSearchSettings'
import {
	MEMORY_MATRIX_FLASH_MAX,
	MEMORY_MATRIX_FLASH_MIN,
	MEMORY_MATRIX_GAP_MAX,
	MEMORY_MATRIX_GAP_MIN,
	MEMORY_MATRIX_GROW_MAX,
	MEMORY_MATRIX_GROW_MIN,
	MEMORY_MATRIX_LENGTH_MAX,
	MEMORY_MATRIX_LENGTH_MIN,
	MEMORY_MATRIX_ROUNDS_MAX,
	MEMORY_MATRIX_ROUNDS_MIN,
	MEMORY_MATRIX_SETTINGS_STORAGE_KEY,
	loadMemoryMatrixSettings,
	resetMemoryMatrixSettings,
	saveMemoryMatrixSettings,
	type MemoryMatrixSettings
} from '../../utils/memoryMatrixSettings'

const props = defineProps<{
	gameId: CognitiveGameId
}>()

const { dwellMsForGame, setGameDwellMs, closeGameSettings, games } = useCognitiveSettings()

const gameName = computed(
	() => games.value.find((game) => game.id === props.gameId)?.name ?? 'Game settings'
)

const faceStorageKey = FACE_FAMILIARITY_ASSETS_STORAGE_KEY
const minFacePairs = MIN_FACE_PAIRS
const maxFacePairs = MAX_FACE_PAIRS
const facePairs = ref<FacePairAsset[]>(loadFacePairs())
const faceMessage = ref('')
const faceWarn = ref(false)

const suppliedPairCount = computed(
	() => facePairs.value.filter(isFacePairFullySupplied).length
)

function onDwellChange(event: Event): void {
	setGameDwellMs(props.gameId, Number((event.target as HTMLInputElement).value))
}

function addFacePair(): void {
	if (facePairs.value.length >= MAX_FACE_PAIRS) return
	facePairs.value.push(createEmptyFacePair(facePairs.value.length))
	faceMessage.value = ''
	faceWarn.value = false
}

function removeFacePair(index: number): void {
	if (facePairs.value.length <= MIN_FACE_PAIRS) return
	facePairs.value.splice(index, 1)
	faceMessage.value = ''
	faceWarn.value = false
}

async function onFaceFile(
	index: number,
	field: 'realSrc' | 'aiSrc',
	event: Event
): Promise<void> {
	const input = event.target as HTMLInputElement
	const file = input.files?.[0]
	if (!file) return
	try {
		const dataUrl = await readImageFileAsDataUrl(file)
		const pair = facePairs.value[index]
		if (!pair) return
		pair[field] = dataUrl
		faceMessage.value = ''
		faceWarn.value = false
	} catch {
		faceMessage.value = 'Could not read that image file.'
		faceWarn.value = true
	} finally {
		input.value = ''
	}
}

function saveFaceAssets(): void {
	facePairs.value = saveFacePairs(facePairs.value)
	const ready = suppliedPairCount.value
	if (ready < 1) {
		faceMessage.value =
			'Saved, but Play still needs at least one pair with both Real and AI photos.'
		faceWarn.value = true
		return
	}
	faceMessage.value = `Saved ${ready} ready pair(s). Session will use all of them.`
	faceWarn.value = false
}

function resetFaceAssets(): void {
	facePairs.value = resetFacePairsToDefaults()
	faceMessage.value = 'Placeholders restored. Upload photos again before Play.'
	faceWarn.value = true
}

const vsStorageKey = VISUAL_SEARCH_SETTINGS_STORAGE_KEY
const vsColsMin = VISUAL_SEARCH_COLUMNS_MIN
const vsColsMax = VISUAL_SEARCH_COLUMNS_MAX
const vsRowsMin = VISUAL_SEARCH_ROWS_MIN
const vsRowsMax = VISUAL_SEARCH_ROWS_MAX
const vsTargetsMin = VISUAL_SEARCH_TARGETS_MIN
const vsTargetsMax = VISUAL_SEARCH_TARGETS_MAX
const vsTimerMin = VISUAL_SEARCH_TIMER_MIN
const vsTimerMax = VISUAL_SEARCH_TIMER_MAX
const vsDraft = ref<VisualSearchSettings>(loadVisualSearchSettings())
const vsMessage = ref('')
const vsWarn = ref(false)

function saveVsSettings(): void {
	vsDraft.value = saveVisualSearchSettings(vsDraft.value)
	vsMessage.value =
		'Saved grid ' +
		vsDraft.value.columns +
		'x' +
		vsDraft.value.rows +
		', ' +
		vsDraft.value.targetCount +
		' targets, ' +
		vsDraft.value.timerSeconds +
		's timer.'
	vsWarn.value = false
}

function resetVsSettings(): void {
	vsDraft.value = resetVisualSearchSettings()
	vsMessage.value = 'Visual Search defaults restored.'
	vsWarn.value = true
}

const mmStorageKey = MEMORY_MATRIX_SETTINGS_STORAGE_KEY
const mmLengthMin = MEMORY_MATRIX_LENGTH_MIN
const mmLengthMax = MEMORY_MATRIX_LENGTH_MAX
const mmRoundsMin = MEMORY_MATRIX_ROUNDS_MIN
const mmRoundsMax = MEMORY_MATRIX_ROUNDS_MAX
const mmGrowMin = MEMORY_MATRIX_GROW_MIN
const mmGrowMax = MEMORY_MATRIX_GROW_MAX
const mmFlashMin = MEMORY_MATRIX_FLASH_MIN
const mmFlashMax = MEMORY_MATRIX_FLASH_MAX
const mmGapMin = MEMORY_MATRIX_GAP_MIN
const mmGapMax = MEMORY_MATRIX_GAP_MAX
const mmDraft = ref<MemoryMatrixSettings>(loadMemoryMatrixSettings())
const mmMessage = ref('')
const mmWarn = ref(false)

function saveMmSettings(): void {
	mmDraft.value = saveMemoryMatrixSettings(mmDraft.value)
	mmMessage.value =
		'Saved start ' +
		mmDraft.value.startLength +
		', ' +
		mmDraft.value.rounds +
		' rounds, grow +' +
		mmDraft.value.growBy +
		', flash ' +
		mmDraft.value.flashMs +
		'ms / gap ' +
		mmDraft.value.gapMs +
		'ms.'
	mmWarn.value = false
}

function resetMmSettings(): void {
	mmDraft.value = resetMemoryMatrixSettings()
	mmMessage.value = 'Memory Matrix defaults restored.'
	mmWarn.value = true
}
</script>

<style scoped>
.cog-game-settings {
	position: fixed;
	inset: 0;
	z-index: 13100;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(0, 0, 0, 0.72);
	padding: 24px;
}

.cog-game-settings__panel {
	width: min(420px, 100%);
	max-height: min(90vh, 900px);
	overflow: auto;
	background: #0a0a0a;
	border: 1px solid #fff;
	color: #fff;
	padding: 20px;
}

.cog-game-settings__panel--wide {
	width: min(720px, 100%);
}

.cog-game-settings__header h2 {
	margin: 0 0 6px;
	font-size: 18px;
	font-weight: 600;
}

.cog-game-settings__header p {
	margin: 0 0 16px;
	color: #aaa;
	font-size: 13px;
}

.cog-game-settings__subheader {
	margin: 0 0 8px;
	font-size: 14px;
	font-weight: 600;
	color: #ddd;
}

.cog-game-settings__section {
	margin-bottom: 16px;
}

.cog-game-settings__field {
	display: flex;
	flex-direction: column;
	gap: 6px;
	font-size: 13px;
	color: #bbb;
}

.cog-game-settings__input {
	width: 100%;
	max-width: 200px;
	padding: 8px 10px;
	border: 1px solid #555;
	background: #111;
	color: #fff;
}

.cog-game-settings__hint {
	margin: 8px 0 0;
	font-size: 12px;
	color: #888;
	line-height: 1.45;
}

.cog-game-settings__hint code {
	font-size: 11px;
	color: #bbb;
}

.cog-game-settings__footer {
	display: flex;
	justify-content: flex-end;
	margin-top: 8px;
}

.cog-game-settings__btn {
	border: 1px solid #fff;
	background: transparent;
	color: #fff;
	padding: 10px 16px;
	cursor: pointer;
}

.cog-game-settings__btn:disabled {
	opacity: 0.35;
	cursor: not-allowed;
}

.cog-game-settings__btn--primary {
	background: #fff;
	color: #000;
}

.cog-face-row {
	display: grid;
	grid-template-columns: minmax(90px, 1fr) auto auto auto;
	gap: 12px;
	align-items: center;
	margin-top: 10px;
	padding: 10px;
	border: 1px solid #333;
	background: #050505;
}

.cog-face-row__label {
	width: 100%;
	padding: 8px 10px;
	border: 1px solid #555;
	background: #111;
	color: #fff;
}

.cog-face-row__upload {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 6px;
	font-size: 12px;
	color: #aaa;
	cursor: pointer;
}

.cog-face-row__upload input[type='file'] {
	width: 100%;
	max-width: 130px;
	font-size: 11px;
	color: #ccc;
}

.cog-face-row__thumb {
	width: 72px;
	height: 72px;
	object-fit: cover;
	border: 1px solid #555;
	background: #111;
}

.cog-face-row__badge {
	font-size: 11px;
	color: #f87171;
}

.cog-face-row__badge--ok {
	color: #4ade80;
}

.cog-face-row__remove {
	align-self: center;
	padding: 8px 10px;
	border: 1px solid #555;
	background: transparent;
	color: #f87171;
	cursor: pointer;
	font-size: 12px;
}

.cog-face-row__remove:hover:not(:disabled) {
	border-color: #f87171;
}

.cog-face-row__remove:disabled {
	opacity: 0.35;
	cursor: not-allowed;
}

.cog-face-actions {
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
	margin-top: 12px;
}

.cog-face-msg {
	margin: 10px 0 0;
	font-size: 13px;
	color: #4ade80;
}

.cog-face-msg--warn {
	color: #fbbf24;
}

@media (max-width: 640px) {
	.cog-face-row {
		grid-template-columns: 1fr;
	}
}
</style>
