<template>
	<div
		ref="shellRef"
		class="cog-shell"
		:class="{
			'cog-shell--hide-os-cursor': hideOsCursor,
			'cog-shell--fullscreen': inGame
		}"
	>
		<div class="cog-shell__stage">
			<div class="cog-shell__panel" :class="{ 'center-panel': !inGame }">
				<CognitiveGamesHub
					v-if="view === 'hub'"
					@play-order="startPlaylist"
					@play-game="startSingle"
					@open-settings="toggleSettings"
				/>

				<MathTrueFalseGame
					v-else-if="activeGameId === 'math-true-false'"
					ref="mathTfRef"
					:playlist-mode="playlistMode"
					@back="returnToHub"
					@next-game="advancePlaylist"
				/>

				<MathFillBlankGame
					v-else-if="activeGameId === 'math-fill-blank'"
					ref="mathFbRef"
					:playlist-mode="playlistMode"
					@back="returnToHub"
					@next-game="advancePlaylist"
				/>

				<div v-else class="cog-placeholder">
					<button type="button" class="btn btn-secondary btn-sm" @click="returnToHub">
						← Games hub
					</button>
					<h2>{{ activeGameName }}</h2>
					<p>
						Module UI arrives in a later phase. Eye-tracker dwell cursor is active in-game only.
					</p>
					<button
						v-if="playlistMode"
						type="button"
						class="btn btn-primary btn-sm"
						@click="advancePlaylist"
					>
						Next game in playlist
					</button>
				</div>
			</div>
		</div>

		<DwellCursor
			v-if="hideOsCursor && gaze.point.value"
			:x="gaze.point.value.x"
			:y="gaze.point.value.y"
			:cursor-color="cursor.cursorColor"
			:dwell-effect-color="cursor.dwellEffectColor"
			:shape="cursor.shape"
			:dwell-effect="cursor.dwellEffect"
			:cursor-size-px="cursor.cursorSizePx"
			:dwell-effect-size-px="cursor.dwellEffectSizePx"
			:progress="dwell.progress.value"
			:dwelling="dwell.dwelling.value"
		/>

		<CognitiveSettingsOverlay v-if="settingsOpen" @close="closeOverlays" />
		<CognitiveQuitModal
			v-if="quitConfirmOpen"
			@confirm="confirmQuit"
			@cancel="closeQuitConfirm"
		/>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import DwellCursor from './DwellCursor.vue'
import CognitiveGamesHub from './CognitiveGamesHub.vue'
import CognitiveSettingsOverlay from './CognitiveSettingsOverlay.vue'
import CognitiveQuitModal from './CognitiveQuitModal.vue'
import MathTrueFalseGame from './MathTrueFalseGame.vue'
import MathFillBlankGame from './MathFillBlankGame.vue'
import { useCognitiveSettings } from '../../composables/useCognitiveSettings'
import { useGazeDevices } from '../../composables/useGazeDevices'
import { useGazePoint } from '../../composables/useGazePoint'
import { useDwellClick } from '../../composables/useDwellClick'
import {
	COGNITIVE_GAMES,
	type CognitiveGameId,
	type DwellEffectStyle,
	type GazeCursorShape,
	type GazeInputSourceId
} from '../../types/cognitiveGame'
import type { GazeDeviceTransport } from '../../types/gazeDevice'

const emit = defineEmits<{
	(e: 'exit'): void
	(e: 'in-game-change', inGame: boolean): void
}>()

type GazeGameRef = { handleGazeTarget: (id: string) => boolean }

const shellRef = ref<HTMLElement | null>(null)
const mathTfRef = ref<GazeGameRef | null>(null)
const mathFbRef = ref<GazeGameRef | null>(null)
const view = ref<'hub' | 'game'>('hub')
const activeGameId = ref<CognitiveGameId | null>(null)
const playlistMode = ref(false)
const playlistIndex = ref(0)

const {
	cursor,
	enabledGames,
	settingsOpen,
	quitConfirmOpen,
	toggleSettings,
	openQuitConfirm,
	closeQuitConfirm,
	closeOverlays,
	dwellMsForGame,
	setCursorShape,
	setDwellEffect
} = useCognitiveSettings()

const inGame = computed(() => view.value === 'game')
const hideOsCursor = computed(
	() => inGame.value && !settingsOpen.value && !quitConfirmOpen.value
)
const { selectedDevice } = useGazeDevices()
const gazeSource = computed(() => transportToGazeSource(selectedDevice.value.transport))
const gaze = useGazePoint(gazeSource)
const dwellMs = computed(() => dwellMsForGame(activeGameId.value))
const dwellPaused = computed(
	() => !inGame.value || settingsOpen.value || quitConfirmOpen.value
)

const dwell = useDwellClick({
	point: gaze.point,
	dwellMs,
	paused: dwellPaused,
	root: shellRef,
	onGazeClick: (targetId) => {
		handleGazeClick(targetId)
	}
})

watch(
	inGame,
	(value) => {
		emit('in-game-change', value)
	},
	{ immediate: true }
)

const activeGameName = computed(() => {
	const game = COGNITIVE_GAMES.find((entry) => entry.id === activeGameId.value)
	return game?.name ?? 'Cognitive game'
})

