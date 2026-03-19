# Import libraries
import cv2
import os
import numpy as np
import pandas as pd
from datetime import datetime
from tqdm import tqdm

# Input file should be an mp4 or mkv
# Preprocessing: Trimming eyegaze video to fixation segments only
def precise_trimmer(recorded_video, eyegaze_video, validated_path):
    # Check if files exist first
    if not os.path.exists(recorded_video):
        print(f"ERROR: Recorded video file not found: {recorded_video}")
        return
    if not os.path.exists(eyegaze_video):
        print(f"ERROR: Eyegaze video file not found: {eyegaze_video}")
        return
    
    # Get file info
    rec_ext = os.path.splitext(recorded_video)[1].lower()
    eye_ext = os.path.splitext(eyegaze_video)[1].lower()
    print(f"\nAttempting to open files:")
    print(f"  Recorded: {os.path.basename(recorded_video)} ({rec_ext})")
    print(f"  Eyegaze: {os.path.basename(eyegaze_video)} ({eye_ext})")
    
    cap_recorded = cv2.VideoCapture(recorded_video)
    cap_eyegaze = cv2.VideoCapture(eyegaze_video)
    
    if not cap_recorded.isOpened():
        print(f"\nERROR: Cannot open recorded video file.")
        print(f"File: {recorded_video}")
        print(f"Format: {rec_ext}")
        print("\nPossible solutions:")
        print("  1. If this is an MKV file, try converting to MP4:")
        print("     ffmpeg -i input.mkv -c:v libx264 -c:a aac output.mp4")
        print("  2. Check if the file path has special characters or spaces")
        print("  3. Ensure the file is not corrupted")
        print("  4. Install K-Lite Codec Pack (Windows) for better codec support")
        return
    
    if not cap_eyegaze.isOpened():
        print(f"\nERROR: Cannot open eyegaze video file.")
        print(f"File: {eyegaze_video}")
        print(f"Format: {eye_ext}")
        print("\nPossible solutions:")
        print("  1. If this is an MKV file, try converting to MP4:")
        print("     ffmpeg -i input.mkv -c:v libx264 -c:a aac output.mp4")
        print("  2. Check if the file path has special characters or spaces")
        print("  3. Ensure the file is not corrupted")
        print("  4. Install K-Lite Codec Pack (Windows) for better codec support")
        cap_recorded.release()
        return
    
    print("PERFECT! Both videos opened successfully!")

    total_frames = int(cap_recorded.get(cv2.CAP_PROP_FRAME_COUNT))
    total_frames_eyegaze = int(cap_eyegaze.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap_recorded.get(cv2.CAP_PROP_FPS)
    current_frame_idx = 0
    eyegaze_offset = 0  # Frame offset for eyegaze video sync (positive = eyegaze is ahead, negative = eyegaze is behind)
    
    # --- TIME CONFIG ---
    skip_seconds = 5.0    # Pause (seconds)
    durasi_ambil = 5.0    # Fixation session (seconds)
    
    skip_frames = int(skip_seconds * fps)
    record_frames = int(durasi_ambil * fps)
    
    segment_counter = 1

    print(f"Videos Loaded:")
    print(f"  - Recorded: {recorded_video} ({total_frames} frames)")
    print(f"  - Eyegaze: {eyegaze_video} ({total_frames_eyegaze} frames)")
    print(f"  - FPS: {fps}")
    print("-------------------------------------------------------")
    print("CONTROL:")
    print(" [ a ] : Prev Frame (Backward 1 frame) |  [ d ] : Next Frame (Forward 1 frame)")
    print(" [ r ] : Fast Backward (Backward 30 frames) | [ f ] : Fast Forward (Forward 30 frames)")
    print(" [ w ] : Eyegaze Offset +1 frame (eyegaze ahead) | [ z ] : Eyegaze Offset -1 frame (eyegaze behind)")
    print(" [ e ] : Eyegaze Offset +10 frames | [ c ] : Eyegaze Offset -10 frames")
    print(" ")
    print(" [ s ] : SET START & SAVE (Mark this as t=0, skip 5s, record 5s)")
    print(" [ x ] : AUTO MODE - Extract multiple segments automatically")
    print(" ")
    print(" [ q ] : Quit")
    print("-------------------------------------------------------")

    while True:
        # Set frame position based on index
        cap_recorded.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)
        
        # Apply offset to eyegaze video for synchronization
        eyegaze_frame_idx = current_frame_idx + eyegaze_offset
        eyegaze_frame_idx = max(0, min(eyegaze_frame_idx, total_frames_eyegaze - 1))  # Clamp to valid range
        cap_eyegaze.set(cv2.CAP_PROP_POS_FRAMES, eyegaze_frame_idx)
        
        ret_recorded, frame_recorded = cap_recorded.read()
        ret_eyegaze, frame_eyegaze = cap_eyegaze.read()
        
        if not ret_recorded or not ret_eyegaze:
            break

        # Resize both frames to same height for side-by-side display
        height = min(frame_recorded.shape[0], frame_eyegaze.shape[0], 600)  # Max 600px height
        
        # Resize recorded video frame
        aspect_ratio_recorded = frame_recorded.shape[1] / frame_recorded.shape[0]
        width_recorded = int(height * aspect_ratio_recorded)
        frame_recorded_resized = cv2.resize(frame_recorded, (width_recorded, height))
        
        # Resize eyegaze video frame
        aspect_ratio_eyegaze = frame_eyegaze.shape[1] / frame_eyegaze.shape[0]
        width_eyegaze = int(height * aspect_ratio_eyegaze)
        frame_eyegaze_resized = cv2.resize(frame_eyegaze, (width_eyegaze, height))
        
        # Combine frames side by side
        combined_frame = np.hstack((frame_recorded_resized, frame_eyegaze_resized))
        
        # Show info on the screen
        offset_str = f"(offset: {eyegaze_offset:+d})" if eyegaze_offset != 0 else "(offset: 0)"
        offset_color = (0, 255, 255) if eyegaze_offset != 0 else (0, 255, 0)  # Yellow if offset, green if synced
        cv2.putText(combined_frame, f"Frame: {current_frame_idx}/{total_frames} {offset_str}", (30, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, offset_color, 2)
        cv2.putText(combined_frame, "A/D:Nav | R/F:Fast | W/Z:Offset+/-1 | E/C:±10", (30, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(combined_frame, "Screen Recording", (30, height - 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(combined_frame, "Eyegaze (Tobii)", (width_recorded + 30, height - 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        cv2.imshow('Precision Cutter - Side by Side View', combined_frame)

        # Wait user input (0 = wait forever until key pressed)
        key = cv2.waitKey(0) & 0xFF

        if key == ord('d'): # Next
            if current_frame_idx < total_frames - 1:
                current_frame_idx += 1
        
        elif key == ord('a'): # Prev
            if current_frame_idx > 0:
                current_frame_idx -= 1
        
        elif key == ord('r'): # Fast Backward
            if current_frame_idx >= 30:
                current_frame_idx -= 30
            else:
                current_frame_idx = 0
        
        elif key == ord('f'): # Fast Forward
            if current_frame_idx < total_frames - 30:
                current_frame_idx += 30
            else:
                current_frame_idx = total_frames - 1
        
        elif key == ord('w'): # Increase eyegaze offset +1
            eyegaze_offset += 1
            print(f"Eyegaze offset: {eyegaze_offset:+d} frames")
        
        elif key == ord('z'): # Decrease eyegaze offset -1
            eyegaze_offset -= 1
            print(f"Eyegaze offset: {eyegaze_offset:+d} frames")
        
        elif key == ord('e'): # Increase eyegaze offset +10
            eyegaze_offset += 10
            print(f"Eyegaze offset: {eyegaze_offset:+d} frames")
        
        elif key == ord('c'): # Decrease eyegaze offset -10
            eyegaze_offset -= 10
            print(f"Eyegaze offset: {eyegaze_offset:+d} frames")
                
        elif key == ord('s'): # SAVE ACTION
            start_save_idx = current_frame_idx + skip_frames
            end_save_idx = start_save_idx + record_frames
            
            if end_save_idx > total_frames:
                print("<!>  Warning: Video duration is not enough for required duration!")
            else:
                print(f"<!> Trigger in frame {current_frame_idx} (eyegaze offset: {eyegaze_offset:+d}).")
                print(f"   Skip {skip_seconds}s to frame {start_save_idx}...")
                print(f"   Recording {durasi_ambil}s from frame {start_save_idx} to {end_save_idx}...")
                
                # Setup Writer for eyegaze video segment only
                outfile_eyegaze = f"{validated_path}_segment_{segment_counter}.mp4"
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                
                height_eye, width_eye, _ = frame_eyegaze.shape
                
                out_eyegaze = cv2.VideoWriter(outfile_eyegaze, fourcc, fps, (width_eye, height_eye))
                
                # Specific loop for saving
                # We save current state to avoid it will be missing
                saved_pos = current_frame_idx 
                
                # Apply offset when saving (synchronize eyegaze segment with recorded video)
                eyegaze_start_idx = start_save_idx + eyegaze_offset
                eyegaze_start_idx = max(0, min(eyegaze_start_idx, total_frames_eyegaze - 1))
                cap_eyegaze.set(cv2.CAP_PROP_POS_FRAMES, eyegaze_start_idx)
                
                print(f"Saving {record_frames} frames...")
                for i in tqdm(range(record_frames), desc="Writing frames", unit="frame"):
                    r_eye, f_eye = cap_eyegaze.read()
                    if not r_eye: break
                    out_eyegaze.write(f_eye)
                
                out_eyegaze.release()
                
                # Get codec info
                codec_int = int(fourcc)
                codec_str = "".join([chr((codec_int >> 8 * i) & 0xFF) for i in range(4)])
                
                # Save segment metadata (including offset and video properties)
                metadata_path = f"{validated_path}_segment_{segment_counter}_metadata.txt"
                with open(metadata_path, 'w') as meta_file:
                    meta_file.write("=" * 50 + "\n")
                    meta_file.write("SEGMENT METADATA\n")
                    meta_file.write("=" * 50 + "\n\n")
                    
                    meta_file.write("[SEGMENT INFO]\n")
                    meta_file.write(f"Segment Number: {segment_counter}\n")
                    meta_file.write(f"Trigger Frame: {current_frame_idx}\n")
                    meta_file.write(f"Recording Range: {start_save_idx} to {end_save_idx}\n")
                    meta_file.write(f"Saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    meta_file.write("[SYNCHRONIZATION]\n")
                    meta_file.write(f"Eyegaze Offset: {eyegaze_offset:+d} frames\n")
                    meta_file.write(f"Eyegaze Start Frame: {eyegaze_start_idx}\n")
                    meta_file.write(f"Skip Duration: {skip_seconds}s ({skip_frames} frames)\n\n")
                    
                    meta_file.write("[VIDEO PROPERTIES]\n")
                    meta_file.write(f"Resolution: {width_eye}x{height_eye}\n")
                    meta_file.write(f"FPS: {fps:.2f}\n")
                    meta_file.write(f"Duration: {durasi_ambil}s\n")
                    meta_file.write(f"Total Frames: {record_frames}\n")
                    meta_file.write(f"Codec: {codec_str}\n\n")
                    
                    meta_file.write("[SOURCE FILES]\n")
                    meta_file.write(f"Recorded Video: {recorded_video}\n")
                    meta_file.write(f"Eyegaze Video: {eyegaze_video}\n")
                    meta_file.write(f"Output File: {outfile_eyegaze}\n")
                
                print(f"\nNICE! Eyegaze fixation segment saved at: {outfile_eyegaze}")
                print(f"      Metadata saved at: {metadata_path}")
                segment_counter += 1
                
                # Return the view position or to the next
                current_frame_idx = saved_pos 
                print("Back to preview mode. Please find the next fixation point. (Next/Fast Forward).")
        
        elif key == ord('x'): # AUTO MODE
            print("\n" + "=" * 60)
            print("AUTO EXTRACTION MODE")
            print("=" * 60)
            num_segments = input("How many fixation segments to extract? (default 3): ").strip()
            num_segments = int(num_segments) if num_segments else 3
            
            print(f"\nWill extract {num_segments} segments starting from frame {current_frame_idx}")
            print(f"Current eyegaze offset: {eyegaze_offset:+d} frames")
            print("Each cycle: Skip {:.1f}s → Record {:.1f}s".format(skip_seconds, durasi_ambil))
            confirm = input("Continue? (y/n): ").strip().lower()
            
            if confirm == 'y':
                auto_start_frame = current_frame_idx
                
                print(f"\nExtracting {num_segments} segments...\n")
                
                for seg_num in tqdm(range(num_segments), desc="Segments", unit="segment"):
                    # Calculate segment boundaries
                    start_save_idx = auto_start_frame + skip_frames
                    end_save_idx = start_save_idx + record_frames
                    
                    if end_save_idx > total_frames:
                        tqdm.write(f"\n<!> Segment {seg_num + 1}: Not enough frames remaining!")
                        break
                    
                    tqdm.write(f"[Segment {segment_counter}] Frame {auto_start_frame} → Skip to {start_save_idx} → Record to {end_save_idx} (offset: {eyegaze_offset:+d})")
                    
                    # Setup Writer
                    outfile_eyegaze = f"{validated_path}_segment_{segment_counter}.mp4"
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    
                    # Apply offset when getting sample frame
                    eyegaze_start_idx = start_save_idx + eyegaze_offset
                    eyegaze_start_idx = max(0, min(eyegaze_start_idx, total_frames_eyegaze - 1))
                    
                    # Get frame dimensions from a sample frame
                    cap_eyegaze.set(cv2.CAP_PROP_POS_FRAMES, eyegaze_start_idx)
                    ret_sample, frame_sample = cap_eyegaze.read()
                    if not ret_sample:
                        tqdm.write(f"<!> Cannot read frame at {eyegaze_start_idx}")
                        break
                    
                    height_eye, width_eye, _ = frame_sample.shape
                    out_eyegaze = cv2.VideoWriter(outfile_eyegaze, fourcc, fps, (width_eye, height_eye))
                    
                    # Save frames with offset applied
                    cap_eyegaze.set(cv2.CAP_PROP_POS_FRAMES, eyegaze_start_idx)
                    for i in tqdm(range(record_frames), desc=f"  Writing seg {segment_counter}", unit="fr", leave=False):
                        r_eye, f_eye = cap_eyegaze.read()
                        if not r_eye: break
                        out_eyegaze.write(f_eye)
                    
                    out_eyegaze.release()
                    
                    # Get codec info
                    codec_int = int(fourcc)
                    codec_str = "".join([chr((codec_int >> 8 * i) & 0xFF) for i in range(4)])
                    
                    # Save segment metadata (including offset and video properties)
                    metadata_path = f"{validated_path}_segment_{segment_counter}_metadata.txt"
                    with open(metadata_path, 'w') as meta_file:
                        meta_file.write("=" * 50 + "\n")
                        meta_file.write("SEGMENT METADATA\n")
                        meta_file.write("=" * 50 + "\n\n")
                        
                        meta_file.write("[SEGMENT INFO]\n")
                        meta_file.write(f"Segment Number: {segment_counter}\n")
                        meta_file.write(f"Auto Mode - Segment {seg_num + 1} of {num_segments}\n")
                        meta_file.write(f"Trigger Frame: {auto_start_frame}\n")
                        meta_file.write(f"Recording Range: {start_save_idx} to {end_save_idx}\n")
                        meta_file.write(f"Saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        
                        meta_file.write("[SYNCHRONIZATION]\n")
                        meta_file.write(f"Eyegaze Offset: {eyegaze_offset:+d} frames\n")
                        meta_file.write(f"Eyegaze Start Frame: {eyegaze_start_idx}\n\n")
                        
                        meta_file.write("[VIDEO PROPERTIES]\n")
                        meta_file.write(f"Resolution: {width_eye}x{height_eye}\n")
                        meta_file.write(f"FPS: {fps:.2f}\n")
                        meta_file.write(f"Duration: {durasi_ambil}s\n")
                        meta_file.write(f"Total Frames: {record_frames}\n")
                        meta_file.write(f"Codec: {codec_str}\n\n")
                        
                        meta_file.write("[SOURCE FILES]\n")
                        meta_file.write(f"Recorded Video: {recorded_video}\n")
                        meta_file.write(f"Eyegaze Video: {eyegaze_video}\n")
                        meta_file.write(f"Output File: {outfile_eyegaze}\n")
                    
                    tqdm.write(f"✅ Segment {segment_counter} saved: {outfile_eyegaze}")
                    tqdm.write(f"   Metadata: {metadata_path}")
                    segment_counter += 1
                    
                    # Move to next fixation point (add full cycle time)
                    auto_start_frame = end_save_idx
                
                print("\n" + "=" * 60)
                print(f"AUTO EXTRACTION COMPLETE - {segment_counter - 1} segments saved")
                print("=" * 60)
                print("Press 'q' to quit or continue manually with other keys...")
                
                # Return to the last processed frame
                current_frame_idx = auto_start_frame
            else:
                print("Auto extraction cancelled.")

        elif key == ord('q'):
            break

    cap_recorded.release()
    cap_eyegaze.release()
    cv2.destroyAllWindows()


def detect_tobii_gaze_overlay(frame):
    """
    Detect Tobii Ghost overlay circle (gaze indicator) using Hough Circle Transform
    The Tobii overlay typically shows a semi-transparent circle showing where user is looking
    Returns: (x, y) coordinates of gaze point or None if not detected
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    
    # Detect circles using Hough Circle Transform
    # Adjusted parameters for Tobii overlay circle detection
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=100,      # Minimum distance between detected circles
        param1=50,        # Canny edge threshold
        param2=30,        # Accumulator threshold (lower = more circles detected)
        minRadius=70,     # Minimum circle radius for Tobii overlay
        maxRadius=75     # Maximum circle radius for Tobii overlay
    )
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        # Get the first (most prominent) circle - should be the Tobii indicator
        circle = circles[0][0]
        gaze_x = circle[0]
        gaze_y = circle[1]
        return (gaze_x, gaze_y)
    
    return None


def calculate_euclidean_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def validate_gaze_accuracy(video_path, ground_truth=(960, 540), roi_radii=[5, 10, 15], output_dir='validation_results'):
    """
    Process eyegaze video segment with Tobii overlay to validate gaze accuracy and precision
    
    Parameters:
    - video_path: Path to trimmed eyegaze video segment (with Tobii overlay)
    - ground_truth: (x, y) coordinates of fixation point on screen (center point)
    - roi_radii: List of ROI radius values in pixels for coverage analysis
    - output_dir: Directory to save results
    """
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}")
        return
    
    # Try to read metadata file (contains offset info)
    metadata = {}
    video_dir = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    metadata_path = os.path.join(video_dir, f"{video_name}_metadata.txt")
    
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.strip().split(':', 1)
                        metadata[key.strip()] = value.strip()
            print(f"✓ Metadata file found - includes offset info")
        except Exception as e:
            print(f"Warning: Could not read metadata file: {e}")
    else:
        print(f"ℹ No metadata file found (offset info unavailable)")
    
    file_ext = os.path.splitext(video_path)[1].lower()
    print(f"Opening: {os.path.basename(video_path)} ({file_ext})")
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"\nERROR: Cannot open video file.")
        print(f"File: {video_path}")
        print(f"Format: {file_ext}")
        print("\nPossible solutions:")
        print("  1. If this is an MKV file, try converting to MP4:")
        print("     ffmpeg -i input.mkv -c:v libx264 -c:a aac output.mp4")
        print("  2. Check if the file path has special characters or spaces")
        print("  3. Ensure the file is not corrupted")
        print("  4. Install K-Lite Codec Pack (Windows) for better codec support")
        return
    
    print("✓ Video opened successfully!")
    
    print("=" * 60)
    print("TOBII GAZE VALIDATION TOOL")
    print("=" * 60)
    print("Automatically detecting Tobii Ghost overlay circle...")
    print("Ground Truth (Center Point):", ground_truth)
    print("ROI Radii for Coverage Analysis:", roi_radii)
    
    if metadata:
        print("\nSegment Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
    
    print("=" * 60)
    
    # Initialize tracking lists
    trajectory_x = []
    trajectory_y = []
    distances = []
    frame_numbers = []
    
    # Process all frames
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    frame_idx = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\nProcessing {total_frames} frames...")
    print("Press 'q' to stop processing early\n")
    
    with tqdm(total=total_frames, desc="Validating frames", unit="frame") as pbar:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect Tobii gaze overlay circle
            gaze_point = detect_tobii_gaze_overlay(frame)
            
            if gaze_point is not None:
                gx, gy = gaze_point
                trajectory_x.append(gx)
                trajectory_y.append(gy)
                
                # Calculate distance from ground truth
                distance = calculate_euclidean_distance(gaze_point, ground_truth)
                distances.append(distance)
                frame_numbers.append(frame_idx)
                
                # Draw visualization
                cv2.circle(frame, (gx, gy), 8, (0, 255, 0), 2)  # Detected gaze point (green circle)
                cv2.circle(frame, ground_truth, 10, (0, 0, 255), 2)  # Ground truth center (red circle)
                cv2.line(frame, (gx, gy), ground_truth, (255, 0, 255), 1)  # Line showing distance
            
            # Show progress
            cv2.putText(frame, f"Frame: {frame_idx}/{total_frames}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow('Gaze Validation', frame)
            
            frame_idx += 1
            pbar.update(1)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                tqdm.write("Processing stopped by user")
                break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Calculate metrics
    if len(trajectory_x) == 0:
        print("\nWAIT, WHAT?! No gaze points detected!")
        return
    
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    # 1. Accuracy (Average Error)
    avg_x = np.mean(trajectory_x)
    avg_y = np.mean(trajectory_y)
    avg_error_x = avg_x - ground_truth[0]
    avg_error_y = avg_y - ground_truth[1]
    avg_distance = np.mean(distances)
    
    print(f"\n1. ACCURACY (Average Error from Ground Truth):")
    print(f"   - Average Detected Position: ({avg_x:.2f}, {avg_y:.2f})")
    print(f"   - Ground Truth Position: {ground_truth}")
    print(f"   - Error X: {avg_error_x:.2f} pixels")
    print(f"   - Error Y: {avg_error_y:.2f} pixels")
    print(f"   - Average Euclidean Distance: {avg_distance:.2f} pixels")
    
    # 2. Precision (Standard Deviation)
    std_x = np.std(trajectory_x)
    std_y = np.std(trajectory_y)
    std_distance = np.std(distances)
    
    print(f"\n2. PRECISION (Stability of Gaze):")
    print(f"   - Standard Deviation X: {std_x:.2f} pixels")
    print(f"   - Standard Deviation Y: {std_y:.2f} pixels")
    print(f"   - Standard Deviation Distance: {std_distance:.2f} pixels")
    
    # 3. ROI Coverage for different radii
    print(f"\n3. ROI COVERAGE (Percentage of frames within ROI):")
    roi_coverage = {}
    for radius in roi_radii:
        frames_in_roi = sum(1 for d in distances if d <= radius)
        percentage = (frames_in_roi / len(distances)) * 100
        roi_coverage[radius] = percentage
        print(f"   - Within {radius}px radius: {percentage:.2f}% ({frames_in_roi}/{len(distances)} frames)")
    
    # 4. Detection Rate
    detection_rate = (len(trajectory_x) / total_frames) * 100
    print(f"\n4. DETECTION RATE:")
    print(f"   - Total Frames: {total_frames}")
    print(f"   - Detected Frames: {len(trajectory_x)}")
    print(f"   - Detection Rate: {detection_rate:.2f}%")
    
    # Save results to files
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Save trajectory data to CSV
    trajectory_df = pd.DataFrame({
        'frame': frame_numbers,
        'detected_x': trajectory_x,
        'detected_y': trajectory_y,
        'ground_truth_x': ground_truth[0],
        'ground_truth_y': ground_truth[1],
        'euclidean_distance': distances
    })
    
    csv_path = os.path.join(output_dir, f'{base_name}_trajectory_{timestamp}.csv')
    trajectory_df.to_csv(csv_path, index=False)
    print(f"\nNICE! Trajectory data saved to: {csv_path}")
    
    # Save trajectory data to Excel
    excel_path = os.path.join(output_dir, f'{base_name}_trajectory_{timestamp}.xlsx')
    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Trajectory sheet
            trajectory_df.to_excel(writer, sheet_name='Trajectory', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Total Frames',
                    'Detected Frames',
                    'Detection Rate (%)',
                    'Ground Truth X',
                    'Ground Truth Y',
                    'Average Detected X',
                    'Average Detected Y',
                    'Error X (pixels)',
                    'Error Y (pixels)',
                    'Average Distance (pixels)',
                    'Std Dev X (pixels)',
                    'Std Dev Y (pixels)',
                    'Std Dev Distance (pixels)'
                ],
                'Value': [
                    total_frames,
                    len(trajectory_x),
                    detection_rate,
                    ground_truth[0],
                    ground_truth[1],
                    avg_x,
                    avg_y,
                    avg_error_x,
                    avg_error_y,
                    avg_distance,
                    std_x,
                    std_y,
                    std_distance
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # ROI Coverage sheet
            roi_data = {
                'Radius (pixels)': list(roi_coverage.keys()),
                'Coverage (%)': list(roi_coverage.values()),
                'Frames Inside ROI': [int(len(distances) * (p/100)) for p in roi_coverage.values()]
            }
            roi_df = pd.DataFrame(roi_data)
            roi_df.to_excel(writer, sheet_name='ROI Coverage', index=False)
        
        print(f"NICE! Excel report saved to: {excel_path}")
    except Exception as e:
        print(f"WARNING! Could not save Excel file: {e}")
        print("   (Make sure openpyxl is installed: pip install openpyxl)")
    
    # Save summary report to text file
    report_path = os.path.join(output_dir, f'{base_name}_report_{timestamp}.txt')
    with open(report_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("GAZE VALIDATION REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Video: {video_path}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Ground Truth: {ground_truth}\n")
        
        # Include metadata if available
        if metadata:
            f.write("\n" + "-" * 60 + "\n")
            f.write("SEGMENT METADATA\n")
            f.write("-" * 60 + "\n")
            for key, value in metadata.items():
                f.write(f"{key}: {value}\n")
        
        f.write("\n" + "-" * 60 + "\n")
        f.write("1. ACCURACY METRICS\n")
        f.write("-" * 60 + "\n")
        f.write(f"Average Detected Position: ({avg_x:.2f}, {avg_y:.2f})\n")
        f.write(f"Error X: {avg_error_x:.2f} pixels\n")
        f.write(f"Error Y: {avg_error_y:.2f} pixels\n")
        f.write(f"Average Euclidean Distance: {avg_distance:.2f} pixels\n")
        f.write("\n" + "-" * 60 + "\n")
        f.write("2. PRECISION METRICS\n")
        f.write("-" * 60 + "\n")
        f.write(f"Standard Deviation X: {std_x:.2f} pixels\n")
        f.write(f"Standard Deviation Y: {std_y:.2f} pixels\n")
        f.write(f"Standard Deviation Distance: {std_distance:.2f} pixels\n")
        f.write("\n" + "-" * 60 + "\n")
        f.write("3. ROI COVERAGE\n")
        f.write("-" * 60 + "\n")
        for radius in roi_radii:
            f.write(f"Within {radius}px: {roi_coverage[radius]:.2f}%\n")
        f.write("\n" + "-" * 60 + "\n")
        f.write("4. DETECTION STATISTICS\n")
        f.write("-" * 60 + "\n")
        f.write(f"Total Frames: {total_frames}\n")
        f.write(f"Detected Frames: {len(trajectory_x)}\n")
        f.write(f"Detection Rate: {detection_rate:.2f}%\n")
        f.write("=" * 60 + "\n")
    
    print(f"NICE! Text report saved to: {report_path}")
    print("\nValidation completed successfully!")
    print("=" * 60)


def main():
    """Main function to run the validation pipeline"""
    print("\n" + "=" * 60)
    print("TOBII EYEGAZE VALIDATION SYSTEM")
    print("=" * 60)
    print("\nThis tool provides two functions:")
    print("1. Precision Trimmer - Trim eyegaze videos to extract fixation segments")
    print("2. Gaze Validator - Validate gaze accuracy and precision")
    print("\n" + "=" * 60)
    
    choice = input("\nSelect mode:\n[1] Precision Trimmer\n[2] Gaze Validator\n[3] Both (Trim then Validate)\nChoice: ").strip()
    
    if choice == '1':
        # Trimming mode
        while True:
            recorded_video = input('\nScreen recording video path: ').strip().strip('"').strip("'")
            if recorded_video:
                break
            print("WAIT! Screen recording path is required! Please enter a valid path.")
        
        while True:
            eyegaze_video = input('Eyegaze video path (with Tobii overlay): ').strip().strip('"').strip("'")
            if eyegaze_video:
                break
            print("WAIT! Eyegaze video path is required! Please enter a valid path.")
        
        # Auto-generate output filename from eyegaze video name
        eyegaze_basename = os.path.splitext(os.path.basename(eyegaze_video))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join('validation_segments', f'{eyegaze_basename}_{timestamp}')
        os.makedirs(output_dir, exist_ok=True)
        
        validated_path = os.path.join(output_dir, f'{eyegaze_basename}_fixation')
        print(f"\nOutput directory: {output_dir}")
        print(f"Segments will be saved as: {validated_path}_segment_N.mp4\n")
        
        precise_trimmer(recorded_video, eyegaze_video, validated_path)
        
    elif choice == '2':
        # Validation mode
        while True:
            video_path = input('\nTrimmed eyegaze segment path (with Tobii overlay): ').strip().strip('"').strip("'")
            if video_path:
                break
            print("WAIT! Video path is required! Please enter a valid path.")
        
        # Ground truth input
        gt_x = input('Ground truth X (default 960): ').strip()
        gt_y = input('Ground truth Y (default 540): ').strip()
        
        gt_x = int(gt_x) if gt_x else 960
        gt_y = int(gt_y) if gt_y else 540
        ground_truth = (gt_x, gt_y)
        
        # ROI radii
        radii_input = input('ROI radii in pixels (default: 5, 10, 15): ').strip()
        if radii_input:
            roi_radii = [int(r.strip()) for r in radii_input.split(',')]
        else:
            roi_radii = [5, 10, 15]
        
        # Auto-generate output directory based on video location
        video_dir = os.path.dirname(video_path)
        video_basename = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(video_dir, f'{video_basename}_validation')
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\nValidation results will be saved to: {output_dir}\n")
        
        validate_gaze_accuracy(video_path, ground_truth, roi_radii, output_dir)
        
    elif choice == '3':
        # Combined mode
        print("\n--- STEP 1: TRIMMING ---")
        while True:
            recorded_video = input('\nScreen recording video path: ').strip().strip('"').strip("'")
            if recorded_video:
                break
            print("WAIT! Screen recording path is required! Please enter a valid path.")
        
        while True:
            eyegaze_video = input('Eyegaze video path (with Tobii overlay): ').strip().strip('"').strip("'")
            if eyegaze_video:
                break
            print("WAIT! Eyegaze video path is required! Please enter a valid path.")
        
        # Auto-generate output filename and directory
        eyegaze_basename = os.path.splitext(os.path.basename(eyegaze_video))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join('validation_segments', f'{eyegaze_basename}_{timestamp}')
        os.makedirs(output_dir, exist_ok=True)
        
        validated_path = os.path.join(output_dir, f'{eyegaze_basename}_fixation')
        print(f"\nOutput directory: {output_dir}")
        print(f"Segments will be saved as: {validated_path}_segment_N.mp4\n")
        
        precise_trimmer(recorded_video, eyegaze_video, validated_path)
        
        print("\n--- STEP 2: VALIDATION ---")
        
        # Auto-detect generated segment files
        segment_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.mp4')])
        
        if not segment_files:
            print("\n UH OH! No segment files found to validate!")
            return
        
        print(f"\nFound {len(segment_files)} segment(s) to validate:")
        for i, seg in enumerate(segment_files, 1):
            print(f"  {i}. {seg}")
        
        # Validate all segments or specific one
        validate_all = input('\nValidate all segments? (y/n, default: y): ').strip().lower()
        
        if validate_all == 'n':
            seg_num = input(f'Which segment to validate? (1-{len(segment_files)}): ').strip()
            try:
                seg_idx = int(seg_num) - 1
                segment_files = [segment_files[seg_idx]]
            except (ValueError, IndexError):
                print("Invalid selection. Validating all segments.")
        
        # Ground truth input
        gt_x = input('\nGround truth X (default 960): ').strip()
        gt_y = input('Ground truth Y (default 540): ').strip()
        
        gt_x = int(gt_x) if gt_x else 960
        gt_y = int(gt_y) if gt_y else 540
        ground_truth = (gt_x, gt_y)
        
        # ROI radii
        radii_input = input('ROI radii in pixels (default: 5,10,15): ').strip()
        if radii_input:
            roi_radii = [int(r.strip()) for r in radii_input.split(',')]
        else:
            roi_radii = [5, 10, 15]
        
        # Create validation subdirectory
        validation_dir = os.path.join(output_dir, 'validation_results')
        os.makedirs(validation_dir, exist_ok=True)
        
        print(f"\nValidation results will be saved to: {validation_dir}\n")
        
        # Validate each segment
        for seg_file in segment_files:
            segment_path = os.path.join(output_dir, seg_file)
            print(f"\n{'='*60}")
            print(f"Validating: {seg_file}")
            print(f"{'='*60}")
            validate_gaze_accuracy(segment_path, ground_truth, roi_radii, validation_dir)
    
    else:
        print("Invalid choice. Exiting...")


if __name__ == "__main__":
    main()
