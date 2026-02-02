"""
Export Manager for WD Word Counter
Supports multiple export formats
"""

import json
import csv
import html
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from jinja2 import Template

class ExportManager:
    def __init__(self, parent_window):
        self.parent = parent_window
    
    def export_stats(self, stats_data, text):
        """Export statistics in multiple formats"""
        formats = {
            "JSON (*.json)": self.export_json,
            "CSV (*.csv)": self.export_csv,
            "Text (*.txt)": self.export_txt,
            "HTML (*.html)": self.export_html,
            "Markdown (*.md)": self.export_markdown,
        }
        
        # Get save location
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self.parent,
            "Export Statistics",
            f"word_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            ";;".join(formats.keys())
        )
        
        if not file_path:
            return False
        
        # Add extension if not present
        if not Path(file_path).suffix:
            for fmt, func in formats.items():
                if fmt in selected_filter:
                    ext = fmt.split('(')[1].split(')')[0]
                    file_path += ext
                    break
        
        # Export based on format
        for fmt, func in formats.items():
            if fmt in selected_filter:
                try:
                    func(file_path, stats_data, text)
                    QMessageBox.information(
                        self.parent, 
                        "Export Successful",
                        f"Statistics exported to:\n{file_path}"
                    )
                    return True
                except Exception as e:
                    QMessageBox.critical(
                        self.parent,
                        "Export Failed",
                        f"Error exporting file:\n{str(e)}"
                    )
                    return False
        
        return False
    
    def export_json(self, file_path, stats_data, text):
        """Export to JSON format"""
        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "tool": "WD Word Counter",
                "version": "2.0"
            },
            "statistics": stats_data,
            "text_preview": text[:1000] + "..." if len(text) > 1000 else text,
            "full_text_length": len(text)
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def export_csv(self, file_path, stats_data, text):
        """Export to CSV format"""
        # Flatten stats for CSV
        rows = []
        for category, value in stats_data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    rows.append([category, sub_key, sub_value])
            else:
                rows.append([category, "", value])
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Metric", "Value"])
            writer.writerows(rows)
    
    def export_txt(self, file_path, stats_data, text):
        """Export to plain text format"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("WD WORD COUNTER - STATISTICS EXPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Text Length: {len(text)} characters\n\n")
            
            f.write("STATISTICS:\n")
            f.write("-" * 40 + "\n")
            
            for key, value in stats_data.items():
                if isinstance(value, dict):
                    f.write(f"\n{key}:\n")
                    for sub_key, sub_value in value.items():
                        f.write(f"  {sub_key}: {sub_value}\n")
                else:
                    f.write(f"{key}: {value}\n")
    
    def export_html(self, file_path, stats_data, text):
        """Export to HTML format with styling"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>WD Word Counter - Statistics</title>
            <style>
                body { 
                    font-family: 'Consolas', monospace; 
                    background: #0a0a0a; 
                    color: #00ff00; 
                    margin: 40px; 
                }
                .container { 
                    max-width: 800px; 
                    margin: 0 auto; 
                    border: 1px solid #333; 
                    padding: 20px; 
                    background: #111; 
                }
                h1 { 
                    color: #00ff00; 
                    border-bottom: 2px solid #333; 
                    padding-bottom: 10px; 
                }
                .stat { 
                    margin: 15px 0; 
                    padding: 10px; 
                    background: #1a1a1a; 
                    border-left: 3px solid #00aa00; 
                }
                .highlight { 
                    color: #00ffff; 
                    font-weight: bold; 
                }
                .preview { 
                    background: #000; 
                    padding: 15px; 
                    border: 1px solid #333; 
                    margin: 20px 0; 
                    white-space: pre-wrap; 
                    font-size: 12px; 
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 WD Word Counter - Analysis Report</h1>
                <p>Generated: {{ export_date }}</p>
                
                <h2>📈 Key Statistics</h2>
                {% for category, value in stats.items() %}
                <div class="stat">
                    <strong>{{ category }}:</strong> 
                    {% if value is mapping %}
                        <ul>
                        {% for k, v in value.items() %}
                            <li>{{ k }}: <span class="highlight">{{ v }}</span></li>
                        {% endfor %}
                        </ul>
                    {% else %}
                        <span class="highlight">{{ value }}</span>
                    {% endif %}
                </div>
                {% endfor %}
                
                <h2>📝 Text Preview</h2>
                <div class="preview">{{ text_preview }}</div>
                
                <p><em>Report generated by WD Word Counter v2.0</em></p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            export_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            stats=stats_data,
            text_preview=html.escape(text[:500] + "..." if len(text) > 500 else text)
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def export_markdown(self, file_path, stats_data, text):
        """Export to Markdown format"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# WD Word Counter - Analysis Report\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            f.write("## 📈 Key Statistics\n\n")
            
            for category, value in stats_data.items():
                if isinstance(value, dict):
                    f.write(f"### {category}\n\n")
                    for sub_key, sub_value in value.items():
                        f.write(f"- **{sub_key}**: `{sub_value}`\n")
                    f.write("\n")
                else:
                    f.write(f"- **{category}**: `{value}`\n")
            
            f.write("\n## 📝 Text Preview\n\n")
            f.write("```\n")
            f.write(text[:500] + "..." if len(text) > 500 else text)
            f.write("\n```\n\n")
            f.write("*--- Report generated by WD Word Counter v2.0 ---*")