<template>
	<div class="modal-overlay" @click.self="$emit('close')">
		<div class="modal-content">
			<div class="modal-header">
				<h2>New Video Project</h2>
				<button class="btn-close" type="button" @click="$emit('close')">x</button>
			</div>
			<div class="modal-body">
				<input
					ref="fileInputRef"
					type="file"
					accept="video/*"
					class="upload-file-input"
					@change="onFileChange"
				>

				<div
					class="upload-dropzone"
					:class="{ 'upload-dropzone--active': isDragging }"
					role="button"
					tabindex="0"
					aria-label="Upload video file"
					@click="openFilePicker"
					@keydown.enter.prevent="openFilePicker"
					@keydown.space.prevent="openFilePicker"
					@dragenter.prevent="onDragEnter"
					@dragover.prevent="onDragOver"
					@dragleave.prevent="onDragLeave"
					@drop.prevent="onDrop"
				>
					<Upload class="upload-dropzone-icon" :size="32" :stroke-width="1.5" />
					<span class="upload-dropzone-title">Drag and drop your video here</span>
					<span class="upload-dropzone-hint">or click to browse · MP4, MOV, WebM</span>
				</div>

				<div class="divider"><span>OR</span></div>

				<div class="input-group youtube-input-group">
					<input
						v-model="youtubeUrl"
						type="url"
						placeholder="https://youtube.com/watch?v=..."
						class="input-text"
						:disabled="isProcessing"
						@paste="onYoutubePaste"
					>
					<p v-if="isProcessing" class="youtube-processing">Downloading from YouTube…</p>
					<p v-else class="youtube-hint">Paste or type a YouTube link to start automatically</p>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Upload } from '@lucide/vue'

const fileInputRef = ref<HTMLInputElement | null>(null)
const youtubeUrl = ref('')
const isDragging = ref(false)
const isProcessing = ref(false)
const lastSubmittedUrl = ref('')
let youtubeDebounceTimer: ReturnType<typeof setTimeout> | null = null

const emit = defineEmits<{
	(e: 'close'): void
	(e: 'select-file', file: File): void
	(e: 'submit-youtube', url: string): void
}>()

function isVideoFile(file: File): boolean {
	return file.type.startsWith('video/') || /\.(mp4|mov|webm|mkv|avi|m4v)$/i.test(file.name)
}

function openFilePicker(): void {
	fileInputRef.value?.click()
}

function selectFile(file: File): void {
	if (!isVideoFile(file)) return
	emit('select-file', file)
}

function onFileChange(event: Event): void {
	const input = event.target as HTMLInputElement
	const file = input.files?.[0]
	if (!file) return
	selectFile(file)
	input.value = ''
}

function onDragEnter(): void {
	isDragging.value = true
}

function onDragOver(): void {
	isDragging.value = true
}

function onDragLeave(): void {
	isDragging.value = false
}

function onDrop(event: DragEvent): void {
	isDragging.value = false
	const file = event.dataTransfer?.files?.[0]
	if (!file) return
	selectFile(file)
}

function isYoutubeUrl(url: string): boolean {
	const trimmed = url.trim()
	if (!trimmed) return false
	try {
		const parsed = new URL(trimmed)
		const host = parsed.hostname.replace(/^www\./, '')
		if (host === 'youtu.be') return parsed.pathname.length > 1
		if (host === 'youtube.com' || host === 'm.youtube.com') {
			return parsed.pathname === '/watch' && parsed.searchParams.has('v')
		}
		return false
	} catch {
		return false
	}
}

function submitYoutubeIfValid(url: string): void {
	const trimmed = url.trim()
	if (!trimmed || !isYoutubeUrl(trimmed) || isProcessing.value) return
	if (trimmed === lastSubmittedUrl.value) return
	lastSubmittedUrl.value = trimmed
	isProcessing.value = true
	emit('submit-youtube', trimmed)
	youtubeUrl.value = ''
}

function resetYoutubeAttempt(): void {
	isProcessing.value = false
	lastSubmittedUrl.value = ''
}

defineExpose({ resetYoutubeAttempt })

function onYoutubePaste(event: ClipboardEvent): void {
	const pasted = event.clipboardData?.getData('text')?.trim() ?? ''
	if (!isYoutubeUrl(pasted)) return
	event.preventDefault()
	youtubeUrl.value = pasted
	submitYoutubeIfValid(pasted)
}

watch(youtubeUrl, (value) => {
	if (youtubeDebounceTimer) clearTimeout(youtubeDebounceTimer)
	if (!value.trim()) return
	youtubeDebounceTimer = setTimeout(() => {
		submitYoutubeIfValid(value)
	}, 600)
})
</script>

<style scoped>
.upload-file-input {
	display: none;
}

.upload-dropzone {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 8px;
	min-height: 132px;
	padding: 24px 20px;
	margin-bottom: 20px;
	border: 2px dashed var(--color-border);
	border-radius: 10px;
	background: var(--color-background);
	color: var(--color-text);
	cursor: pointer;
	transition:
		border-color 0.2s ease,
		background-color 0.2s ease,
		box-shadow 0.2s ease;
}

.upload-dropzone:hover,
.upload-dropzone:focus-visible {
	border-color: var(--color-accent);
	background: rgba(6, 158, 189, 0.06);
	box-shadow: 0 0 0 1px rgba(6, 158, 189, 0.15);
	outline: none;
}

.upload-dropzone--active {
	border-color: var(--color-accent);
	background: rgba(6, 158, 189, 0.12);
	box-shadow: 0 0 0 2px rgba(6, 158, 189, 0.2);
}

.upload-dropzone-icon {
	color: var(--color-accent);
	flex-shrink: 0;
	transition: transform 0.2s ease;
}

.upload-dropzone:hover .upload-dropzone-icon,
.upload-dropzone--active .upload-dropzone-icon {
	transform: translateY(-2px);
}

.upload-dropzone-title {
	font-size: 14px;
	font-weight: 500;
	color: var(--color-text);
}

.upload-dropzone-hint {
	font-size: 12px;
	color: var(--color-text-dim);
}

.youtube-input-group {
	margin-bottom: 0;
}

.youtube-hint {
	margin: 8px 0 0;
	font-size: 12px;
	color: var(--color-text-dim);
}

.youtube-processing {
	margin: 8px 0 0;
	font-size: 12px;
	color: var(--color-accent);
}
</style>
