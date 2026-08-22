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

		<section class="editor-section settings-card">
			<h2>System Tests</h2>
			<div class="settings-grid">
				<SettingsTestCard title="OBS WebSocket" description="Test connection to OBS Studio" :result="obsTest" @run="testObs()" />
				<SettingsTestCard title="Tobii Ghost Overlay" description="Check if SSOverlay.exe is running" :result="tobiiTest" @run="testTobii()" />
				<SettingsTestCard title="Virtual Camera" description="Check if virtual camera is accessible" :result="cameraTest" @run="testVirtualCamera()" />
				<SettingsTestCard title="Gaze Detection" description="Test Tobii comet detection on current frame" :result="gazeTest" @run="testGazeDetection()" />
			</div>
			<div class="settings-actions">
				<button class="btn btn-success" type="button" :disabled="runningAllTests" @click="runAllTests()">
					{{ runningAllTests ? 'Running tests...' : 'Run All Tests' }}
				</button>
			</div>
		</section>

		<section class="editor-section settings-card">
			<h2>OBS Recording Manager</h2>
			<p class="help-text">Import OBS recordings (eyegaze-*.mp4) from your Videos folder into the current session.</p>
			<div class="settings-actions">
				<button class="btn btn-primary" type="button" :disabled="loadingVideos" @click="loadVideosList()">
					Refresh List
				</button>
				<button class="btn btn-success" type="button" :disabled="!selectedFilePath || importingFile" @click="importSelectedFile()">
					{{ importingFile ? 'Importing...' : 'Import Selected File' }}
				</button>
			</div>
			<p v-if="videosFolder" class="help-text">Folder: {{ videosFolder }}</p>
			<div v-if="loadingVideos" class="info-box">Loading recordings...</div>
			<div v-else-if="videoFiles.length === 0" class="info-box">No eyegaze-*.mp4 files found. Click Refresh List.</div>
			<div v-else class="file-list">
				<div
					v-for="file in videoFiles"
					:key="file.path"
					class="file-item-result"
					:class="{ selected: selectedFilePath === file.path }"
					@click="selectVideoFile(file.path)"
				>
					<div>
						<strong>{{ file.filename }}</strong>
						<div class="help-text">{{ file.size_mb }} MB · Created {{ file.created }}</div>
					</div>
				</div>
			</div>
			<div v-if="importMessage.tone !== 'idle'" :class="resultClass(importMessage.tone)">
				{{ importMessage.message }}
			</div>
		</section>

		<section class="editor-section settings-card">
			<h2>Configuration</h2>
			<div class="settings-form-grid">
				<div>
					<h3>OBS</h3>
					<label class="input-group">
						<span>Host</span>
						<input v-model="settings.obs_host" class="input-text" type="text">
					</label>
					<label class="input-group">
						<span>Port</span>
						<input v-model.number="settings.obs_port" class="input-text" type="number">
					</label>
					<label class="input-group">
						<span>Password</span>
						<input v-model="settings.obs_password" class="input-text" type="password" placeholder="Leave blank to keep current">
					</label>
				</div>
				<div>
					<h3>Detection</h3>
					<label class="input-group">
						<span>Virtual camera index</span>
						<input v-model.number="settings.virtual_camera_index" class="input-text" type="number">
					</label>
					<label class="input-group">
						<span>Hough param1</span>
						<input v-model.number="settings.hough_param1" class="input-text" type="number">
					</label>
					<label class="input-group">
						<span>Hough param2</span>
						<input v-model.number="settings.hough_param2" class="input-text" type="number">
					</label>
					<div class="settings-inline-inputs">
						<label class="input-group">
							<span>Min radius</span>
							<input v-model.number="settings.min_radius" class="input-text" type="number">
						</label>
						<label class="input-group">
							<span>Max radius</span>
							<input v-model.number="settings.max_radius" class="input-text" type="number">
						</label>
					</div>
				</div>
			</div>

			<h3>Folder Paths</h3>
			<div class="settings-form-grid">
				<label class="input-group">
					<span>Upload folder</span>
					<input v-model="settings.upload_folder" class="input-text" type="text">
				</label>
				<label class="input-group">
					<span>Sessions folder</span>
					<input v-model="settings.sessions_folder" class="input-text" type="text">
				</label>
				<label class="input-group">
					<span>Downloaded folder</span>
					<input v-model="settings.downloaded_folder" class="input-text" type="text">
				</label>
				<label class="input-group">
					<span>Projects folder</span>
					<input v-model="settings.projects_folder" class="input-text" type="text">
				</label>
			</div>
			<div class="info-box">Use absolute paths or paths relative to the app directory.</div>

			<div class="settings-actions">
				<button class="btn btn-secondary" type="button" @click="loadConfig()">Reset to Current</button>
				<button class="btn btn-primary" type="button" :disabled="savingConfig" @click="saveConfig()">
					{{ savingConfig ? 'Saving...' : 'Save Settings' }}
				</button>
			</div>
			<div v-if="configMessage.tone !== 'idle'" :class="resultClass(configMessage.tone)">
				{{ configMessage.message }}
			</div>
		</section>
	</div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import SettingsTestCard from './SettingsTestCard.vue'
import { useSettings, type TestResultTone } from '../../composables/useSettings'

defineEmits<{
	(e: 'back'): void
}>()

const {
	settings,
	configMessage,
	importMessage,
	obsTest,
	tobiiTest,
	cameraTest,
	gazeTest,
	videoFiles,
	videosFolder,
	loadingVideos,
	importingFile,
	selectedFilePath,
	savingConfig,
	runningAllTests,
	loadConfig,
	saveConfig,
	testObs,
	testTobii,
	testVirtualCamera,
	testGazeDetection,
	runAllTests,
	loadVideosList,
	selectVideoFile,
	importSelectedFile
} = useSettings()

function resultClass(tone: TestResultTone): string {
	if (tone === 'error') return 'error-box'
	return 'info-box'
}

onMounted(() => {
	void loadConfig()
})
</script>

<style scoped>
.settings-page {
	min-height: 100vh;
	padding: 20px;
	background: var(--color-bg, #f5f5f5);
}

.settings-header {
	display: flex;
	align-items: center;
	gap: 16px;
	margin-bottom: 20px;
}

.settings-header h1 {
	margin: 0 0 4px;
}

.settings-header p {
	margin: 0;
	color: #666;
}

.settings-card {
	margin-bottom: 20px;
}

.settings-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
	gap: 16px;
}

.settings-form-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
	gap: 16px;
	margin-bottom: 16px;
}

.settings-inline-inputs {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 12px;
}

.settings-actions {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	margin: 16px 0;
}

.file-item-result.selected {
	border-color: var(--color-primary, #007bff);
	background: #e7f3ff;
}
</style>
