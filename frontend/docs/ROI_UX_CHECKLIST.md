# ROI drawing UX verification checklist

Use after layout or canvas changes. All coordinates must stay in **native video pixels**.

## Setup

1. `cd frontend && npm run dev`
2. Load a video and draw at least one ROI per scenario below.

## Alignment (letterboxing)

| Case | Steps | Pass criteria |
|------|--------|----------------|
| 16:9 video | Load 1920×1080 (or similar) in a tall window | ROI corners sit on video edges, not black bars |
| 4:3 video | Load 640×480 in a wide window | Pillars left/right; draw on content only |
| Ultrawide | Load 21:9 in square-ish panel | Letterbox top/bottom; mouse matches frame |
| Resize mid-draw | Start drag, resize window before mouse-up | Box completes on correct pixels; no jump |
| Resize mid-edit | Select ROI, resize window, drag handle | Handle stays under cursor |

## Interaction

- [ ] New ROI: drag empty area → semi-transparent preview → release creates ROI
- [ ] Select: click ROI → green border + corner handles
- [ ] Move: drag body → position updates in sidebar list
- [ ] Resize: each corner (tl/tr/bl/br) respects min size
- [ ] Delete: sidebar button, list ×, or Delete/Backspace key

## Gaze feedback

- [ ] Import CSV with x, y, timestamp
- [ ] Scrub/play: red dot at current-time sample
- [ ] When dot is inside ROI: dashed amber border + slightly stronger fill

## Accessibility / chrome

- [ ] ROI list items ≥44px tall; remove button is tappable
- [ ] Screen reader: playback, import, ROI list labels present
- [ ] Label at top of frame: draws inside ROI, not clipped

## Regression signal

**Before fix:** canvas covered full container; clicks on letterbox mapped to wrong video pixels.

**After fix:** canvas CSS box equals visible `object-contain` frame; `getBoundingClientRect()` on canvas maps 1:1 to `videoWidth`×`videoHeight` bitmap.
