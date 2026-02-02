"""
Theme Manager for WD Word Counter
Supports multiple UI themes
"""

from PyQt6.QtGui import QPalette, QColor

class ThemeManager:
    THEMES = {
        "terminal_black": {
            "name": "Terminal Black",
            "colors": {
                "background": "#0a0a0a",
                "foreground": "#00ff00",
                "accent": "#00ffff",
                "panel": "#111111",
                "border": "#333333",
                "input_bg": "#000000",
                "stat_bg": "#1a1a1a",
                "success": "#00ff00",
                "warning": "#ffff00",
                "error": "#ff5555"
            }
        },
        "light_mode": {
            "name": "Light Mode",
            "colors": {
                "background": "#f5f5f5",
                "foreground": "#333333",
                "accent": "#0066cc",
                "panel": "#ffffff",
                "border": "#dddddd",
                "input_bg": "#ffffff",
                "stat_bg": "#f9f9f9",
                "success": "#00aa00",
                "warning": "#ff8800",
                "error": "#cc0000"
            }
        },
        "solarized": {
            "name": "Solarized",
            "colors": {
                "background": "#002b36",
                "foreground": "#839496",
                "accent": "#2aa198",
                "panel": "#073642",
                "border": "#586e75",
                "input_bg": "#073642",
                "stat_bg": "#073642",
                "success": "#859900",
                "warning": "#b58900",
                "error": "#dc322f"
            }
        },
        "night_reading": {
            "name": "Night Reading",
            "colors": {
                "background": "#1a1a2e",
                "foreground": "#e6e6e6",
                "accent": "#4cc9f0",
                "panel": "#16213e",
                "border": "#0f3460",
                "input_bg": "#0f3460",
                "stat_bg": "#16213e",
                "success": "#4ade80",
                "warning": "#fbbf24",
                "error": "#f87171"
            }
        }
    }
    
    @staticmethod
    def apply_theme(app, theme_name="terminal_black"):
        """Apply a theme to the application"""
        if theme_name not in ThemeManager.THEMES:
            theme_name = "terminal_black"
        
        theme = ThemeManager.THEMES[theme_name]
        colors = theme["colors"]
        
        # Create palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(colors["background"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["foreground"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(colors["input_bg"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(colors["foreground"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(colors["panel"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["foreground"]))
        
        app.setPalette(palette)
        
        # Generate stylesheet
        stylesheet = ThemeManager.generate_stylesheet(colors)
        
        return stylesheet
    
    @staticmethod
    def generate_stylesheet(colors):
        """Generate QSS stylesheet from colors"""
        return f"""
        /* Main window */
        QMainWindow {{
            background-color: {colors['background']};
        }}
        
        /* Panels */
        #leftPanel, #rightPanel {{
            background-color: {colors['panel']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            padding: 10px;
        }}
        
        /* Section labels */
        #sectionLabel {{
            color: {colors['accent']};
            font-family: 'Consolas', monospace;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        #subsectionLabel {{
            color: {colors['accent']};
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 5px;
        }}
        
        /* Text input */
        #textInput {{
            background-color: {colors['input_bg']};
            color: {colors['foreground']};
            font-family: 'Consolas', monospace;
            font-size: 12px;
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 10px;
            selection-background-color: {colors['accent']}40;
        }}
        
        /* Buttons */
        QPushButton {{
            font-family: 'Consolas', monospace;
            font-size: 11px;
            font-weight: bold;
            padding: 8px 15px;
            border: none;
            border-radius: 4px;
            min-width: 80px;
            background-color: {colors['panel']};
            color: {colors['foreground']};
        }}
        
        QPushButton:hover {{
            background-color: {colors['accent']};
            color: {colors['background']};
        }}
        
        /* Statistics */
        #statFrame {{
            background-color: {colors['stat_bg']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
        }}
        
        #statLabel {{
            color: {colors['foreground']};
            font-family: 'Consolas', monospace;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        #statValue {{
            color: {colors['success']};
            font-family: 'Consolas', monospace;
            font-size: 18px;
            font-weight: bold;
        }}
        
        /* Separator */
        #separator {{
            border: 1px solid {colors['border']};
            margin: 15px 0;
        }}
        """