declare module 'webgazer' {
	export interface WebGazerGazeData {
		x: number
		y: number
	}

	export interface WebGazerInstance {
		detectCompatibility(): boolean
		isReady(): boolean
		begin(onFail?: () => void): Promise<WebGazerInstance>
		pause(): WebGazerInstance
		resume(): Promise<WebGazerInstance>
		end(): WebGazerInstance
		stopVideo(): WebGazerInstance
		setGazeListener(
			listener: (data: WebGazerGazeData | null, elapsedTime: number) => void
		): WebGazerInstance
		clearGazeListener(): WebGazerInstance
		addMouseEventListeners(): WebGazerInstance
		removeMouseEventListeners(): WebGazerInstance
		setRegression(name: string): WebGazerInstance
		setTracker(name: string): WebGazerInstance
		showVideoPreview(val: boolean): WebGazerInstance
		showPredictionPoints(val: boolean): WebGazerInstance
		saveDataAcrossSessions(val: boolean): WebGazerInstance
		setCameraConstraints(constraints: MediaStreamConstraints): Promise<void>
	}

	const webgazer: WebGazerInstance
	export default webgazer
}
