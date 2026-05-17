import type { GazeCoordinate, RegionOfInterest } from '../types/gaze'
import type { GazeImportSummary } from '../stores/useGazeStore'

const DB_NAME = 'sorot-local'
const DB_VERSION = 1
const STORE_NAME = 'workspace'
const WORKSPACE_KEY = 'current'

export interface PersistedWorkspace {
	gazeCoordinates: GazeCoordinate[]
	regionsOfInterest: RegionOfInterest[]
	sourceFileName: string | null
	videoFileName: string | null
	videoFps: number | null
	importSummary: GazeImportSummary | null
	savedAt: string
}

function openDatabase(): Promise<IDBDatabase> {
	return new Promise((resolve, reject) => {
		const request = indexedDB.open(DB_NAME, DB_VERSION)

		request.onerror = () => {
			reject(request.error ?? new Error('Failed to open IndexedDB'))
		}

		request.onupgradeneeded = () => {
			const database = request.result
			if (!database.objectStoreNames.contains(STORE_NAME)) {
				database.createObjectStore(STORE_NAME)
			}
		}

		request.onsuccess = () => {
			resolve(request.result)
		}
	})
}

function runTransaction<T>(
	mode: IDBTransactionMode,
	run: (store: IDBObjectStore) => IDBRequest<T>
): Promise<T> {
	return openDatabase().then(
		(database) =>
			new Promise<T>((resolve, reject) => {
				const transaction = database.transaction(STORE_NAME, mode)
				const store = transaction.objectStore(STORE_NAME)
				const request = run(store)

				request.onerror = () => {
					reject(request.error ?? new Error('IndexedDB request failed'))
				}

				transaction.oncomplete = () => {
					resolve(request.result)
				}

				transaction.onerror = () => {
					reject(transaction.error ?? new Error('IndexedDB transaction failed'))
				}
			})
	)
}

/** Persist gaze, ROIs, and video metadata locally (no file blobs). */
export async function saveWorkspaceSnapshot(snapshot: PersistedWorkspace): Promise<void> {
	if (typeof indexedDB === 'undefined') {
		return
	}

	await runTransaction('readwrite', (store) =>
		store.put({ ...snapshot, savedAt: new Date().toISOString() }, WORKSPACE_KEY)
	)
}

/** Restore last saved workspace, or null when none / unsupported. */
export async function loadWorkspaceSnapshot(): Promise<PersistedWorkspace | null> {
	if (typeof indexedDB === 'undefined') {
		return null
	}

	try {
		const record = await runTransaction<PersistedWorkspace | undefined>('readonly', (store) =>
			store.get(WORKSPACE_KEY)
		)
		return record ?? null
	} catch {
		return null
	}
}

export async function clearWorkspaceSnapshot(): Promise<void> {
	if (typeof indexedDB === 'undefined') {
		return
	}

	try {
		await runTransaction('readwrite', (store) => store.delete(WORKSPACE_KEY))
	} catch {
		// Ignore cleanup failures
	}
}
