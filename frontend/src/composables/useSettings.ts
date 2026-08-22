import { ref } from 'vue'
import { apiGet, apiPost } from './useApiClient'

export interface AppSettings {
	obs_host: string
	obs_port: number
	obs_password: string
	virtual_camera_index: number
	hough_param1: number
	hough_param2: number
	min_radius: number
	max_radius: number
	upload_folder: string
	sessions_folder: string
	downloaded_folder: string
	projects_folder: string
}

export interface SettingsVideoFile {
	filename: string
	path: string
	size_mb: number
	created: string
	modified?: string
}

export type TestResultTone = 'idle' | 'loading' | 'success' | 'error' | 'warning'

export interface TestResultState {
	tone: TestResultTone
	message: string
}

function idleResult(): TestResultState {
	return { tone: 'idle', message: '' }
}

function defaultSettings(): AppSettings {
	return {
		obs_host: 'localhost',
		obs_port: 4455,
		obs_password: '',
		virtual_camera_index: 0,
		hough_param1: 50,
		hough_param2: 13,
		min_radius: 65,
		max_radius: 80,
		upload_folder: 'uploaded_videos',
		sessions_folder: 'sessions',
		downloaded_folder: 'downloaded_videos',
		projects_folder: 'projects'
	}
}

export function useSettings() {
	const settings = ref<AppSettings>(defaultSettings())
	const configMessage = ref<TestResultState>(idleResult())
	const importMessage = ref<TestResultState>(idleResult())
	const obsTest = ref<TestResultState>(idleResult())
	const cameraTest = ref<TestResultState>(idleResult())
	const gazeTest = ref<TestResultState>(idleResult())
	const videoFiles = ref<SettingsVideoFile[]>([])
	const videosFolder = ref<string | null>(null)
	const loadingVideos = ref(false)
	const importingFile = ref(false)
	const selectedFilePath = ref<string | null>(null)
	const savingConfig = ref(false)
	const runningAllTests = ref(false)

	async function loadConfig(): Promise<void> {
		try {
			const response = await apiGet<{ success?: boolean; settings?: AppSettings & { obs_password_set?: boolean } }>(
				'/api/settings/get-config'
			)
			if (!response.success || !response.settings) return
			settings.value = {
				...defaultSettings(),
				...response.settings,
				obs_password: ''
			}
		} catch {
			configMessage.value = { tone: 'error', message: 'Failed to load settings from server.' }
		}
	}

	async function saveConfig(): Promise<void> {
		savingConfig.value = true
		configMessage.value = { tone: 'loading', message: 'Saving settings...' }
		try {
			const payload: Record<string, string | number> = {
				obs_host: settings.value.obs_host,
				obs_port: settings.value.obs_port,
				virtual_camera_index: settings.value.virtual_camera_index,
				hough_param1: settings.value.hough_param1,
				hough_param2: settings.value.hough_param2,
				min_radius: settings.value.min_radius,
				max_radius: settings.value.max_radius,
				upload_folder: settings.value.upload_folder,
				sessions_folder: settings.value.sessions_folder,
				downloaded_folder: settings.value.downloaded_folder,
				projects_folder: settings.value.projects_folder
			}
			if (settings.value.obs_password.trim()) {
				payload.obs_password = settings.value.obs_password
			}
			const response = await apiPost<{ success?: boolean; message?: string }>('/api/settings/update-config', payload)
			if (!response.success) {
				throw new Error(response.message ?? 'Save failed')
			}
			configMessage.value = { tone: 'success', message: 'Settings saved successfully.' }
			await loadConfig()
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Failed to save settings'
			configMessage.value = { tone: 'error', message }
		} finally {
			savingConfig.value = false
		}
	}

	async function testObs(): Promise<void> {
		obsTest.value = { tone: 'loading', message: 'Testing OBS connection...' }
		try {
			const response = await apiPost<{
				success?: boolean
				message?: string
				error?: string
				obs_version?: string
				websocket_version?: string
			}>('/api/settings/test-obs')
			if (!response.success) {
				obsTest.value = { tone: 'error', message: response.message ?? response.error ?? 'OBS test failed' }
				return
			}
			obsTest.value = {
				tone: 'success',
				message: `Connected. OBS ${response.obs_version ?? 'unknown'} / WebSocket ${response.websocket_version ?? 'unknown'}`
			}
		} catch (error) {
			obsTest.value = { tone: 'error', message: error instanceof Error ? error.message : 'OBS test failed' }
		}
	}

	async function testVirtualCamera(): Promise<void> {
		cameraTest.value = { tone: 'loading', message: 'Testing virtual camera...' }
		try {
			const response = await apiPost<{ success?: boolean; message?: string; error?: string; resolution?: string }>(
				'/api/settings/test-virtual-camera'
			)
			if (!response.success) {
				cameraTest.value = { tone: 'error', message: response.message ?? response.error ?? 'Camera test failed' }
				return
			}
			cameraTest.value = {
				tone: 'success',
				message: `${response.message ?? 'Camera working'} (${response.resolution ?? 'unknown resolution'})`
			}
		} catch (error) {
			cameraTest.value = { tone: 'error', message: error instanceof Error ? error.message : 'Camera test failed' }
		}
	}

	async function testGazeDetection(): Promise<void> {
		gazeTest.value = { tone: 'loading', message: 'Testing gaze detection...' }
		try {
			const response = await apiPost<{
				success?: boolean
				detected?: boolean
				message?: string
				error?: string
				position?: { x: number; y: number }
				frame_size?: { width: number; height: number }
			}>('/api/settings/test-gaze-detection')
			if (!response.success) {
				gazeTest.value = { tone: 'error', message: response.message ?? response.error ?? 'Detection test failed' }
				return
			}
			if (response.detected && response.position) {
				gazeTest.value = {
					tone: 'success',
					message: `Detected at (${response.position.x}, ${response.position.y}) on ${response.frame_size?.width ?? '?'}x${response.frame_size?.height ?? '?'} frame`
				}
				return
			}
			gazeTest.value = { tone: 'warning', message: 'No gaze marker detected in the current frame.' }
		} catch (error) {
			gazeTest.value = { tone: 'error', message: error instanceof Error ? error.message : 'Detection test failed' }
		}
	}

	async function runAllTests(): Promise<void> {
		runningAllTests.value = true
		await testObs()
		await testVirtualCamera()
		await testGazeDetection()
		runningAllTests.value = false
	}

	async function loadVideosList(): Promise<void> {
		loadingVideos.value = true
		selectedFilePath.value = null
		try {
			const response = await apiGet<{
				success?: boolean
				files?: SettingsVideoFile[]
				videos_folder?: string
				message?: string
				error?: string
			}>('/api/settings/list-videos-folder')
			if (!response.success) {
				importMessage.value = { tone: 'error', message: response.message ?? response.error ?? 'Failed to list videos' }
				videoFiles.value = []
				return
			}
			videoFiles.value = response.files ?? []
			videosFolder.value = response.videos_folder ?? null
		} catch (error) {
			importMessage.value = { tone: 'error', message: error instanceof Error ? error.message : 'Failed to list videos' }
			videoFiles.value = []
		} finally {
			loadingVideos.value = false
		}
	}

	function selectVideoFile(path: string): void {
		selectedFilePath.value = path
	}

	async function importSelectedFile(): Promise<void> {
		if (!selectedFilePath.value) return
		importingFile.value = true
		importMessage.value = { tone: 'loading', message: 'Importing file...' }
		try {
			const response = await apiPost<{
				success?: boolean
				message?: string
				error?: string
				destination?: string
				filename?: string
			}>('/api/settings/import-obs-recording', { file_path: selectedFilePath.value })
			if (!response.success) {
				throw new Error(response.message ?? response.error ?? 'Import failed')
			}
			importMessage.value = {
				tone: 'success',
				message: `Imported ${response.filename ?? 'file'} to ${response.destination ?? 'session folder'}.`
			}
		} catch (error) {
			importMessage.value = { tone: 'error', message: error instanceof Error ? error.message : 'Import failed' }
		} finally {
			importingFile.value = false
		}
	}

	return {
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
		loadConfig,
		saveConfig,
		testObs,
		testVirtualCamera,
		testGazeDetection,
		runAllTests,
		loadVideosList,
		selectVideoFile,
		importSelectedFile
	}
}
