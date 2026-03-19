#!/usr/bin/env python3
"""
Test script for the /api/process_roi endpoint

This script demonstrates how to use the ROI processing API from Python.
Run the Flask app first, then execute this script.
"""

import requests
import json
import sys

def test_process_roi(video_path, rois, gaze_data=None):
    """
    Test the ROI processing API endpoint.
    
    Args:
        video_path: Path to video file
        rois: List of ROI dictionaries
        gaze_data: Optional list of gaze point dictionaries
    """
    
    # API endpoint
    url = 'http://localhost:5000/api/process_roi'
    
    # Prepare payload
    payload = {
        'video_path': video_path,
        'rois': rois,
        'gaze_data': gaze_data or [],
        'start_frame': 0,
        'end_frame': 30,  # Process first 30 frames for testing
        'analysis_type': 'both'
    }
    
    print(f"\n{'='*60}")
    print("Testing ROI Processing API")
    print(f"{'='*60}\n")
    print(f"Video: {video_path}")
    print(f"ROIs: {len(rois)}")
    print(f"Gaze points: {len(gaze_data) if gaze_data else 0}")
    print(f"Frame range: 0-30\n")
    
    try:
        # Send POST request
        print("Sending request to API...")
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("\n✅ API call successful!\n")
                
                # Print summary
                summary = result['summary']
                print(f"Summary:")
                print(f"  Frames processed: {summary['total_frames_processed']}")
                print(f"  FPS: {summary['fps']}")
                print(f"  Frame range: {summary['start_frame']}-{summary['end_frame']}")
                
                print(f"\n{'='*60}")
                print("ROI Summaries:")
                print(f"{'='*60}")
                
                for roi_summary in summary['roi_summaries']:
                    print(f"\n📍 {roi_summary['label']}")
                    print(f"   Total gaze hits: {roi_summary['total_gaze_hits']}")
                    print(f"   Average intensity:")
                    intensities = roi_summary['avg_intensity']
                    print(f"     R: {intensities['r']:.2f}")
                    print(f"     G: {intensities['g']:.2f}")
                    print(f"     B: {intensities['b']:.2f}")
                    print(f"     Gray: {intensities['gray']:.2f}")
                    print(f"     Avg: {intensities['avg']:.2f}")
                
                # Show sample frame data
                if result['frames']:
                    print(f"\n{'='*60}")
                    print("Sample Frame Data (First 3 frames):")
                    print(f"{'='*60}")
                    
                    for frame_data in result['frames'][:3]:
                        print(f"\nFrame {frame_data['frame']} @ {frame_data['timestamp']:.2f}s")
                        for roi in frame_data['rois']:
                            print(f"  → {roi['label']}: ", end='')
                            if 'mean_intensity' in roi:
                                print(f"intensity={roi['mean_intensity']['avg']:.2f}", end='')
                            if 'gaze_hits' in roi:
                                print(f", gaze_hits={roi['gaze_hits']}/{roi['gaze_total']}", end='')
                            print()
                
                print(f"\n{'='*60}")
                print("✅ Test completed successfully!")
                print(f"{'='*60}\n")
                
                return result
                
            else:
                print(f"\n❌ API returned error: {result.get('error', 'Unknown error')}")
                return None
        else:
            error_msg = response.json().get('error', 'Unknown error')
            print(f"\n❌ HTTP Error {response.status_code}: {error_msg}")
            return None
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timeout - video processing may take too long")
        return None
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection error - is the Flask app running on port 5000?")
        return None
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return None


def main():
    """Run test cases"""
    
    # Example 1: Process ROIs without gaze data (intensity only)
    print("\nTest 1: Intensity analysis without gaze data")
    print("-" * 60)
    
    video_path = "uploaded_videos/example_video.mp4"
    rois = [
        {
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 150,
            "label": "Top Left ROI"
        },
        {
            "x": 400,
            "y": 200,
            "width": 300,
            "height": 200,
            "label": "Center ROI"
        }
    ]
    
    result1 = test_process_roi(video_path, rois)
    
    # Example 2: Process with gaze data
    print("\n\nTest 2: Full analysis with gaze data")
    print("-" * 60)
    
    # Generate sample gaze data
    gaze_data = []
    for frame in range(30):
        # Simulate gaze points moving across the screen
        x = 150 + (frame * 5)
        y = 175 + (frame * 2)
        gaze_data.append({
            "frame": frame,
            "x": x,
            "y": y
        })
    
    result2 = test_process_roi(video_path, rois, gaze_data)
    
    # Save results to file
    if result2:
        output_file = "roi_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(result2, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")


if __name__ == '__main__':
    # Check if video path provided as argument
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        
        # Simple test with provided video
        rois = [
            {"x": 100, "y": 100, "width": 200, "height": 150, "label": "ROI 1"},
            {"x": 350, "y": 150, "width": 250, "height": 180, "label": "ROI 2"}
        ]
        
        test_process_roi(video_path, rois)
    else:
        # Run full test suite
        main()
