import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import json

# ==============================================================================
# CONFIGURATION - These should match the game settings
# ==============================================================================

# Screen resolution (will be read from metadata if available)
DEFAULT_LEBAR_LAYAR = 1920
DEFAULT_TINGGI_LAYAR = 1080

# Button positions (should match game3_with_recording.py)
def get_button_positions(lebar_layar, tinggi_layar):
    return {
        "benar": {"pos": (lebar_layar - 300, tinggi_layar * 0.25), "size": (300, 150)},
        "salah": {"pos": (lebar_layar - 300, tinggi_layar * 0.75), "size": (300, 150)},
    }

# Question positions (should match game3_with_recording.py)
def get_question_positions(lebar_layar, tinggi_layar):
    POSISI_AWAL_SOAL_Y = tinggi_layar * 0.1
    JARAK_ANTAR_SOAL = 125
    return POSISI_AWAL_SOAL_Y, JARAK_ANTAR_SOAL

# Colors
COLORS = {
    'Question': '#FFB347',      # Light orange
    'Background': '#808080',     # Gray
    'Button_Correct': '#90EE90', # Light green
    'Button_Wrong': '#FFB6C1'    # Light red/pink
}

# ==============================================================================
# VISUALIZATION FUNCTIONS
# ==============================================================================

def save_area_timeline_plot(gaze_df, output_dir, num_questions):
    """
    1. Line graph showing time (x-axis) vs area (y-axis) with vertical dashed lines separating questions.
    Areas: question_text, background, button_benar, button_salah
    """
    fps = 60  # Assuming 60 FPS
    
    # Prepare data
    gaze_df = gaze_df.copy()
    gaze_df['time_seconds'] = gaze_df['timestamp']
    
    # Map ROI to simplified categories
    def map_roi(roi):
        if roi == 'question_text':
            return 'Question'
        elif roi == 'background':
            return 'Background'
        elif roi == 'button_benar':
            return 'Button Correct'
        elif roi == 'button_salah':
            return 'Button Wrong'
        else:
            return 'Background'
    
    gaze_df['area_category'] = gaze_df['roi'].apply(map_roi)
    
    # Create numeric encoding for areas (for line plot)
    area_encoding = {
        'Question': 3,
        'Button Correct': 2,
        'Button Wrong': 1,
        'Background': 0
    }
    gaze_df['area_numeric'] = gaze_df['area_category'].map(area_encoding)
    
    # Create plot
    plt.figure(figsize=(16, 6))
    
    # Plot line for each area
    for area in ['Question', 'Button Correct', 'Button Wrong', 'Background']:
        area_data = gaze_df[gaze_df['area_category'] == area]
        if len(area_data) > 0:
            plt.scatter(area_data['time_seconds'], area_data['area_numeric'], 
                       c=COLORS[area.replace(' ', '_')], label=area, alpha=0.6, s=10)
    
    # Add vertical dashed lines for question transitions
    unique_questions = sorted(gaze_df['question_index'].unique())
    question_times = []
    for q_idx in unique_questions:
        q_data = gaze_df[gaze_df['question_index'] == q_idx]
        if len(q_data) > 0:
            start_time = q_data['time_seconds'].min()
            question_times.append((q_idx, start_time))
    
    for q_idx, start_time in question_times[1:]:  # Skip first question (starts at 0)
        plt.axvline(x=start_time, color='black', linestyle='--', alpha=0.5, linewidth=1.5)
        plt.text(start_time, 3.5, f'Q{q_idx+1}', ha='center', fontsize=9, 
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    # Add Q1 label at the beginning
    if question_times:
        plt.text(question_times[0][1], 3.5, f'Q{question_times[0][0]+1}', ha='left', fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    plt.yticks([0, 1, 2, 3], ['Background', 'Button Wrong', 'Button Correct', 'Question'])
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Area', fontsize=12)
    plt.title('Gaze Area Over Time - Question Sections', fontsize=14, fontweight='bold')
    plt.legend(loc='upper right', fontsize=10)
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    
    timeline_path = os.path.join(output_dir, "area_timeline.png")
    plt.savefig(timeline_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Area timeline saved: {timeline_path}")


def save_question_area_histogram(gaze_df, output_dir, num_questions):
    """
    2. Histogram showing duration per area for each question.
    X-axis: Questions (with sub-bars for each area)
    Y-axis: Two versions - percentage (%) and seconds
    """
    fps = 60  # Assuming 60 FPS
    
    # Map ROI to categories
    def map_roi(roi):
        if roi == 'question_text':
            return 'Question'
        elif roi == 'background':
            return 'Background'
        elif roi == 'button_benar':
            return 'Button Correct'
        elif roi == 'button_salah':
            return 'Button Wrong'
        else:
            return 'Background'
    
    gaze_df = gaze_df.copy()
    gaze_df['area_category'] = gaze_df['roi'].apply(map_roi)
    
    # Get unique questions
    unique_questions = sorted([q for q in gaze_df['question_index'].unique() if q < num_questions])
    
    if len(unique_questions) == 0:
        print("⚠ No question data found for histogram")
        return
    
    # Calculate durations for each question and area
    question_data = []
    for q_idx in unique_questions:
        q_data = gaze_df[gaze_df['question_index'] == q_idx]
        total_frames = len(q_data)
        total_seconds = total_frames / fps
        
        area_counts = q_data['area_category'].value_counts()
        
        question_data.append({
            'question': f'Q{q_idx + 1}',
            'question_idx': q_idx,
            'Question_seconds': area_counts.get('Question', 0) / fps,
            'Background_seconds': area_counts.get('Background', 0) / fps,
            'Button_Correct_seconds': area_counts.get('Button Correct', 0) / fps,
            'Button_Wrong_seconds': area_counts.get('Button Wrong', 0) / fps,
            'total_seconds': total_seconds,
            'Question_pct': (area_counts.get('Question', 0) / total_frames * 100) if total_frames > 0 else 0,
            'Background_pct': (area_counts.get('Background', 0) / total_frames * 100) if total_frames > 0 else 0,
            'Button_Correct_pct': (area_counts.get('Button Correct', 0) / total_frames * 100) if total_frames > 0 else 0,
            'Button_Wrong_pct': (area_counts.get('Button Wrong', 0) / total_frames * 100) if total_frames > 0 else 0,
        })
    
    df = pd.DataFrame(question_data)
    
    # --- Plot 1: Percentage ---
    fig, ax = plt.subplots(figsize=(14, 6))
    
    x = np.arange(len(df))
    width = 0.2
    
    ax.bar(x - 1.5*width, df['Question_pct'], width, label='Question Area', color=COLORS['Question'])
    ax.bar(x - 0.5*width, df['Background_pct'], width, label='Background', color=COLORS['Background'])
    ax.bar(x + 0.5*width, df['Button_Correct_pct'], width, label='Button Correct', color=COLORS['Button_Correct'])
    ax.bar(x + 1.5*width, df['Button_Wrong_pct'], width, label='Button Wrong', color=COLORS['Button_Wrong'])
    
    ax.set_xlabel('Question', fontsize=12)
    ax.set_ylabel('Percent Time Allocated (%)', fontsize=12)
    ax.set_title('Gaze Duration per Area by Question (Percentage)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(df['question'])
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    pct_path = os.path.join(output_dir, "area_duration_percentage.png")
    plt.savefig(pct_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Area duration (percentage) saved: {pct_path}")
    
    # --- Plot 2: Seconds ---
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.bar(x - 1.5*width, df['Question_seconds'], width, label='Question Area', color=COLORS['Question'])
    ax.bar(x - 0.5*width, df['Background_seconds'], width, label='Background', color=COLORS['Background'])
    ax.bar(x + 0.5*width, df['Button_Correct_seconds'], width, label='Button Correct', color=COLORS['Button_Correct'])
    ax.bar(x + 1.5*width, df['Button_Wrong_seconds'], width, label='Button Wrong', color=COLORS['Button_Wrong'])
    
    ax.set_xlabel('Question', fontsize=12)
    ax.set_ylabel('Duration (seconds)', fontsize=12)
    ax.set_title('Gaze Duration per Area by Question (Seconds)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(df['question'])
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    sec_path = os.path.join(output_dir, "area_duration_seconds.png")
    plt.savefig(sec_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Area duration (seconds) saved: {sec_path}")
    
    # Save data as CSV
    csv_path = os.path.join(output_dir, "area_duration_data.csv")
    df.to_csv(csv_path, index=False)
    print(f"✓ Area duration data saved: {csv_path}")


def save_gaze_trajectory_histograms(gaze_df, output_dir, num_questions, lebar_layar, tinggi_layar):
    """
    3. Gaze position trajectory vs area histogram.
    Shows distribution of gaze points relative to the target area boundaries.
    Creates combined histograms for X and Y positions for each question showing all areas.
    """
    unique_questions = sorted([q for q in gaze_df['question_index'].unique() if q < num_questions])
    
    if len(unique_questions) == 0:
        print("⚠ No question data found for trajectory histograms")
        return
    
    # Create subdirectory for trajectory plots
    trajectory_dir = os.path.join(output_dir, "gaze_trajectories")
    os.makedirs(trajectory_dir, exist_ok=True)
    
    # Get button positions
    TOMBOL = get_button_positions(lebar_layar, tinggi_layar)
    POSISI_AWAL_SOAL_Y, JARAK_ANTAR_SOAL = get_question_positions(lebar_layar, tinggi_layar)
    
    # Process each question
    for q_idx in unique_questions:
        q_data = gaze_df[gaze_df['question_index'] == q_idx].copy()
        
        if len(q_data) == 0:
            continue
        
        # Create a 3x2 subplot (3 areas × 2 axes)
        fig, axes = plt.subplots(3, 2, figsize=(16, 12))
        fig.suptitle(f'Q{q_idx + 1}: Gaze Position Distribution vs Area Boundaries', 
                     fontsize=16, fontweight='bold', y=0.995)
        
        # Calculate Y position for this question
        y_pos = POSISI_AWAL_SOAL_Y + (q_idx * JARAK_ANTAR_SOAL)
        
        # --- Row 1: Question Text Area Analysis ---
        question_gaze = q_data[q_data['roi'] == 'question_text']
        
        if len(question_gaze) > 0:
            # Estimate question area bounds
            q_text = q_data['question_text'].iloc[0]
            estimated_text_width = len(q_text) * 35
            soal_rect_width = min(estimated_text_width, lebar_layar - 400)
            
            question_bounds = {
                'x_min': 100,
                'x_max': 100 + soal_rect_width,
                'y_min': y_pos - 10,
                'y_max': y_pos + 80
            }
            
            # X-axis histogram
            axes[0, 0].hist(question_gaze['gaze_x'], bins=30, color=COLORS['Question'], alpha=0.7, edgecolor='black')
            axes[0, 0].axvline(question_bounds['x_min'], color='red', linestyle='--', linewidth=2, label='Area Boundary')
            axes[0, 0].axvline(question_bounds['x_max'], color='red', linestyle='--', linewidth=2)
            axes[0, 0].set_xlabel('X Position (pixels)', fontsize=10)
            axes[0, 0].set_ylabel('Frequency', fontsize=10)
            axes[0, 0].set_title('Question Area - X Distribution', fontweight='bold', fontsize=11)
            axes[0, 0].legend(fontsize=9)
            axes[0, 0].grid(True, alpha=0.3)
            
            # Y-axis histogram
            axes[0, 1].hist(question_gaze['gaze_y'], bins=30, color=COLORS['Question'], alpha=0.7, edgecolor='black')
            axes[0, 1].axvline(question_bounds['y_min'], color='red', linestyle='--', linewidth=2, label='Area Boundary')
            axes[0, 1].axvline(question_bounds['y_max'], color='red', linestyle='--', linewidth=2)
            axes[0, 1].set_xlabel('Y Position (pixels)', fontsize=10)
            axes[0, 1].set_ylabel('Frequency', fontsize=10)
            axes[0, 1].set_title('Question Area - Y Distribution', fontweight='bold', fontsize=11)
            axes[0, 1].legend(fontsize=9)
            axes[0, 1].grid(True, alpha=0.3)
        else:
            axes[0, 0].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[0, 0].transAxes)
            axes[0, 1].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[0, 1].transAxes)
            axes[0, 0].set_title('Question Area - X Distribution', fontweight='bold', fontsize=11)
            axes[0, 1].set_title('Question Area - Y Distribution', fontweight='bold', fontsize=11)
        
        # --- Row 2: Button Correct (Benar) Analysis ---
        button_benar_gaze = q_data[q_data['roi'] == 'button_benar']
        
        if len(button_benar_gaze) > 0:
            btn_benar = TOMBOL['benar']
            benar_bounds = {
                'x_min': btn_benar['pos'][0],
                'x_max': btn_benar['pos'][0] + btn_benar['size'][0],
                'y_min': btn_benar['pos'][1],
                'y_max': btn_benar['pos'][1] + btn_benar['size'][1]
            }
            
            # X-axis histogram
            axes[1, 0].hist(button_benar_gaze['gaze_x'], bins=20, color=COLORS['Button_Correct'], alpha=0.7, edgecolor='black')
            axes[1, 0].axvline(benar_bounds['x_min'], color='red', linestyle='--', linewidth=2, label='Button Boundary')
            axes[1, 0].axvline(benar_bounds['x_max'], color='red', linestyle='--', linewidth=2)
            axes[1, 0].set_xlabel('X Position (pixels)', fontsize=10)
            axes[1, 0].set_ylabel('Frequency', fontsize=10)
            axes[1, 0].set_title('Button Correct - X Distribution', fontweight='bold', fontsize=11)
            axes[1, 0].legend(fontsize=9)
            axes[1, 0].grid(True, alpha=0.3)
            
            # Y-axis histogram
            axes[1, 1].hist(button_benar_gaze['gaze_y'], bins=20, color=COLORS['Button_Correct'], alpha=0.7, edgecolor='black')
            axes[1, 1].axvline(benar_bounds['y_min'], color='red', linestyle='--', linewidth=2, label='Button Boundary')
            axes[1, 1].axvline(benar_bounds['y_max'], color='red', linestyle='--', linewidth=2)
            axes[1, 1].set_xlabel('Y Position (pixels)', fontsize=10)
            axes[1, 1].set_ylabel('Frequency', fontsize=10)
            axes[1, 1].set_title('Button Correct - Y Distribution', fontweight='bold', fontsize=11)
            axes[1, 1].legend(fontsize=9)
            axes[1, 1].grid(True, alpha=0.3)
        else:
            axes[1, 0].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[1, 0].transAxes)
            axes[1, 1].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[1, 1].transAxes)
            axes[1, 0].set_title('Button Correct - X Distribution', fontweight='bold', fontsize=11)
            axes[1, 1].set_title('Button Correct - Y Distribution', fontweight='bold', fontsize=11)
        
        # --- Row 3: Button Wrong (Salah) Analysis ---
        button_salah_gaze = q_data[q_data['roi'] == 'button_salah']
        
        if len(button_salah_gaze) > 0:
            btn_salah = TOMBOL['salah']
            salah_bounds = {
                'x_min': btn_salah['pos'][0],
                'x_max': btn_salah['pos'][0] + btn_salah['size'][0],
                'y_min': btn_salah['pos'][1],
                'y_max': btn_salah['pos'][1] + btn_salah['size'][1]
            }
            
            # X-axis histogram
            axes[2, 0].hist(button_salah_gaze['gaze_x'], bins=20, color=COLORS['Button_Wrong'], alpha=0.7, edgecolor='black')
            axes[2, 0].axvline(salah_bounds['x_min'], color='red', linestyle='--', linewidth=2, label='Button Boundary')
            axes[2, 0].axvline(salah_bounds['x_max'], color='red', linestyle='--', linewidth=2)
            axes[2, 0].set_xlabel('X Position (pixels)', fontsize=10)
            axes[2, 0].set_ylabel('Frequency', fontsize=10)
            axes[2, 0].set_title('Button Wrong - X Distribution', fontweight='bold', fontsize=11)
            axes[2, 0].legend(fontsize=9)
            axes[2, 0].grid(True, alpha=0.3)
            
            # Y-axis histogram
            axes[2, 1].hist(button_salah_gaze['gaze_y'], bins=20, color=COLORS['Button_Wrong'], alpha=0.7, edgecolor='black')
            axes[2, 1].axvline(salah_bounds['y_min'], color='red', linestyle='--', linewidth=2, label='Button Boundary')
            axes[2, 1].axvline(salah_bounds['y_max'], color='red', linestyle='--', linewidth=2)
            axes[2, 1].set_xlabel('Y Position (pixels)', fontsize=10)
            axes[2, 1].set_ylabel('Frequency', fontsize=10)
            axes[2, 1].set_title('Button Wrong - Y Distribution', fontweight='bold', fontsize=11)
            axes[2, 1].legend(fontsize=9)
            axes[2, 1].grid(True, alpha=0.3)
        else:
            axes[2, 0].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[2, 0].transAxes)
            axes[2, 1].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[2, 1].transAxes)
            axes[2, 0].set_title('Button Wrong - X Distribution', fontweight='bold', fontsize=11)
            axes[2, 1].set_title('Button Wrong - Y Distribution', fontweight='bold', fontsize=11)
        
        plt.tight_layout()
        combined_path = os.path.join(trajectory_dir, f"q{q_idx + 1}_trajectory_combined.png")
        plt.savefig(combined_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✓ Q{q_idx + 1} combined trajectory saved: {combined_path}")
    
    print(f"✓ All trajectory histograms saved in: {trajectory_dir}")


# ==============================================================================
# MAIN PROCESSING FUNCTION
# ==============================================================================

def is_valid_session_directory(session_dir):
    """Check if directory contains required CSV files for processing."""
    gaze_csv = os.path.join(session_dir, "gaze_data.csv")
    return os.path.exists(gaze_csv)


def process_session_directory(session_dir, verbose=True):
    """Process a game session directory and generate all visualizations."""
    
    if not os.path.isdir(session_dir):
        if verbose:
            print(f"❌ Error: Directory '{session_dir}' not found")
        return False
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"Processing session: {os.path.basename(session_dir)}")
        print(f"{'='*70}\n")
    
    # Load CSV files
    gaze_csv = os.path.join(session_dir, "gaze_data.csv")
    metadata_csv = os.path.join(session_dir, "session_metadata.csv")
    
    if not os.path.exists(gaze_csv):
        if verbose:
            print(f"❌ Error: 'gaze_data.csv' not found in {session_dir}")
        return False
    
    # Load gaze data
    if verbose:
        print(f"Loading gaze data from: {os.path.basename(gaze_csv)}")
    gaze_df = pd.read_csv(gaze_csv)
    if verbose:
        print(f"✓ Loaded {len(gaze_df)} gaze records")
    
    # Load metadata to get screen resolution and question count
    lebar_layar = DEFAULT_LEBAR_LAYAR
    tinggi_layar = DEFAULT_TINGGI_LAYAR
    num_questions = 6  # Default
    
    if os.path.exists(metadata_csv):
        if verbose:
            print(f"Loading metadata from: {os.path.basename(metadata_csv)}")
        metadata_df = pd.read_csv(metadata_csv)
        
        if 'screen_resolution' in metadata_df.columns:
            res_str = metadata_df['screen_resolution'].iloc[0]
            if 'x' in res_str:
                lebar_layar, tinggi_layar = map(int, res_str.split('x'))
                if verbose:
                    print(f"✓ Screen resolution: {lebar_layar}x{tinggi_layar}")
        
        if 'total_questions' in metadata_df.columns:
            num_questions = int(metadata_df['total_questions'].iloc[0])
            if verbose:
                print(f"✓ Total questions: {num_questions}")
    else:
        if verbose:
            print(f"⚠ Warning: 'session_metadata.csv' not found, using defaults")
            print(f"  Screen resolution: {lebar_layar}x{tinggi_layar}")
            print(f"  Total questions: {num_questions}")
    
    if verbose:
        print(f"\n{'='*70}")
        print("Generating visualizations...")
        print(f"{'='*70}\n")
    
    # Generate all plots
    try:
        save_area_timeline_plot(gaze_df, session_dir, num_questions)
        if verbose:
            print()
        
        save_question_area_histogram(gaze_df, session_dir, num_questions)
        if verbose:
            print()
        
        save_gaze_trajectory_histograms(gaze_df, session_dir, num_questions, lebar_layar, tinggi_layar)
        if verbose:
            print()
        
        if verbose:
            print(f"{'='*70}")
            print("✅ All visualizations generated successfully!")
            print(f"{'='*70}\n")
        return True
        
    except Exception as e:
        if verbose:
            print(f"\n❌ Error generating visualizations: {e}")
            import traceback
            traceback.print_exc()
        return False


def batch_process_sessions(parent_dir):
    """Batch process all valid game sessions in a parent directory."""
    
    if not os.path.isdir(parent_dir):
        print(f"❌ Error: Directory '{parent_dir}' not found")
        return False
    
    print(f"\n{'='*70}")
    print(f"BATCH PROCESSING MODE")
    print(f"{'='*70}")
    print(f"Scanning directory: {parent_dir}")
    print(f"{'='*70}\n")
    
    # Find all subdirectories
    subdirs = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
    
    if not subdirs:
        print("❌ No subdirectories found")
        return False
    
    print(f"Found {len(subdirs)} subdirectories")
    print("Checking for valid game sessions...\n")
    
    # Filter valid sessions
    valid_sessions = []
    invalid_sessions = []
    
    for subdir in subdirs:
        full_path = os.path.join(parent_dir, subdir)
        if is_valid_session_directory(full_path):
            valid_sessions.append(full_path)
            print(f"  ✓ {subdir}")
        else:
            invalid_sessions.append(subdir)
            print(f"  ✗ {subdir} (missing gaze_data.csv)")
    
    print(f"\n{'='*70}")
    print(f"Valid sessions: {len(valid_sessions)}")
    print(f"Invalid/Incomplete sessions: {len(invalid_sessions)}")
    print(f"{'='*70}\n")
    
    if not valid_sessions:
        print("❌ No valid sessions to process")
        return False
    
    # Process each valid session
    successful = []
    failed = []
    
    for i, session_path in enumerate(valid_sessions, 1):
        session_name = os.path.basename(session_path)
        print(f"\n{'='*70}")
        print(f"[{i}/{len(valid_sessions)}] Processing: {session_name}")
        print(f"{'='*70}")
        
        try:
            success = process_session_directory(session_path, verbose=False)
            if success:
                successful.append(session_name)
                print(f"✅ {session_name} - Success")
            else:
                failed.append(session_name)
                print(f"❌ {session_name} - Failed")
        except Exception as e:
            failed.append(session_name)
            print(f"❌ {session_name} - Error: {e}")
    
    # Print summary
    print(f"\n{'='*70}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'='*70}")
    print(f"Total sessions found: {len(subdirs)}")
    print(f"Valid sessions: {len(valid_sessions)}")
    print(f"Successfully processed: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Skipped (incomplete): {len(invalid_sessions)}")
    
    if successful:
        print(f"\n✅ Successfully processed sessions:")
        for name in successful:
            print(f"   - {name}")
    
    if failed:
        print(f"\n❌ Failed sessions:")
        for name in failed:
            print(f"   - {name}")
    
    if invalid_sessions:
        print(f"\n⚠ Skipped sessions (missing gaze_data.csv):")
        for name in invalid_sessions:
            print(f"   - {name}")
    
    print(f"\n{'='*70}\n")
    
    return len(failed) == 0


# ==============================================================================
# COMMAND LINE INTERFACE
# ==============================================================================

if __name__ == "__main__":
    # Check if arguments provided via command line
    if len(sys.argv) >= 2:
        target_path = sys.argv[1]
        batch_mode = len(sys.argv) > 2 and sys.argv[2] == "--batch"
    else:
        # Interactive mode
        print("\n" + "="*70)
        print("Visualization Generator for Eye-Tracker Game Sessions")
        print("="*70)
        print("\nThis script will generate visualization plots from CSV files:")
        print("  1. Area timeline plot")
        print("  2. Question area duration histograms (percentage & seconds)")
        print("  3. Gaze trajectory histograms per question")
        print("\n" + "="*70)
        
        # Ask for processing mode
        print("\nSelect processing mode:")
        print("  1. Single session (process one session directory)")
        print("  2. Batch mode (process all sessions in a parent folder)")
        
        while True:
            mode_choice = input("\nEnter choice (1 or 2): ").strip()
            if mode_choice in ['1', '2']:
                break
            print("❌ Invalid choice. Please enter 1 or 2.")
        
        batch_mode = (mode_choice == '2')
        
        # Ask for path
        if batch_mode:
            print("\n" + "="*70)
            print("BATCH MODE - Process all valid sessions in a parent folder")
            print("="*70)
            print("\nExample path:")
            print('  C:\\Users\\kahli\\tugasakhir\\workspace\\Game Session')
            target_path = input("\nEnter parent folder path: ").strip().strip('"').strip("'")
        else:
            print("\n" + "="*70)
            print("SINGLE SESSION MODE")
            print("="*70)
            print("\nExample path:")
            print('  game_session_2026-01-09_10-30-45')
            print('  C:\\Users\\kahli\\tugasakhir\\workspace\\Game Session\\game_session_2026-01-09_10-30-45')
            target_path = input("\nEnter session directory path: ").strip().strip('"').strip("'")
        
        if not target_path:
            print("\n❌ Error: No path provided")
            sys.exit(1)
    
    # Process based on mode
    if batch_mode:
        success = batch_process_sessions(target_path)
    else:
        success = process_session_directory(target_path)
    
    sys.exit(0 if success else 1)
