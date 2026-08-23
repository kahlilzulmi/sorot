<template>
	<div
		class="cog-overlay"
		role="dialog"
		aria-modal="true"
		aria-label="Cognitive game settings"
		@pointerdown.self="closeColorPopovers"
	>
		<div class="cog-panel">
			<header class="cog-panel__header">
				<h2>Game settings</h2>
				<p>Hotkey <kbd>s</kbd> toggles this panel. Changes apply immediately.</p>
			</header>

			<section class="cog-section">
				<h3>Live preview</h3>
				<div class="cog-preview-stage" aria-hidden="true">
					<div class="cog-preview-stage__grid" />
					<div class="cog-preview-stage__target" />
					<DwellCursor
						embedded
						:x="0"
						:y="0"
						:cursor-color="cursor.cursorColor"
						:dwell-effect-color="cursor.dwellEffectColor"
						:shape="cursor.shape"
						:dwell-effect="cursor.dwellEffect"
						:progress="previewProgress"
						:dwelling="previewDwelling"
					/>
					<p
						v-if="cursor.shape === 'transparent' && cursor.dwellEffect === 'transparent'"
						class="cog-preview-stage__empty"
					>
						Invisible pointer + dwell
					</p>
				</div>
				<p class="cog-hint">Animated sample dwell — updates as you change shape, effect, and colors.</p>
			</section>

			<section class="cog-section">
				<h3>Cursor shape</h3>
				<div class="cog-shape-grid">
					<button
						v-for="option in shapeOptions"
						:key="option.id"
						type="button"
						class="cog-shape-btn"
						:class="{ active: cursor.shape === option.id }"
						:data-gaze-target="`settings-shape-${option.id}`"
						@click="setCursorShape(option.id)"
					>
						<span
							class="cog-shape-preview"
							:class="`preview--${option.id}`"
							:style="{ color: cursor.cursorColor }"
						/>
						{{ option.label }}
					</button>
				</div>
				<div class="cog-field cog-field--inline">
					<span>Cursor color</span>
					<div
						ref="cursorColorFieldRef"
						class="cog-color-field"
						:class="{ 'cog-color-field--disabled': cursor.shape === 'transparent' }"
					>
						<button
							type="button"
							class="cog-color-swatch"
							:style="{ background: cursor.cursorColor }"
							:disabled="cursor.shape === 'transparent'"
							:aria-expanded="openColorPopover === 'cursor'"
							aria-label="Cursor color"
							@click.stop="toggleColorPopover('cursor')"
						/>
						<div
							v-if="openColorPopover === 'cursor'"
							class="cog-color-popover"
						>
							<input
								:value="cursor.cursorColor"
								class="cog-color"
								type="color"
								@pointerdown.stop
								@input="onCursorColorInput"
							>
							<input
								:value="cursorHexDraft"
								class="cog-color-popover__value"
								type="text"
								spellcheck="false"
								autocomplete="off"
								aria-label="Cursor color hex"
								maxlength="7"
								@pointerdown.stop
								@input="onCursorHexInput"
								@change="onCursorHexCommit"
								@keydown.enter.prevent="onCursorHexCommit"
							>
						</div>
					</div>
				</div>
				<p v-if="cursor.shape === 'transparent'" class="cog-hint">
					Pointer glyph is hidden — cursor color does not apply.
				</p>
			</section>

			<section class="cog-section">
				<h3>Dwell effect</h3>
				<div class="cog-shape-grid">
					<button
						v-for="option in dwellEffectOptions"
						:key="option.id"
						type="button"
						class="cog-shape-btn"
						:class="{ active: cursor.dwellEffect === option.id }"
						:data-gaze-target="`settings-dwell-${option.id}`"
						@click="setDwellEffect(option.id)"
					>
						<span
							class="cog-shape-preview"
							:class="`preview--${option.id}`"
							:style="{ color: cursor.dwellEffectColor }"
						/>
						{{ option.label }}
					</button>
				</div>
				<div class="cog-field cog-field--inline">
					<span>Dwell effect color</span>
					<div
						ref="dwellColorFieldRef"
						class="cog-color-field"
						:class="{ 'cog-color-field--disabled': cursor.dwellEffect === 'transparent' }"
					>
						<button
							type="button"
							class="cog-color-swatch"
							:style="{ background: cursor.dwellEffectColor }"
							:disabled="cursor.dwellEffect === 'transparent'"
							:aria-expanded="openColorPopover === 'dwell'"
							aria-label="Dwell effect color"
							@click.stop="toggleColorPopover('dwell')"
						/>
						<div
							v-if="openColorPopover === 'dwell'"
							class="cog-color-popover"
						>
							<input
								:value="cursor.dwellEffectColor"
								class="cog-color"
								type="color"
								@pointerdown.stop
								@input="onDwellEffectColorInput"
							>
							<input
								:value="dwellHexDraft"
								class="cog-color-popover__value"
								type="text"
								spellcheck="false"
								autocomplete="off"
								aria-label="Dwell effect color hex"
								maxlength="7"
								@pointerdown.stop
								@input="onDwellHexInput"
								@change="onDwellHexCommit"
								@keydown.enter.prevent="onDwellHexCommit"
							>
						</div>
					</div>
				</div>
				<p v-if="cursor.dwellEffect === 'transparent'" class="cog-hint">
					No dwell progress UI — effect color does not apply.
				</p>
				<p v-else class="cog-hint">Shown while gaze dwells on a target — separate from the pointer glyph.</p>
			</section>

			<footer class="cog-panel__footer">
				<button type="button" class="cog-btn" data-gaze-target="settings-close" @click="$emit('close')">
					Close
				</button>
			</footer>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import DwellCursor from './DwellCursor.vue'
