const fs = require('fs')
const p = 'frontend/src/components/cognitive/CognitiveGameShell.vue'
let s = fs.readFileSync(p, 'utf8')

if (!s.includes("from '../../utils/faceFamiliarityAssets'")) {
	s = s.replace(
		"import FaceFamiliarityGame from './FaceFamiliarityGame.vue'",
		"import FaceFamiliarityGame from './FaceFamiliarityGame.vue'\nimport {\n\thasSuppliedFacePhotos,\n\tfacePhotosMissingMessage\n} from '../../utils/faceFamiliarityAssets'"
	)
}

s = s.replace(/\n\t\t\t\t\t@asset-editor-change="onFaceAssetEditorChange"/, '')
s = s.replace(/\nconst faceAssetEditorOpen = ref\(false\)\r?/, '\n')

s = s.replace(
	/const hideOsCursor = computed\(\r?\n\t\(\) =>\r?\n\t\tinGame\.value &&\r?\n\t\t!settingsOpen\.value &&\r?\n\t\t!quitConfirmOpen\.value &&\r?\n\t\t!faceAssetEditorOpen\.value\r?\n\)/,
	'const hideOsCursor = computed(\n\t() => inGame.value && !settingsOpen.value && !quitConfirmOpen.value\n)'
)

s = s.replace(
	/const dwellPaused = computed\(\r?\n\t\(\) =>\r?\n\t\t!inGame\.value \|\|\r?\n\t\tsettingsOpen\.value \|\|\r?\n\t\tquitConfirmOpen\.value \|\|\r?\n\t\tfaceAssetEditorOpen\.value\r?\n\)/,
	'const dwellPaused = computed(\n\t() => !inGame.value || settingsOpen.value || quitConfirmOpen.value\n)'
)

s = s.replace(
	/function onFaceAssetEditorChange\(open: boolean\): void \{\r?\n\tfaceAssetEditorOpen\.value = open\r?\n\}\r?\n\r?\n/,
	''
)

s = s.replace(/\r?\n\tfaceAssetEditorOpen\.value = false/, '')

if (!s.includes('function ensureFacePhotosReady')) {
	s = s.replace(
		'function startSingle(id: CognitiveGameId): void {\n\tplaylistMode.value = false',
		`function ensureFacePhotosReady(id: CognitiveGameId): boolean {
	if (id !== 'face-familiarity') return true
	if (hasSuppliedFacePhotos()) return true
	window.alert(facePhotosMissingMessage())
	return false
}

function startSingle(id: CognitiveGameId): void {
	if (!ensureFacePhotosReady(id)) return
	playlistMode.value = false`
	)
}

if (!s.includes("ids.includes('face-familiarity')")) {
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
console.log({
	import: s.includes('hasSuppliedFacePhotos'),
	guardSingle: s.includes('ensureFacePhotosReady'),
	guardPlaylist: s.includes("ids.includes('face-familiarity')"),
	noAsset: !s.includes('faceAssetEditorOpen') && !s.includes('asset-editor-change')
})
