<template>
	<div class="cog-hub">
		<header class="cog-hub__header">
			<h1>Cognitive Games</h1>
			<p>
				Check games to include, drag the handle or use ↑↓ to reorder, then play the playlist
				or open a single module. Mouse only on this screen — dwell starts in-game.
			</p>
		</header>

		<section class="cog-hub__actions">
			<button
				type="button"
				class="btn btn-primary"
				:disabled="enabledCount === 0"
				@click="$emit('play-order')"
			>
				Play in order ({{ enabledCount }})
			</button>
			<button type="button" class="btn btn-secondary" @click="$emit('open-settings')">
				Cursor settings (S)
			</button>
		</section>

		<TransitionGroup
			name="cog-reorder"
			tag="section"
			class="cog-hub__list"
			:class="{ 'cog-hub__list--dragging': Boolean(dragId) }"
			@dragover.prevent
		>
			<article
				v-for="(game, index) in games"
				:key="game.id"
				class="cog-game-card"
				:class="{
					'cog-game-card--disabled': !isGameEnabled(game.id),
					'cog-game-card--dragging': dragId === game.id,
					'cog-game-card--drop-before': dropHint?.id === game.id && dropHint.edge === 'before',
					'cog-game-card--drop-after': dropHint?.id === game.id && dropHint.edge === 'after'
				}"
				@dragover.prevent="onDragOver(game.id, $event)"
				@drop.prevent="onDrop"
				@dragleave="onDragLeave(game.id, $event)"
			>
				<div class="cog-game-card__reorder">
					<button
						type="button"
						class="btn btn-secondary btn-sm cog-game-card__move-btn"
						:disabled="index === 0 || Boolean(dragId)"
						title="Move up"
						@click="moveGame(game.id, -1)"
					>
						<ChevronUp :size="16" />
					</button>
					<button
						type="button"
						class="cog-game-card__grip"
						draggable="true"
						title="Drag to reorder"
						aria-label="Drag to reorder"
						@dragstart="onDragStart(game.id, $event)"
						@dragend="onDragEnd"
					>
						<GripVertical :size="18" />
					</button>
					<button
						type="button"
						class="btn btn-secondary btn-sm cog-game-card__move-btn"
						:disabled="index === games.length - 1 || Boolean(dragId)"
						title="Move down"
						@click="moveGame(game.id, 1)"
					>
						<ChevronDown :size="16" />
					</button>
				</div>

				<label class="cog-game-card__check">
					<input
						type="checkbox"
						:checked="isGameEnabled(game.id)"
						:disabled="isGameEnabled(game.id) && enabledCount <= 1"
						@change="toggleGameEnabled(game.id)"
					>
					<span class="cog-game-card__index">{{ index + 1 }}</span>
				</label>

				<div class="cog-game-card__body">
					<strong>{{ game.name }}</strong>
					<span class="cog-game-card__desc">{{ game.description }}</span>
					<label class="cog-game-card__dwell">
						<span>Dwell</span>
						<input
							:value="dwellMsForGame(game.id)"
							class="cog-game-card__dwell-input"
							type="number"
							min="200"
							step="100"
							title="Dwell time in milliseconds"
							@change="onCardDwellChange(game.id, $event)"
							@click.stop
						>
						<span>ms</span>
					</label>
				</div>

				<div class="cog-game-card__controls">
					<button
						type="button"
						class="btn btn-secondary btn-sm cog-game-card__gear"
						title="Game settings"
						aria-label="Game settings"
						@click="openGameSettings(game.id)"
					>
						<Settings :size="16" />
					</button>
					<button
						type="button"
						class="btn btn-info btn-sm"
						:disabled="!isGameEnabled(game.id)"
						@click="$emit('play-game', game.id)"
					>
						Play
					</button>
				</div>
			</article>
		</TransitionGroup>

		<CognitiveGameSettingsPanel
			v-if="gameSettingsOpenId"
			:game-id="gameSettingsOpenId"
		/>

		<p class="cog-hub__hint">Operator: <kbd>q</kbd> leave mode · <kbd>s</kbd> cursor settings</p>
	</div>
</template>

<script setup lang="ts">
import { ref, TransitionGroup } from 'vue'
import { ChevronDown, ChevronUp, GripVertical, Settings } from '@lucide/vue'
import CognitiveGameSettingsPanel from './CognitiveGameSettingsPanel.vue'
import { useCognitiveSettings } from '../../composables/useCognitiveSettings'
import type { CognitiveGameId } from '../../types/cognitiveGame'

