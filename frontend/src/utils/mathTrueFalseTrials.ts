export interface MathTrueFalseTrial {
	id: string
	/** Display equation, e.g. `8 × 7 = 56`. */
	expression: string
	/** Whether the shown equation is mathematically true. */
	isTrue: boolean
}

const OPS = ['+', '-', '×', '÷'] as const
type MathOp = (typeof OPS)[number]

function randInt(min: number, max: number): number {
	return Math.floor(Math.random() * (max - min + 1)) + min
}

function pick<T>(items: readonly T[]): T {
	return items[randInt(0, items.length - 1)] as T
}

function evalOp(a: number, b: number, op: MathOp): number {
	switch (op) {
		case '+':
			return a + b
		case '-':
			return a - b
		case '×':
			return a * b
		case '÷':
			return a / b
	}
}

function formatOp(op: MathOp): string {
	return op
}

function makeTrueEquation(): { expression: string; isTrue: true } {
	const kind = randInt(0, 4)
	if (kind === 4) {
		const base = randInt(2, 9)
		const square = base * base
		return { expression: `${base}² = ${square}`, isTrue: true }
	}
	const op = pick(OPS)
	if (op === '÷') {
		const b = randInt(2, 12)
		const quotient = randInt(2, 12)
		const a = b * quotient
		return { expression: `${a} ${formatOp(op)} ${b} = ${quotient}`, isTrue: true }
	}
	if (op === '×') {
		const a = randInt(2, 12)
		const b = randInt(2, 12)
		return { expression: `${a} ${formatOp(op)} ${b} = ${a * b}`, isTrue: true }
	}
	if (op === '+') {
		const a = randInt(10, 200)
		const b = randInt(10, 200)
		return { expression: `${a} ${formatOp(op)} ${b} = ${a + b}`, isTrue: true }
	}
	const a = randInt(20, 200)
	const b = randInt(1, a - 1)
	return { expression: `${a} ${formatOp(op)} ${b} = ${a - b}`, isTrue: true }
}

function makeFalseEquation(): { expression: string; isTrue: false } {
	const trueEq = makeTrueEquation()
	const match = trueEq.expression.match(/^(.*?)=\s*(-?\d+)\s*$/)
	if (!match) {
		return { expression: '2 + 2 = 5', isTrue: false }
	}
	const left = match[1]?.trim() ?? ''
	const correct = Number(match[2])
	let wrong = correct + pick([-3, -2, -1, 1, 2, 3, 5, 10])
	if (wrong === correct) wrong = correct + 1
	return { expression: `${left} = ${wrong}`, isTrue: false }
}

/** Build a session of True/False equation trials (UFYP-style Benar/Salah). */
export function createMathTrueFalseSession(count = 5): MathTrueFalseTrial[] {
	const trials: MathTrueFalseTrial[] = []
	for (let i = 0; i < count; i += 1) {
		const makeTrue = i % 2 === 0 ? Math.random() < 0.55 : Math.random() < 0.45
		const built = makeTrue ? makeTrueEquation() : makeFalseEquation()
		trials.push({
			id: `math-tf-${i}-${Date.now()}-${randInt(100, 999)}`,
			expression: built.expression,
			isTrue: built.isTrue
		})
	}
	// Ensure at least one true and one false when count >= 2.
	if (count >= 2) {
		const hasTrue = trials.some((t) => t.isTrue)
		const hasFalse = trials.some((t) => !t.isTrue)
		if (!hasTrue) {
			const built = makeTrueEquation()
			trials[0] = { ...trials[0]!, expression: built.expression, isTrue: true }
		}
		if (!hasFalse) {
			const built = makeFalseEquation()
			trials[1] = { ...trials[1]!, expression: built.expression, isTrue: false }
		}
	}
	return trials
}

/** Silence unused-eval warning helper for future fill-blank. */
export function previewEval(a: number, b: number, op: MathOp): number {
	return evalOp(a, b, op)
}
