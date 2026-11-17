<template>
	<div class="settings-page">
		<header class="settings-header">
			<button class="btn btn-secondary btn-sm" type="button" @click="$emit('back')">
				Back to editor
			</button>
			<div>
				<h1>Settings and Diagnostics</h1>
				<p>OBS connection, gaze detection tests, and storage paths</p>
			</div>
		</header>

		<GazeLiveCheck
			:settings="settings"
			:capture-devices="captureDevices"
			:loading-capture-devices="loadingCaptureDevices"
			@camera-change="onVirtualCameraChange"
			@refresh-cameras="loadCaptureDevices"
			@hough-change="applyHoughSettings"
		/>

		<GazeDeviceSelector />

		<section class="settings-card">
			<h2>System Tests</h2>
			<div class="settings-grid">
				<SettingsTestCard title="OBS WebSocket" description="Test connection to OBS Studio" :result="obsTest" @run="testObs()" />
				<SettingsTestCard title="Virtual Camera" description="Check if virtual camera is accessible" :result="cameraTest" @run="testVirtualCamera()" />
				<SettingsTestCard title="Gaze marker detection" description="Test overlay gaze marker on current frame" :result="gazeTest" @run="testGazeDetection()" />
			</div>
			<div class="settings-actions">
				<button class="btn btn-success" type="button" :disabled="runningAllTests" @click="runAllTests()">
					{{ runningAllTests ? 'Running tests...' : 'Run All Tests' }}
				</button>
			</div>
		</section>

		<section class="settings-card">
			<h2>OBS Recording Manager</h2>
			<p class="settings-help">Import OBS recordings (eyegaze-*.mp4) from your Videos folder into the current session.</p>
			<div class="settings-actions">
				<button class="btn btn-primary" type="button" :disabled="loadingVideos" @click="loadVideosList()">
					Refresh List
				</button>
				<button class="btn btn-success" type="button" :disabled="!selectedFilePath || importingFile" @click="importSelectedFile()">
					{{ importingFile ? 'Importing...' : 'Import Selected File' }}
				</button>
			</div>
			<p v-if="videosFolder" class="settings-help">Folder: {{ videosFolder }}</p>
			<div v-if="loadingVideos" class="settings-banner">Loading recordings...</div>
			<div v-else-if="videoFiles.length === 0" class="settings-banner">No eyegaze-*.mp4 files found. Click Refresh List.</div>
			<div v-else class="settings-file-list">
				<button
					v-for="file in videoFiles"
					:key="file.path"
					type="button"
					class="settings-file-item"
					:class="{ selected: selectedFilePath === file.path }"
					@click="selectVideoFile(file.path)"
				>
					<strong>{{ file.filename }}</strong>
					<span class="settings-help">{{ file.size_mb }} MB · Created {{ file.created }}</span>
				</button>
			</div>
			<div v-if="importMessage.tone !== 'idle'" class="settings-banner" :class="importMessage.tone">
				{{ importMessage.message }}
			</div>
		</section>

		<section class="settings-card">
			<h2>Configuration</h2>
			<div class="settings-form-grid">
				<div>
					<h3>OBS</h3>
					<label class="settings-field">
						<span>Host</span>
						<input v-model="settings.obs_host" class="settings-input" type="text">
					</label>
					<label class="settings-field">
						<span>Port</span>
						<input v-model.number="settings.obs_port" class="settings-input" type="number">
					</label>
					<label class="settings-field">
						<span>Password</span>
						<input v-model="settings.obs_password" class="settings-input" type="password" placeholder="Leave blank to keep current">
					</label>
				</div>
			</div>

			<h3>Folder Paths</h3>
			<div class="settings-form-grid">
				<label class="settings-field">
					<span>Upload folder</span>
					<input v-model="settings.upload_folder" class="settings-input" type="text">
				</label>
				<label class="settings-field">
					<span>Sessions folder</span>
					<input v-model="settings.sessions_folder" class="settings-input" type="text">
				</label>
				<label class="settings-field">
					<span>Downloaded folder</span>
					<input v-model="settings.downloaded_folder" class="settings-input" type="text">
				</label>
				<label class="settings-field">
					<span>Projects folder</span>
					<input v-model="settings.projects_folder" class="settings-input" type="text">
				</label>
			</div>
			<div class="settings-banner">Use absolute paths or paths relative to the app directory.</div>

			<div class="settings-actions">
				<button class="btn btn-secondary" type="button" @click="loadConfig()">Reset to Current</button>
				<button class="btn btn-primary" type="button" :disabled="savingConfig" @click="saveConfig()">
					{{ savingConfig ? 'Saving...' : 'Save Settings' }}
				</button>
			</div>
			<div v-if="configMessage.tone !== 'idle'" class="settings-banner" :class="configMessage.tone">
				{{ configMessage.message }}
			</div>
		</section>
	</div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import GazeDeviceSelector from './GazeDeviceSelector.vue'
