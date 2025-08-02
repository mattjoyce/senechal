
from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "app/themes/obsidian"
DEST_DIR = BASE_DIR / "app/static/themes/css"
DEST_DIR.mkdir(parents=True, exist_ok=True)

BASE_TEMPLATE = """
/* Simple CSS theme based on Obsidian: {theme_name} ({mode}) */

body {{
  margin: 0;
  padding: 0;
  min-height: 100vh;
  background-color: {background};
}}

.theme-selector {{
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.9);
  padding: 5px;
  border-radius: 4px;
  border: 1px solid {text_faint};
}}

.markdown-container {{
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
}}

.markdown-body {{
  background-color: {background};
  color: {text};
  font-family: system-ui, sans-serif;
  line-height: 1.6;
  padding: 1rem;
}}

.markdown-body code,
.markdown-body pre {{
  background-color: {code_bg};
  padding: 0.2em 0.4em;
  border-radius: 4px;
}}

.markdown-body h1, .markdown-body h2, .markdown-body h3 {{
  color: {accent};
}}

.markdown-body a {{
  color: {accent};
  text-decoration: underline;
}}

.markdown-body blockquote {{
  border-left: 4px solid {accent};
  padding-left: 1em;
  color: {text_faint};
}}

.markdown-body table {{
  border-collapse: collapse;
  width: 100%;
}}

.markdown-body th,
.markdown-body td {{
  border: 1px solid {text_faint};
  padding: 0.5em;
}}

.markdown-body th {{
  background-color: {background_secondary};
}}
"""

def extract_colors(css_content):
    # Default colors
    colors = {
        "background": "#1a1b26",
        "text": "#c0caf5", 
        "accent": "#7aa2f7",
        "text_faint": "#9aa5ce",
        "background_secondary": "#24283b",
        "code_bg": "#1e202e"
    }
    
    # Extract actual colors from theme CSS
    # Look for common Obsidian theme patterns
    bg_matches = re.findall(r'--bg[^:]*:\s*rgb\(([^)]+)\)', css_content)
    if bg_matches:
        rgb_values = bg_matches[0].replace('var(--bg_x)', '').strip()
        if ',' in rgb_values and not 'var(' in rgb_values:
            try:
                r, g, b = map(int, rgb_values.split(','))
                colors["background"] = f"rgb({r}, {g}, {b})"
            except:
                pass
    
    fg_matches = re.findall(r'--fg[^:]*:\s*rgb\(([^)]+)\)', css_content)
    if fg_matches:
        rgb_values = fg_matches[0].replace('var(--fg_x)', '').strip()
        if ',' in rgb_values and not 'var(' in rgb_values:
            try:
                r, g, b = map(int, rgb_values.split(','))
                colors["text"] = f"rgb({r}, {g}, {b})"
            except:
                pass
    
    # Look for cyan/blue accent colors
    cyan_matches = re.findall(r'--cyan[^:]*:\s*rgb\(([^)]+)\)', css_content)
    if cyan_matches:
        rgb_values = cyan_matches[0].replace('var(--cyan_x)', '').strip()
        if ',' in rgb_values and not 'var(' in rgb_values:
            try:
                r, g, b = map(int, rgb_values.split(','))
                colors["accent"] = f"rgb({r}, {g}, {b})"
            except:
                pass
    
    return colors

def convert_themes():
    for theme_dir in SOURCE_DIR.iterdir():
        theme_name = theme_dir.name
        css_file = theme_dir / "theme.css"
        if not css_file.exists():
            continue

        with css_file.open() as f:
            css_content = f.read()

        for mode in ["dark", "light"]:
            # Extract colors from the entire CSS content for this theme
            colors = extract_colors(css_content)
            
            # Adjust for light mode
            if mode == "light":
                colors["background"] = "#ffffff"
                colors["text"] = "#2e3338"
                colors["background_secondary"] = "#f5f5f5"
            
            out_css = BASE_TEMPLATE.format(
                theme_name=theme_name,
                mode=mode,
                background=colors["background"],
                background_secondary=colors["background_secondary"],
                text=colors["text"],
                text_faint=colors["text_faint"],
                accent=colors["accent"],
                code_bg=colors["code_bg"],
            )

            # Replace spaces with hyphens for URL-friendly filenames
            safe_theme_name = theme_name.replace(" ", "-")
            out_path = DEST_DIR / f"{safe_theme_name}-{mode}.css"
            with out_path.open("w") as f:
                f.write(out_css)

if __name__ == "__main__":
    convert_themes()
