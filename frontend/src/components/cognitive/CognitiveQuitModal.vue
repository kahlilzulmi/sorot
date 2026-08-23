<template>
	<div class="cog-overlay" role="dialog" aria-modal="true" aria-label="Quit confirmation">
		<div class="cog-confirm">
			<p>Apakah Anda yakin ingin keluar dari pengujian?</p>
			<div class="cog-confirm__actions">
				<button type="button" class="cog-btn cog-btn--ghost" data-gaze-target="quit-no" @click="$emit('cancel')">
					Tidak
				</button>
				<button type="button" class="cog-btn" data-gaze-target="quit-yes" @click="$emit('confirm')">
					Ya
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
defineEmits<{
	(e: 'confirm'): void
	(e: 'cancel'): void
}>()
</script>

<style scoped>
.cog-overlay {
	position: fixed;
	inset: 0;
	z-index: 13000;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(0, 0, 0, 0.8);
	padding: 24px;
}

.cog-confirm {
	width: min(420px, 100%);
	border: 1px solid #fff;
	background: #000;
	color: #fff;
	padding: 28px 24px;
	text-align: center;
}

.cog-confirm p {
	margin: 0 0 22px;
	font-size: 16px;
	line-height: 1.45;
}

.cog-confirm__actions {
	display: flex;
	justify-content: center;
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
