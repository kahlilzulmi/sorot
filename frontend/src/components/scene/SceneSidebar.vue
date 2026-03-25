<template>
	<aside class="left-sidebar">
		<div class="editor-section">
			<h2>
				<Clapperboard class="header-icon" />
				Scenes
			</h2>

			<div class="scene-list">
				<div
					v-for="(scene, idx) in scenes"
					:key="`${scene.name}-${idx}`"
					:class="['scene-item', { active: activeSceneIdx === idx }]"
					@click="$emit('select-scene', idx)"
				>
					<div class="scene-header">
						<div class="scene-title">
							<strong>{{ scene.name }}</strong>
							<span v-if="scene.custom_name"> - {{ scene.custom_name }}</span>
						</div>
					</div>

					<div class="scene-body">
						<div class="scene-thumbnail" v-if="videoInfo">
							<img
								:src="thumbnailUrl(scene.start_frame)"
								:alt="`Scene ${idx + 1} thumbnail`"
							>
						</div>

						<div class="scene-info">
							<div class="scene-details">
								<small><strong>Frame:</strong> {{ scene.start_frame }} - {{ scene.end_frame }}</small>
								<small><strong>ROIs:</strong> {{ scene.rois.length }}</small>
							</div>
						</div>
					</div>

					<div class="item-menu">
						<button class="btn-menu" type="button" @click.stop="toggleMenu(idx)">
							<MoreVertical class="header-icon" />
						</button>
						<div v-if="openMenuIdx === idx" class="dropdown-menu" @click.stop>
							<button class="menu-item" type="button" @click="$emit('rename-scene', idx)">
								<Edit2 class="header-icon" /> Rename
							</button>
							<button class="menu-item menu-delete" type="button" @click="$emit('delete-scene', idx)">
								<Trash2 class="header-icon" /> Delete
							</button>
						</div>
					</div>
				</div>
			</div>

			<div class="scene-controls">
				<button class="btn btn-secondary btn-sm" type="button" @click="$emit('add-scene')">
					<Plus class="header-icon" /> Add Scene
				</button>
			</div>
		</div>
	</aside>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Clapperboard, Edit2, MoreVertical, Plus, Trash2 } from '@lucide/vue'

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
	start_frame: number
	end_frame: number
	rois: Roi[]
}

interface VideoInfo {
	filename: string
}

const openMenuIdx = ref<number | null>(null)

const props = defineProps<{
	scenes: Scene[]
	activeSceneIdx: number
	videoInfo: VideoInfo | null
}>()

defineEmits<{
	(e: 'select-scene', index: number): void
	(e: 'add-scene'): void
	(e: 'rename-scene', index: number): void
	(e: 'delete-scene', index: number): void
}>()

function toggleMenu(index: number): void {
	openMenuIdx.value = openMenuIdx.value === index ? null : index
}

function thumbnailUrl(frame: number): string {
	if (!props.videoInfo) return ''
	return `/api/thumbnail?frame=${frame}`
}
</script>
