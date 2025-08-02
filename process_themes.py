
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
    # Extract base HSL values
    base_h = re.search(r'--base-h:\s*(\d+)', css_content)
    base_s = re.search(r'--base-s:\s*(\d+)%', css_content) 
    base_l = re.search(r'--base-l:\s*(\d+)%', css_content)
    
    accent_h = re.search(r'--accent-h:\s*(\d+)', css_content)
    accent_s = re.search(r'--accent-s:\s*(\d+)%', css_content)
    accent_l = re.search(r'--accent-l:\s*(\d+)%', css_content)
    
    # Default fallback colors
    colors = {
        "background": "#1a1b26",
        "text": "#c0caf5", 
        "accent": "#7aa2f7",
        "text_faint": "#9aa5ce",
        "background_secondary": "#24283b",
        "code_bg": "#1e202e"
    }
    
    # Use extracted HSL values if available
    if base_h and base_s and base_l:
        h = int(base_h.group(1))
        s = int(base_s.group(1))
        l = int(base_l.group(1))
        
        # Calculate dark theme colors based on base HSL
        colors["background"] = f"hsl({h}, {s}%, {max(l-75, 5)}%)"
        colors["background_secondary"] = f"hsl({h}, {s}%, {max(l-70, 8)}%)"
        colors["text"] = f"hsl({h}, {max(s-10, 0)}%, {min(l+65, 90)}%)"
        colors["text_faint"] = f"hsl({h}, {max(s-10, 0)}%, {min(l+35, 70)}%)"
        colors["code_bg"] = f"hsl({h}, {s}%, {max(l-65, 10)}%)"
    
    if accent_h and accent_s and accent_l:
        ah = int(accent_h.group(1))
        as_ = int(accent_s.group(1))
        al = int(accent_l.group(1))
        colors["accent"] = f"hsl({ah}, {as_}%, {al}%)"
    
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
