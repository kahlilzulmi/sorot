/** Strip UTF-8 BOM and normalize line endings. */
export function normalizeCsvText(rawText: string): string {
	return rawText.replace(/^\uFEFF/, '').replace(/\r\n/g, '\n').replace(/\r/g, '\n')
}

/**
 * Parse a single CSV record, respecting double-quoted fields and escaped quotes.
 */
export function parseCsvRecord(line: string): string[] {
	const fields: string[] = []
	let current = ''
	let inQuotes = false

	for (let index = 0; index < line.length; index += 1) {
		const character = line[index]

		if (character === '"') {
			if (inQuotes && line[index + 1] === '"') {
				current += '"'
				index += 1
			} else {
				inQuotes = !inQuotes
			}
			continue
		}

		if (character === ',' && !inQuotes) {
			fields.push(current.trim())
			current = ''
			continue
		}

		current += character
	}

	fields.push(current.trim())
	return fields
}

/** Split CSV text into non-empty logical rows (handles quoted newlines). */
export function splitCsvRecords(csvText: string): string[] {
	const records: string[] = []
	let current = ''
	let inQuotes = false

	for (let index = 0; index < csvText.length; index += 1) {
		const character = csvText[index]

		if (character === '"') {
			if (inQuotes && csvText[index + 1] === '"') {
				current += '""'
				index += 1
			} else {
				inQuotes = !inQuotes
				current += character
			}
			continue
		}

		if ((character === '\n' || character === '\r') && !inQuotes) {
			if (character === '\r' && csvText[index + 1] === '\n') {
				index += 1
			}
			if (current.trim().length > 0) {
				records.push(current)
			}
			current = ''
			continue
		}

		current += character
	}

	if (current.trim().length > 0) {
		records.push(current)
	}

	return records
}

export function escapeCsvField(value: string | number): string {
	const text = String(value)
	if (/[",\n\r]/.test(text)) {
		return `"${text.replace(/"/g, '""')}"`
	}
	return text
}

export function buildCsvContent(headers: string[], rows: Array<Array<string | number>>): string {
	const headerLine = headers.map(escapeCsvField).join(',')
	const dataLines = rows.map((row) => row.map(escapeCsvField).join(','))
	return [headerLine, ...dataLines].join('\n')
}
