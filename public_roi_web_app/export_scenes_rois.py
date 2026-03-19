#!/usr/bin/env python3
"""
Export Scenes and ROIs - Python Script

This script demonstrates how to export scenes and ROIs data from the
Video ROI Analyzer application using the /api/export-scenes-rois endpoint.

Features:
- Export to CSV (flat table format)
- Export to JSON (nested structure)
- Normalized coordinates (0-1 range)
- Timestamp calculations (HH:MM:SS)
- Frame numbers and durations

Usage:
    python export_scenes_rois.py
    python export_scenes_rois.py --format json
    python export_scenes_rois.py --workspace path/to/workspace.json
"""

import requests
import json
import argparse
import os
import sys
from pathlib import Path


def load_workspace(workspace_path):
    """Load workspace JSON file."""
    try:
        with open(workspace_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'scenes' not in data or 'video_info' not in data:
            print(f"❌ Invalid workspace file: missing required fields")
            return None
        
        return data
    except FileNotFoundError:
        print(f"❌ Workspace file not found: {workspace_path}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in workspace file")
        return None


def export_scenes_rois(scenes, video_info, format='csv', filename='export', api_url='http://localhost:5000'):
    """
    Export scenes and ROIs data via API endpoint.
    
    Args:
        scenes: List of scene dictionaries
        video_info: Video metadata dictionary
        format: 'csv' or 'json'
        filename: Base filename for export
        api_url: Base URL for API server
    
    Returns:
        Response data or None if failed
    """
    
    endpoint = f"{api_url}/api/export-scenes-rois"
    
    payload = {
        'scenes': scenes,
        'video_info': video_info,
        'format': format,
        'filename': filename,
        'include_normalized': True,
        'include_timestamps': True
    }
    
    print(f"\n{'='*60}")
    print(f"Exporting Scenes and ROIs to {format.upper()}")
    print(f"{'='*60}\n")
    print(f"API Endpoint: {endpoint}")
    print(f"Scenes: {len(scenes)}")
    print(f"Total ROIs: {sum(len(s.get('rois', [])) for s in scenes)}")
    print(f"Video: {video_info.get('filename', 'Unknown')}")
    print(f"Resolution: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
    print(f"FPS: {video_info.get('fps', 0)}")
    print()
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print(f"✅ Export successful!\n")
                print(f"Format: {result['format'].upper()}")
                print(f"Filename: {result['filename']}")
                print(f"Path: {result['path']}")
                
                if format == 'csv':
                    print(f"Rows exported: {result['rows']}")
                
                print(f"Scenes: {result['scenes']}")
                print(f"Total ROIs: {result['total_rois']}")
                
                print(f"\n{'='*60}")
                print("✅ Export completed successfully!")
                print(f"{'='*60}\n")
                
                return result
            else:
                error = result.get('error', 'Unknown error')
                print(f"❌ Export failed: {error}")
                return None
                
        else:
            error_data = response.json()
            print(f"❌ HTTP Error {response.status_code}: {error_data.get('error', 'Unknown error')}")
            return None
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error - is the Flask server running on {api_url}?")
        return None
    except requests.exceptions.Timeout:
        print(f"❌ Request timeout")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None


def create_sample_data():
    """Create sample scenes and ROIs for testing."""
    
    video_info = {
        'filename': 'sample_video.mp4',
        'width': 1920,
        'height': 1080,
        'fps': 30.0,
        'total_frames': 900
    }
    
    scenes = [
        {
            'name': 'Scene 1',
            'custom_name': 'Introduction',
            'start_frame': 0,
            'end_frame': 299,
            'rois': [
                {
                    'label': 'Logo',
                    'x': 100,
                    'y': 100,
                    'width': 300,
                    'height': 200,
                    'color_tag': '#61AFEF'
                },
                {
                    'label': 'Product',
                    'x': 800,
                    'y': 400,
                    'width': 400,
                    'height': 300,
                    'color_tag': '#98C379'
                }
            ]
        },
        {
            'name': 'Scene 2',
            'custom_name': 'Main Content',
            'start_frame': 300,
            'end_frame': 599,
            'rois': [
                {
                    'label': 'Text Area',
                    'x': 200,
                    'y': 200,
                    'width': 600,
                    'height': 400,
                    'color_tag': '#E5C07B'
                },
                {
                    'label': 'CTA Button',
                    'x': 1400,
                    'y': 900,
                    'width': 300,
                    'height': 100,
                    'color_tag': '#E06C75'
                }
            ]
        },
        {
            'name': 'Scene 3',
            'custom_name': 'Conclusion',
            'start_frame': 600,
            'end_frame': 899,
            'rois': [
                {
                    'label': 'Contact Info',
                    'x': 500,
                    'y': 800,
                    'width': 920,
                    'height': 200,
                    'color_tag': '#C678DD'
                }
            ]
        }
    ]
    
    return scenes, video_info


def main():
    parser = argparse.ArgumentParser(
        description='Export scenes and ROIs data from Video ROI Analyzer'
    )
    parser.add_argument(
        '--workspace',
        type=str,
        help='Path to workspace JSON file'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['csv', 'json'],
        default='csv',
        help='Export format (default: csv)'
    )
    parser.add_argument(
        '--filename',
        type=str,
        default='scenes_rois_export',
        help='Base filename for export (default: scenes_rois_export)'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default='http://localhost:5000',
        help='API server URL (default: http://localhost:5000)'
    )
    parser.add_argument(
        '--sample',
        action='store_true',
        help='Use sample data instead of loading workspace'
    )
    
    args = parser.parse_args()
    
    # Load data
    if args.sample:
        print("Using sample data...")
        scenes, video_info = create_sample_data()
    elif args.workspace:
        print(f"Loading workspace: {args.workspace}")
        workspace = load_workspace(args.workspace)
        if not workspace:
            sys.exit(1)
        scenes = workspace['scenes']
        video_info = workspace['video_info']
    else:
        # Try to find workspace files in projects directory
        projects_dir = Path('projects')
        if projects_dir.exists():
            workspace_files = list(projects_dir.glob('*.json'))
            if workspace_files:
                print(f"\nFound {len(workspace_files)} workspace file(s):")
                for i, f in enumerate(workspace_files, 1):
                    print(f"  {i}. {f.name}")
                
                choice = input(f"\nSelect workspace (1-{len(workspace_files)}) or press Enter to use sample data: ").strip()
                
                if choice.isdigit() and 1 <= int(choice) <= len(workspace_files):
                    workspace_path = workspace_files[int(choice) - 1]
                    print(f"\nLoading: {workspace_path}")
                    workspace = load_workspace(workspace_path)
                    if not workspace:
                        sys.exit(1)
                    scenes = workspace['scenes']
                    video_info = workspace['video_info']
                else:
                    print("\nUsing sample data...")
                    scenes, video_info = create_sample_data()
            else:
                print("\nNo workspace files found. Using sample data...")
                scenes, video_info = create_sample_data()
        else:
            print("\nNo projects directory found. Using sample data...")
            scenes, video_info = create_sample_data()
    
    # Export data
    result = export_scenes_rois(
        scenes,
        video_info,
        format=args.format,
        filename=args.filename,
        api_url=args.api_url
    )
    
    if result:
        print(f"\n💡 Tip: You can find the exported file at:")
        print(f"   {result['path']}")
        
        if args.format == 'csv':
            print(f"\n💡 CSV file can be opened in:")
            print(f"   - Microsoft Excel")
            print(f"   - Google Sheets")
            print(f"   - Python pandas: pd.read_csv('{result['filename']}')")
        else:
            print(f"\n💡 JSON file can be used in:")
            print(f"   - Python: json.load(open('{result['filename']}'))")
            print(f"   - JavaScript: fetch('{result['filename']}').then(r => r.json())")
            print(f"   - Any programming language with JSON support")
        
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