import { useCognitiveSettings } from '../../composables/useCognitiveSettings'
import type { DwellEffectStyle, GazeCursorShape } from '../../types/cognitiveGame'

defineEmits<{
	(e: 'close'): void
}>()

const {
	cursor,
	setCursorShape,
	setDwellEffect,
	setCursorColor,
	setDwellEffectColor
} = useCognitiveSettings()

type ColorPopoverId = 'cursor' | 'dwell'

const openColorPopover = ref<ColorPopoverId | null>(null)
const cursorColorFieldRef = ref<HTMLElement | null>(null)
const dwellColorFieldRef = ref<HTMLElement | null>(null)
const cursorHexDraft = ref(cursor.cursorColor)
const dwellHexDraft = ref(cursor.dwellEffectColor)

const shapeOptions: { id: GazeCursorShape; label: string }[] = [
	{ id: 'transparent', label: 'Transparent' },
	{ id: 'arrow', label: 'Arrow' },
	{ id: 'dot', label: 'Dot' }
]

const dwellEffectOptions: { id: DwellEffectStyle; label: string }[] = [
	{ id: 'transparent', label: 'Transparent' },
	{ id: 'ring', label: 'Ring' },
	{ id: 'pie', label: 'Pie fill' }
]

const previewProgress = ref(0)
const previewDwelling = computed(
	() => cursor.dwellEffect !== 'transparent' || cursor.shape !== 'transparent'
)

const PREVIEW_CYCLE_MS = 2000
let previewRaf = 0
let previewStartedAt = 0

function tickPreview(now: number): void {
	if (!previewStartedAt) previewStartedAt = now
	const elapsed = (now - previewStartedAt) % PREVIEW_CYCLE_MS
	const fillMs = PREVIEW_CYCLE_MS * 0.72
	const pauseMs = PREVIEW_CYCLE_MS * 0.12
	if (elapsed <= fillMs) {
		previewProgress.value = elapsed / fillMs
	} else if (elapsed <= fillMs + pauseMs) {
		previewProgress.value = 1
	} else {
		previewProgress.value = 0
	}
	previewRaf = requestAnimationFrame(tickPreview)
}

function closeColorPopovers(): void {
	openColorPopover.value = null
}

function toggleColorPopover(id: ColorPopoverId): void {
	if (openColorPopover.value === id) {
		openColorPopover.value = null
		return
	}
	if (id === 'cursor') cursorHexDraft.value = cursor.cursorColor
	else dwellHexDraft.value = cursor.dwellEffectColor
	openColorPopover.value = id
}

