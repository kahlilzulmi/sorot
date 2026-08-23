<template>
	<div
		class="cog-game-settings"
		role="dialog"
		aria-modal="true"
		:aria-label="`${gameName} settings`"
		@click.self="closeGameSettings"
	>
		<div class="cog-game-settings__panel">
			<header class="cog-game-settings__header">
				<h2>{{ gameName }}</h2>
				<p>Module settings. Day one: dwell time only.</p>
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

			<footer class="cog-game-settings__footer">
				<button type="button" class="cog-game-settings__btn" @click="closeGameSettings">
					Close
				</button>
			</footer>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useCognitiveSettings } from '../../composables/useCognitiveSettings'
import type { CognitiveGameId } from '../../types/cognitiveGame'

const props = defineProps<{
	gameId: CognitiveGameId
}>()

const { dwellMsForGame, setGameDwellMs, closeGameSettings, games } = useCognitiveSettings()

const gameName = computed(
	() => games.value.find((game) => game.id === props.gameId)?.name ?? 'Game settings'
)

function onDwellChange(event: Event): void {
	setGameDwellMs(props.gameId, Number((event.target as HTMLInputElement).value))
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
	background: #0a0a0a;
	border: 1px solid #fff;
	color: #fff;
	padding: 20px;
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
}

.cog-game-settings__footer {
	display: flex;
	justify-content: flex-end;
}

.cog-game-settings__btn {
	border: 1px solid #fff;
	background: transparent;
	color: #fff;
	padding: 10px 16px;
	cursor: pointer;
}
</style>
