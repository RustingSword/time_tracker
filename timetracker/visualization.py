"""Visualization module for the time tracker application."""

import os
import contextlib
from datetime import date
from typing import List, Dict, Tuple

# Suppress IMK messages
with contextlib.redirect_stderr(open(os.devnull, 'w')):
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')

import numpy as np
import pandas as pd

from .config import VisualizationConfig
from .models import ActivitySummary


class ActivityVisualizer:
    """Handles visualization of activity data."""
    
    def __init__(self, config: VisualizationConfig = VisualizationConfig()):
        """Initialize the visualizer with configuration."""
        self.config = config
        plt.style.use(config.style)

    def create_visualizations(self, summaries: List[ActivitySummary], 
                            target_date: date,
                            plot_type: str = 'both') -> None:
        """Create requested visualizations."""
        if not summaries:
            return

        # Prepare data
        data = pd.DataFrame([
            {
                'category': s.category,
                'minutes': s.minutes,
                'percentage': s.percentage
            }
            for s in summaries
        ])
        
        # Generate color palette
        colors = plt.cm.Set3(np.linspace(0, 1, len(data)))

        # Create requested plots
        if plot_type in ['bar', 'both']:
            self._create_bar_chart(data, colors, target_date)
        if plot_type in ['pie', 'both']:
            self._create_pie_chart(data, colors, target_date)

    def _create_bar_chart(self, data: pd.DataFrame, colors: np.ndarray, 
                         target_date: date) -> None:
        """Create a horizontal bar chart of time distribution."""
        plt.figure(figsize=self.config.figure_size_bar)
        
        # Sort data by duration
        data = data.sort_values('minutes')
        
        # Create bars
        ax = plt.gca()
        bars = ax.barh(range(len(data)), data['minutes'], color=colors)
        
        # Configure axes
        ax.set_yticks(range(len(data)))
        ax.set_yticklabels(data['category'])
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                   f' {width:.1f}m', va='center')
        
        # Style the plot
        plt.title(f"Time Spent per Category - {target_date}", pad=20)
        plt.xlabel("Time (minutes)")
        plt.ylabel("Category")
        plt.grid(axis="x", alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        # Save and cleanup
        plt.savefig('activity_bar.png', bbox_inches='tight', dpi=self.config.dpi)
        plt.close()

    def _create_pie_chart(self, data: pd.DataFrame, colors: np.ndarray, 
                         target_date: date) -> None:
        """Create a pie chart of time distribution."""
        plt.figure(figsize=self.config.figure_size_pie)
        
        # Process data for pie chart
        processed_data = self._process_pie_data(data)
        
        # Create pie chart
        patches, texts, autotexts = plt.pie(
            processed_data['values'],
            explode=processed_data['explode'],
            labels=processed_data['labels'],
            autopct=self._make_autopct(processed_data['values']),
            startangle=90,
            colors=processed_data['colors'],
            shadow=True,
            labeldistance=1.1,
            pctdistance=0.75,
        )
        
        # Style labels
        plt.setp(autotexts, size=8, weight="bold")
        plt.setp(texts, size=9)
        
        # Add legend
        self._add_pie_legend(patches, processed_data)
        
        # Final styling
        plt.title(f"Time Distribution by Category - {target_date}", pad=20)
        plt.axis('equal')
        plt.tight_layout()
        
        # Save and cleanup
        plt.savefig('activity_pie.png', bbox_inches='tight', dpi=self.config.dpi)
        plt.close()

    def _process_pie_data(self, data: pd.DataFrame) -> Dict:
        """Process data for pie chart visualization."""
        values = []
        labels = []
        colors_filtered = []
        explode = []
        other_sum = 0
        other_activities = []
        main_categories = []
        
        total = data['minutes'].sum()
        
        for i, row in data.iterrows():
            pct = (row['minutes'] / total) * 100
            if pct < self.config.small_segment_threshold:
                other_sum += row['minutes']
                other_activities.append(f"{row['category']} ({row['minutes']:.1f}m)")
            else:
                values.append(row['minutes'])
                labels.append(row['category'])
                colors_filtered.append(plt.cm.Set3(i / len(data)))
                explode.append(0.1 if pct < 10 else 0)
                main_categories.append(f"{row['category']} ({row['minutes']:.1f}m)")
        
        # Add "Other" category if needed
        if other_sum > 0:
            values.append(other_sum)
            labels.append("Other")
            colors_filtered.append(plt.cm.Greys(0.5))
            explode.append(0.1)
            main_categories.append(f"Other ({other_sum:.1f}m)")
            
        return {
            'values': values,
            'labels': labels,
            'colors': colors_filtered,
            'explode': explode,
            'main_categories': main_categories,
            'other_activities': other_activities
        }

    def _make_autopct(self, values: List[float]):
        """Create function for percentage labels."""
        def autopct(pct):
            total = sum(values)
            val = pct * total / 100.0
            return f'{pct:.1f}%\n({val:.1f}m)'
        return autopct

    def _add_pie_legend(self, patches: List, data: Dict) -> None:
        """Add legend to pie chart."""
        legend_labels = data['main_categories'].copy()
        if data['other_activities']:
            legend_labels.append("Small categories:")
            legend_labels.extend([f"  • {act}" for act in data['other_activities']])
        
        plt.legend(
            patches,
            legend_labels,
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=8
        )
