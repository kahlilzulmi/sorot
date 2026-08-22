import type { GazeCoordinate } from '../types/gaze'
import type { GazeImportSummary } from '../types/gazeImport'

const DB_NAME = 'sorot-local'
const DB_VERSION = 1
const STORE_NAME = 'workspace'
const WORKSPACE_KEY = 'current'

export interface PersistedGazeSnapshot {
	gazeCoordinates: GazeCoordinate[]
	sourceFileName: string | null
	videoFileName: string | null
	videoFps: number | null
	importSummary: GazeImportSummary | null
	savedAt: string
}

/** @deprecated Legacy snapshot shape; ROIs are ignored on restore (scene ROIs come from workspace JSON). */
export interface LegacyPersistedWorkspace extends PersistedGazeSnapshot {
	regionsOfInterest?: unknown[]
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

function normalizeSnapshot(record: LegacyPersistedWorkspace): PersistedGazeSnapshot {
	return {
		gazeCoordinates: record.gazeCoordinates ?? [],
		sourceFileName: record.sourceFileName ?? null,
		videoFileName: record.videoFileName ?? null,
		videoFps: record.videoFps ?? null,
		importSummary: record.importSummary ?? null,
		savedAt: record.savedAt ?? new Date().toISOString()
	}
}

/** Persist imported gaze and video metadata locally (no file blobs). */
export async function saveWorkspaceSnapshot(snapshot: PersistedGazeSnapshot): Promise<void> {
	if (typeof indexedDB === 'undefined') {
		return
	}

	await runTransaction('readwrite', (store) =>
		store.put({ ...snapshot, savedAt: new Date().toISOString() }, WORKSPACE_KEY)
	)
}

/** Restore last saved gaze snapshot, or null when none / unsupported. */
export async function loadWorkspaceSnapshot(): Promise<PersistedGazeSnapshot | null> {
	if (typeof indexedDB === 'undefined') {
		return null
	}

	try {
		const record = await runTransaction<LegacyPersistedWorkspace | undefined>('readonly', (store) =>
			store.get(WORKSPACE_KEY)
		)
		if (!record) return null
		return normalizeSnapshot(record)
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
