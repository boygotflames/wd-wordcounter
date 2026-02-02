"""
WD - Minimalist Word Counter UI
Black terminal aesthetic design
"""

import sys
import json
import time
import warnings
from datetime import datetime
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# ADD THESE IMPORTS
import re
import numpy as np
from collections import Counter
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import textstat  # pip install textstat
from src.export_manager import ExportManager
from src.theme_manager import ThemeManager

# Import Rust backend
try:
    import wdlib
    HAS_RUST = True
except ImportError:
    HAS_RUST = False
    print("Rust backend not found, using Python fallback")

class WDMainWindow(QMainWindow):
    """Main application window with black aesthetic"""
    
    def __init__(self):
        super().__init__()
        self.stats_history = []
        self.last_update_time = 0
        self.update_interval = 500  # ms
        self.theme_manager = ThemeManager()
        self.current_theme = "terminal_black"
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("WD - Word Counter")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Left panel - Input area
        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")
        self.left_layout = QVBoxLayout(left_panel)
        
        # Input label
        input_label = QLabel("📝 PASTE YOUR TEXT")
        input_label.setObjectName("sectionLabel")
        
        # Text input area
        self.text_input = QPlainTextEdit()
        self.text_input.setObjectName("textInput")
        self.text_input.setPlaceholderText(
            "Paste your text here...\n"
            "Word counting happens in real-time.\n"
            "Press Ctrl+V to paste, Ctrl+A to select all."
        )
        
        # Input buttons
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setObjectName("dangerBtn")
        self.clear_btn.clicked.connect(self.clear_text)
        
        self.paste_btn = QPushButton("📋 Paste")
        self.paste_btn.setObjectName("primaryBtn")
        self.paste_btn.clicked.connect(self.paste_from_clipboard)
        
        self.export_btn = QPushButton("💾 Export Stats")
        self.export_btn.setObjectName("secondaryBtn")
        self.export_btn.clicked.connect(self.export_stats)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.paste_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        
        # Add to left layout
        self.left_layout.addWidget(input_label)
        self.left_layout.addWidget(self.text_input)
        self.left_layout.addLayout(button_layout)
        
        # ADD TO init_ui METHOD (after creating buttons)
        self.create_theme_selector()
        
        # Right panel - Stats area
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_panel)
        
        # Stats label
        stats_label = QLabel("📊 LIVE STATISTICS")
        stats_label.setObjectName("sectionLabel")
        
        # Stats display area
        stats_scroll = QScrollArea()
        stats_scroll.setWidgetResizable(True)
        stats_scroll.setObjectName("statsScroll")
        
        stats_container = QWidget()
        self.stats_layout = QVBoxLayout(stats_container)
        self.stats_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Initialize stat widgets
        self.stat_widgets = {}
        self.create_stat_widget("Words", "wordCount", "0")
        self.create_stat_widget("Characters", "charCount", "0")
        self.create_stat_widget("Characters (no spaces)", "charNoSpaceCount", "0")
        self.create_stat_widget("Sentences", "sentenceCount", "0")
        self.create_stat_widget("Paragraphs", "paragraphCount", "0")
        self.create_stat_widget("Unique Words", "uniqueWordCount", "0")
        self.create_stat_widget("Avg Word Length", "avgWordLength", "0.0")
        self.create_stat_widget("Reading Time", "readingTime", "0s")
        
        # Add spacing
        self.stats_layout.addSpacing(20)
        
        # ADD READABILITY SCORES SECTION
        self.create_readability_section()
        
        # Top words section
        top_words_label = QLabel("🏆 TOP WORDS")
        top_words_label.setObjectName("subsectionLabel")
        self.stats_layout.addWidget(top_words_label)
        
        self.top_words_text = QLabel("No data")
        self.top_words_text.setObjectName("monospaceText")
        self.stats_layout.addWidget(self.top_words_text)
        
        # Longest words section
        longest_words_label = QLabel("📏 LONGEST WORDS")
        longest_words_label.setObjectName("subsectionLabel")
        self.stats_layout.addWidget(longest_words_label)
        
        self.longest_words_text = QLabel("No data")
        self.longest_words_text.setObjectName("monospaceText")
        self.stats_layout.addWidget(self.longest_words_text)
        
        # AFTER CREATING STATS LAYOUT, ADD HEATMAP SECTION
        self.create_heatmap_section()
        
        # ADD AFTER OTHER SECTIONS:
        self.create_keyword_analysis_section()
        
        # Add stretch at bottom
        self.stats_layout.addStretch()
        
        # Set scroll area widget
        stats_scroll.setWidget(stats_container)
        
        # Add to right layout
        right_layout.addWidget(stats_label)
        right_layout.addWidget(stats_scroll)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 3)
        main_layout.addWidget(right_panel, 1)
        
        # Connect signals
        self.text_input.textChanged.connect(self.on_text_changed)
        
        # Timer for debounced updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_stats)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Backend indicator
        backend_text = "⚡ Rust Backend" if HAS_RUST else "🐍 Python Backend"
        self.backend_label = QLabel(backend_text)
        self.status_bar.addPermanentWidget(self.backend_label)
        
        # Set focus to input
        self.text_input.setFocus()
        
    def create_stat_widget(self, label: str, key: str, initial_value: str):
        """Create a statistic display widget"""
        stat_frame = QFrame()
        stat_frame.setObjectName("statFrame")
        stat_layout = QVBoxLayout(stat_frame)
        stat_layout.setContentsMargins(10, 5, 10, 5)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setObjectName("statLabel")
        
        # Value
        value_widget = QLabel(initial_value)
        value_widget.setObjectName("statValue")
        value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        stat_layout.addWidget(label_widget)
        stat_layout.addWidget(value_widget)
        
        self.stats_layout.addWidget(stat_frame)
        self.stat_widgets[key] = value_widget
        
    def setup_styles(self):
        """Set up the black terminal aesthetic"""
        style_sheet = """
        /* Main window */
        QMainWindow {
            background-color: #0a0a0a;
        }
        
        /* Panels */
        #leftPanel, #rightPanel {
            background-color: #111111;
            border: 1px solid #333333;
            border-radius: 8px;
            padding: 10px;
        }
        
        /* Section labels */
        #sectionLabel {
            color: #00ff00;
            font-family: 'Consolas', monospace;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        #subsectionLabel {
            color: #00ffff;
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 5px;
        }
        
        /* Text input */
        #textInput {
            background-color: #000000;
            color: #00ff00;
            font-family: 'Consolas', monospace;
            font-size: 12px;
            border: 1px solid #333333;
            border-radius: 4px;
            padding: 10px;
            selection-background-color: #003300;
        }
        
        #textInput::placeholder {
            color: #555555;
            font-style: italic;
        }
        
        /* Buttons */
        QPushButton {
            font-family: 'Consolas', monospace;
            font-size: 11px;
            font-weight: bold;
            padding: 8px 15px;
            border: none;
            border-radius: 4px;
            min-width: 80px;
        }
        
        #primaryBtn {
            background-color: #006600;
            color: #ffffff;
        }
        
        #primaryBtn:hover {
            background-color: #008800;
        }
        
        #secondaryBtn {
            background-color: #003366;
            color: #ffffff;
        }
        
        #secondaryBtn:hover {
            background-color: #004488;
        }
        
        #dangerBtn {
            background-color: #660000;
            color: #ffffff;
        }
        
        #dangerBtn:hover {
            background-color: #880000;
        }
        
        /* Statistics */
        #statFrame {
            background-color: #1a1a1a;
            border: 1px solid #222222;
            border-radius: 4px;
        }
        
        #statLabel {
            color: #cccccc;
            font-family: 'Consolas', monospace;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        #statValue {
            color: #00ff00;
            font-family: 'Consolas', monospace;
            font-size: 18px;
            font-weight: bold;
        }
        
        /* Monospace text */
        #monospaceText {
            color: #aaaaaa;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            background-color: #000000;
            padding: 5px;
            border-radius: 3px;
        }
        
        /* Scroll area */
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            background-color: #222222;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #444444;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
        
        /* Status bar */
        QStatusBar {
            background-color: #111111;
            color: #00ff00;
            font-family: 'Consolas', monospace;
            font-size: 10px;
            border-top: 1px solid #333333;
        }
        """
        
        self.setStyleSheet(style_sheet)
        
        # Set font
        font = QFont("Consolas", 10)
        self.setFont(font)
        
    def on_text_changed(self):
        """Handle text changes with debouncing"""
        self.update_timer.stop()
        self.update_timer.start(self.update_interval)
        
    def update_stats(self):
        """Update statistics based on current text"""
        text = self.text_input.toPlainText()
        
        if HAS_RUST:
            stats = wdlib.analyze_text_fast(text)
            stats_dict = json.loads(stats.to_json())
        else:
            stats_dict = self.analyze_with_python(text)
        
        # Update basic stats
        self.stat_widgets["wordCount"].setText(f"{stats_dict.get('words', 0):,}")
        self.stat_widgets["charCount"].setText(f"{stats_dict.get('characters', 0):,}")
        self.stat_widgets["charNoSpaceCount"].setText(f"{stats_dict.get('characters_no_spaces', 0):,}")
        self.stat_widgets["sentenceCount"].setText(f"{stats_dict.get('sentences', 0):,}")
        self.stat_widgets["paragraphCount"].setText(f"{stats_dict.get('paragraphs', 0):,}")
        self.stat_widgets["uniqueWordCount"].setText(f"{stats_dict.get('unique_words', 0):,}")
        
        avg_length = stats_dict.get('avg_word_length', 0.0)
        self.stat_widgets["avgWordLength"].setText(f"{avg_length:.2f}")
        
        reading_time = stats_dict.get('reading_time_seconds', 0)
        self.stat_widgets["readingTime"].setText(f"{reading_time}s ({reading_time//60}m)")
        
        # Update top words
        top_words = stats_dict.get('top_words', [])
        if top_words:
            top_text = "\n".join([f"{word}: {count}" for word, count in top_words[:5]])
            self.top_words_text.setText(top_text)
        else:
            self.top_words_text.setText("No data")
            
        # Update longest words
        longest_words = stats_dict.get('longest_words', [])
        if longest_words:
            long_text = "\n".join([f"{word} ({len(word)} chars)" for word in longest_words[:5]])
            self.longest_words_text.setText(long_text)
        else:
            self.longest_words_text.setText("No data")
            
        # Update heatmap
        self.update_heatmap()
        
        # Update readability
        self.update_readability_scores(text)
            
        # Update status
        self.status_bar.showMessage(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        # Store in history
        self.stats_history.append({
            'timestamp': time.time(),
            'stats': stats_dict,
            'text_preview': text[:100] + "..." if len(text) > 100 else text
        })
        
        # Keep only last 100 entries
        if len(self.stats_history) > 100:
            self.stats_history.pop(0)
            
    def analyze_with_python(self, text: str) -> Dict[str, Any]:
        """Fallback Python analyzer if Rust not available"""
        import re
        from collections import Counter
        
        stats = {
            'words': 0,
            'characters': 0,
            'characters_no_spaces': 0,
            'sentences': 0,
            'paragraphs': 0,
            'unique_words': 0,
            'avg_word_length': 0.0,
            'reading_time_seconds': 0,
            'top_words': [],
            'longest_words': []
        }
        
        if not text.strip():
            return stats
            
        # Basic counts
        stats['characters'] = len(text)
        stats['characters_no_spaces'] = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
        
        # Paragraphs
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        stats['paragraphs'] = len(paragraphs)
        
        # Sentences
        sentences = re.split(r'[.!?]+', text)
        stats['sentences'] = len([s for s in sentences if s.strip()])
        
        # Words
        words = re.findall(r'\b\w+\b', text.lower())
        stats['words'] = len(words)
        
        if words:
            # Word frequency
            word_counts = Counter(words)
            stats['unique_words'] = len(word_counts)
            stats['top_words'] = word_counts.most_common(5)
            
            # Longest words
            unique_words = list(set(words))
            unique_words.sort(key=len, reverse=True)
            stats['longest_words'] = unique_words[:5]
            
            # Average word length
            total_letters = sum(len(word) for word in words)
            stats['avg_word_length'] = total_letters / len(words)
            
            # Reading time
            stats['reading_time_seconds'] = int((len(words) / 225) * 60)
            
        return stats
        
    def create_heatmap_section(self):
        """Create heatmap visualization section"""
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        self.stats_layout.addWidget(separator)
        
        # Heatmap label
        heatmap_label = QLabel("🔥 WORD FREQUENCY HEATMAP")
        heatmap_label.setObjectName("subsectionLabel")
        self.stats_layout.addWidget(heatmap_label)
        
        # Create matplotlib figure for heatmap
        self.heatmap_figure = Figure(figsize=(8, 3), dpi=80, facecolor='#0a0a0a')
        self.heatmap_canvas = FigureCanvas(self.heatmap_figure)
        self.heatmap_canvas.setMaximumHeight(200)
        self.heatmap_canvas.setObjectName("heatmapCanvas")
        self.stats_layout.addWidget(self.heatmap_canvas)
        
        # Heatmap controls
        heatmap_controls = QHBoxLayout()
        
        self.heatmap_words_slider = QSlider(Qt.Orientation.Horizontal)
        self.heatmap_words_slider.setRange(5, 50)
        self.heatmap_words_slider.setValue(15)
        self.heatmap_words_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.heatmap_words_slider.valueChanged.connect(self.update_heatmap)
        
        controls_label = QLabel("Top Words:")
        controls_label.setStyleSheet("color: #aaaaaa;")
        heatmap_controls.addWidget(controls_label)
        heatmap_controls.addWidget(self.heatmap_words_slider)
        heatmap_controls.addStretch()
        
        self.stats_layout.addLayout(heatmap_controls)
        
    def generate_word_heatmap(self, text, top_n=15):
        """Generate heatmap data for word frequency distribution"""
        if not text.strip():
            return None
        
        # Split text into chunks
        chunks = self.split_text_into_chunks(text, num_chunks=20)
        
        # Get top N words overall
        words = self.extract_words(text.lower())
        word_counts = Counter(words)
        top_words = [word for word, _ in word_counts.most_common(top_n)]
        
        if not top_words:
            return None
        
        # Create frequency matrix
        freq_matrix = np.zeros((len(top_words), len(chunks)))
        
        for i, chunk in enumerate(chunks):
            chunk_words = self.extract_words(chunk.lower())
            chunk_counts = Counter(chunk_words)
            for j, word in enumerate(top_words):
                freq_matrix[j, i] = chunk_counts.get(word, 0)
        
        return {
            'matrix': freq_matrix,
            'words': top_words,
            'chunks': [f"Part {i+1}" for i in range(len(chunks))]
        }
        
    def update_heatmap(self):
        """Update the heatmap visualization"""
        text = self.text_input.toPlainText()
        top_n = self.heatmap_words_slider.value()
        
        heatmap_data = self.generate_word_heatmap(text, top_n)
        
        if not heatmap_data:
            self.heatmap_figure.clear()
            self.heatmap_canvas.draw()
            return
        
        self.heatmap_figure.clear()
        ax = self.heatmap_figure.add_subplot(111)
        ax.set_facecolor('#0a0a0a')
        
        # Create custom colormap (terminal green theme)
        colors = ["#0a0a0a", "#006600", "#00aa00", "#00ff00"]
        cmap = LinearSegmentedColormap.from_list("terminal_green", colors)
        
        # Plot heatmap
        im = ax.imshow(heatmap_data['matrix'], aspect='auto', cmap=cmap, 
                       interpolation='nearest')
        
        # Set labels
        ax.set_xticks(range(len(heatmap_data['chunks'])))
        ax.set_xticklabels(heatmap_data['chunks'], rotation=45, ha='right', fontsize=8)
        ax.set_yticks(range(len(heatmap_data['words'])))
        ax.set_yticklabels(heatmap_data['words'], fontsize=8)
        
        # Styling for dark theme
        ax.tick_params(axis='x', colors='#aaaaaa')
        ax.tick_params(axis='y', colors='#aaaaaa')
        for spine in ax.spines.values():
            spine.set_color('#333333')
        
        # Add colorbar
        cbar = self.heatmap_figure.colorbar(im, ax=ax)
        cbar.ax.yaxis.set_tick_params(color='#aaaaaa')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#aaaaaa')
        cbar.set_label('Frequency', color='#aaaaaa')
        
        ax.set_title(f'Word Frequency Heatmap (Top {top_n} Words)', fontsize=10, color='#00ff00')
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                self.heatmap_figure.tight_layout()
            except Exception:
                pass
        
        self.heatmap_canvas.draw()
        
    def create_readability_section(self):
        """Create readability analysis section"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        self.stats_layout.addWidget(separator)
        
        readability_label = QLabel("📊 READABILITY ANALYSIS")
        readability_label.setObjectName("subsectionLabel")
        self.stats_layout.addWidget(readability_label)
        
        # Readability scores grid
        readability_grid = QGridLayout()
        
        scores = [
            ("Flesch Reading Ease", "flesch_ease", self.calculate_flesch_ease),
            ("Flesch-Kincaid Grade", "flesch_grade", self.calculate_flesch_grade),
            ("Gunning Fog Index", "gunning_fog", self.calculate_gunning_fog),
            ("Coleman-Liau Index", "coleman_liau", self.calculate_coleman_liau),
            ("SMOG Index", "smog", self.calculate_smog),
            ("Automated Readability", "automated", self.calculate_automated),
        ]
        
        self.readability_widgets = {}
        
        for i, (label, key, func) in enumerate(scores):
            row = i // 2
            col = (i % 2) * 2
            
            # Label
            lbl = QLabel(label)
            lbl.setObjectName("readabilityLabel")
            readability_grid.addWidget(lbl, row, col)
            
            # Value
            val = QLabel("0.0")
            val.setObjectName("readabilityValue")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            readability_grid.addWidget(val, row, col + 1)
            
            self.readability_widgets[key] = (val, func)
        
        self.stats_layout.addLayout(readability_grid)
        
        # Readability description
        self.readability_desc = QLabel("")
        self.readability_desc.setObjectName("readabilityDesc")
        self.readability_desc.setWordWrap(True)
        self.stats_layout.addWidget(self.readability_desc)

    def calculate_flesch_ease(self, text):
        """Calculate Flesch Reading Ease score"""
        try:
            score = textstat.flesch_reading_ease(text)
            if score < 0: score = 0
            if score > 100: score = 100
            return score
        except:
            return 0.0

    def calculate_flesch_grade(self, text):
        """Calculate Flesch-Kincaid Grade Level"""
        try:
            return textstat.flesch_kincaid_grade(text)
        except:
            return 0.0

    def calculate_gunning_fog(self, text):
        """Calculate Gunning Fog Index"""
        try:
            return textstat.gunning_fog(text)
        except:
            return 0.0

    def calculate_coleman_liau(self, text):
        """Calculate Coleman-Liau Index"""
        try:
            return textstat.coleman_liau_index(text)
        except:
            return 0.0

    def calculate_smog(self, text):
        """Calculate SMOG Index"""
        try:
            return textstat.smog_index(text)
        except:
            return 0.0

    def calculate_automated(self, text):
        """Calculate Automated Readability Index"""
        try:
            return textstat.automated_readability_index(text)
        except:
            return 0.0

    def update_readability_scores(self, text):
        """Update all readability scores"""
        if not text.strip():
            for key, (widget, _) in self.readability_widgets.items():
                widget.setText("0.0")
            self.readability_desc.setText("")
            return
        
        for key, (widget, func) in self.readability_widgets.items():
            score = func(text)
            widget.setText(f"{score:.1f}")
        
        # Update description based on Flesch Reading Ease
        flesch_score = self.calculate_flesch_ease(text)
        if flesch_score >= 90:
            level = "Very Easy (5th grade)"
        elif flesch_score >= 80:
            level = "Easy (6th grade)"
        elif flesch_score >= 70:
            level = "Fairly Easy (7th grade)"
        elif flesch_score >= 60:
            level = "Standard (8th-9th grade)"
        elif flesch_score >= 50:
            level = "Fairly Difficult (10th-12th grade)"
        elif flesch_score >= 30:
            level = "Difficult (College)"
        else:
            level = "Very Difficult (College Graduate)"
        
        self.readability_desc.setText(
            f"📚 Reading Level: {level} | Target audience: {self.get_target_audience(flesch_score)}"
        )

    def get_target_audience(self, score):
        """Get target audience based on readability score"""
        if score >= 80:
            return "Children, casual readers"
        elif score >= 60:
            return "General public, blogs"
        elif score >= 40:
            return "Academic, professional"
        else:
            return "Experts, technical papers"

    def create_keyword_analysis_section(self):
        """Create keyword density analysis section"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        self.stats_layout.addWidget(separator)
        
        keyword_label = QLabel("🔑 KEYWORD DENSITY")
        keyword_label.setObjectName("subsectionLabel")
        self.stats_layout.addWidget(keyword_label)
        
        # Keyword input
        keyword_layout = QHBoxLayout()
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Enter keywords (comma separated)...")
        self.keyword_input.setObjectName("keywordInput")
        self.keyword_input.textChanged.connect(self.update_keyword_analysis)
        
        keyword_layout.addWidget(QLabel("Keywords:"))
        keyword_layout.addWidget(self.keyword_input)
        self.stats_layout.addLayout(keyword_layout)
        
        # Keyword results table
        self.keyword_table = QTableWidget()
        self.keyword_table.setColumnCount(4)
        self.keyword_table.setHorizontalHeaderLabels(["Keyword", "Count", "Density", "Status"])
        self.keyword_table.setMaximumHeight(150)
        self.keyword_table.setObjectName("keywordTable")
        self.stats_layout.addWidget(self.keyword_table)
        
        # SEO recommendations
        self.seo_recommendations = QLabel("")
        self.seo_recommendations.setObjectName("seoRecommendations")
        self.seo_recommendations.setWordWrap(True)
        self.stats_layout.addWidget(self.seo_recommendations)

    def update_keyword_analysis(self):
        """Update keyword density analysis"""
        text = self.text_input.toPlainText()
        keywords_text = self.keyword_input.text()
        
        if not text.strip() or not keywords_text.strip():
            self.keyword_table.setRowCount(0)
            self.seo_recommendations.setText("")
            return
        
        keywords = [k.strip().lower() for k in keywords_text.split(',')]
        words = self.extract_words(text.lower())
        total_words = len(words)
        
        self.keyword_table.setRowCount(len(keywords))
        
        from collections import Counter
        word_counts = Counter(words)
        
        optimal_density = 1.0  # 1% optimal keyword density for SEO
        recommendations = []
        
        for i, keyword in enumerate(keywords):
            count = word_counts.get(keyword, 0)
            density = (count / total_words * 100) if total_words > 0 else 0
            
            # Keyword
            kw_item = QTableWidgetItem(keyword)
            self.keyword_table.setItem(i, 0, kw_item)
            
            # Count
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.keyword_table.setItem(i, 1, count_item)
            
            # Density
            density_item = QTableWidgetItem(f"{density:.2f}%")
            density_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Color code based on SEO optimal range
            if 0.5 <= density <= 2.0:
                density_item.setForeground(QColor(0, 255, 0))  # Green - optimal
            elif density < 0.5:
                density_item.setForeground(QColor(255, 165, 0))  # Orange - low
            else:
                density_item.setForeground(QColor(255, 0, 0))  # Red - high
            
            self.keyword_table.setItem(i, 2, density_item)
            
            # Status
            if density == 0:
                status = "❌ Not found"
                recommendations.append(f"Add keyword '{keyword}'")
            elif density < 0.5:
                status = "⚠️ Too low"
                recommendations.append(f"Increase '{keyword}' usage")
            elif density > 2.0:
                status = "⚠️ Too high"
                recommendations.append(f"Reduce '{keyword}' usage")
            else:
                status = "✅ Optimal"
            
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.keyword_table.setItem(i, 3, status_item)
        
        # Resize columns
        self.keyword_table.resizeColumnsToContents()
        
        # SEO recommendations
        if recommendations:
            self.seo_recommendations.setText("💡 Recommendations: " + "; ".join(recommendations[:3]))
        else:
            self.seo_recommendations.setText("✅ All keywords are optimally used")

    def extract_words(self, text):
        """Extract words from text (helper method)"""
        import re
        return re.findall(r'\b[a-zA-Z]+\b', text)
        
    def split_text_into_chunks(self, text, num_chunks=20):
        """Split text into roughly equal chunks"""
        if not text:
            return []
        
        length = len(text)
        chunk_size = max(1, length // num_chunks)
        
        chunks = []
        for i in range(0, length, chunk_size):
            chunks.append(text[i:i+chunk_size])
            
        # Ensure we don't exceed num_chunks (merge remainder into last chunk)
        if len(chunks) > num_chunks:
            last_chunk = "".join(chunks[num_chunks-1:])
            chunks = chunks[:num_chunks-1]
            chunks.append(last_chunk)
            
        return chunks
        
    def clear_text(self):
        """Clear the text input"""
        self.text_input.clear()
        self.update_stats()
        
    def paste_from_clipboard(self):
        """Paste from clipboard"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.text_input.setPlainText(text)
            self.update_stats()
            
    def export_stats(self):
        """Export statistics to file"""
        text = self.text_input.toPlainText()
        
        if not text.strip():
            QMessageBox.warning(self, "No Data", "No text to export.")
            return
        
        # Generate stats
        if HAS_RUST:
            stats = wdlib.analyze_text_fast(text)
            stats_dict = json.loads(stats.to_json())
        else:
            stats_dict = self.analyze_with_python(text)
        
        # Use ExportManager
        exporter = ExportManager(self)
        exporter.export_stats(stats_dict, text)
        
    def create_theme_selector(self):
        """Create theme selection dropdown"""
        theme_layout = QHBoxLayout()
        
        theme_label = QLabel("Theme:")
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        for theme_id, theme_info in self.theme_manager.THEMES.items():
            self.theme_combo.addItem(theme_info["name"], theme_id)
        
        self.theme_combo.setCurrentText("Terminal Black")
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)
        
        theme_layout.addStretch()
        
        # Add to left layout
        self.left_layout.addLayout(theme_layout)
        
    def change_theme(self):
        """Change the application theme"""
        theme_id = self.theme_combo.currentData()
        stylesheet = self.theme_manager.apply_theme(QApplication.instance(), theme_id)
        self.setStyleSheet(stylesheet)
        self.current_theme = theme_id