const playableIds = computed(() => enabledGames.value.map((game) => game.id))

function transportToGazeSource(transport: GazeDeviceTransport): GazeInputSourceId {
	switch (transport) {
		case 'mouse':
			return 'mouse'
		case 'webgazer':
			return 'webgazer'
		case 'tobii_overlay':
		case 'tobii_sdk':
		case 'virtual_camera':
			return 'tobii-overlay'
		default:
			return 'mouse'
	}
}

function handleGazeClick(targetId: string): void {
	if (targetId === 'quit-yes') {
		confirmQuit()
		return
	}
	if (targetId === 'quit-no') {
		closeQuitConfirm()
		return
	}
	if (targetId === 'settings-close') {
		closeOverlays()
		return
	}
	if (targetId.startsWith('settings-shape-')) {
		const shape = targetId.replace('settings-shape-', '') as GazeCursorShape
		if (shape === 'arrow' || shape === 'dot' || shape === 'transparent') {
			setCursorShape(shape)
		}
		return
	}
	if (targetId.startsWith('settings-dwell-')) {
		const effect = targetId.replace('settings-dwell-', '') as DwellEffectStyle
		if (effect === 'ring' || effect === 'pie' || effect === 'transparent') {
			setDwellEffect(effect)
		}
		return
	}
	if (targetId === 'math-tf-next-game' || targetId === 'math-fb-next-game') {
		advancePlaylist()
		return
	}
	if (mathTfRef.value?.handleGazeTarget(targetId)) {
		return
	}
	if (mathFbRef.value?.handleGazeTarget(targetId)) {
		return
	}
}

function startSingle(id: CognitiveGameId): void {
	playlistMode.value = false
	activeGameId.value = id
	view.value = 'game'
	closeOverlays()
}

function startPlaylist(): void {
	const ids = playableIds.value
	if (ids.length === 0) return
	playlistMode.value = true
	playlistIndex.value = 0
	activeGameId.value = ids[0] ?? null
	view.value = 'game'
	closeOverlays()
}

function advancePlaylist(): void {
	if (!playlistMode.value) return
	const ids = playableIds.value
	const next = playlistIndex.value + 1
	if (next >= ids.length) {
		returnToHub()
		return
	}
	playlistIndex.value = next
	activeGameId.value = ids[next] ?? null
}

function returnToHub(): void {
	view.value = 'hub'
	activeGameId.value = null
	playlistMode.value = false
	closeOverlays()
}

function confirmQuit(): void {
	closeOverlays()
	emit('exit')
}

function onKeyDown(event: KeyboardEvent): void {
	const tag = (event.target as HTMLElement | null)?.tagName
	if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

	if (event.key === 'q' || event.key === 'Q') {
		event.preventDefault()
		if (inGame.value) {
			returnToHub()
			return
		}
		openQuitConfirm()
		return
	}
	if (event.key === 's' || event.key === 'S') {
		event.preventDefault()
		toggleSettings()
	}
}

onMounted(() => {
	window.addEventListener('keydown', onKeyDown)
})

onUnmounted(() => {
	window.removeEventListener('keydown', onKeyDown)
	emit('in-game-change', false)
})
</script>

<style scoped>
.cog-shell {
	height: calc(100vh - 120px);
	min-height: 480px;
	overflow: auto;
	padding: 10px 12px;
	background: var(--color-background);
	color: var(--color-text);
}

.cog-shell--fullscreen {
	position: fixed;
	inset: 0;
	z-index: 40;
	display: flex;
	flex-direction: column;
	width: 100vw;
	height: 100vh;
	min-height: 100vh;
	padding: 0;
	overflow: hidden;
	background: #000;
}

.cog-shell--hide-os-cursor,
.cog-shell--hide-os-cursor * {
	cursor: none !important;
}

.cog-shell__stage {
	max-width: 1920px;
	min-width: 1000px;
	margin: 0 auto;
	height: 100%;
}

.cog-shell--fullscreen .cog-shell__stage {
	flex: 1;
	width: 100%;
	min-width: 0;
	max-width: none;
	height: 100%;
	margin: 0;
}

.cog-shell__panel {
	min-height: calc(100% - 4px);
	overflow: auto;
	padding: 16px 18px;
}

.cog-shell--fullscreen .cog-shell__panel {
	display: flex;
	flex-direction: column;
	height: 100%;
	min-height: 100%;
	padding: 0;
	overflow: hidden;
	background: transparent !important;
	border: none !important;
	border-radius: 0 !important;
	box-shadow: none !important;
}

.cog-shell--fullscreen .cog-shell__panel > * {
	flex: 1 1 auto;
	min-height: 0;
	width: 100%;
	height: 100%;
}

.cog-shell--fullscreen .cog-placeholder {
	flex: 1;
	display: flex;
	flex-direction: column;
	justify-content: center;
	max-width: none;
	padding: clamp(1.5rem, 4vw, 3rem);
}

.cog-placeholder {
	max-width: 720px;
	padding: 12px 4px 32px;
}

.cog-placeholder h2 {
	margin: 16px 0 10px;
	font-size: 22px;
	color: var(--color-accent);
}

.cog-placeholder p {
	margin: 0 0 16px;
	color: var(--color-text-dim);
	line-height: 1.5;
}
</style>

