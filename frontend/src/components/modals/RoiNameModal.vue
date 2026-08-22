<template>
	<div class="modal-overlay" @click.self="$emit('cancel')">
		<div class="modal-content modal-small">
			<div class="modal-header">
				<h2>Name this ROI</h2>
				<button class="btn-close" type="button" @click="$emit('cancel')">x</button>
			</div>
			<div class="modal-body">
				<div class="input-group">
					<label><strong>ROI Label:</strong></label>
					<input
						:model-value="label"
						type="text"
						placeholder="Enter ROI name..."
						class="input-text"
						@input="onInput"
						@keyup.enter="$emit('confirm')"
					>
				</div>
				<div v-if="bounds" class="roi-info">
					<small>
						Position: {{ bounds.x }}, {{ bounds.y }} |
						Size: {{ bounds.width }}x{{ bounds.height }}
					</small>
				</div>
			</div>
			<div class="modal-actions">
				<button class="btn btn-primary" type="button" @click="$emit('confirm')">Save ROI</button>
				<button class="btn btn-secondary" type="button" @click="$emit('cancel')">Cancel</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { RoiBounds } from '../../composables/useRoiEditor'

defineProps<{
	label: string
	bounds: RoiBounds | null
}>()

const emit = defineEmits<{
	(e: 'update:label', value: string): void
	(e: 'confirm'): void
	(e: 'cancel'): void
}>()

function onInput(event: Event): void {
	const target = event.target as HTMLInputElement
	emit('update:label', target.value)
}
</script>
