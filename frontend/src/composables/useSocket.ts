import { onBeforeUnmount, ref } from 'vue'
import { io, type Socket } from 'socket.io-client'

export interface GazeDetectedPayload {
	x: number
	y: number
	frame?: number
	timestamp?: number
}

export function useSocket() {
	const connected = ref(false)
	let socket: Socket | null = null

	function connect(): void {
		if (socket?.connected) return
		socket = io({
			path: '/socket.io',
			transports: ['websocket', 'polling']
		})

		socket.on('connect', () => {
			connected.value = true
		})
		socket.on('disconnect', () => {
			connected.value = false
		})
	}

	function disconnect(): void {
		socket?.disconnect()
		socket = null
		connected.value = false
	}

	function onGazeDetected(handler: (payload: GazeDetectedPayload) => void): void {
		socket?.on('gaze_detected', handler)
	}

	function offGazeDetected(handler: (payload: GazeDetectedPayload) => void): void {
		socket?.off('gaze_detected', handler)
	}

	function emitRecordFrame(frameNum: number, timestamp: number): void {
		socket?.emit('record_frame', { frame_num: frameNum, timestamp })
	}

	onBeforeUnmount(() => {
		disconnect()
	})

	return {
		connected,
		connect,
		disconnect,
		onGazeDetected,
		offGazeDetected,
		emitRecordFrame
	}
}
