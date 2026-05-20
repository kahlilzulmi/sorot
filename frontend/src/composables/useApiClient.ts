export class ApiError extends Error {
	readonly status: number
	readonly body: unknown

	constructor(message: string, status: number, body: unknown = undefined) {
		super(message)
		this.name = 'ApiError'
		this.status = status
		this.body = body
	}
}

async function parseJsonSafe(response: Response): Promise<unknown> {
	const text = await response.text()
	if (!text) return undefined
	try {
		return JSON.parse(text) as unknown
	} catch {
		return text
	}
}

function errorMessage(body: unknown, fallback: string): string {
	if (body && typeof body === 'object' && 'error' in body) {
		const err = (body as { error?: unknown }).error
		if (typeof err === 'string') return err
	}
	return fallback
}

export async function apiGet<T>(path: string): Promise<T> {
	const response = await fetch(path)
	const body = await parseJsonSafe(response)
	if (!response.ok) {
		throw new ApiError(errorMessage(body, response.statusText), response.status, body)
	}
	return body as T
}

export async function apiPost<T>(path: string, payload?: unknown): Promise<T> {
	const response = await fetch(path, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: payload === undefined ? undefined : JSON.stringify(payload)
	})
	const body = await parseJsonSafe(response)
	if (!response.ok) {
		throw new ApiError(errorMessage(body, response.statusText), response.status, body)
	}
	return body as T
}

export async function apiPostForm<T>(path: string, formData: FormData): Promise<T> {
	const response = await fetch(path, {
		method: 'POST',
		body: formData
	})
	const body = await parseJsonSafe(response)
	if (!response.ok) {
		throw new ApiError(errorMessage(body, response.statusText), response.status, body)
	}
	return body as T
}
