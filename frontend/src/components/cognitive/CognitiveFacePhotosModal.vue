<template>
	<div
		class="cog-overlay"
		role="dialog"
		aria-modal="true"
		aria-labelledby="face-photos-modal-title"
		@click.self="$emit('dismiss')"
	>
		<div class="cog-confirm">
			<h2 id="face-photos-modal-title" class="cog-confirm__title">Photos required</h2>
			<p
				v-for="(paragraph, index) in paragraphs"
				:key="index"
				class="cog-confirm__body"
			>
				{{ paragraph }}
			</p>
			<div class="cog-confirm__actions">
				<button type="button" class="cog-btn cog-btn--ghost" @click="$emit('dismiss')">
					OK
				</button>
				<button type="button" class="cog-btn" @click="$emit('open-settings')">
					Open settings
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { facePhotosMissingMessage } from '../../utils/faceFamiliarityAssets'

defineEmits<{
	(e: 'dismiss'): void
	(e: 'open-settings'): void
}>()

const paragraphs = computed(() =>
	facePhotosMissingMessage()
		.split(/\n\n+/)
		.map((part) => part.trim())
		.filter(Boolean)
)
</script>

<style scoped>
.cog-overlay {
	position: fixed;
	inset: 0;
	z-index: 13200;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(0, 0, 0, 0.8);
	padding: 24px;
}

.cog-confirm {
	width: min(440px, 100%);
	border: 1px solid #fff;
	background: #000;
	color: #fff;
	padding: 28px 24px;
	text-align: center;
}

.cog-confirm__title {
	margin: 0 0 14px;
	font-size: 18px;
	font-weight: 600;
}

.cog-confirm__body {
	margin: 0 0 12px;
	font-size: 15px;
	line-height: 1.45;
	color: #e8e8e8;
}

.cog-confirm__body:last-of-type {
	margin-bottom: 22px;
}

.cog-confirm__actions {
	display: flex;
	justify-content: center;
	flex-wrap: wrap;
	gap: 12px;
}

.cog-btn {
	min-width: 96px;
	padding: 10px 16px;
	border: 1px solid #fff;
	background: #fff;
	color: #000;
	cursor: pointer;
	font-size: 14px;
}

.cog-btn--ghost {
	background: transparent;
	color: #fff;
}
</style>
