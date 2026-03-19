"""
Trim ground truth CSV - remove opening frames, keep only 1 frame for opening.
"""

import pandas as pd

# Load original
df = pd.read_csv("../stimulus_ground_truth.csv")
print(f"Original frames: {len(df)}")

# Keep only 1 opening frame (frame 0), then start from TUTORIAL_INSTRUCTION (original frame 300)
opening_frame = df[df['frame'] == 0].copy()
rest_frames = df[df['frame'] >= 300].copy()

# Combine
trimmed = pd.concat([opening_frame, rest_frames], ignore_index=True)

# Renumber frames starting from 0
trimmed['frame'] = range(len(trimmed))
trimmed['timestamp'] = trimmed['frame'] / 60.0

print(f"Trimmed frames: {len(trimmed)}")
print(f"First GT data at frame: {trimmed[trimmed['gt_x_px'].notna()].iloc[0]['frame']}")

# Save
output_path = "../stimulus_ground_truth_trimmed.csv"
trimmed.to_csv(output_path, index=False)
print(f"Saved to: {output_path}")