import GazeLiveCheck from './GazeLiveCheck.vue'
import SettingsTestCard from './SettingsTestCard.vue'
import { useSettings } from '../../composables/useSettings'

defineEmits<{
	(e: 'back'): void
}>()

const {
	settings,
	configMessage,
	importMessage,
	obsTest,
	cameraTest,
	gazeTest,
	videoFiles,
	videosFolder,
	loadingVideos,
	importingFile,
	selectedFilePath,
	savingConfig,
	runningAllTests,
	captureDevices,
	loadingCaptureDevices,
	loadConfig,
	loadCaptureDevices,
	onVirtualCameraChange,
	applyHoughSettings,
	saveConfig,
	testObs,
	testVirtualCamera,
	testGazeDetection,
	runAllTests,
	loadVideosList,
	selectVideoFile,
	importSelectedFile
} = useSettings()

onMounted(() => {
	void loadConfig()
	void loadCaptureDevices()
})
</script>

<style scoped>
.settings-page {
	min-height: 100vh;
	padding: 24px;
	background: var(--color-background);
	color: var(--color-text);
}

.settings-header {
	display: flex;
	align-items: center;
	gap: 16px;
	margin-bottom: 24px;
}

.settings-header h1 {
	margin: 0 0 4px;
	font-size: 22px;
	color: var(--color-accent);
}

.settings-header p {
	margin: 0;
	font-size: 13px;
	color: var(--color-text-dim);
}

.settings-card {
	background: var(--color-panel);
	border: 1px solid var(--color-border);
	border-radius: 10px;
	padding: 20px;
	margin-bottom: 20px;
	box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}

.settings-card h2 {
	margin: 0 0 16px;
	padding-bottom: 10px;
	border-bottom: 1px solid var(--color-border);
	font-size: 16px;
	color: var(--color-text);
}

.settings-card h3 {
	margin: 0 0 12px;
	font-size: 14px;
	color: var(--color-accent);
}

.settings-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
	gap: 14px;
}

.settings-form-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
	gap: 20px;
	margin-bottom: 16px;
}

.settings-inline-inputs {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 12px;
}

.settings-field {
	display: flex;
	flex-direction: column;
	gap: 6px;
	margin-bottom: 12px;
}

.settings-field span {
	font-size: 12px;
	color: var(--color-text-dim);
}

.settings-input {
	width: 100%;
	max-width: 100%;
	box-sizing: border-box;
	padding: 10px 12px;
	border: 1px solid var(--color-border);
	border-radius: 6px;
	background: var(--color-background);
	color: var(--color-text);
	font-size: 14px;
}

.settings-input:focus {
	outline: none;
	border-color: var(--color-accent);
}

.settings-actions {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	margin: 16px 0 0;
}

.settings-actions--compact {
	margin: 0 0 12px;
}

.settings-help {
	display: block;
	margin: 8px 0;
	font-size: 12px;
	color: var(--color-text-dim);
}

.settings-banner {
	margin-top: 12px;
	padding: 10px 12px;
	border-radius: 6px;
	border: 1px solid var(--color-border);
	background: var(--color-background);
	color: var(--color-text);
	font-size: 13px;
}

.settings-banner.error {
	border-color: var(--color-danger);
	color: var(--color-danger);
	background: rgba(224, 108, 117, 0.12);
}

.settings-banner.success {
	border-color: var(--color-success);
	color: var(--color-success);
	background: rgba(152, 195, 121, 0.12);
}

.settings-banner.loading,
.settings-banner.warning {
	border-color: var(--color-warning);
	color: var(--color-warning);
	background: rgba(229, 192, 123, 0.12);
}

.settings-file-list {
	display: flex;
	flex-direction: column;
	gap: 8px;
	margin-top: 12px;
}

.settings-file-item {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 4px;
	width: 100%;
	padding: 12px;
	border: 1px solid var(--color-border);
	border-radius: 6px;
	background: var(--color-background);
	color: var(--color-text);
	text-align: left;
	cursor: pointer;
}

.settings-file-item:hover {
	border-color: var(--color-accent);
}

.settings-file-item.selected {
	border-color: var(--color-accent);
	background: rgba(6, 158, 189, 0.15);
}
</style>
