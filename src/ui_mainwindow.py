"""
WD - Minimalist Word Counter UI
Black terminal aesthetic design
"""

import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

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
        left_layout = QVBoxLayout(left_panel)
        
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
        left_layout.addWidget(input_label)
        left_layout.addWidget(self.text_input)
        left_layout.addLayout(button_layout)
        
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
            
        # Save to file
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Statistics",
            f"word_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if file_name:
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(stats_dict, f, indent=2, ensure_ascii=False)
                
            QMessageBox.information(self, "Success", f"Statistics exported to {file_name}")