export type GazeDeviceCategory = 'fallback' | 'eye_tracker' | 'webcam' | 'custom'

/** How the frontend/backend will eventually source gaze samples for this device. */
export type GazeDeviceTransport =
	| 'mouse'
	| 'tobii_overlay'
	| 'tobii_sdk'
	| 'virtual_camera'
	| 'webgazer'
	| 'import_only'
	| 'custom'

export interface GazeDeviceDefinition {
	id: string
	name: string
	manufacturer: string
	category: GazeDeviceCategory
	transport: GazeDeviceTransport
	description: string
	builtin: boolean
}

export interface CustomGazeDeviceInput {
	name: string
	manufacturer: string
	description: string
}

export const BUILTIN_GAZE_DEVICES: GazeDeviceDefinition[] = [
	{
		id: 'mouse-pointer',
		name: 'Mouse pointer',
		manufacturer: 'System fallback',
		category: 'fallback',
		transport: 'mouse',
		description: 'Use the mouse cursor as gaze input. Works on any machine without hardware.',
		builtin: true
	},
	{
		id: 'tobii-eye-tracker-5',
		name: 'Tobii Eye Tracker 5',
		manufacturer: 'Tobii',
		category: 'eye_tracker',
		transport: 'tobii_overlay',
		description: 'Consumer eye tracker via Tobii Ghost virtual camera and overlay marker detection.',
		builtin: true
	},
	{
		id: 'tobii-eye-tracker-4',
		name: 'Tobii Eye Tracker 4',
		manufacturer: 'Tobii',
		category: 'eye_tracker',
		transport: 'tobii_overlay',
		description: 'Tobii Eye Tracker 4 with virtual camera overlay pipeline.',
		builtin: true
	},
	{
		id: 'tobii-pro-spectrum',
		name: 'Tobii Pro Spectrum',
		manufacturer: 'Tobii',
		category: 'eye_tracker',
		transport: 'tobii_sdk',
		description: 'Research-grade Tobii Pro Spectrum (SDK integration planned).',
		builtin: true
	},
	{
		id: 'tobii-pro-nano',
		name: 'Tobii Pro Nano',
		manufacturer: 'Tobii',
		category: 'eye_tracker',
		transport: 'tobii_sdk',
		description: 'Compact Tobii Pro Nano (SDK integration planned).',
		builtin: true
	},
	{
		id: 'tobii-pro-spark',
		name: 'Tobii Pro Spark',
		manufacturer: 'Tobii',
		category: 'eye_tracker',
		transport: 'tobii_sdk',
		description: 'Tobii Pro Spark mobile eye tracker (SDK integration planned).',
		builtin: true
	},
	{
		id: 'pupil-neon',
		name: 'Pupil Neon',
		manufacturer: 'Pupil Labs',
		category: 'eye_tracker',
		transport: 'import_only',
		description: 'Pupil Labs Neon — import gaze stream or connect via custom pipeline.',
		builtin: true
	},
	{
		id: 'pupil-core',
		name: 'Pupil Core',
		manufacturer: 'Pupil Labs',
		category: 'eye_tracker',
		transport: 'import_only',
		description: 'Pupil Core DIY eye tracker — import gaze data or add a custom device.',
		builtin: true
	},
	{
		id: 'gazepoint-gp3',
		name: 'GP3',
		manufacturer: 'Gazepoint',
		category: 'eye_tracker',
		transport: 'import_only',
		description: 'Gazepoint GP3 desktop eye tracker (live bridge planned).',
		builtin: true
	},
	{
		id: 'smart-eye-pro',
		name: 'Smart Eye Pro',
		manufacturer: 'Smart Eye',
		category: 'eye_tracker',
		transport: 'import_only',
		description: 'Smart Eye Pro automotive/research tracker (live bridge planned).',
		builtin: true
	},
	{
		id: 'eyelink-1000-plus',
		name: 'EyeLink 1000 Plus',
		manufacturer: 'SR Research',
		category: 'eye_tracker',
		transport: 'import_only',
		description: 'SR Research EyeLink 1000 Plus — typically used with imported gaze files.',
		builtin: true
	},
	{
		id: 'varjo-xr3',
		name: 'Varjo XR-3',
		manufacturer: 'Varjo',
		category: 'eye_tracker',
		transport: 'import_only',
		description: 'Varjo XR-3 mixed reality headset eye tracking (live bridge planned).',
		builtin: true
	},
	{
		id: 'htc-vive-pro-eye',
		name: 'VIVE Pro Eye',
		manufacturer: 'HTC',
		category: 'eye_tracker',
		transport: 'import_only',
		description: 'HTC VIVE Pro Eye VR headset eye tracking (live bridge planned).',
		builtin: true
	},
	{
		id: 'pimax-crystal',
		name: 'Pimax Crystal',
		manufacturer: 'Pimax',
		category: 'eye_tracker',
		transport: 'import_only',
		description: 'Pimax Crystal headset eye tracking (live bridge planned).',
		builtin: true
	},
	{
		id: 'webcam-webgazer',
		name: 'Webcam (WebGazer)',
		manufacturer: 'WebGazer.js',
		category: 'webcam',
		transport: 'webgazer',
		description: 'Standard webcam with browser-based WebGazer.js gaze estimation (client-side).',
		builtin: true
	},
	{
		id: 'generic-webcam',
		name: 'Generic webcam',
		manufacturer: 'Custom',
		category: 'webcam',
		transport: 'custom',
		description: 'Any USB webcam — add as a custom device and wire your own gaze pipeline.',
		builtin: true
	},
	{
		id: 'virtual-camera-overlay',
		name: 'Virtual camera overlay',
		manufacturer: 'Generic',
		category: 'eye_tracker',
		transport: 'virtual_camera',
		description: 'Any eye tracker that exposes a virtual camera with an on-screen gaze marker.',
		builtin: true
	}
]

export const DEFAULT_GAZE_DEVICE_ID = 'mouse-pointer'

export const GAZE_DEVICE_STORAGE_KEY = 'sorot.gazeDeviceId'
export const CUSTOM_GAZE_DEVICES_STORAGE_KEY = 'sorot.customGazeDevices'

export function categoryLabel(category: GazeDeviceCategory): string {
	switch (category) {
		case 'fallback':
			return 'Fallback'
		case 'eye_tracker':
			return 'Eye tracker'
		case 'webcam':
			return 'Webcam'
		case 'custom':
			return 'Custom'
	}
}

export function createCustomDeviceId(): string {
	return `custom-${crypto.randomUUID()}`
}

export function buildCustomDevice(input: CustomGazeDeviceInput, id = createCustomDeviceId()): GazeDeviceDefinition {
	return {
		id,
		name: input.name.trim(),
		manufacturer: input.manufacturer.trim() || 'Custom',
		category: 'custom',
		transport: 'custom',
		description: input.description.trim() || 'User-defined gaze input device.',
		builtin: false
	}
}
