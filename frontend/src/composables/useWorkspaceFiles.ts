import { ref, type Ref } from 'vue'
import { apiPost } from './useApiClient'
import type { VideoInfo, WorkspaceScene } from '../types/workspace'

export interface WorkspaceDocument {
	version: string
	timestamp: string
	video_info: VideoInfo
	scenes: WorkspaceScene[]
	youtube_url?: string
	workspace_file?: string | null
}

interface SaveWorkspaceResponse {
	success: boolean
	last_updated?: string
	workspace_file?: string
	error?: string
}

interface ImportWorkspaceResponse {
	success: boolean
	video_info?: VideoInfo
	scenes?: WorkspaceScene[]
	last_updated?: string
	downloaded_from_url?: boolean
	error?: string
}

export function useWorkspaceFiles(
	videoInfo: Ref<VideoInfo | null>,
	videoSrc: Ref<string>,
	scenes: Ref<WorkspaceScene[]>,
	currentWorkspaceFile: Ref<string | null>,
	lastUpdated: Ref<string | null>,
	lastYoutubeUrl: Ref<string>,
	setStatus: (message: string) => void,
	onImported: (importedScenes: WorkspaceScene[]) => void
) {
	const showSaveAsModal = ref(false)
	const saveAsFilename = ref('')

	function buildWorkspaceDocument(): WorkspaceDocument | null {
		if (!videoInfo.value) return null
		return {
			version: '1.0',
			timestamp: new Date().toISOString(),
			video_info: videoInfo.value,
			scenes: scenes.value,
			youtube_url: lastYoutubeUrl.value || '',
			workspace_file: currentWorkspaceFile.value
		}
	}

	async function saveWorkspace(): Promise<void> {
		const workspace = buildWorkspaceDocument()
		if (!workspace) {
			window.alert('No workspace to save')
			return
		}
		try {
			const response = await apiPost<SaveWorkspaceResponse>('/api/save-workspace', workspace)
			if (response.success) {
				if (response.last_updated) lastUpdated.value = response.last_updated
				if (response.workspace_file) currentWorkspaceFile.value = response.workspace_file
				setStatus(`Saved to ${currentWorkspaceFile.value ?? 'workspace'}`)
				window.alert(`Workspace saved to ${currentWorkspaceFile.value}`)
			} else {
				window.alert('Failed to save workspace')
			}
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Save failed'
			window.alert(`Error saving workspace: ${message}`)
		}
	}

	function openSaveAsModal(): void {
		if (!videoInfo.value) {
			window.alert('No workspace to save')
			return
		}
		if (currentWorkspaceFile.value) {
			saveAsFilename.value = currentWorkspaceFile.value.replace(/\.json$/i, '')
		} else {
			const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
			saveAsFilename.value = `workspace_${stamp}`
		}
		showSaveAsModal.value = true
	}

	async function confirmSaveAs(): Promise<void> {
		const workspace = buildWorkspaceDocument()
		if (!workspace) return
		workspace.workspace_file = saveAsFilename.value.trim() || null
		try {
			const response = await apiPost<SaveWorkspaceResponse>('/api/save-workspace-as', workspace)
			if (response.success) {
				if (response.last_updated) lastUpdated.value = response.last_updated
				if (response.workspace_file) currentWorkspaceFile.value = response.workspace_file
				showSaveAsModal.value = false
				setStatus(`Saved as ${currentWorkspaceFile.value}`)
				window.alert(`Workspace saved as ${currentWorkspaceFile.value}`)
			} else {
				window.alert('Failed to save workspace')
			}
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Save failed'
			window.alert(`Error saving workspace: ${message}`)
		}
	}

	async function importWorkspaceFile(file: File): Promise<boolean> {
		try {
			const text = await file.text()
			const workspace = JSON.parse(text) as WorkspaceDocument
			if (!workspace.video_info || !workspace.scenes) {
				window.alert('Invalid workspace file format')
				return false
			}

			const response = await apiPost<ImportWorkspaceResponse>('/api/import-workspace', workspace)
			if (!response.success) {
				window.alert(response.error ?? 'Failed to import workspace')
				return false
			}

			const resolvedVideo = response.video_info ?? workspace.video_info
			const resolvedScenes = (response.scenes ?? workspace.scenes).map((scene) => ({
				...scene,
				custom_name: scene.custom_name ?? '',
				rois: scene.rois ?? []
			}))

			videoInfo.value = resolvedVideo
			scenes.value = resolvedScenes
			currentWorkspaceFile.value = file.name
			lastUpdated.value = response.last_updated ?? new Date().toISOString()
			onImported(resolvedScenes)

			if (response.downloaded_from_url) {
				setStatus('Workspace imported (video auto-downloaded)')
				window.alert(
					'Workspace imported. The video was missing, so it was auto-downloaded from the saved URL.'
				)
			} else {
				setStatus('Workspace imported')
				window.alert('Workspace imported successfully!')
			}
			return true
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Import failed'
			window.alert(`Failed to import workspace: ${message}`)
			return false
		}
	}

	async function quickExport(format: 'csv' | 'json'): Promise<void> {
		if (!videoInfo.value || scenes.value.length === 0) {
			window.alert('Nothing to export')
			return
		}
		try {
			const response = await apiPost<{ success?: boolean; download_url?: string }>(
				'/api/export-scenes-rois',
				{ format, scenes: scenes.value, video_info: videoInfo.value }
			)
			if (response.download_url) {
				window.open(response.download_url, '_blank')
				setStatus(`Exported ${format.toUpperCase()}`)
			}
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Export failed'
			window.alert(`Export failed: ${message}`)
		}
	}

	return {
		showSaveAsModal,
		saveAsFilename,
		saveWorkspace,
		openSaveAsModal,
		confirmSaveAs,
		importWorkspaceFile,
		quickExport
	}
}
