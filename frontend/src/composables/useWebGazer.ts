import { ref } from 'vue'
import type { WebGazerInstance } from 'webgazer'

export type WebGazerStatus = 'idle' | 'starting' | 'running' | 'error'

export interface BrowserCameraInfo {
	deviceId: string
	label: string
}

type GazeHandler = (x: number, y: number) => void

const WEBGAZER_CAMERA_STORAGE_KEY = 'sorot.webgazerCameraId'

let refCount = 0
let started = false
let webgazerModule: WebGazerInstance | null = null
const handlers = new Set<GazeHandler>()

const status = ref<WebGazerStatus>('idle')
const errorMessage = ref<string | null>(null)
const preferredCameraId = ref<string | null>(readPreferredCameraId())
const browserCameras = ref<BrowserCameraInfo[]>([])
const listingCameras = ref(false)

function readPreferredCameraId(): string | null {
	if (typeof window === 'undefined') return null
	try {
		const stored = window.localStorage.getItem(WEBGAZER_CAMERA_STORAGE_KEY)
		return stored?.trim() || null
	} catch {
		return null
	}
}

function persistPreferredCameraId(deviceId: string | null): void {
	if (typeof window === 'undefined') return
	try {
		if (deviceId) {
			window.localStorage.setItem(WEBGAZER_CAMERA_STORAGE_KEY, deviceId)
		} else {
			window.localStorage.removeItem(WEBGAZER_CAMERA_STORAGE_KEY)
		}
	} catch {
		// Ignore quota / private-mode failures.
	}
}

function buildCameraConstraints(deviceId: string | null): MediaStreamConstraints {
	const video: MediaTrackConstraints = {
		width: { min: 320, ideal: 640, max: 1920 },
		height: { min: 240, ideal: 480, max: 1080 }
	}
	if (deviceId) {
		video.deviceId = { exact: deviceId }
	} else {
		video.facingMode = 'user'
	}
	return { video }
}

function resolveWebGazerModule(mod: unknown): WebGazerInstance {
	const candidate =
		(mod as { default?: WebGazerInstance }).default ??
		(mod as WebGazerInstance)

	if (!candidate?.begin || !candidate.setTracker) {
		throw new Error('WebGazer module failed to load.')
	}

	return candidate
}

async function loadWebGazer(): Promise<WebGazerInstance> {
	if (webgazerModule) return webgazerModule
	const mod = await import('webgazer')
	webgazerModule = resolveWebGazerModule(mod)
	return webgazerModule
}

function notifyHandlers(x: number, y: number): void {
	if (!Number.isFinite(x) || !Number.isFinite(y)) return
	for (const handler of handlers) {
		handler(x, y)
	}
}

async function startInternal(): Promise<boolean> {
	if (typeof window === 'undefined') return false
	if (started) {
		status.value = 'running'
		return true
	}

	status.value = 'starting'
	errorMessage.value = null

	try {
		const webgazer = await loadWebGazer()
		if (!webgazer.detectCompatibility()) {
			throw new Error('This browser does not support webcam access (getUserMedia).')
		}

		webgazer.clearGazeListener()
		webgazer.removeMouseEventListeners()

		webgazer
			.saveDataAcrossSessions(true)
			.setRegression('ridge')
			.setTracker('TFFacemesh')
			.showVideoPreview(false)
			.showPredictionPoints(false)
			.setGazeListener((data) => {
				if (!data) return
				notifyHandlers(data.x, data.y)
			})

		webgazer.addMouseEventListeners()

		try {
			await webgazer.setCameraConstraints(buildCameraConstraints(preferredCameraId.value))
		} catch {
			if (preferredCameraId.value) {
				await webgazer.setCameraConstraints(buildCameraConstraints(null))
			}
		}

		try {
			await webgazer.begin()
		} catch (beginError) {
			if (!preferredCameraId.value) throw beginError
			await webgazer.setCameraConstraints(buildCameraConstraints(null))
			await webgazer.begin()
		}

		started = true
		status.value = 'running'
		return true
	} catch (error) {
		status.value = 'error'
		errorMessage.value =
			error instanceof Error ? error.message : 'WebGazer failed to start.'
		return false
	}
}

function stopInternal(): void {
	if (!started || refCount > 0) return
	if (!webgazerModule) {
		status.value = 'idle'
		return
	}

	webgazerModule.clearGazeListener()
	webgazerModule.removeMouseEventListeners()

	try {
		webgazerModule.stopVideo()
	} catch {
		// Camera may already be stopped.
	}

	try {
		webgazerModule.end()
	} catch {
		// DOM nodes may already be removed.
	}

	started = false
	status.value = 'idle'
	errorMessage.value = null
}

export function useWebGazer() {
	function onGaze(handler: GazeHandler): () => void {
		handlers.add(handler)
		return () => {
			handlers.delete(handler)
		}
	}

	async function start(): Promise<boolean> {
		refCount += 1
		const ok = await startInternal()
		if (!ok) {
			refCount = Math.max(0, refCount - 1)
		}
		return ok
	}

	function stop(): void {
		refCount = Math.max(0, refCount - 1)
		stopInternal()
	}

	/** Stop camera immediately regardless of ref-count (device deselected). */
	function shutdown(): void {
		refCount = 0
		stopInternal()
	}

	function isReady(): boolean {
		return started && (webgazerModule?.isReady() ?? false)
	}

	async function listBrowserCameras(): Promise<void> {
		if (typeof navigator === 'undefined' || !navigator.mediaDevices?.enumerateDevices) {
			browserCameras.value = []
			return
		}

		listingCameras.value = true
		try {
			let devices = await navigator.mediaDevices.enumerateDevices()
			const videoInputs = devices.filter((device) => device.kind === 'videoinput')
			const missingLabels = videoInputs.length === 0 || videoInputs.some((device) => !device.label)
			if (missingLabels) {
				const stream = await navigator.mediaDevices.getUserMedia({ video: true })
				stream.getTracks().forEach((track) => track.stop())
				devices = await navigator.mediaDevices.enumerateDevices()
			}
			browserCameras.value = devices
				.filter((device) => device.kind === 'videoinput')
				.map((device, index) => ({
					deviceId: device.deviceId,
					label: device.label.trim() || `Camera ${index + 1}`
				}))
		} catch (error) {
			errorMessage.value =
				error instanceof Error ? error.message : 'Could not list browser cameras.'
		} finally {
			listingCameras.value = false
		}
	}

	async function setPreferredCameraId(deviceId: string | null): Promise<void> {
		preferredCameraId.value = deviceId
		persistPreferredCameraId(deviceId)
		if (!started) return

		const keepCount = refCount
		shutdown()
		refCount = keepCount
		await startInternal()
	}

	return {
		status,
		errorMessage,
		preferredCameraId,
		browserCameras,
		listingCameras,
		onGaze,
		start,
		stop,
		shutdown,
		isReady,
		listBrowserCameras,
		setPreferredCameraId
	}
}
