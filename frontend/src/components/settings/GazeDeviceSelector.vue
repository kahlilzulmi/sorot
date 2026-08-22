<template>
	<section class="settings-card">
		<h2>Gaze Input Device</h2>
		<p class="settings-help">
			Choose how gaze coordinates are captured. Mouse works everywhere; eye trackers and webcams can be added over time.
		</p>

		<div class="device-filters">
			<button
				v-for="filter in filters"
				:key="filter.id"
				type="button"
				class="device-filter-btn"
				:class="{ active: deviceFilter === filter.id }"
				@click="deviceFilter = filter.id"
			>
				{{ filter.label }}
			</button>
		</div>

		<div class="device-grid">
			<button
				v-for="device in filteredDevices"
				:key="device.id"
				type="button"
				class="device-card"
				:class="{ selected: selectedDeviceId === device.id }"
				@click="selectDevice(device.id)"
			>
				<span class="device-card-category">{{ categoryLabel(device.category) }}</span>
				<strong class="device-card-name">{{ device.name }}</strong>
				<span class="device-card-vendor">{{ device.manufacturer }}</span>
			</button>
		</div>

		<div v-if="selectedDevice" class="device-detail">
			<div class="device-detail-header">
				<div>
					<strong>{{ selectedDevice.name }}</strong>
					<span class="settings-help">{{ selectedDevice.manufacturer }}</span>
				</div>
				<button
					class="btn btn-secondary btn-sm"
					type="button"
					:disabled="testingDevice"
					@click="testSelectedDevice()"
				>
					{{ testingDevice ? 'Testing...' : 'Test device' }}
				</button>
			</div>
			<p class="device-detail-desc">{{ selectedDevice.description }}</p>
			<div
				v-if="deviceTest.tone !== 'idle'"
				class="settings-banner"
				:class="deviceTest.tone"
			>
				{{ deviceTest.message }}
			</div>
		</div>

		<div class="custom-device-panel">
			<h3>Add custom device</h3>
			<p class="settings-help">Register webcams, lab hardware, or future pipelines without waiting for a built-in entry.</p>
			<div class="custom-device-form">
				<label class="settings-field">
					<span>Device name</span>
					<input v-model="customForm.name" class="settings-input" type="text" placeholder="e.g. Lab webcam #2">
				</label>
				<label class="settings-field">
					<span>Manufacturer</span>
					<input v-model="customForm.manufacturer" class="settings-input" type="text" placeholder="Optional">
				</label>
				<label class="settings-field">
					<span>Notes</span>
					<input v-model="customForm.description" class="settings-input" type="text" placeholder="How this device will provide gaze data">
				</label>
			</div>
			<button class="btn btn-primary btn-sm" type="button" :disabled="!customForm.name.trim()" @click="addCustomDevice()">
				Add device
			</button>

			<div v-if="customDevices.length > 0" class="custom-device-list">
				<div v-for="device in customDevices" :key="device.id" class="custom-device-item">
					<div>
						<strong>{{ device.name }}</strong>
						<span class="settings-help">{{ device.manufacturer }}</span>
					</div>
					<button class="btn btn-secondary btn-sm" type="button" @click="removeCustomDevice(device.id)">
						Remove
					</button>
				</div>
			</div>
		</div>
	</section>
</template>

<script setup lang="ts">
import { categoryLabel, type GazeDeviceCategory } from '../../types/gazeDevice'
import { useGazeDevices } from '../../composables/useGazeDevices'

const filters: { id: 'all' | GazeDeviceCategory; label: string }[] = [
	{ id: 'all', label: 'All' },
	{ id: 'fallback', label: 'Fallback' },
	{ id: 'eye_tracker', label: 'Eye trackers' },
	{ id: 'webcam', label: 'Webcam' },
	{ id: 'custom', label: 'Custom' }
]

const {
	filteredDevices,
	selectedDevice,
	selectedDeviceId,
	deviceFilter,
	deviceTest,
	testingDevice,
	customForm,
	customDevices,
	selectDevice,
	addCustomDevice,
	removeCustomDevice,
	testSelectedDevice
} = useGazeDevices()
</script>

<style scoped>
.device-filters {
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
	margin-bottom: 14px;
}

.device-filter-btn {
	padding: 6px 12px;
	border: 1px solid var(--color-border);
	border-radius: 999px;
	background: var(--color-background);
	color: var(--color-text-dim);
	font-size: 12px;
	cursor: pointer;
	transition: border-color 0.2s ease, color 0.2s ease, background-color 0.2s ease;
}

.device-filter-btn:hover,
.device-filter-btn.active {
	border-color: var(--color-accent);
	color: var(--color-text);
	background: rgba(6, 158, 189, 0.1);
}

.device-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
	gap: 10px;
	margin-bottom: 16px;
}

.device-card {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 4px;
	padding: 12px;
	border: 1px solid var(--color-border);
	border-radius: 8px;
	background: var(--color-background);
	color: var(--color-text);
	text-align: left;
	cursor: pointer;
	transition: border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
}

.device-card:hover {
	border-color: var(--color-accent);
}

.device-card.selected {
	border-color: var(--color-accent);
	background: rgba(6, 158, 189, 0.12);
	box-shadow: 0 0 0 1px rgba(6, 158, 189, 0.2);
}

.device-card-category {
	font-size: 10px;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	color: var(--color-accent);
}

.device-card-name {
	font-size: 13px;
	color: var(--color-text);
}

.device-card-vendor {
	font-size: 11px;
	color: var(--color-text-dim);
}

.device-detail {
	padding: 14px;
	border: 1px solid var(--color-border);
	border-radius: 8px;
	background: var(--color-background);
	margin-bottom: 20px;
}

.device-detail-header {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 12px;
	margin-bottom: 8px;
}

.device-detail-desc {
	margin: 0;
	font-size: 13px;
	color: var(--color-text-dim);
	line-height: 1.5;
}

.custom-device-panel {
	border-top: 1px solid var(--color-border);
	padding-top: 16px;
}

.custom-device-panel h3 {
	margin: 0 0 8px;
	font-size: 14px;
	color: var(--color-accent);
}

.custom-device-form {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
	gap: 12px;
	margin-bottom: 12px;
}

.custom-device-list {
	display: flex;
	flex-direction: column;
	gap: 8px;
	margin-top: 14px;
}

.custom-device-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	padding: 10px 12px;
	border: 1px solid var(--color-border);
	border-radius: 6px;
	background: var(--color-background);
}

.settings-help {
	display: block;
	margin: 8px 0;
	font-size: 12px;
	color: var(--color-text-dim);
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
</style>
