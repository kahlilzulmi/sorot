import { onBeforeUnmount, ref, type Ref } from 'vue'
import { apiGet, apiPost } from './useApiClient'

export type ProgressStepStatus = 'pending' | 'active' | 'success' | 'error'

export interface ProgressStep {
	key: string
	label: string
	status: ProgressStepStatus
}

export interface ObsRecordingFile {
	path: string
	filename: string
	size_mb: number
	created: string
}

interface ProgressPollResponse {
	progress?: number
	status?: string
	complete?: boolean
	is_processing?: boolean
	error?: string
}

interface VerifyCompletionResponse {
	complete?: boolean
	files_found?: Record<string, string>
}

export function usePostProcessing(
	sessionDir: Ref<string | null>,
	manualImportRequired: Ref<boolean>,
	obsRecordingPath: Ref<string | null>,
	setStatus: (message: string) => void
) {
	const showProgressModal = ref(false)
	const processing = ref(false)
	const processingStatus = ref('')
	const progressSteps = ref<ProgressStep[]>([])
	const progressMessage = ref('Initializing...')
	const progressError = ref<string | null>(null)
	const progressComplete = ref(false)
	const progressPercent = ref(0)
	const generatedFiles = ref<Record<string, string>>({})

	const showObsFilePickerModal = ref(false)
	const loadingObsFiles = ref(false)
	const importingObsFile = ref(false)
	const availableObsFiles = ref<ObsRecordingFile[]>([])

	let progressPollInterval: ReturnType<typeof setInterval> | null = null
	let progressPollCount = 0
	const maxProgressPolls = 600

	const progressBlocking = (): boolean =>
		showProgressModal.value && !progressComplete.value && !progressError.value

	function canOpenModal(): boolean {
		return !progressBlocking()
	}

	function resetProgressModal(): void {
		progressSteps.value = []
		progressMessage.value = 'Initializing...'
		progressError.value = null
		progressComplete.value = false
		progressPercent.value = 0
		generatedFiles.value = {}
		progressPollCount = 0
		showProgressModal.value = true
		stopProgressPolling()
	}

	function closeProgressModal(): void {
		if (processing.value && !progressComplete.value && !progressError.value) return
		stopProgressPolling()
		showProgressModal.value = false
	}

	function progressStatusLabel(status: ProgressStepStatus): string {
		if (status === 'success') return 'Done'
		if (status === 'active') return 'In progress'
		if (status === 'error') return 'Error'
		return 'Pending'
	}

	function stopProgressPolling(): void {
		if (progressPollInterval) {
			clearInterval(progressPollInterval)
			progressPollInterval = null
		}
	}

	async function pollProgress(): Promise<void> {
		if (progressPollCount >= maxProgressPolls) {
			stopProgressPolling()
			progressError.value = 'Processing timeout - took longer than expected'
			processing.value = false
			return
		}
		progressPollCount++

		try {
			const data = await apiGet<ProgressPollResponse>('/api/processing/progress')
			progressPercent.value = data.progress ?? 0
			progressMessage.value = data.status ?? 'Processing...'

			if (data.complete && (data.progress ?? 0) >= 100) {
				await verifyProcessingCompletion()
				return
			}

			if (data.error || (data.progress ?? 0) < 0) {
				stopProgressPolling()
				progressError.value = data.status ?? 'Processing failed'
				progressMessage.value = 'Processing encountered an error'
				processing.value = false
				return
			}

			if (!data.is_processing && !data.complete) {
				await verifyProcessingCompletion()
			}
		} catch {
			// Continue polling on transient network errors
		}
	}

	async function verifyProcessingCompletion(): Promise<void> {
		try {
			const data = await apiGet<VerifyCompletionResponse>('/api/processing/verify-completion')
			if (data.complete) {
				generatedFiles.value = data.files_found ?? {}
				progressComplete.value = true
				progressPercent.value = 100
				progressMessage.value = 'Processing complete!'
				setStatus('Processing complete!')
			} else {
				progressError.value = 'Some output files may be missing'
				progressMessage.value = 'Processing completed with warnings'
			}
		} catch {
			progressError.value = 'Could not verify processing results'
		} finally {
			stopProgressPolling()
			processing.value = false
		}
	}

	function startProgressPolling(): void {
		stopProgressPolling()
		progressPollInterval = setInterval(() => {
			void pollProgress()
		}, 1000)
	}

	async function runPostProcessingPipeline(): Promise<void> {
		resetProgressModal()
		processing.value = true
		progressMessage.value = 'Starting post-processing...'
		try {
			const response = await apiPost<{ error?: string }>('/api/processing/start-post-processing')
			if (response.error) {
				throw new Error(response.error)
			}
			startProgressPolling()
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Failed to start processing'
			progressError.value = message
			progressMessage.value = 'Failed to start processing'
			setStatus('Processing failed')
			processing.value = false
		}
	}

	async function runProcessingAction(
		path: string,
		statusLabel: string,
		closeProcessModal: () => void
	): Promise<void> {
		if (!sessionDir.value) {
			window.alert('No recording session found')
			return
		}
		if (manualImportRequired.value) {
			window.alert('Please import the eye gaze recording file first.')
			return
		}
		processing.value = true
		processingStatus.value = statusLabel
		try {
			await apiPost(path)
			setStatus(statusLabel)
			closeProcessModal()
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Processing failed'
			window.alert(message)
		} finally {
			processing.value = false
			processingStatus.value = ''
		}
	}

	async function generateHeatmaps(closeProcessModal: () => void): Promise<void> {
		await runProcessingAction('/api/processing/generate-heatmaps', 'Generating heatmaps...', closeProcessModal)
	}

	async function generateRoiStats(closeProcessModal: () => void): Promise<void> {
		await runProcessingAction('/api/processing/roi-statistics', 'Generating ROI statistics...', closeProcessModal)
	}

	async function generateOverlayVideo(closeProcessModal: () => void): Promise<void> {
		await runProcessingAction('/api/processing/overlay-video', 'Creating overlay video...', closeProcessModal)
	}

	async function generateHeatmapOverlayVideo(closeProcessModal: () => void): Promise<void> {
		await runProcessingAction(
			'/api/processing/overlay-heatmap-video',
			'Creating heatmap overlay videos...',
			closeProcessModal
		)
	}

	async function processAll(closeProcessModal: () => void): Promise<void> {
		if (!sessionDir.value) {
			window.alert('No recording session found')
			return
		}
		if (manualImportRequired.value) {
			window.alert('Please import the eye gaze recording file first.')
			return
		}
		closeProcessModal()
		processing.value = true
		processingStatus.value = 'Running full post-processing pipeline...'
		try {
			await apiPost('/api/processing/generate-heatmaps')
			await apiPost('/api/processing/roi-statistics')
			await apiPost('/api/processing/overlay-video')
			await apiPost('/api/processing/overlay-heatmap-video')
			setStatus('All processing complete')
			window.alert('All processing complete. Check the session folder for outputs.')
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Processing failed'
			window.alert(`Failed during processing: ${message}`)
		} finally {
			processing.value = false
			processingStatus.value = ''
		}
	}

	async function openObsFilePicker(): Promise<void> {
		loadingObsFiles.value = true
		showObsFilePickerModal.value = true
		try {
			const response = await apiGet<{ success?: boolean; files?: ObsRecordingFile[]; error?: string }>(
				'/api/settings/list-obs-recordings'
			)
			if (!response.success) {
				window.alert(`Failed to load available files: ${response.error ?? 'Unknown error'}`)
				showObsFilePickerModal.value = false
				return
			}
			availableObsFiles.value = response.files ?? []
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Error loading files'
			window.alert(message)
			showObsFilePickerModal.value = false
		} finally {
			loadingObsFiles.value = false
		}
	}

	async function selectObsFile(filePath: string): Promise<void> {
		importingObsFile.value = true
		try {
			const response = await apiPost<{ success?: boolean; destination?: string; filename?: string; error?: string }>(
				'/api/settings/import-obs-recording',
				{ file_path: filePath }
			)
			if (!response.success) {
				window.alert(`Failed to import file: ${response.error ?? 'Unknown error'}`)
				return
			}
			obsRecordingPath.value = response.destination ?? null
			manualImportRequired.value = false
			showObsFilePickerModal.value = false
			window.alert(`Eye gaze file imported: ${response.filename ?? 'file'}`)
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Import failed'
			window.alert(message)
		} finally {
			importingObsFile.value = false
		}
	}

	async function generateReportsFromImport(hasImportedGaze: boolean, hasScenes: boolean, hasRois: boolean): Promise<void> {
		if (!hasImportedGaze) {
			window.alert('No imported gaze data available')
			return
		}
		if (!hasScenes) {
			window.alert('Please define at least one scene')
			return
		}
		if (!hasRois) {
			const proceed = window.confirm('No ROIs defined. Generate reports anyway?')
			if (!proceed) return
		}

		resetProgressModal()
		processing.value = true
		progressMessage.value = 'Generating reports from imported data...'

		try {
			const response = await apiPost<{
				success?: boolean
				error?: string
				session_dir?: string
				gaze_points_processed?: number
				excel_report?: string
				pdf_report?: string
			}>('/api/generate-reports-from-import')

			if (!response.success) {
				throw new Error(response.error ?? 'Report generation failed')
			}

			if (response.session_dir) {
				sessionDir.value = response.session_dir
			}
			progressComplete.value = true
			progressPercent.value = 100
			progressMessage.value = `Reports generated successfully. Gaze points processed: ${response.gaze_points_processed ?? 0}. Excel: ${response.excel_report ?? 'n/a'}. PDF: ${response.pdf_report ?? 'n/a'}.`
			setStatus('Import reports generated')
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Report generation failed'
			progressError.value = message
			progressMessage.value = 'Report generation failed'
			setStatus('Report generation failed')
		} finally {
			processing.value = false
		}
	}

	onBeforeUnmount(() => {
		stopProgressPolling()
	})

	return {
		showProgressModal,
		processing,
		processingStatus,
		progressSteps,
		progressMessage,
		progressError,
		progressComplete,
		progressPercent,
		generatedFiles,
		showObsFilePickerModal,
		loadingObsFiles,
		importingObsFile,
		availableObsFiles,
		canOpenModal,
		progressBlocking,
		resetProgressModal,
		closeProgressModal,
		progressStatusLabel,
		runPostProcessingPipeline,
		generateHeatmaps,
		generateRoiStats,
		generateOverlayVideo,
		generateHeatmapOverlayVideo,
		processAll,
		openObsFilePicker,
		selectObsFile,
		generateReportsFromImport
	}
}
