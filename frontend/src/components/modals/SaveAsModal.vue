<template>
	<div class="modal-overlay" @click.self="$emit('cancel')">
		<div class="modal-content modal-small">
			<div class="modal-header">
				<h2>Save Workspace As</h2>
				<button class="btn-close" type="button" @click="$emit('cancel')">x</button>
			</div>
			<div class="modal-body">
				<div class="input-group">
					<label><strong>Workspace Filename:</strong></label>
					<input
						:model-value="filename"
						type="text"
						placeholder="Enter filename..."
						class="input-text"
						@input="onInput"
						@keyup.enter="$emit('confirm')"
					>
					<small class="help-text">File will be saved in the projects folder. Extension .json is added automatically.</small>
				</div>

				<div v-if="currentWorkspaceFile" class="info-box">
					<small><strong>Current file:</strong> {{ currentWorkspaceFile }}</small>
				</div>

				<div class="modal-actions">
					<button class="btn btn-secondary" type="button" @click="$emit('cancel')">Cancel</button>
					<button class="btn btn-primary" type="button" @click="$emit('confirm')">Save As</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
defineProps<{
	filename: string
	currentWorkspaceFile: string | null
}>()

const emit = defineEmits<{
	(e: 'update:filename', value: string): void
	(e: 'confirm'): void
	(e: 'cancel'): void
}>()

function onInput(event: Event): void {
	const target = event.target as HTMLInputElement
	emit('update:filename', target.value)
}
</script>
