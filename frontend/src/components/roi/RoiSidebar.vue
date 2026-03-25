<template>
	<aside class="right-sidebar">
		<div class="editor-section">
			<h2>
				<SquareDashed class="header-icon" />
				ROIs
				<span v-if="currentScene" class="scene-badge">{{ currentScene.custom_name || currentScene.name }}</span>
			</h2>

			<div class="roi-list" v-if="currentScene">
				<div
					v-for="(roi, idx) in currentScene.rois"
					:key="`${roi.label}-${idx}`"
					:class="['roi-item', { active: selectedROIIdx === idx }]"
					:style="{ borderLeftColor: roi.color_tag || '#61AFEF', borderLeftWidth: '4px', borderLeftStyle: 'solid' }"
					@click="$emit('select-roi', idx)"
				>
					<div>
						<strong>{{ roi.label }}</strong><br>
						<small>{{ roi.x }}, {{ roi.y }} | {{ roi.width }}x{{ roi.height }}</small>
					</div>
					<div class="item-menu">
						<button class="btn-menu" type="button" @click.stop="toggleMenu(idx)">
							<MoreVertical class="header-icon" />
						</button>
						<div v-if="openMenuIdx === idx" class="dropdown-menu" @click.stop>
							<button class="menu-item" type="button" @click="$emit('rename-roi', idx)">
								<Edit2 class="header-icon" /> Rename
							</button>
							<button class="menu-item menu-delete" type="button" @click="$emit('delete-roi', idx)">
								<Trash2 class="header-icon" /> Delete
							</button>
						</div>
					</div>
				</div>
			</div>

			<div class="roi-controls">
				<p><em>Click and drag on video to draw ROI</em></p>
			</div>
		</div>
	</aside>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Edit2, MoreVertical, SquareDashed, Trash2 } from '@lucide/vue'

interface Roi {
	label: string
	x: number
	y: number
	width: number
	height: number
	color_tag?: string
}

interface Scene {
	name: string
	custom_name?: string
	rois: Roi[]
}

const openMenuIdx = ref<number | null>(null)

defineProps<{
	currentScene: Scene | null
	selectedROIIdx: number
}>()

defineEmits<{
	(e: 'select-roi', index: number): void
	(e: 'rename-roi', index: number): void
	(e: 'delete-roi', index: number): void
}>()

function toggleMenu(index: number): void {
	openMenuIdx.value = openMenuIdx.value === index ? null : index
}
</script>