function normalizeHexColor(raw: string): string | null {
	const trimmed = raw.trim()
	const withHash = trimmed.startsWith('#') ? trimmed : `#${trimmed}`
	const short = /^#([0-9a-fA-F]{3})$/.exec(withHash)
	if (short) {
		const [r, g, b] = short[1].split('')
		return `#${r}${r}${g}${g}${b}${b}`.toLowerCase()
	}
	if (/^#[0-9a-fA-F]{6}$/.test(withHash)) return withHash.toLowerCase()
	return null
}

function pointInRect(x: number, y: number, rect: DOMRect | undefined): boolean {
	if (!rect) return false
	return x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom
}

function onDocumentPointerDown(event: PointerEvent): void {
	if (!openColorPopover.value) return
	const field =
		openColorPopover.value === 'cursor' ? cursorColorFieldRef.value : dwellColorFieldRef.value
	if (!field) {
		closeColorPopovers()
		return
	}
	const swatch = field.querySelector('.cog-color-swatch') as HTMLElement | null
	const popover = field.querySelector('.cog-color-popover') as HTMLElement | null
	const { clientX: x, clientY: y } = event
	if (pointInRect(x, y, swatch?.getBoundingClientRect())) return
	if (pointInRect(x, y, popover?.getBoundingClientRect())) return
	closeColorPopovers()
}

function onEscape(event: KeyboardEvent): void {
	if (event.key !== 'Escape') return
	if (openColorPopover.value) {
		event.stopPropagation()
		closeColorPopovers()
	}
}

function onCursorColorInput(event: Event): void {
	const value = (event.target as HTMLInputElement).value
	setCursorColor(value)
	cursorHexDraft.value = value
}

function onDwellEffectColorInput(event: Event): void {
	const value = (event.target as HTMLInputElement).value
	setDwellEffectColor(value)
	dwellHexDraft.value = value
}

function onCursorHexInput(event: Event): void {
	const raw = (event.target as HTMLInputElement).value
	cursorHexDraft.value = raw
	const normalized = normalizeHexColor(raw)
	if (normalized) setCursorColor(normalized)
}

function onDwellHexInput(event: Event): void {
	const raw = (event.target as HTMLInputElement).value
	dwellHexDraft.value = raw
	const normalized = normalizeHexColor(raw)
	if (normalized) setDwellEffectColor(normalized)
}

function onCursorHexCommit(): void {
	const normalized = normalizeHexColor(cursorHexDraft.value)
	if (normalized) {
		setCursorColor(normalized)
		cursorHexDraft.value = normalized
		return
	}
	cursorHexDraft.value = cursor.cursorColor
}

function onDwellHexCommit(): void {
	const normalized = normalizeHexColor(dwellHexDraft.value)
	if (normalized) {
		setDwellEffectColor(normalized)
		dwellHexDraft.value = normalized
		return
	}
	dwellHexDraft.value = cursor.dwellEffectColor
}

onMounted(() => {
	previewRaf = requestAnimationFrame(tickPreview)
	document.addEventListener('pointerdown', onDocumentPointerDown, true)
	window.addEventListener('keydown', onEscape, true)
})

onUnmounted(() => {
	cancelAnimationFrame(previewRaf)
	document.removeEventListener('pointerdown', onDocumentPointerDown, true)
	window.removeEventListener('keydown', onEscape, true)
	closeColorPopovers()
})
</script>

<style scoped>
.cog-overlay {
	position: fixed;
	inset: 0;
	z-index: 13000;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(0, 0, 0, 0.72);
	padding: 24px;
}

.cog-panel {
	width: min(520px, 100%);
	max-height: 90vh;
	overflow: auto;
	background: #0a0a0a;
	border: 1px solid #fff;
	color: #fff;
	padding: 20px;
}

.cog-panel__header h2 {
	margin: 0 0 6px;
	font-size: 20px;
	font-weight: 600;
}

.cog-panel__header p {
	margin: 0 0 16px;
	color: #aaa;
	font-size: 13px;
}

.cog-section {
	margin-bottom: 18px;
}

.cog-section h3 {
	margin: 0 0 10px;
	font-size: 13px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	color: #ccc;
}

.cog-preview-stage {
	position: relative;
	height: 132px;
	overflow: hidden;
	border: 1px solid #444;
	border-radius: 8px;
	background: radial-gradient(circle at center, #1a1a1a 0%, #0d0d0d 70%);
}

.cog-preview-stage__grid {
	position: absolute;
	inset: 0;
	opacity: 0.35;
	background-image:
		linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
		linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
	background-size: 24px 24px;
	background-position: center;
}

.cog-preview-stage__target {
	position: absolute;
	top: 50%;
	left: 50%;
	width: 56px;
	height: 56px;
	transform: translate(-50%, -50%);
	border: 1px dashed rgba(255, 255, 255, 0.28);
	border-radius: 50%;
	box-shadow: inset 0 0 18px rgba(255, 255, 255, 0.04);
}

.cog-preview-stage__empty {
	position: absolute;
	left: 50%;
	bottom: 12px;
	margin: 0;
	transform: translateX(-50%);
	font-size: 11px;
	color: #777;
	white-space: nowrap;
}

.cog-shape-grid {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 8px;
}

.cog-shape-btn {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 10px 12px;
	border: 1px solid #555;
	background: #111;
	color: #fff;
	cursor: pointer;
	text-align: left;
}

.cog-shape-btn.active {
	border-color: #fff;
	background: #1a1a1a;
}

.cog-shape-preview {
	width: 18px;
	height: 18px;
	flex-shrink: 0;
}

.preview--arrow {
	clip-path: polygon(15% 10%, 85% 50%, 40% 58%, 28% 90%);
	background: currentColor;
}

.preview--dot {
	border-radius: 50%;
	background: currentColor;
}

.preview--transparent {
	border-radius: 50%;
	border: 1px dashed currentColor;
	background: transparent;
	opacity: 0.55;
}

.preview--ring {
	border-radius: 50%;
	border: 2px solid currentColor;
}

.preview--pie {
	border-radius: 50%;
	background: conic-gradient(currentColor 120deg, transparent 0);
}

.cog-field {
	display: flex;
	flex-direction: column;
	gap: 6px;
	font-size: 13px;
	color: #bbb;
}

.cog-field--inline {
	margin-top: 10px;
}

.cog-color-field {
	position: relative;
	display: inline-block;
	width: fit-content;
	max-width: max-content;
	vertical-align: top;
}

.cog-color-field--disabled {
	opacity: 0.45;
}

.cog-color-swatch {
	display: block;
	width: 44px;
	height: 32px;
	padding: 0;
	border: 1px solid #777;
	border-radius: 4px;
	cursor: pointer;
	box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.35);
}

.cog-color-swatch:disabled {
	cursor: not-allowed;
}

.cog-color-popover {
	position: absolute;
	top: calc(100% + 8px);
	left: 0;
	z-index: 5;
	display: inline-flex;
	align-items: center;
	gap: 10px;
	width: max-content;
	max-width: max-content;
	padding: 10px 12px;
	background: #111;
	border: 1px solid #fff;
	box-shadow: 0 12px 28px rgba(0, 0, 0, 0.55);
}

.cog-color-popover__value {
	box-sizing: border-box;
	width: 5.75rem;
	min-width: 5.75rem;
	padding: 4px 6px;
	border: 1px solid #555;
	border-radius: 3px;
	background: #0a0a0a;
	font-size: 12px;
	font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
	color: #eee;
}

.cog-color-popover__value:focus {
	outline: none;
	border-color: #fff;
}

/* Keep native color control tiny — Chromium expands hit area if width is fluid. */
.cog-color {
	box-sizing: border-box;
	width: 36px;
	min-width: 36px;
	max-width: 36px;
	height: 28px;
	padding: 0;
	border: 1px solid #555;
	background: #0a0a0a;
	cursor: pointer;
	appearance: none;
	-webkit-appearance: none;
}

.cog-color::-webkit-color-swatch-wrapper {
	padding: 0;
}

.cog-color::-webkit-color-swatch {
	border: none;
	border-radius: 2px;
}

.cog-hint {
	margin: 8px 0 0;
	font-size: 12px;
	color: #888;
}

.cog-btn {
	border: 1px solid #fff;
	background: transparent;
	color: #fff;
	padding: 10px 16px;
	cursor: pointer;
}

.cog-panel__footer {
	display: flex;
	justify-content: flex-end;
	margin-top: 8px;
}

kbd {
	padding: 1px 5px;
	border: 1px solid #666;
	border-radius: 3px;
	font-size: 12px;
}
</style>
