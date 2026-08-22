import { computed, ref } from 'vue'
import { apiPost } from './useApiClient'
import type { TestResultState, TestResultTone } from './useSettings'
import {
	BUILTIN_GAZE_DEVICES,
	buildCustomDevice,
	CUSTOM_GAZE_DEVICES_STORAGE_KEY,
	createCustomDeviceId,
	DEFAULT_GAZE_DEVICE_ID,
	GAZE_DEVICE_STORAGE_KEY,
	type CustomGazeDeviceInput,
	type GazeDeviceCategory,
	type GazeDeviceDefinition
} from '../types/gazeDevice'

type DeviceFilter = 'all' | GazeDeviceCategory

const customDevices = ref<GazeDeviceDefinition[]>(readCustomDevices())
const selectedDeviceId = ref<string>(readSelectedDeviceId())
const deviceTest = ref<TestResultState>({ tone: 'idle', message: '' })
const testingDevice = ref(false)
const customForm = ref<CustomGazeDeviceInput>({
	name: '',
	manufacturer: '',
	description: ''
})
const deviceFilter = ref<DeviceFilter>('all')

function readSelectedDeviceId(): string {
	if (typeof window === 'undefined') return DEFAULT_GAZE_DEVICE_ID
	try {
		const stored = window.localStorage.getItem(GAZE_DEVICE_STORAGE_KEY)
		return stored?.trim() || DEFAULT_GAZE_DEVICE_ID
	} catch {
		return DEFAULT_GAZE_DEVICE_ID
	}
}

function readCustomDevices(): GazeDeviceDefinition[] {
	if (typeof window === 'undefined') return []
	try {
		const raw = window.localStorage.getItem(CUSTOM_GAZE_DEVICES_STORAGE_KEY)
		if (!raw) return []
		const parsed = JSON.parse(raw) as GazeDeviceDefinition[]
		return Array.isArray(parsed) ? parsed.filter((device) => !device.builtin) : []
	} catch {
		return []
	}
}

function persistSelectedDeviceId(deviceId: string): void {
	if (typeof window === 'undefined') return
	window.localStorage.setItem(GAZE_DEVICE_STORAGE_KEY, deviceId)
}

function persistCustomDevices(): void {
	if (typeof window === 'undefined') return
	window.localStorage.setItem(CUSTOM_GAZE_DEVICES_STORAGE_KEY, JSON.stringify(customDevices.value))
}

const allDevices = computed(() => [...BUILTIN_GAZE_DEVICES, ...customDevices.value])

const selectedDevice = computed(() => {
	return allDevices.value.find((device) => device.id === selectedDeviceId.value) ?? BUILTIN_GAZE_DEVICES[0]
})

const filteredDevices = computed(() => {
	if (deviceFilter.value === 'all') return allDevices.value
	return allDevices.value.filter((device) => device.category === deviceFilter.value)
})

function selectDevice(deviceId: string): void {
	selectedDeviceId.value = deviceId
	persistSelectedDeviceId(deviceId)
	deviceTest.value = { tone: 'idle', message: '' }
}

function addCustomDevice(): boolean {
	const name = customForm.value.name.trim()
	if (!name) return false
	const device = buildCustomDevice({
		name,
		manufacturer: customForm.value.manufacturer,
		description: customForm.value.description
	}, createCustomDeviceId())
	customDevices.value = [...customDevices.value, device]
	persistCustomDevices()
	selectDevice(device.id)
	customForm.value = { name: '', manufacturer: '', description: '' }
	return true
}

function removeCustomDevice(deviceId: string): void {
	customDevices.value = customDevices.value.filter((device) => device.id !== deviceId)
	persistCustomDevices()
	if (selectedDeviceId.value === deviceId) {
		selectDevice(DEFAULT_GAZE_DEVICE_ID)
	}
}

async function testOverlayPipeline(): Promise<TestResultState> {
	const overlay = await apiPost<{ running?: boolean | null; message?: string }>('/api/settings/test-tobii')
	if (overlay.running === false) {
		return { tone: 'error', message: overlay.message ?? 'Overlay service is not running.' }
	}
	if (overlay.running === null) {
		return { tone: 'warning', message: overlay.message ?? 'Overlay status could not be verified.' }
	}

	const camera = await apiPost<{ success?: boolean; message?: string; error?: string; resolution?: string }>(
		'/api/settings/test-virtual-camera'
	)
	if (!camera.success) {
		return { tone: 'error', message: camera.message ?? camera.error ?? 'Virtual camera test failed.' }
	}

	const gaze = await apiPost<{
		success?: boolean
		detected?: boolean
		message?: string
		error?: string
		position?: { x: number; y: number }
	}>('/api/settings/test-gaze-detection')
	if (!gaze.success) {
		return { tone: 'error', message: gaze.message ?? gaze.error ?? 'Gaze marker detection failed.' }
	}
	if (gaze.detected && gaze.position) {
		return {
			tone: 'success',
			message: `Overlay, camera, and marker OK — detected at (${gaze.position.x}, ${gaze.position.y}).`
		}
	}
	return { tone: 'warning', message: 'Overlay and camera OK, but no gaze marker detected in the current frame.' }
}

async function testVirtualCameraOnly(): Promise<TestResultState> {
	const camera = await apiPost<{ success?: boolean; message?: string; error?: string; resolution?: string }>(
		'/api/settings/test-virtual-camera'
	)
	if (!camera.success) {
		return { tone: 'error', message: camera.message ?? camera.error ?? 'Virtual camera test failed.' }
	}
	return {
		tone: 'success',
		message: `${camera.message ?? 'Virtual camera accessible'} (${camera.resolution ?? 'unknown resolution'})`
	}
}

async function testSelectedDevice(): Promise<void> {
	const device = selectedDevice.value
	testingDevice.value = true
	deviceTest.value = { tone: 'loading', message: `Testing ${device.name}...` }

	try {
		let result: TestResultState

		switch (device.transport) {
			case 'mouse':
				result = {
					tone: 'success',
					message: 'Mouse fallback ready. Move the pointer in the editor to simulate gaze.'
				}
				break
			case 'tobii_overlay':
				result = await testOverlayPipeline()
				break
			case 'tobii_sdk':
				result = {
					tone: 'warning',
					message: 'Tobii SDK live stream is not wired yet. Use overlay mode or import gaze data for now.'
				}
				break
			case 'virtual_camera':
				result = await testVirtualCameraOnly()
				break
			case 'webgazer':
				result = {
					tone: 'warning',
					message: 'WebGazer webcam tracking is planned for Phase 3. Select mouse or overlay device meanwhile.'
				}
				break
			case 'import_only':
				result = {
					tone: 'warning',
					message: 'This tracker is import-only for now. Use Import mode or add a custom live bridge later.'
				}
				break
			case 'custom':
				result = {
					tone: 'warning',
					message: 'Custom device registered. Wire a gaze pipeline in a future phase or use import mode.'
				}
				break
			default:
				result = { tone: 'error', message: 'Unknown device transport.' }
		}

		deviceTest.value = result
	} catch (error) {
		deviceTest.value = {
			tone: 'error',
			message: error instanceof Error ? error.message : 'Device test failed.'
		}
	} finally {
		testingDevice.value = false
	}
}

export function useGazeDevices() {
	return {
		allDevices,
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
	}
}

export function gazeDeviceToneLabel(tone: TestResultTone): string {
	switch (tone) {
		case 'success':
			return 'Ready'
		case 'error':
			return 'Failed'
		case 'warning':
			return 'Pending'
		case 'loading':
			return 'Testing'
		default:
			return 'Idle'
	}
}
