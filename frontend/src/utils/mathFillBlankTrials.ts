export type MathFillBlankSlot = 'a' | 'b' | 'result'

export interface MathFillBlankTrial {
	id: string
	op: '+' | '-' | '×' | '÷'
	a: number
	b: number
	result: number
	blankSlot: MathFillBlankSlot
	/** Four options; exactly one equals the blanked value. */
	choices: [number, number, number, number]
}

const OPS = ['+', '-', '×', '÷'] as const
type MathOp = (typeof OPS)[number]

function randInt(min: number, max: number): number {
	return Math.floor(Math.random() * (max - min + 1)) + min
}

function pick<T>(items: readonly T[]): T {
	return items[randInt(0, items.length - 1)] as T
}

function shuffleInPlace<T>(items: T[]): T[] {
	for (let i = items.length - 1; i > 0; i -= 1) {
		const j = randInt(0, i)
		const tmp = items[i]!
		items[i] = items[j]!
		items[j] = tmp
	}
	return items
}

function buildEquation(): { op: MathOp; a: number; b: number; result: number } {
	const op = pick(OPS)
	if (op === '÷') {
		const b = randInt(2, 12)
		const result = randInt(2, 12)
		return { op, a: b * result, b, result }
	}
	if (op === '×') {
		const a = randInt(2, 12)
		const b = randInt(2, 12)
		return { op, a, b, result: a * b }
	}
	if (op === '+') {
		const a = randInt(1, 50)
		const b = randInt(1, 50)
		return { op, a, b, result: a + b }
	}
	const a = randInt(10, 80)
	const b = randInt(1, a - 1)
	return { op, a, b, result: a - b }
}

function blankValue(eq: { a: number; b: number; result: number }, slot: MathFillBlankSlot): number {
	if (slot === 'a') return eq.a
	if (slot === 'b') return eq.b
	return eq.result
}

function makeDistractors(correct: number): number[] {
	const distractors = new Set<number>()
	const deltas = [-5, -3, -2, -1, 1, 2, 3, 4, 5, 6, 8, 10]
	while (distractors.size < 3) {
		const candidate = correct + pick(deltas)
		if (candidate !== correct && candidate >= 0) {
			distractors.add(candidate)
		}
	}
	return [...distractors]
}

function makeTrial(index: number): MathFillBlankTrial {
	const eq = buildEquation()
	const blankSlot = pick(['a', 'b', 'result'] as const)
	const correct = blankValue(eq, blankSlot)
	const choices = shuffleInPlace([correct, ...makeDistractors(correct)]) as [
		number,
		number,
		number,
		number
	]
	return {
		id: `math-fb-${index}-${Date.now()}-${randInt(100, 999)}`,
		op: eq.op,
		a: eq.a,
		b: eq.b,
		result: eq.result,
		blankSlot,
		choices
	}
}

/** Prompt with `...` in the blank slot (UFYP fill-blank style). */
export function formatFillBlankPrompt(trial: MathFillBlankTrial): string {
	const a = trial.blankSlot === 'a' ? '...' : String(trial.a)
	const b = trial.blankSlot === 'b' ? '...' : String(trial.b)
	const result = trial.blankSlot === 'result' ? '...' : String(trial.result)
	return `${a} ${trial.op} ${b} = ${result}`
}

/** Fill blank with a chosen value (for correct/wrong feedback display). */
export function formatFillBlankFilled(trial: MathFillBlankTrial, chosen: number): string {
	const a = trial.blankSlot === 'a' ? String(chosen) : String(trial.a)
	const b = trial.blankSlot === 'b' ? String(chosen) : String(trial.b)
	const result = trial.blankSlot === 'result' ? String(chosen) : String(trial.result)
	return `${a} ${trial.op} ${b} = ${result}`
}

export function correctFillBlankAnswer(trial: MathFillBlankTrial): number {
	return blankValue(trial, trial.blankSlot)
}

/** Build a session of fill-blank equation trials (2×2 answer grid). */
export function createMathFillBlankSession(count = 5): MathFillBlankTrial[] {
	const trials: MathFillBlankTrial[] = []
	for (let i = 0; i < count; i += 1) {
		trials.push(makeTrial(i))
	}
	return trials
}
