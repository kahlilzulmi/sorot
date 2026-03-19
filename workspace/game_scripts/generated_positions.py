import numpy as np
import pandas as pd
import os

# ==============================================================================
# 1. CONFIGURATION (Must match genvidsim4.py)
# ==============================================================================
WIDTH, HEIGHT = 1920, 1080
FPS = 60

# Durations (seconds)
DURASI_PERINTAH = 3
DURASI_PERSIAPAN = 3
DURASI_BUKA_TUTUP = 5
DURASI_TUTORIAL = 8
DURASI_FIKSASI = 5
DURASI_GERAK_HALUS = 10
DURASI_SAKADIK_PER_TITIK = 3

# Global Frame Counter
current_frame = 0
frame_data = []

# ==============================================================================
# 2. RECORDING FUNCTIONS
# ==============================================================================

def record_frames(duration_sec, x=None, y=None, phase_name="unknown"):
    """
    Records frame data for a specific duration.
    If x or y is None, it's treated as a non-target frame (NaN).
    """
    global current_frame
    num_frames = int(duration_sec * FPS)
    
    for _ in range(num_frames):
        # If x or y is None, we store np.nan
        val_x = x if x is not None else np.nan
        val_y = y if y is not None else np.nan
        
        frame_data.append({
            "frame": current_frame,
            "timestamp": current_frame / FPS,
            "phase": phase_name,
            "gt_x_px": val_x,
            "gt_y_px": val_y,
            "gt_x_norm": val_x / WIDTH if x is not None else np.nan,
            "gt_y_norm": val_y / HEIGHT if y is not None else np.nan
        })
        current_frame += 1

def run_task_wrapper(task_name, task_func, task_duration, **kwargs):
    """
    Simulates the run_task wrapper from genvidsim4.py.
    1. Instruction Phase (NaN)
    2. Task Execution
    """
    # Instruction Phase
    record_frames(DURASI_PERINTAH, phase_name=f"{task_name}_INSTRUCTION")
    
    # Execute Task
    task_func(task_duration, task_name, **kwargs)

def action_static_target(duration, task_name, position):
    record_frames(duration, x=position[0], y=position[1], phase_name=task_name)

def action_smooth_pursuit(duration, task_name, path_x, path_y):
    # Preparation Phase (Countdown) - Target is visible at start_pos, 
    # but usually we ignore this for strict scoring. Setting to NaN as requested.
    record_frames(DURASI_PERSIAPAN, phase_name=f"{task_name}_PREPARATION")
    
    # Movement Phase
    num_frames = int(duration * FPS)
    # Ensure path arrays match the number of frames exactly
    # genvidsim4 uses np.linspace which generates num samples.
    # We need to make sure we iterate correctly.
    
    # If path is shorter/longer due to rounding, we adjust
    path_len = len(path_x)
    
    for i in range(num_frames):
        # Handle potential index out of bounds if rounding differs slightly
        idx = min(i, path_len - 1)
        record_frames(1/FPS, x=path_x[idx], y=path_y[idx], phase_name=task_name)

def action_saccades(duration, task_name, points, duration_per_point):
    # Saccades doesn't have a main duration, it depends on points * duration_per_point
    for i, point in enumerate(points):
        record_frames(duration_per_point, x=point[0], y=point[1], phase_name=f"{task_name}_POINT_{i+1}")

def display_fullscreen_text(duration, phase_name):
    record_frames(duration, phase_name=phase_name)

# ==============================================================================
# 3. GENERATE GROUND TRUTH
# ==============================================================================
print("Generating Ground Truth Data...")

# 1. Opening
display_fullscreen_text(DURASI_BUKA_TUTUP, "OPENING")

