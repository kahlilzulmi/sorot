const fs = require('fs')

// --- Shell: remove in-game asset editor; gate Play on face photos ---
{
	const p = 'frontend/src/components/cognitive/CognitiveGameShell.vue'
	let s = fs.readFileSync(p, 'utf8')

	if (!s.includes('hasSuppliedFacePhotos')) {
		s = s.replace(
			"import FaceFamiliarityGame from './FaceFamiliarityGame.vue'",
			"import FaceFamiliarityGame from './FaceFamiliarityGame.vue'\nimport {\n\thasSuppliedFacePhotos,\n\tfacePhotosMissingMessage\n} from '../../utils/faceFamiliarityAssets'"
		)
	}

	s = s.replace(
		/\n\t\t\t\t\t@asset-editor-change="onFaceAssetEditorChange"/,
		''
	)
	s = s.replace(/\nconst faceAssetEditorOpen = ref\(false\)/, '')
	s = s.replace(
		/\n\t\t!faceAssetEditorOpen\.value/,
		''
	)
	s = s.replace(
		/\n\t\tfaceAssetEditorOpen\.value/,
		''
	)
	// clean hideOsCursor / dwellPaused if trailing && alone
	s = s.replace(
		/const hideOsCursor = computed\(\n\t\(\) =>\n\t\tinGame\.value &&\n\t\t!settingsOpen\.value &&\n\t\t!quitConfirmOpen\.value\n\)/,
		`const hideOsCursor = computed(\n\t() => inGame.value && !settingsOpen.value && !quitConfirmOpen.value\n)`
	)
	s = s.replace(
		/const dwellPaused = computed\(\n\t\(\) =>\n\t\t!inGame\.value \|\|\n\t\tsettingsOpen\.value \|\|\n\t\tquitConfirmOpen\.value\n\)/,
		`const dwellPaused = computed(\n\t() => !inGame.value || settingsOpen.value || quitConfirmOpen.value\n)`
	)

	s = s.replace(
		/function onFaceAssetEditorChange\(open: boolean\): void \{\n\tfaceAssetEditorOpen\.value = open\n\}\n\n/,
		''
	)
	s = s.replace(/\n\tfaceAssetEditorOpen\.value = false/, '')

	if (!s.includes('ensureFacePhotosReady')) {
		s = s.replace(
			'function startSingle(id: CognitiveGameId): void {',
			`function ensureFacePhotosReady(id: CognitiveGameId): boolean {
	if (id !== 'face-familiarity') return true
	if (hasSuppliedFacePhotos()) return true
	window.alert(facePhotosMissingMessage())
	return false
}

function startSingle(id: CognitiveGameId): void {
	if (!ensureFacePhotosReady(id)) return`
		)
	}

	if (!s.includes('ensureFacePhotosReady(ids[0]')) {
		s = s.replace(
			`function startPlaylist(): void {
	const ids = playableIds.value
	if (ids.length === 0) return
	playlistMode.value = true`,
			`function startPlaylist(): void {
	const ids = playableIds.value
	if (ids.length === 0) return
	if (ids.includes('face-familiarity') && !hasSuppliedFacePhotos()) {
		window.alert(facePhotosMissingMessage())
		return
	}
	playlistMode.value = true`
		)
	}

	fs.writeFileSync(p, s)
	console.log('shell', {
		import: s.includes('hasSuppliedFacePhotos'),
		guard: s.includes('ensureFacePhotosReady'),
		noAssetEvt: !s.includes('asset-editor-change'),
		noFaceEditor: !s.includes('faceAssetEditorOpen')
	})
}

// --- Settings panel: fix import names to match assets exports ---
{
	const p = 'frontend/src/components/cognitive/CognitiveGameSettingsPanel.vue'
	let s = fs.readFileSync(p, 'utf8')
	s = s.replace(/readImageFileAsDataUrl/g, 'readImageFileAsDataUrl')
	s = s.replace(
		/isFacePairFullySupplied/g,
		'isFacePairFullySupplied'
	)
	// If wrong names from earlier drafts:
	s = s.replace(/readImageFileAsDataUrl/g, 'readImageFileAsDataUrl')
	fs.writeFileSync(p, s)

	// Verify imports exist in file
	const needs = [
		'readImageFileAsDataUrl',
		'isFacePairFullySupplied',
		'isPlaceholderImageSrc',
		'loadFacePairs',
		'saveFacePairs',
		'resetFacePairsToDefaults',
		'dwellMsForGame',
		'setGameDwellMs'
	]
	for (const n of needs) {
		if (!s.includes(n)) console.log('MISSING in settings', n)
	}
	console.log('settings imports ok-ish')
}