defineEmits<{
	(e: 'play-order'): void
	(e: 'play-game', id: CognitiveGameId): void
	(e: 'open-settings'): void
}>()

const {
	games,
	enabledCount,
	isGameEnabled,
	toggleGameEnabled,
	moveGame,
	moveGameToIndex,
	dwellMsForGame,
	setGameDwellMs,
	openGameSettings,
	gameSettingsOpenId
} = useCognitiveSettings()

const dragId = ref<CognitiveGameId | null>(null)
const dropHint = ref<{ id: CognitiveGameId; edge: 'before' | 'after' } | null>(null)
let dragGhostEl: HTMLElement | null = null
let lastInsertIndex = -1

function onCardDwellChange(id: CognitiveGameId, event: Event): void {
	setGameDwellMs(id, Number((event.target as HTMLInputElement).value))
}

function clearDragState(): void {
	dragId.value = null
	dropHint.value = null
	lastInsertIndex = -1
	if (dragGhostEl?.parentNode) dragGhostEl.parentNode.removeChild(dragGhostEl)
	dragGhostEl = null
}

function onDragStart(id: CognitiveGameId, event: DragEvent): void {
	dragId.value = id
	dropHint.value = null
	lastInsertIndex = games.value.findIndex((game) => game.id === id)
	event.dataTransfer?.setData('text/plain', id)
	if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'

	const card = (event.currentTarget as HTMLElement | null)?.closest(
		'.cog-game-card'
	) as HTMLElement | null
	if (card && event.dataTransfer) {
		const ghost = card.cloneNode(true) as HTMLElement
		ghost.classList.add('cog-game-card--drag-ghost')
		ghost.style.width = `${card.getBoundingClientRect().width}px`
		ghost.style.position = 'fixed'
		ghost.style.top = '-1200px'
		ghost.style.left = '-1200px'
		ghost.style.pointerEvents = 'none'
		document.body.appendChild(ghost)
		dragGhostEl = ghost
		const rect = card.getBoundingClientRect()
		event.dataTransfer.setDragImage(
			ghost,
			event.clientX - rect.left,
			event.clientY - rect.top
		)
	}
}

function onDragOver(id: CognitiveGameId, event: DragEvent): void {
	if (!dragId.value || dragId.value === id) {
		dropHint.value = null
		return
	}
	if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'

	const target = event.currentTarget as HTMLElement
	const rect = target.getBoundingClientRect()
	const edge: 'before' | 'after' =
		event.clientY < rect.top + rect.height / 2 ? 'before' : 'after'
	dropHint.value = { id, edge }

	const order = games.value.map((game) => game.id)
	const fromIndex = order.indexOf(dragId.value)
	const overIndex = order.indexOf(id)
	if (fromIndex < 0 || overIndex < 0) return

	let insertIndex = edge === 'before' ? overIndex : overIndex + 1
	if (fromIndex < insertIndex) insertIndex -= 1
	if (insertIndex === fromIndex || insertIndex === lastInsertIndex) return

	lastInsertIndex = insertIndex
	moveGameToIndex(dragId.value, insertIndex)
}

function onDragLeave(id: CognitiveGameId, event: DragEvent): void {
	const related = event.relatedTarget as Node | null
	const current = event.currentTarget as HTMLElement
	if (related && current.contains(related)) return
	if (dropHint.value?.id === id) dropHint.value = null
}

function onDrop(event: DragEvent): void {
	event.preventDefault()
	clearDragState()
}

function onDragEnd(): void {
	clearDragState()
}
</script>

<style scoped>
.cog-hub {
	width: 100%;
	max-width: 1100px;
	margin: 0 auto;
	padding: 8px 4px 32px;
	color: var(--color-text);
}

.cog-hub__header h1 {
	margin: 0 0 8px;
	font-size: 24px;
	font-weight: 600;
	color: var(--color-accent);
}

.cog-hub__header p {
	margin: 0;
	color: var(--color-text-dim);
	max-width: 48rem;
	line-height: 1.5;
	font-size: 14px;
}

.cog-hub__actions {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	margin: 20px 0 16px;
}

.cog-hub__list {
	display: flex;
	flex-direction: column;
	gap: 10px;
	position: relative;
}

.cog-hub__list--dragging {
	cursor: grabbing;
}

.cog-hub__list--dragging .cog-game-card:not(.cog-game-card--dragging) {
	transition: transform 0.28s cubic-bezier(0.2, 0.8, 0.2, 1), border-color 0.15s ease,
		box-shadow 0.15s ease, opacity 0.15s ease;
}

