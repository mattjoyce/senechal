
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
    variables = {
        "--background-primary": "#111",
        "--background-secondary": "#222",
        "--text-normal": "#eee",
        "--text-faint": "#aaa",
        "--accent": "#7aa2f7",
        "--code-background": "#1e1e2e",
    }
    matches = re.findall(r'--([\w-]+):\s*(#[\da-fA-F]{3,6});', css_content)
    for key, val in matches:
        variables[f"--{key}"] = val
    return variables

def convert_themes():
    for theme_dir in SOURCE_DIR.iterdir():
        theme_name = theme_dir.name
        css_file = theme_dir / "theme.css"
        if not css_file.exists():
            continue

        with css_file.open() as f:
            css_content = f.read()

        for mode in ["dark", "light"]:
            mode_block = re.search(rf"\.theme-{mode}\s*\{{([^}}]+)\}}", css_content)
            if not mode_block:
                continue
            mode_vars = extract_colors(mode_block.group(1))
            out_css = BASE_TEMPLATE.format(
                theme_name=theme_name,
                mode=mode,
                background=mode_vars["--background-primary"],
                background_secondary=mode_vars["--background-secondary"],
                text=mode_vars["--text-normal"],
                text_faint=mode_vars["--text-faint"],
                accent=mode_vars["--accent"],
                code_bg=mode_vars["--code-background"],
            )

            out_path = DEST_DIR / f"{theme_name}-{mode}.css"
            with out_path.open("w") as f:
                f.write(out_css)

if __name__ == "__main__":
    convert_themes()
