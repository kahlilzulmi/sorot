<template>
	<div class="flex min-h-screen flex-col bg-slate-950 text-slate-200 lg:flex-row">
		<ControlSidebar
			:gaze-extraction-enabled="gazeExtractionEnabled"
			:gaze-extraction-active="gazeExtractionActive"
			:gaze-extraction-validation="gazeExtractionValidation"
			@video-selected="onVideoSelected"
			@update:gaze-extraction-enabled="gazeExtractionEnabled = $event"
			@update:gaze-extraction-active="gazeExtractionActive = $event"
			@update:gaze-extraction-validation="gazeExtractionValidation = $event"
		/>

		<main class="flex min-h-0 min-w-0 flex-1 flex-col">
			<header class="flex shrink-0 items-center justify-between border-b border-slate-800 px-4 py-3 lg:hidden">
				<span class="font-semibold text-cyan-400">Sorot</span>
				<span v-if="videoFileName" class="truncate text-xs text-slate-500">{{ videoFileName }}</span>
			</header>

			<p
				v-if="extractionStatus"
				class="shrink-0 border-b border-slate-800 px-4 py-2 text-xs text-amber-300/90"
				role="status"
			>
				{{ extractionStatus }}
			</p>

			<VideoPlayerCanvas
				:video-object-url="videoObjectUrl"
				:gaze-extraction-enabled="gazeExtractionEnabled"
				:gaze-extraction-active="gazeExtractionActive"
				:gaze-extraction-validation="gazeExtractionValidation"
				@extraction-status="onExtractionStatus"
			/>
		</main>
	</div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ControlSidebar from './components/layout/ControlSidebar.vue'
import VideoPlayerCanvas from './components/video/VideoPlayerCanvas.vue'
import { useGazeStore } from './stores/useGazeStore'

const gazeStore = useGazeStore()
const videoObjectUrl = ref<string | null>(null)
const videoFileName = ref<string | null>(null)
const gazeExtractionEnabled = ref(false)
const gazeExtractionActive = ref(false)
const gazeExtractionValidation = ref(false)
const extractionStatus = ref('')

watch(gazeExtractionEnabled, (enabled) => {
	if (!enabled) {
		gazeExtractionActive.value = false
		extractionStatus.value = ''
	}
})

function onExtractionStatus(message: string): void {
	extractionStatus.value = message
	if (message.includes('extraction paused')) {
		gazeExtractionActive.value = false
	}
}

function onVideoSelected(file: File): void {
	if (videoObjectUrl.value?.startsWith('blob:')) {
		URL.revokeObjectURL(videoObjectUrl.value)
	}

	videoObjectUrl.value = URL.createObjectURL(file)
	videoFileName.value = file.name
	gazeStore.setVideoMetadata(file.name, null)
	gazeStore.setCurrentTime(0)
	gazeStore.setPlaying(false)
}

function onGlobalKeydown(event: KeyboardEvent): void {
	if (event.key !== 'Delete' && event.key !== 'Backspace') return
	const target = event.target as HTMLElement
	if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) return
	if (gazeStore.deleteActiveRoi()) {
		event.preventDefault()
	}
}

onMounted(async () => {
	window.addEventListener('keydown', onGlobalKeydown)
	const restored = await gazeStore.restoreWorkspaceFromIndexedDb()
	if (restored && gazeStore.videoFileName) {
		videoFileName.value = gazeStore.videoFileName
	}
})

onBeforeUnmount(() => {
	window.removeEventListener('keydown', onGlobalKeydown)
	if (videoObjectUrl.value?.startsWith('blob:')) {
		URL.revokeObjectURL(videoObjectUrl.value)
	}
})
</script>
