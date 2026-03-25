<template>
	<div class="modal-overlay" @click.self="$emit('close')">
		<div class="modal-content">
			<div class="modal-header">
				<h2>New Video Project</h2>
				<button class="btn-close" type="button" @click="$emit('close')">x</button>
			</div>
			<div class="modal-body">
				<div class="input-group">
					<input
						ref="fileInputRef"
						type="file"
						accept="video/*"
						style="display: none"
						@change="onFileChange"
					>
					<button class="btn btn-primary btn-block" type="button" @click="fileInputRef?.click()">
						Upload Video File
					</button>
				</div>

				<div class="divider"><span>OR</span></div>

				<div class="input-group">
					<input
						v-model="youtubeUrl"
						type="text"
						placeholder="https://youtube.com/watch?v=..."
						class="input-text"
					>
				</div>

				<div class="modal-actions">
					<button class="btn btn-secondary" type="button" @click="$emit('close')">Cancel</button>
					<button class="btn btn-info" type="button" :disabled="!youtubeUrl.trim()" @click="submitYoutube">
						Use URL
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const fileInputRef = ref<HTMLInputElement | null>(null)
const youtubeUrl = ref('')

const emit = defineEmits<{
	(e: 'close'): void
	(e: 'select-file', file: File): void
	(e: 'submit-youtube', url: string): void
}>()

function onFileChange(event: Event): void {
	const input = event.target as HTMLInputElement
	const file = input.files?.[0]
	if (!file) return
	emit('select-file', file)
	input.value = ''
}

function submitYoutube(): void {
	const url = youtubeUrl.value.trim()
	if (!url) return
	emit('submit-youtube', url)
	youtubeUrl.value = ''
}
</script>
