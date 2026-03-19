"""
Visualization Module

This module provides visualization functions for gaze tracking data analysis,
including trajectory plots, heatmaps, scanpaths, and statistical charts.

Author: Kahlil Gibran Al Zulmi
Institution: Institut Teknologi Sepuluh Nopember
Date: November 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.collections import LineCollection
import seaborn as sns
from typing import List, Tuple, Dict, Any, Optional
import cv2
from scipy.ndimage import gaussian_filter

from utils.logger import log_info, log_error


# ============================================================================
# CONFIGURATION
# ============================================================================

# Set matplotlib style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Default figure size
DEFAULT_FIGSIZE = (12, 8)

# Colormap for heatmaps
HEATMAP_COLORMAP = 'hot'


# ============================================================================
# GAZE TRAJECTORY VISUALIZATION
# ============================================================================

def plot_gaze_trajectory(
    gaze_points: List[Tuple[float, float]],
    screen_size: Tuple[int, int] = (1920, 1080),
    title: str = "Gaze Trajectory",
    show_points: bool = True,
    show_path: bool = True,
    color_by_time: bool = True,
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot gaze trajectory over time.
    
    Args:
        gaze_points: List of (x, y) gaze coordinates
        screen_size: Screen dimensions (width, height)
        title: Plot title
        show_points: Show individual gaze points
        show_path: Show connecting path lines
        color_by_time: Color points/lines by temporal order
        output_path: Path to save figure (if provided)
        
    Returns:
        matplotlib Figure object
    """
    try:
        fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
        
        if not gaze_points:
            ax.text(0.5, 0.5, 'No gaze data', ha='center', va='center')
            return fig
        
        # Extract x and y coordinates
        x_coords = [p[0] for p in gaze_points]
        y_coords = [p[1] for p in gaze_points]
        
        # Create time array for coloring
        time_array = np.arange(len(gaze_points))
        
        if color_by_time:
            # Color by temporal order
            if show_path:
                points = np.array([x_coords, y_coords]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                lc = LineCollection(segments, cmap='viridis', alpha=0.7)
                lc.set_array(time_array[:-1])
                lc.set_linewidth(2)
                ax.add_collection(lc)
                
            if show_points:
                scatter = ax.scatter(
                    x_coords, y_coords,
                    c=time_array, cmap='viridis',
                    s=30, alpha=0.6, edgecolors='white', linewidths=0.5
                )
                plt.colorbar(scatter, ax=ax, label='Time (frames)')
        else:
            # Single color
            if show_path:
                ax.plot(x_coords, y_coords, 'b-', alpha=0.5, linewidth=1.5)
            if show_points:
                ax.scatter(x_coords, y_coords, c='blue', s=30, alpha=0.6)
        
        # Mark start and end points
        ax.scatter(x_coords[0], y_coords[0], c='green', s=200, marker='o',
                  edgecolors='white', linewidths=2, label='Start', zorder=10)
        ax.scatter(x_coords[-1], y_coords[-1], c='red', s=200, marker='X',
                  edgecolors='white', linewidths=2, label='End', zorder=10)
        
        # Set limits and labels
        ax.set_xlim(0, screen_size[0])
        ax.set_ylim(0, screen_size[1])
        ax.invert_yaxis()  # Invert y-axis to match screen coordinates
        ax.set_xlabel('X Position (pixels)', fontsize=12)
        ax.set_ylabel('Y Position (pixels)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            log_info(f"Gaze trajectory saved to {output_path}")
        
        return fig
    
    except Exception as e:
        log_error(f"Error plotting gaze trajectory: {str(e)}")
        raise


# ============================================================================
# HEATMAP VISUALIZATION
# ============================================================================

def generate_gaze_heatmap(
    gaze_points: List[Tuple[float, float]],
    screen_size: Tuple[int, int] = (1920, 1080),
    background_image: Optional[np.ndarray] = None,
    sigma: float = 20,
    title: str = "Gaze Heatmap",
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Generate heatmap showing gaze fixation density.
    
    Args:
        gaze_points: List of (x, y) gaze coordinates
        screen_size: Screen dimensions (width, height)
        background_image: Optional background image to overlay heatmap on
        sigma: Gaussian blur sigma for smoothing
        title: Plot title
        output_path: Path to save figure (if provided)
        
    Returns:
        matplotlib Figure object
    """
    try:
        fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
        
        if not gaze_points:
            ax.text(0.5, 0.5, 'No gaze data', ha='center', va='center')
            return fig
        
        # Create 2D histogram
        x_coords = [p[0] for p in gaze_points]
        y_coords = [p[1] for p in gaze_points]
        
        # Create heatmap
        heatmap, xedges, yedges = np.histogram2d(
            x_coords, y_coords,
            bins=[screen_size[0]//10, screen_size[1]//10],
            range=[[0, screen_size[0]], [0, screen_size[1]]]
        )
        
        # Apply Gaussian smoothing
        heatmap = gaussian_filter(heatmap, sigma=sigma/10)
        
        # Normalize
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()
        
        # Show background image if provided
        if background_image is not None:
            ax.imshow(background_image, extent=[0, screen_size[0], screen_size[1], 0], alpha=0.5)
        
        # Show heatmap
        im = ax.imshow(
            heatmap.T,
            extent=[0, screen_size[0], 0, screen_size[1]],
            origin='lower',
            cmap=HEATMAP_COLORMAP,
            alpha=0.7,
            interpolation='bilinear'
        )
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Fixation Density', fontsize=12)
        
        # Set labels and title
        ax.set_xlim(0, screen_size[0])
        ax.set_ylim(0, screen_size[1])
        ax.invert_yaxis()
        ax.set_xlabel('X Position (pixels)', fontsize=12)
        ax.set_ylabel('Y Position (pixels)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_aspect('equal')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            log_info(f"Gaze heatmap saved to {output_path}")
        
        return fig
    
    except Exception as e:
        log_error(f"Error generating gaze heatmap: {str(e)}")
        raise


# ============================================================================
# SCANPATH VISUALIZATION
# ============================================================================

def plot_scanpath(
    fixations: List[Dict[str, Any]],
    screen_size: Tuple[int, int] = (1920, 1080),
    background_image: Optional[np.ndarray] = None,
    show_duration: bool = True,
    show_numbers: bool = True,
    title: str = "Scanpath Analysis",
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot scanpath with fixations and saccades.
    
    Args:
        fixations: List of fixation dicts with 'x', 'y', 'duration' keys
        screen_size: Screen dimensions (width, height)
        background_image: Optional background image
        show_duration: Size circles by fixation duration
        show_numbers: Show fixation sequence numbers
        title: Plot title
        output_path: Path to save figure (if provided)
        
    Returns:
        matplotlib Figure object
    """
    try:
        fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
        
        if not fixations:
            ax.text(0.5, 0.5, 'No fixation data', ha='center', va='center')
            return fig
        
        # Show background if provided
        if background_image is not None:
            ax.imshow(background_image, extent=[0, screen_size[0], screen_size[1], 0], alpha=0.5)
        
        # Extract coordinates and durations
        x_coords = [f['x'] for f in fixations]
        y_coords = [f['y'] for f in fixations]
        durations = [f.get('duration', 100) for f in fixations]
        
        # Normalize durations for circle sizes
        if show_duration:
            min_dur = min(durations)
            max_dur = max(durations)
            if max_dur > min_dur:
                sizes = [(d - min_dur) / (max_dur - min_dur) * 500 + 100 for d in durations]
            else:
                sizes = [200] * len(durations)
        else:
            sizes = [200] * len(durations)
        
        # Draw saccades (lines between fixations)
        for i in range(len(fixations) - 1):
            ax.plot(
                [x_coords[i], x_coords[i+1]],
                [y_coords[i], y_coords[i+1]],
                'b-', alpha=0.3, linewidth=2, zorder=1
            )
            
            # Add arrow at midpoint
            mid_x = (x_coords[i] + x_coords[i+1]) / 2
            mid_y = (y_coords[i] + y_coords[i+1]) / 2
            dx = x_coords[i+1] - x_coords[i]
            dy = y_coords[i+1] - y_coords[i]
            ax.arrow(mid_x - dx*0.1, mid_y - dy*0.1, dx*0.1, dy*0.1,
                    head_width=20, head_length=15, fc='blue', ec='blue',
                    alpha=0.5, zorder=2)
        
        # Draw fixations
        scatter = ax.scatter(
            x_coords, y_coords,
            s=sizes, c=range(len(fixations)),
            cmap='viridis', alpha=0.7,
            edgecolors='white', linewidths=2, zorder=3
        )
        
        # Add fixation numbers
        if show_numbers:
            for i, (x, y) in enumerate(zip(x_coords, y_coords)):
                ax.text(x, y, str(i+1), ha='center', va='center',
                       fontsize=10, fontweight='bold', color='white', zorder=4)
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Fixation Order', fontsize=12)
        
        # Set labels and title
        ax.set_xlim(0, screen_size[0])
        ax.set_ylim(0, screen_size[1])
        ax.invert_yaxis()
        ax.set_xlabel('X Position (pixels)', fontsize=12)
        ax.set_ylabel('Y Position (pixels)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_aspect('equal')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            log_info(f"Scanpath plot saved to {output_path}")
        
        return fig
    
    except Exception as e:
        log_error(f"Error plotting scanpath: {str(e)}")
        raise


# ============================================================================
# TEMPORAL ANALYSIS
# ============================================================================

def plot_gaze_timeline(
    timestamps: List[float],
    x_coords: List[float],
    y_coords: List[float],
    title: str = "Gaze Position Over Time",
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot gaze x and y positions over time.
    
    Args:
        timestamps: List of timestamps (seconds)
        x_coords: List of x coordinates
        y_coords: List of y coordinates
        title: Plot title
        output_path: Path to save figure (if provided)
        
    Returns:
        matplotlib Figure object
    """
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        
        # Plot X coordinate
        ax1.plot(timestamps, x_coords, 'b-', linewidth=1.5, alpha=0.7, label='X Position')
        ax1.set_ylabel('X Position (pixels)', fontsize=12)
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper right')
        
        # Plot Y coordinate
        ax2.plot(timestamps, y_coords, 'r-', linewidth=1.5, alpha=0.7, label='Y Position')
        ax2.set_xlabel('Time (seconds)', fontsize=12)
        ax2.set_ylabel('Y Position (pixels)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            log_info(f"Gaze timeline saved to {output_path}")
        
        return fig
    
    except Exception as e:
        log_error(f"Error plotting gaze timeline: {str(e)}")
        raise


def plot_velocity_profile(
    timestamps: List[float],
    velocities: List[float],
    threshold: Optional[float] = None,
    title: str = "Gaze Velocity Profile",
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot gaze velocity over time.
    
    Args:
        timestamps: List of timestamps (seconds)
        velocities: List of velocity values (pixels/second)
        threshold: Optional threshold line to show
        title: Plot title
        output_path: Path to save figure (if provided)
        
    Returns:
        matplotlib Figure object
    """
    try:
        fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
        
        # Plot velocity
        ax.plot(timestamps, velocities, 'b-', linewidth=1.5, alpha=0.7, label='Velocity')
        
        # Add threshold line if provided
        if threshold is not None:
            ax.axhline(y=threshold, color='r', linestyle='--', linewidth=2,
                      alpha=0.7, label=f'Threshold ({threshold:.1f} px/s)')
        
        # Labels and title
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Velocity (pixels/second)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            log_info(f"Velocity profile saved to {output_path}")
        
        return fig
    
    except Exception as e:
        log_error(f"Error plotting velocity profile: {str(e)}")
        raise


# ============================================================================
# REGION OF INTEREST (ROI) ANALYSIS
# ============================================================================

def plot_roi_analysis(
    gaze_points: List[Tuple[float, float]],
    rois: List[Dict[str, Any]],
    screen_size: Tuple[int, int] = (1920, 1080),
    background_image: Optional[np.ndarray] = None,
    title: str = "ROI Analysis",
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot gaze points with regions of interest.
    
    Args:
        gaze_points: List of (x, y) gaze coordinates
        rois: List of ROI dicts with 'name', 'x', 'y', 'width', 'height'
        screen_size: Screen dimensions (width, height)
        background_image: Optional background image
        title: Plot title
        output_path: Path to save figure (if provided)
        
    Returns:
        matplotlib Figure object
    """
    try:
        fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
        
        # Show background if provided
        if background_image is not None:
            ax.imshow(background_image, extent=[0, screen_size[0], screen_size[1], 0], alpha=0.5)
        
        # Draw ROIs
        colors = plt.cm.Set3(np.linspace(0, 1, len(rois)))
        for i, roi in enumerate(rois):
            rect = Rectangle(
                (roi['x'], roi['y']),
                roi['width'], roi['height'],
                linewidth=2, edgecolor=colors[i],
                facecolor=colors[i], alpha=0.3,
                label=roi.get('name', f'ROI {i+1}')
            )
            ax.add_patch(rect)
        
        # Plot gaze points
        if gaze_points:
            x_coords = [p[0] for p in gaze_points]
            y_coords = [p[1] for p in gaze_points]
            ax.scatter(x_coords, y_coords, c='red', s=10, alpha=0.5, label='Gaze Points')
        
        # Set limits and labels
        ax.set_xlim(0, screen_size[0])
        ax.set_ylim(0, screen_size[1])
        ax.invert_yaxis()
        ax.set_xlabel('X Position (pixels)', fontsize=12)
        ax.set_ylabel('Y Position (pixels)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
        ax.set_aspect('equal')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            log_info(f"ROI analysis plot saved to {output_path}")
        
        return fig
    
    except Exception as e:
        log_error(f"Error plotting ROI analysis: {str(e)}")
        raise


# ============================================================================
# STATISTICAL CHARTS
# ============================================================================

def plot_fixation_duration_histogram(
    durations: List[float],
    bins: int = 30,
    title: str = "Fixation Duration Distribution",
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot histogram of fixation durations.
    
    Args:
        durations: List of fixation durations (milliseconds)
        bins: Number of histogram bins
        title: Plot title
        output_path: Path to save figure (if provided)
        
    Returns:
        matplotlib Figure object
    """
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot histogram
        n, bins_edges, patches = ax.hist(durations, bins=bins, color='skyblue',
                                         edgecolor='black', alpha=0.7)
        
        # Add mean line
        mean_duration = np.mean(durations)
        ax.axvline(mean_duration, color='red', linestyle='--', linewidth=2,
                  label=f'Mean: {mean_duration:.1f} ms')
        
        # Add median line
        median_duration = np.median(durations)
        ax.axvline(median_duration, color='green', linestyle='--', linewidth=2,
                  label=f'Median: {median_duration:.1f} ms')
        
        # Labels and title
        ax.set_xlabel('Duration (milliseconds)', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            log_info(f"Duration histogram saved to {output_path}")
        
        return fig
    
    except Exception as e:
        log_error(f"Error plotting fixation duration histogram: {str(e)}")
        raise


def plot_roi_attention_pie(
    roi_data: Dict[str, float],
    title: str = "Attention Distribution by ROI",
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot pie chart of attention distribution across ROIs.
    
    Args:
        roi_data: Dictionary mapping ROI names to percentages
        title: Plot title
        output_path: Path to save figure (if provided)
        
    Returns:
        matplotlib Figure object
    """
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Prepare data
        labels = list(roi_data.keys())
        sizes = list(roi_data.values())
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90,
            textprops={'fontsize': 11}
        )
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.axis('equal')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            log_info(f"ROI attention pie chart saved to {output_path}")
        
        return fig
    
    except Exception as e:
        log_error(f"Error plotting ROI attention pie chart: {str(e)}")
        raise


# ============================================================================
# COMPARISON PLOTS
# ============================================================================

def plot_session_comparison(
    session_data: List[Dict[str, Any]],
    metric: str = 'score',
    title: str = "Session Comparison",
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot bar chart comparing multiple sessions.
    
    Args:
        session_data: List of session dicts with 'name' and metric keys
        metric: Metric to compare (e.g., 'score', 'accuracy', 'time')
        title: Plot title
        output_path: Path to save figure (if provided)
        
    Returns:
        matplotlib Figure object
    """
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Extract data
        names = [s['name'] for s in session_data]
        values = [s[metric] for s in session_data]
        
        # Create bar chart
        bars = ax.bar(range(len(names)), values, color='steelblue',
                      edgecolor='black', alpha=0.7)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Labels and title
        ax.set_xlabel('Session', fontsize=12)
        ax.set_ylabel(metric.capitalize(), fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            log_info(f"Session comparison saved to {output_path}")
        
        return fig
    
    except Exception as e:
        log_error(f"Error plotting session comparison: {str(e)}")
        raise


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def close_all_figures():
    """Close all matplotlib figures to free memory."""
    plt.close('all')


def calculate_velocity(
    gaze_points: List[Tuple[float, float]],
    timestamps: List[float]
) -> List[float]:
    """
    Calculate gaze velocity between consecutive points.
    
    Args:
        gaze_points: List of (x, y) gaze coordinates
        timestamps: List of timestamps (seconds)
        
    Returns:
        List of velocity values (pixels/second)
    """
    velocities = []
    
    for i in range(1, len(gaze_points)):
        dx = gaze_points[i][0] - gaze_points[i-1][0]
        dy = gaze_points[i][1] - gaze_points[i-1][1]
        dt = timestamps[i] - timestamps[i-1]
        
        if dt > 0:
            distance = np.sqrt(dx**2 + dy**2)
            velocity = distance / dt
            velocities.append(velocity)
        else:
            velocities.append(0)
    
    return velocities


if __name__ == "__main__":
    # Test visualization functions
    print("Visualization Module Test")
    print("=" * 60)
    
    # Generate sample data
    np.random.seed(42)
    n_points = 100
    
    # Random walk gaze trajectory
    gaze_x = np.cumsum(np.random.randn(n_points) * 50) + 960
    gaze_y = np.cumsum(np.random.randn(n_points) * 50) + 540
    gaze_points = list(zip(gaze_x, gaze_y))
    
    # Test trajectory plot
    fig1 = plot_gaze_trajectory(gaze_points, title="Test Gaze Trajectory")
    print("✓ Gaze trajectory plot created")
    
    # Test heatmap
    fig2 = generate_gaze_heatmap(gaze_points, title="Test Gaze Heatmap")
    print("✓ Gaze heatmap created")
    
    # Test fixations
    fixations = [
        {'x': 960, 'y': 540, 'duration': 200},
        {'x': 800, 'y': 400, 'duration': 150},
        {'x': 1100, 'y': 600, 'duration': 300},
        {'x': 900, 'y': 500, 'duration': 180}
    ]
    fig3 = plot_scanpath(fixations, title="Test Scanpath")
    print("✓ Scanpath plot created")
    
    print("\n✓ All visualization functions working")
    plt.close('all')
