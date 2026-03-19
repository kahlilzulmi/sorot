"""
Euclidean Distance Visualization for Gaze Tracking
===================================================
This script visualizes how Euclidean distance is calculated and used
to evaluate gaze detection accuracy.

Mathematical Formula:
    d = √[(x_detected - x_GT)² + (y_detected - y_GT)²]

Author: Eye Gaze Detection Comparison System
Date: January 30, 2026
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
import os

# Configuration
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "visualizations")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Constants
WIDTH = 1920
HEIGHT = 1080
DISTANCE_THRESHOLD = 75.0  # pixels

# Color scheme
COLOR_GT = '#00FF00'        # Green for Ground Truth
COLOR_ACCURATE = '#FFFF00'  # Yellow for accurate detection
COLOR_ERROR = '#FF0000'     # Red for error detection
COLOR_THRESHOLD = '#0088FF' # Blue for threshold circle


def calculate_euclidean_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points."""
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def visualize_basic_concept():
    """Visualize the basic concept of Euclidean distance."""
    print("Generating: Basic Euclidean Distance Concept...")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Example coordinates
    gt_x, gt_y = 500, 400
    det_x, det_y = 650, 550
    
    # Calculate distance
    distance = calculate_euclidean_distance(gt_x, gt_y, det_x, det_y)
    
    # Draw coordinate system
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 800)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlabel('X coordinate (pixels)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y coordinate (pixels)', fontsize=12, fontweight='bold')
    ax.set_title('Euclidean Distance: Basic Concept', fontsize=16, fontweight='bold', pad=20)
    
    # Draw points
    ax.plot(gt_x, gt_y, 'o', color=COLOR_GT, markersize=20, label='Ground Truth (GT)', zorder=5)
    ax.plot(det_x, det_y, 'o', color=COLOR_ERROR, markersize=20, label='Detected Position', zorder=5)
    
    # Draw distance line
    ax.plot([gt_x, det_x], [gt_y, det_y], 'k--', linewidth=2, alpha=0.7, zorder=3)
    
    # Draw right triangle components
    ax.plot([gt_x, det_x], [gt_y, gt_y], 'b-', linewidth=1.5, alpha=0.5, label=f'Δx = {det_x - gt_x}px')
    ax.plot([det_x, det_x], [gt_y, det_y], 'r-', linewidth=1.5, alpha=0.5, label=f'Δy = {det_y - gt_y}px')
    
    # Annotate distance
    mid_x = (gt_x + det_x) / 2
    mid_y = (gt_y + det_y) / 2
    ax.annotate(f'd = {distance:.1f}px', 
                xy=(mid_x, mid_y), xytext=(mid_x + 50, mid_y + 50),
                fontsize=14, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', lw=2))
    
    # Add formula text box
    formula_text = (
        "Euclidean Distance Formula:\n\n"
        f"d = √[(x₂ - x₁)² + (y₂ - y₁)²]\n\n"
        f"d = √[({det_x} - {gt_x})² + ({det_y} - {gt_y})²]\n"
        f"d = √[{(det_x - gt_x)**2} + {(det_y - gt_y)**2}]\n"
        f"d = √{(det_x - gt_x)**2 + (det_y - gt_y)**2}\n"
        f"d = {distance:.2f} pixels"
    )
    
    ax.text(0.02, 0.98, formula_text,
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax.legend(loc='upper right', fontsize=11)
    ax.invert_yaxis()  # Match image coordinate system
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '1_basic_concept.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 1_basic_concept.png")


def visualize_threshold_concept():
    """Visualize the threshold radius concept."""
    print("Generating: Threshold Radius Concept...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Left plot: Accurate tracking (within threshold)
    gt_x1, gt_y1 = 500, 400
    det_x1, det_y1 = 540, 430
    distance1 = calculate_euclidean_distance(gt_x1, gt_y1, det_x1, det_y1)
    
    ax1.set_xlim(300, 700)
    ax1.set_ylim(200, 600)
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('ACCURATE TRACKING\n(Within Threshold)', fontsize=14, fontweight='bold', color='green')
    ax1.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax1.set_ylabel('Y coordinate (pixels)', fontsize=11)
    
    # Draw threshold circle
    circle1 = Circle((gt_x1, gt_y1), DISTANCE_THRESHOLD, 
                     color=COLOR_THRESHOLD, fill=False, linewidth=3, 
                     linestyle='--', label=f'Threshold Radius ({DISTANCE_THRESHOLD}px)')
    ax1.add_patch(circle1)
    
    # Fill acceptable zone
    circle1_fill = Circle((gt_x1, gt_y1), DISTANCE_THRESHOLD, 
                          color=COLOR_GT, alpha=0.1)
    ax1.add_patch(circle1_fill)
    
    # Draw points
    ax1.plot(gt_x1, gt_y1, 'o', color=COLOR_GT, markersize=15, label='Ground Truth', zorder=5)
    ax1.plot(det_x1, det_y1, 'o', color=COLOR_ACCURATE, markersize=15, label='Detected (Accurate)', zorder=5)
    
    # Draw distance line
    ax1.plot([gt_x1, det_x1], [gt_y1, det_y1], 'k-', linewidth=2, alpha=0.7)
    
    # Annotate
    ax1.text(gt_x1, gt_y1 - 100, f'd = {distance1:.1f}px < {DISTANCE_THRESHOLD}px\n✓ ACCURATE',
             ha='center', fontsize=12, fontweight='bold', color='green',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    
    ax1.legend(loc='upper left', fontsize=9)
    ax1.invert_yaxis()
    
    # Right plot: Inaccurate tracking (outside threshold)
    gt_x2, gt_y2 = 500, 400
    det_x2, det_y2 = 620, 480
    distance2 = calculate_euclidean_distance(gt_x2, gt_y2, det_x2, det_y2)
    
    ax2.set_xlim(300, 700)
    ax2.set_ylim(200, 600)
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)
    ax2.set_title('ERROR TRACKING\n(Outside Threshold)', fontsize=14, fontweight='bold', color='red')
    ax2.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax2.set_ylabel('Y coordinate (pixels)', fontsize=11)
    
    # Draw threshold circle
    circle2 = Circle((gt_x2, gt_y2), DISTANCE_THRESHOLD, 
                     color=COLOR_THRESHOLD, fill=False, linewidth=3,
                     linestyle='--', label=f'Threshold Radius ({DISTANCE_THRESHOLD}px)')
    ax2.add_patch(circle2)
    
    # Fill acceptable zone
    circle2_fill = Circle((gt_x2, gt_y2), DISTANCE_THRESHOLD, 
                          color=COLOR_GT, alpha=0.1)
    ax2.add_patch(circle2_fill)
    
    # Draw actual distance circle
    circle2_dist = Circle((gt_x2, gt_y2), distance2,
                          color=COLOR_ERROR, fill=False, linewidth=2,
                          linestyle=':', alpha=0.5)
    ax2.add_patch(circle2_dist)
    
    # Draw points
    ax2.plot(gt_x2, gt_y2, 'o', color=COLOR_GT, markersize=15, label='Ground Truth', zorder=5)
    ax2.plot(det_x2, det_y2, 'o', color=COLOR_ERROR, markersize=15, label='Detected (Error)', zorder=5)
    
    # Draw distance line
    ax2.plot([gt_x2, det_x2], [gt_y2, det_y2], 'r-', linewidth=2, alpha=0.7)
    
    # Annotate
    ax2.text(gt_x2, gt_y2 - 100, f'd = {distance2:.1f}px > {DISTANCE_THRESHOLD}px\n✗ ERROR',
             ha='center', fontsize=12, fontweight='bold', color='red',
             bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))
    
    ax2.legend(loc='upper left', fontsize=9)
    ax2.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '2_threshold_concept.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 2_threshold_concept.png")


def visualize_multiple_scenarios():
    """Visualize multiple tracking scenarios."""
    print("Generating: Multiple Tracking Scenarios...")
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    scenarios = [
        {'name': 'Perfect Tracking', 'gt': (500, 400), 'det': (500, 400), 'color': 'green'},
        {'name': 'Excellent (20px)', 'gt': (500, 400), 'det': (515, 412), 'color': 'green'},
        {'name': 'Good (45px)', 'gt': (500, 400), 'det': (535, 430), 'color': 'green'},
        {'name': 'Acceptable (70px)', 'gt': (500, 400), 'det': (555, 445), 'color': 'orange'},
        {'name': 'Poor (95px)', 'gt': (500, 400), 'det': (580, 460), 'color': 'red'},
        {'name': 'Failed (150px)', 'gt': (500, 400), 'det': (620, 500), 'color': 'darkred'},
    ]
    
    for idx, (ax, scenario) in enumerate(zip(axes, scenarios)):
        gt_x, gt_y = scenario['gt']
        det_x, det_y = scenario['det']
        distance = calculate_euclidean_distance(gt_x, gt_y, det_x, det_y)
        
        ax.set_xlim(300, 700)
        ax.set_ylim(200, 600)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
        ax.set_title(f"{scenario['name']}\nd = {distance:.1f}px", 
                     fontsize=12, fontweight='bold', color=scenario['color'])
        
        # Draw threshold circle
        circle = Circle((gt_x, gt_y), DISTANCE_THRESHOLD,
                       color=COLOR_THRESHOLD, fill=False, linewidth=2,
                       linestyle='--', alpha=0.5)
        ax.add_patch(circle)
        
        # Fill zone
        zone_color = COLOR_GT if distance <= DISTANCE_THRESHOLD else COLOR_ERROR
        circle_fill = Circle((gt_x, gt_y), DISTANCE_THRESHOLD,
                            color=zone_color, alpha=0.1)
        ax.add_patch(circle_fill)
        
        # Draw points
        ax.plot(gt_x, gt_y, 'o', color=COLOR_GT, markersize=12, zorder=5)
        det_color = COLOR_ACCURATE if distance <= DISTANCE_THRESHOLD else COLOR_ERROR
        ax.plot(det_x, det_y, 'o', color=det_color, markersize=12, zorder=5)
        
        # Draw line
        line_color = 'green' if distance <= DISTANCE_THRESHOLD else 'red'
        ax.plot([gt_x, det_x], [gt_y, det_y], color=line_color, 
               linewidth=2, alpha=0.7)
        
        # Status text
        status = '✓ Within Threshold' if distance <= DISTANCE_THRESHOLD else '✗ Outside Threshold'
        status_color = 'lightgreen' if distance <= DISTANCE_THRESHOLD else 'lightcoral'
        ax.text(0.5, 0.05, status, transform=ax.transAxes,
               ha='center', fontsize=10, fontweight='bold',
               bbox=dict(boxstyle='round', facecolor=status_color, alpha=0.8))
        
        ax.invert_yaxis()
        ax.set_xticks([])
        ax.set_yticks([])
    
    plt.suptitle('Tracking Quality by Euclidean Distance', 
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '3_multiple_scenarios.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 3_multiple_scenarios.png")


def visualize_metrics_calculation():
    """Visualize how metrics are calculated from distances."""
    print("Generating: Metrics Calculation Visualization...")
    
    # Generate sample data
    np.random.seed(42)
    n_frames = 100
    gt_x = 500 + np.sin(np.linspace(0, 4*np.pi, n_frames)) * 200
    gt_y = 400 + np.cos(np.linspace(0, 4*np.pi, n_frames)) * 150
    
    # Simulate detection with some error
    det_x = gt_x + np.random.normal(0, 30, n_frames)
    det_y = gt_y + np.random.normal(0, 30, n_frames)
    
    # Calculate distances
    distances = np.array([calculate_euclidean_distance(gx, gy, dx, dy) 
                         for gx, gy, dx, dy in zip(gt_x, gt_y, det_x, det_y)])
    
    # Classify frames
    within_radius = distances <= DISTANCE_THRESHOLD
    outside_radius = ~within_radius
    
    # Calculate metrics
    accuracy = (within_radius.sum() / len(distances)) * 100
    mean_error = distances[outside_radius].mean() if outside_radius.any() else 0
    std_error = distances[outside_radius].std() if outside_radius.any() else 0
    max_error = distances[outside_radius].max() if outside_radius.any() else 0
    
    # Calculate MSE/RMSE
    if outside_radius.any():
        mse = (distances[outside_radius] ** 2).mean()
        rmse = np.sqrt(mse)
    else:
        mse = rmse = 0
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Distance timeline
    ax1 = axes[0, 0]
    colors = ['green' if w else 'red' for w in within_radius]
    ax1.scatter(range(n_frames), distances, c=colors, s=30, alpha=0.6)
    ax1.axhline(y=DISTANCE_THRESHOLD, color='blue', linestyle='--', linewidth=2,
               label=f'Threshold ({DISTANCE_THRESHOLD}px)')
    ax1.set_xlabel('Frame Number', fontsize=11)
    ax1.set_ylabel('Euclidean Distance (pixels)', fontsize=11)
    ax1.set_title('Distance Timeline', fontsize=13, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add metrics text
    metrics_text = (
        f"Accuracy: {accuracy:.1f}%\n"
        f"Frames within: {within_radius.sum()}\n"
        f"Frames outside: {outside_radius.sum()}"
    )
    ax1.text(0.02, 0.98, metrics_text, transform=ax1.transAxes,
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Plot 2: Trajectory comparison
    ax2 = axes[0, 1]
    ax2.plot(gt_x, gt_y, 'g-', linewidth=2, alpha=0.7, label='Ground Truth')
    ax2.plot(det_x, det_y, 'r--', linewidth=1, alpha=0.7, label='Detected')
    ax2.scatter(gt_x[::10], gt_y[::10], c='green', s=50, zorder=5)
    ax2.scatter(det_x[::10], det_y[::10], c='red', s=50, zorder=5)
    ax2.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax2.set_ylabel('Y coordinate (pixels)', fontsize=11)
    ax2.set_title('Trajectory Comparison', fontsize=13, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')
    ax2.invert_yaxis()
    
    # Plot 3: Distance histogram
    ax3 = axes[1, 0]
    ax3.hist(distances[within_radius], bins=20, color='green', alpha=0.6, 
            label=f'Within radius ({within_radius.sum()} frames)', edgecolor='black')
    ax3.hist(distances[outside_radius], bins=20, color='red', alpha=0.6,
            label=f'Outside radius ({outside_radius.sum()} frames)', edgecolor='black')
    ax3.axvline(x=DISTANCE_THRESHOLD, color='blue', linestyle='--', linewidth=2,
               label=f'Threshold ({DISTANCE_THRESHOLD}px)')
    ax3.set_xlabel('Euclidean Distance (pixels)', fontsize=11)
    ax3.set_ylabel('Frequency', fontsize=11)
    ax3.set_title('Distance Distribution', fontsize=13, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Metrics summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    summary_text = (
        "EVALUATION METRICS\n"
        "=" * 50 + "\n\n"
        f"Total Frames: {n_frames}\n\n"
        
        "CLASSIFICATION:\n"
        f"  • Frames within radius (≤{DISTANCE_THRESHOLD}px): {within_radius.sum()} ({accuracy:.1f}%)\n"
        f"  • Frames outside radius (>{DISTANCE_THRESHOLD}px): {outside_radius.sum()} ({100-accuracy:.1f}%)\n\n"
        
        "ERROR METRICS (from frames outside radius):\n"
        f"  • Mean Distance: {mean_error:.2f} px\n"
        f"  • Std Distance: {std_error:.2f} px\n"
        f"  • Max Distance: {max_error:.2f} px\n"
        f"  • MSE: {mse:.2f} px²\n"
        f"  • RMSE: {rmse:.2f} px\n\n"
        
        "KEY INSIGHT:\n"
        "Distance metrics are calculated ONLY from\n"
        "error frames (outside threshold) to avoid\n"
        "inflating values with acceptable tracking."
    )
    
    ax4.text(0.1, 0.95, summary_text, transform=ax4.transAxes,
            fontsize=11, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    plt.suptitle('Metrics Calculation from Euclidean Distance', 
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '4_metrics_calculation.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 4_metrics_calculation.png")


def create_summary_infographic():
    """Create a summary infographic of the Euclidean distance concept."""
    print("Generating: Summary Infographic...")
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Title
    fig.suptitle('Euclidean Distance in Gaze Tracking: Complete Guide', 
                fontsize=18, fontweight='bold', y=0.98)
    
    # Section 1: Formula (top left)
    ax1 = fig.add_subplot(gs[0, :])
    ax1.axis('off')
    formula_text = (
        "EUCLIDEAN DISTANCE FORMULA\n\n"
        "d = √[(x_detected - x_GT)² + (y_detected - y_GT)²]\n\n"
        "Where:\n"
        "  • (x_GT, y_GT) = Ground truth gaze position (from stimulus)\n"
        "  • (x_detected, y_detected) = Algorithm's detected position\n"
        "  • d = Distance in pixels between the two points"
    )
    ax1.text(0.5, 0.5, formula_text, transform=ax1.transAxes,
            fontsize=13, ha='center', va='center', fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=1', facecolor='#E8F4F8', edgecolor='black', linewidth=2))
    
    # Section 2: Visual example (middle left)
    ax2 = fig.add_subplot(gs[1, 0])
    gt_x, gt_y = 100, 100
    det_x, det_y = 180, 150
    dist = calculate_euclidean_distance(gt_x, gt_y, det_x, det_y)
    
    ax2.set_xlim(0, 250)
    ax2.set_ylim(0, 250)
    ax2.set_aspect('equal')
    ax2.set_title('Visual Example', fontsize=12, fontweight='bold')
    circle_ax2 = Circle((gt_x, gt_y), DISTANCE_THRESHOLD, 
                        color=COLOR_THRESHOLD, fill=False, linewidth=2, linestyle='--')
    ax2.add_patch(circle_ax2)
    ax2.plot(gt_x, gt_y, 'o', color=COLOR_GT, markersize=15, label='GT')
    ax2.plot(det_x, det_y, 'o', color=COLOR_ERROR, markersize=15, label='Detected')
    ax2.plot([gt_x, det_x], [gt_y, det_y], 'k-', linewidth=2)
    ax2.text(140, 125, f'{dist:.1f}px', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='yellow'))
    ax2.legend(loc='upper right')
    ax2.invert_yaxis()
    ax2.grid(True, alpha=0.3)
    
    # Section 3: Threshold concept (middle center)
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.axis('off')
    ax3.set_title('Threshold Classification', fontsize=12, fontweight='bold')
    threshold_text = (
        f"Threshold: {DISTANCE_THRESHOLD} pixels\n"
        "(Radius of gaze stimulus)\n\n"
        f"• d ≤ {DISTANCE_THRESHOLD}px → ✓ Accurate\n"
        "  (Within target area)\n\n"
        f"• d > {DISTANCE_THRESHOLD}px → ✗ Error\n"
        "  (Outside target area)\n\n"
        "Accuracy = % of frames\n"
        "within threshold"
    )
    ax3.text(0.5, 0.5, threshold_text, transform=ax3.transAxes,
            fontsize=11, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF4E6'))
    
    # Section 4: Metrics (middle right)
    ax4 = fig.add_subplot(gs[1, 2])
    ax4.axis('off')
    ax4.set_title('Calculated Metrics', fontsize=12, fontweight='bold')
    metrics_text = (
        "From frames OUTSIDE radius:\n\n"
        "• Mean Distance\n"
        "  Average error magnitude\n\n"
        "• Std Distance\n"
        "  Error consistency\n\n"
        "• MSE/RMSE\n"
        "  Squared error penalty\n\n"
        "From ALL frames:\n\n"
        "• Accuracy %\n"
        "  % within threshold"
    )
    ax4.text(0.5, 0.5, metrics_text, transform=ax4.transAxes,
            fontsize=11, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#E8F5E9'))
    
    # Section 5: Example scenarios (bottom)
    scenarios_data = [
        (20, 'Excellent', 'green'),
        (50, 'Good', 'green'),
        (75, 'Threshold', 'orange'),
        (100, 'Poor', 'red')
    ]
    
    for idx, (distance, label, color) in enumerate(scenarios_data):
        ax = fig.add_subplot(gs[2, idx])
        ax.set_xlim(0, 200)
        ax.set_ylim(0, 200)
        ax.set_aspect('equal')
        ax.set_title(f'{label}\n({distance}px)', fontsize=10, fontweight='bold', color=color)
        ax.set_xticks([])
        ax.set_yticks([])
        
        gx, gy = 100, 100
        dx, dy = gx + distance * 0.7, gy + distance * 0.7
        
        circle = Circle((gx, gy), DISTANCE_THRESHOLD, 
                       color=COLOR_THRESHOLD, fill=False, linewidth=2, linestyle='--')
        ax.add_patch(circle)
        
        fill_color = COLOR_GT if distance <= DISTANCE_THRESHOLD else COLOR_ERROR
        circle_fill = Circle((gx, gy), DISTANCE_THRESHOLD, color=fill_color, alpha=0.1)
        ax.add_patch(circle_fill)
        
        ax.plot(gx, gy, 'o', color=COLOR_GT, markersize=12)
        det_color = COLOR_ACCURATE if distance <= DISTANCE_THRESHOLD else COLOR_ERROR
        ax.plot(dx, dy, 'o', color=det_color, markersize=12)
        ax.plot([gx, dx], [gy, dy], 'k-', linewidth=2)
        
        ax.invert_yaxis()
    
    plt.savefig(os.path.join(OUTPUT_DIR, '5_summary_infographic.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: 5_summary_infographic.png")


def main():
    """Generate all visualizations."""
    print("\n" + "="*80)
    print("EUCLIDEAN DISTANCE VISUALIZATION GENERATOR")
    print("="*80)
    print(f"\nOutput directory: {OUTPUT_DIR}\n")
    
    # Generate all visualizations
    visualize_basic_concept()
    visualize_threshold_concept()
    visualize_multiple_scenarios()
    visualize_metrics_calculation()
    create_summary_infographic()
    
    print("\n" + "="*80)
    print("ALL VISUALIZATIONS COMPLETED!")
    print("="*80)
    print(f"\nGenerated {5} visualization files in:")
    print(f"  {OUTPUT_DIR}\n")
    print("Files:")
    print("  1. 1_basic_concept.png - Basic Euclidean distance formula")
    print("  2. 2_threshold_concept.png - Accurate vs Error tracking")
    print("  3. 3_multiple_scenarios.png - Various tracking quality examples")
    print("  4. 4_metrics_calculation.png - How metrics are computed")
    print("  5. 5_summary_infographic.png - Complete visual summary")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
