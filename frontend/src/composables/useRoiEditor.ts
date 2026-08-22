import { computed, type Ref } from 'vue'
import type { WorkspaceRoi, WorkspaceScene } from '../types/workspace'

const ROI_COLOR_PALETTE = [
	'#61AFEF',
	'#98C379',
	'#E5C07B',
	'#E06C75',
	'#C678DD',
	'#56B6C2',
	'#D19A66',
	'#BE5046'
] as const

export interface RoiBounds {
	x: number
	y: number
	width: number
	height: number
}

export function useRoiEditor(
	scenes: Ref<WorkspaceScene[]>,
	currentScene: Ref<WorkspaceScene | null>,
	selectedRoiIdx: Ref<number | null>
) {
	const rois = computed<WorkspaceRoi[]>(() => currentScene.value?.rois ?? [])

	function selectRoi(index: number | null): void {
		if (index === null) {
			selectedRoiIdx.value = null
			return
		}
		if (index < 0 || index >= rois.value.length) return
		selectedRoiIdx.value = index
	}

	function updateRoiBounds(index: number, bounds: RoiBounds): void {
		const scene = currentScene.value
		if (!scene) return
		const roi = scene.rois[index]
		if (!roi) return
		roi.x = Math.round(bounds.x)
		roi.y = Math.round(bounds.y)
		roi.width = Math.round(bounds.width)
		roi.height = Math.round(bounds.height)
	}

	function addRegionOfInterest(bounds: RoiBounds, label?: string): void {
		const scene = currentScene.value
		if (!scene) return
		const nextIndex = scene.rois.length
		const roi: WorkspaceRoi = {
			label: label?.trim() || `ROI ${nextIndex + 1}`,
			x: Math.round(bounds.x),
			y: Math.round(bounds.y),
			width: Math.round(bounds.width),
			height: Math.round(bounds.height),
			color_tag: ROI_COLOR_PALETTE[nextIndex % ROI_COLOR_PALETTE.length]
		}
		scene.rois.push(roi)
		selectedRoiIdx.value = scene.rois.length - 1
	}

	function deleteRoi(index: number): void {
		const scene = currentScene.value
		if (!scene) return
		if (index < 0 || index >= scene.rois.length) return
		scene.rois.splice(index, 1)
		if (scene.rois.length === 0) {
			selectedRoiIdx.value = null
		} else if (selectedRoiIdx.value !== null && selectedRoiIdx.value >= scene.rois.length) {
			selectedRoiIdx.value = scene.rois.length - 1
		}
	}

	function renameRoi(index: number, label: string): void {
		const scene = currentScene.value
		if (!scene) return
		const roi = scene.rois[index]
		if (!roi) return
		roi.label = label
	}

	return {
		rois,
		selectRoi,
		updateRoiBounds,
		addRegionOfInterest,
		deleteRoi,
		renameRoi
	}
}
