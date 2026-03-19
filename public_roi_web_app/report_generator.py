import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from datetime import datetime
import numpy as np

# PDF generation
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ReportGenerator:
    """Generate PDF and Excel reports for gaze analysis."""
    
    def __init__(self, session_dir, gaze_data, video_info, scenes, participant_name="Participant", tracking_mode="Eye Tracking"):
        """
        Initialize report generator.
        
        Args:
            session_dir: Output directory
            gaze_data: List of gaze data entries
            video_info: Ad video metadata
            scenes: Scene definitions
            participant_name: Name of participant
            tracking_mode: "Eye Tracking" or "Mouse Tracking"
        """
        self.session_dir = session_dir
        self.gaze_data = gaze_data
        self.video_info = video_info
        self.scenes = scenes
        self.participant_name = participant_name
        self.tracking_mode = tracking_mode
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    def generate_excel_report(self):
        """
        Generate comprehensive Excel report with multiple sheets.
        Returns path to Excel file.
        """
        excel_path = os.path.join(self.session_dir, f'report_{self.participant_name}.xlsx')
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Sheet 1: Overview
            overview_data = self._generate_overview_data()
            pd.DataFrame(overview_data).to_excel(writer, sheet_name='Overview', index=False)
            
            # Sheet 2: ROI Statistics per Scene
            roi_stats = self._generate_roi_statistics()
            pd.DataFrame(roi_stats).to_excel(writer, sheet_name='ROI Statistics', index=False)
            
            # Sheet 3: Raw Gaze Data
            df_gaze = pd.DataFrame(self.gaze_data)
            df_gaze.to_excel(writer, sheet_name='Raw Gaze Data', index=False)
            
            # Sheet 4: Scene Summary
            scene_summary = self._generate_scene_summary()
            pd.DataFrame(scene_summary).to_excel(writer, sheet_name='Scene Summary', index=False)
        
        print(f"Excel report generated: {excel_path}")
        return excel_path
    
    def generate_pdf_report(self, heatmap_paths=None, trajectory_paths=None):
        """
        Generate executive PDF report with charts, heatmaps, and gaze trajectories.
        Returns path to PDF file.
        """
        if not REPORTLAB_AVAILABLE:
            print("Warning: reportlab not installed. Skipping PDF generation.")
            return None
        
        pdf_path = os.path.join(self.session_dir, f'report_{self.participant_name}.pdf')
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("Eye Tracking Analysis Report", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Metadata
        meta_style = styles['Normal']
        story.append(Paragraph(f"<b>Participant:</b> {self.participant_name}", meta_style))
        story.append(Paragraph(f"<b>Date:</b> {self.timestamp}", meta_style))
        story.append(Paragraph(f"<b>Tracking Mode:</b> {self.tracking_mode}", meta_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Video Properties
        story.append(Paragraph("<b>Video Properties:</b>", meta_style))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;File: {self.video_info['filename']}", meta_style))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;Resolution: {self.video_info.get('width', 'N/A')} x {self.video_info.get('height', 'N/A')}", meta_style))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;FPS: {self.video_info.get('fps', 'N/A'):.2f}", meta_style))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;Duration: {self.video_info.get('duration', 0):.2f}s ({int(self.video_info.get('duration', 0) // 60)}:{int(self.video_info.get('duration', 0) % 60):02d})", meta_style))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;Total Frames: {self.video_info.get('total_frames', 'N/A')}", meta_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_data = self._generate_overview_data()
        for item in summary_data:
            story.append(Paragraph(f"<b>{item['Metric']}:</b> {item['Value']}", meta_style))
        story.append(Spacer(1, 0.3*inch))
        
        # ROI Statistics Table
        story.append(Paragraph("ROI Performance by Scene", styles['Heading2']))
        roi_stats = self._generate_roi_statistics()
        if roi_stats:
            table_data = [['Scene', 'ROI', 'Gaze Count', 'Percentage']]
            for stat in roi_stats:
                table_data.append([
                    stat['scene'],
                    stat['roi_label'],
                    str(stat['gaze_count']),
                    f"{stat['percentage']:.1f}%"
                ])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
        story.append(PageBreak())
        
        # Add heatmaps for each scene
        if heatmap_paths:
            story.append(Paragraph("Attention Heatmaps", styles['Heading2']))
            story.append(Spacer(1, 0.2*inch))
            for heatmap in heatmap_paths:
                # Use display_name if available, otherwise scene_name
                display_name = heatmap.get('display_name') or heatmap.get('scene_name')
                story.append(Paragraph(f"{display_name}", styles['Heading3']))
                if os.path.exists(heatmap['path']):
                    img = Image(heatmap['path'], width=5*inch, height=3*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
            story.append(PageBreak())
        
        # Add gaze trajectories for each scene
        if trajectory_paths:
            story.append(Paragraph("Gaze Trajectories & Fixations", styles['Heading2']))
            story.append(Paragraph(
                "Cyan lines show saccadic eye movements. Red circles show fixation points "
                "(larger circles = longer fixation duration). Numbers indicate viewing sequence.",
                styles['Normal']
            ))
            story.append(Spacer(1, 0.2*inch))
            for trajectory in trajectory_paths:
                display_name = trajectory.get('display_name') or trajectory.get('scene_name')
                story.append(Paragraph(f"{display_name}", styles['Heading3']))
                
                # Add trajectory stats
                fix_count = trajectory.get('fixation_count', 0)
                gaze_points = trajectory.get('total_gaze_points', 0)
                story.append(Paragraph(
                    f"<i>Fixations: {fix_count} | Total Gaze Points: {gaze_points}</i>",
                    styles['Normal']
                ))
                
                if os.path.exists(trajectory['path']):
                    img = Image(trajectory['path'], width=5*inch, height=3*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
        
        # Build PDF
        doc.build(story)
        print(f"PDF report generated: {pdf_path}")
        return pdf_path
    
    def _generate_overview_data(self):
        """Generate overview statistics."""
        df = pd.DataFrame(self.gaze_data)
        total_frames = len(df)
        detected_frames = df['gaze_x'].notna().sum()
        detection_rate = (detected_frames / total_frames * 100) if total_frames > 0 else 0
        
        return [
            {'Metric': 'Tracking Mode', 'Value': self.tracking_mode},
            {'Metric': 'Video File', 'Value': self.video_info.get('filename', 'N/A')},
            {'Metric': 'Video Resolution', 'Value': f"{self.video_info.get('width', 'N/A')} x {self.video_info.get('height', 'N/A')}"},
            {'Metric': 'Video FPS', 'Value': f"{self.video_info.get('fps', 0):.2f}"},
            {'Metric': 'Video Duration', 'Value': f"{self.video_info.get('duration', 0):.2f}s"},
            {'Metric': 'Video Total Frames', 'Value': self.video_info.get('total_frames', 'N/A')},
            {'Metric': 'Recorded Frames', 'Value': total_frames},
            {'Metric': 'Detected Frames', 'Value': detected_frames},
            {'Metric': 'Detection Rate', 'Value': f"{detection_rate:.1f}%"},
            {'Metric': 'Number of Scenes', 'Value': len(self.scenes)}
        ]
    
    def _generate_roi_statistics(self):
        """Generate ROI statistics per scene."""
        df = pd.DataFrame(self.gaze_data)
        stats = []
        
        for scene in self.scenes:
            scene_frames = df[df['scene_name'] == scene['name']]
            if scene_frames.empty:
                continue
            
            roi_counts = scene_frames['roi_label'].value_counts()
            total = len(scene_frames)
            
            for roi in scene.get('rois', []):
                count = roi_counts.get(roi['label'], 0)
                percentage = (count / total * 100) if total > 0 else 0
                
                # Get display name (custom_name if available, otherwise scene name)
                display_name = scene.get('custom_name') or scene['name']
                
                stats.append({
                    'scene': scene['name'],
                    'custom_name': scene.get('custom_name', ''),
                    'display_name': display_name,
                    'roi_label': roi['label'],
                    'gaze_count': int(count),
                    'percentage': round(percentage, 2),
                    'total_frames': int(total)
                })
        
        return stats
    
    def _generate_scene_summary(self):
        """Generate scene-level summary."""
        df = pd.DataFrame(self.gaze_data)
        summary = []
        
        for scene in self.scenes:
            scene_frames = df[df['scene_name'] == scene['name']]
            if scene_frames.empty:
                continue
            
            detected = scene_frames['gaze_x'].notna().sum()
            total = len(scene_frames)
            detection_rate = (detected / total * 100) if total > 0 else 0
            
            # Get display name (custom_name if available, otherwise scene name)
            display_name = scene.get('custom_name') or scene['name']
            
            summary.append({
                'Scene': scene['name'],
                'Custom Name': scene.get('custom_name', ''),
                'Display Name': display_name,
                'Start Frame': scene['start_frame'],
                'End Frame': scene['end_frame'],
                'Total Frames': total,
                'Detected Frames': detected,
                'Detection Rate (%)': round(detection_rate, 2)
            })
        
        return summary