# 2. Tutorial
margin = 150
path_x = np.linspace(margin, WIDTH - margin, DURASI_TUTORIAL * FPS)
path_y = np.full_like(path_x, HEIGHT // 2)
run_task_wrapper("TUTORIAL", action_smooth_pursuit, DURASI_TUTORIAL, path_x=path_x, path_y=path_y)

# 3. Fixation
center_point = (WIDTH // 2, HEIGHT // 2)
run_task_wrapper("TASK_1_FIXATION", action_static_target, DURASI_FIKSASI, position=center_point)

# 4. Smooth Pursuit
# Horizontal L->R
path_x_ltr = np.linspace(margin, WIDTH - margin, int(DURASI_GERAK_HALUS * FPS))
path_y_h = np.full_like(path_x_ltr, HEIGHT // 2)
run_task_wrapper("TASK_2A_HORIZONTAL_LTR", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_ltr, path_y=path_y_h)

# Horizontal R->L
run_task_wrapper("TASK_2B_HORIZONTAL_RTL", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_ltr[::-1], path_y=path_y_h)

# Vertical T->B
path_y_ttb = np.linspace(margin, HEIGHT - margin, int(DURASI_GERAK_HALUS * FPS))
path_x_v = np.full_like(path_y_ttb, WIDTH // 2)
run_task_wrapper("TASK_3A_VERTICAL_TTB", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_v, path_y=path_y_ttb)

# Vertical B->T
run_task_wrapper("TASK_3B_VERTICAL_BTT", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_v, path_y=path_y_ttb[::-1])

# Circular CW
radius = (HEIGHT // 2) - margin
t = np.linspace(0, 2 * np.pi * 2, int(DURASI_GERAK_HALUS * FPS))
path_x_cw = center_point[0] + radius * np.cos(t)
path_y_cw = center_point[1] + radius * np.sin(t)
run_task_wrapper("TASK_4A_CIRCULAR_CW", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_cw, path_y=path_y_cw)

# Circular CCW
run_task_wrapper("TASK_4B_CIRCULAR_CCW", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_cw, path_y=path_y_cw[::-1])

# 5. Saccades
margin_sacc = 200
points_structured = [ 
    (margin_sacc, margin_sacc), 
    (WIDTH - margin_sacc, margin_sacc), 
    (WIDTH - margin_sacc, HEIGHT - margin_sacc), 
    (margin_sacc, HEIGHT - margin_sacc), 
    center_point 
]
run_task_wrapper("TASK_5A_SACCADES_STRUCTURED", action_saccades, 0, points=points_structured, duration_per_point=DURASI_SAKADIK_PER_TITIK)

points_random = [ 
    (WIDTH - margin_sacc, margin_sacc), 
    (margin_sacc, HEIGHT - margin_sacc), 
    (WIDTH // 2, margin_sacc), 
    (WIDTH - margin_sacc, HEIGHT // 2), 
    center_point 
]
run_task_wrapper("TASK_5B_SACCADES_RANDOM", action_saccades, 0, points=points_random, duration_per_point=DURASI_SAKADIK_PER_TITIK)

# 6. Closing
display_fullscreen_text(DURASI_BUKA_TUTUP, "CLOSING")

# Save to CSV
df_gt = pd.DataFrame(frame_data)
output_csv = "stimulus_ground_truth.csv"
df_gt.to_csv(output_csv, index=False)
print(f"Ground truth saved to {output_csv}")
print(f"Total Frames: {len(df_gt)}")
print(f"Valid Target Frames: {df_gt['gt_x_px'].count()}")

# ==============================================================================
# 4. COMPARE WITH DETECTED DATA
# ==============================================================================

def run_comparison():
    print("\n" + "="*50)
    print("COMPARISON CONFIGURATION")
    print("="*50)
    
    # 1. Get Detected CSV Path
    default_path = "output/detected_positions.csv"
    detected_csv_path = input(f"Enter path to detected CSV [default: {default_path}]: ").strip()
    if not detected_csv_path:
        detected_csv_path = default_path
        
    if not os.path.exists(detected_csv_path):
        print(f"Error: File not found at {detected_csv_path}")
        return

    # 2. Get Synchronization Offset
    print("\nSynchronization Offset:")
    print("Positive value: Detected video starts AFTER stimulus (shift detected frames LEFT/EARLIER)")
    print("Negative value: Detected video starts BEFORE stimulus (shift detected frames RIGHT/LATER)")
    
    # Find the start frame of the TUTORIAL phase for Quick Sync
    tutorial_start_frame = df_gt[df_gt['phase'] == 'TUTORIAL'].iloc[0]['frame']
    print(f"\n[Quick Sync] Tutorial Phase starts at frame: {tutorial_start_frame}")
    print(f"             (Use this if your video starts exactly at the Tutorial)")
    
    offset_input = input(f"Enter offset in seconds, frames (e.g. 150f), or 'q' for Quick Sync (Tutorial Start) [default: 0]: ").strip()
    
    offset_frames = 0
    if offset_input.lower() == 'q':
        # User cut video to start right before tutorial
        # So Frame 0 of detected video = Frame X (Tutorial Start) of Ground Truth
        # We need to shift detected frames by +X so that 0 becomes X
        # Wait, the logic below is: adjusted = frame - offset
        # If detected 0 should match GT 100:
        # 100 = 0 - offset => offset = -100
        # So we need NEGATIVE of the start frame
        offset_frames = -tutorial_start_frame
        print(f"Quick Sync selected. Offset set to {-offset_frames} frames (Video starts at Tutorial).")
        
    elif offset_input:
        if offset_input.lower().endswith('f'):
            try:
                offset_frames = int(offset_input[:-1])
            except ValueError:
                print("Invalid frame format. Using 0.")
        else:
            try:
                offset_seconds = float(offset_input)
                offset_frames = int(offset_seconds * FPS)
            except ValueError:
                print("Invalid seconds format. Using 0.")
    
    print(f"Applying offset: {offset_frames} frames")

    try:
        # Load detected data
        df_det = pd.read_csv(detected_csv_path)
        
        # Ensure 'frame' column exists
        if 'frame' not in df_det.columns:
            print("Error: Detected CSV must have a 'frame' column.")
            return

        # Apply Offset to Detected Frames
        # If detected video starts LATER (positive offset), frame 100 in detected is actually frame (100 - offset) in stimulus time
        # If detected video starts EARLIER (negative offset), frame 100 in detected is actually frame (100 + offset) in stimulus time
        # We want to align Detected Frame X with Ground Truth Frame Y
        
        # Let's adjust the detected 'frame' column to match Ground Truth 'frame'
        # Adjusted Frame = Original Frame - Offset Frames
        df_det['frame_adjusted'] = df_det['frame'] - offset_frames
        
        # Filter out frames that fall outside valid range after adjustment
        # (Optional, but merge will handle it)
        
        # Merge Ground Truth and Detected data on 'frame' (GT) vs 'frame_adjusted' (Det)
        merged = pd.merge(df_gt, df_det, left_on='frame', right_on='frame_adjusted', how='left', suffixes=('_gt', '_det'))
        
        # Filter: Only consider frames where Ground Truth is valid (not NaN)
        valid_frames = merged.dropna(subset=['gt_x_px', 'gt_y_px'])
        
        if len(valid_frames) == 0:
            print("No overlapping valid frames found for comparison.")
        else:
            # Assume detected columns are 'x' and 'y' or 'detected_x', 'detected_y'
            # Check for various common column names
            possible_x_cols = ['detected_x', 'x', 'refined_x', 'raw_x']
            possible_y_cols = ['detected_y', 'y', 'refined_y', 'raw_y']
            
            det_x_col = next((col for col in possible_x_cols if col in df_det.columns), None)
            det_y_col = next((col for col in possible_y_cols if col in df_det.columns), None)
            
            if det_x_col is None:
                    print(f"Warning: Could not find x-coordinate column. Available: {df_det.columns.tolist()}")
                    return
            
            print(f"Using columns: {det_x_col}, {det_y_col}")

            # Calculate Detection Rate
            detected_count = valid_frames[det_x_col].count()
            total_valid_gt = len(valid_frames)
            detection_rate = (detected_count / total_valid_gt) * 100
            
            print("\n" + "-"*30)
            print("RESULTS")
            print("-"*30)
            print(f"Total Valid Ground Truth Frames: {total_valid_gt}")
            print(f"Successfully Detected Frames:    {detected_count}")
            print(f"Detection Rate:                  {detection_rate:.2f}%")
            
            # Calculate Euclidean Error for detected frames only
            comparison_df = valid_frames.dropna(subset=[det_x_col, det_y_col])
            
            if len(comparison_df) > 0:
                # Euclidean Distance
                comparison_df['error_px'] = np.sqrt(
                    (comparison_df['gt_x_px'] - comparison_df[det_x_col])**2 + 
                    (comparison_df['gt_y_px'] - comparison_df[det_y_col])**2
                )
                
                mean_error = comparison_df['error_px'].mean()
                std_error = comparison_df['error_px'].std()
                max_error = comparison_df['error_px'].max()
                
                print(f"Mean Euclidean Error:          {mean_error:.2f} px")
                print(f"Std Dev Error:                 {std_error:.2f} px")
                print(f"Max Error:                     {max_error:.2f} px")
                
                # Optional: Error by Phase
                print("\nError by Phase:")
                phase_stats = comparison_df.groupby('phase')['error_px'].agg(['mean', 'count'])
                print(phase_stats)
                
                # Save comparison results
                output_filename = f"comparison_results_offset_{offset_frames}.csv"
                comparison_df.to_csv(output_filename, index=False)
                print(f"\nDetailed comparison saved to '{output_filename}'")
            else:
                print("No frames have both GT and Detected data to calculate error.")

    except Exception as e:
        print(f"An error occurred during comparison: {e}")

if __name__ == "__main__":
    # Ask if user wants to regenerate ground truth or just compare
    choice = input("Do you want to (re)generate ground truth? (y/n) [default: y]: ").strip().lower()
    if choice != 'n':
        # The generation code above runs automatically on import/execution
        # But since we wrapped it in functions, we should probably move the execution block
        # For now, the script structure executes generation first.
        pass 
    
    run_comparison()