.cog-reorder-move {
	transition: transform 0.32s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.cog-game-card {
	position: relative;
	display: grid;
	grid-template-columns: auto auto 1fr auto;
	gap: 12px;
	align-items: center;
	padding: 14px 16px;
	background: var(--color-background);
	border: 1px solid var(--color-border);
	border-radius: 8px;
	box-shadow: none;
	transition: border-color 0.15s ease, opacity 0.18s ease, transform 0.18s ease,
		box-shadow 0.18s ease;
}

.cog-game-card--disabled {
	opacity: 0.55;
}

.cog-game-card--dragging {
	opacity: 0.42;
	transform: scale(0.985);
	border-style: dashed;
	border-color: var(--color-accent);
	box-shadow: inset 0 0 0 1px rgba(56, 189, 248, 0.15);
}

.cog-game-card--drop-before::before,
.cog-game-card--drop-after::after {
	content: '';
	position: absolute;
	left: 8px;
	right: 8px;
	height: 3px;
	border-radius: 999px;
	background: var(--color-accent);
	box-shadow: 0 0 10px rgba(56, 189, 248, 0.55);
	pointer-events: none;
	z-index: 2;
}

.cog-game-card--drop-before::before {
	top: -7px;
}

.cog-game-card--drop-after::after {
	bottom: -7px;
}

.cog-game-card__reorder {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 4px;
}

.cog-game-card__move-btn {
	width: 32px;
	height: 24px;
	padding: 0;
	display: inline-flex;
	align-items: center;
	justify-content: center;
}

.cog-game-card__grip {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 32px;
	height: 32px;
	padding: 0;
	border: 1px solid var(--color-border);
	border-radius: 6px;
	background: var(--color-background);
	color: var(--color-text-dim);
	cursor: grab;
	transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
}

.cog-game-card__grip:hover {
	border-color: var(--color-accent);
	color: var(--color-accent);
}

.cog-game-card__grip:active,
.cog-hub__list--dragging .cog-game-card__grip {
	cursor: grabbing;
}

.cog-game-card__check {
	display: inline-flex;
	align-items: center;
	gap: 8px;
	cursor: pointer;
	user-select: none;
}

.cog-game-card__check input {
	width: 16px;
	height: 16px;
	accent-color: var(--color-accent);
}

.cog-game-card__index {
	font-size: 12px;
	color: var(--color-text-dim);
	min-width: 1.25rem;
}

.cog-game-card__body {
	display: flex;
	flex-direction: column;
	gap: 4px;
	min-width: 0;
}

.cog-game-card__body strong {
	font-size: 15px;
	color: var(--color-text);
}

.cog-game-card__desc {
	font-size: 13px;
	color: var(--color-text-dim);
	line-height: 1.4;
}

.cog-game-card__dwell {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	margin-top: 4px;
	font-size: 12px;
	color: var(--color-text-dim);
}

.cog-game-card__dwell-input {
	width: 72px;
	padding: 4px 6px;
	border: 1px solid var(--color-border);
	border-radius: 4px;
	background: var(--color-background);
	color: var(--color-text);
	font-size: 12px;
}

.cog-game-card__controls {
	display: flex;
	align-items: center;
	gap: 8px;
}

.cog-game-card__gear {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 32px;
	height: 32px;
	padding: 0;
}

.cog-hub__hint {
	margin-top: 20px;
	color: var(--color-text-dim);
	font-size: 12px;
}

kbd {
	padding: 1px 5px;
	border: 1px solid var(--color-border);
	border-radius: 3px;
	background: var(--color-background);
}

@media (max-width: 720px) {
	.cog-game-card {
		grid-template-columns: auto auto 1fr;
	}

	.cog-game-card__controls {
		grid-column: 1 / -1;
		justify-content: flex-end;
	}
}
</style>

<!-- Drag ghost is appended to document.body (outside scoped root). -->
<style>
.cog-game-card--drag-ghost {
	display: grid;
	grid-template-columns: auto auto 1fr auto;
	gap: 12px;
	align-items: center;
	padding: 14px 16px;
	background: #1e2127;
	border: 1px solid #38bdf8;
	border-radius: 8px;
	box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(56, 189, 248, 0.25);
	opacity: 0.92;
	transform: scale(1.02) rotate(0.6deg);
	color: #e5e7eb;
	z-index: 20000;
}
</style>
