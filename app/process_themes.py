import os
import re

INPUT_DIR = './themes/obsidian'
OUTPUT_DIR = './themes/css'

BASE_TEMPLATE = '''
/* Generated from Obsidian theme: {theme_name} */

.markdown-body {{
  background: var(--background-primary);
  color: var(--text-normal);
  font-family: system-ui, sans-serif;
  line-height: 1.6;
  padding: 1rem;
}}

.markdown-body h1, 
.markdown-body h2, 
.markdown-body h3 {{
  color: var(--accent);
  margin-top: 1.5em;
}}

.markdown-body pre,
.markdown-body code {{
  background: var(--code-background, #1e1e2e);
  font-family: monospace;
  padding: 0.5em;
  border-radius: 5px;
  overflow-x: auto;
}}

.markdown-body pre.frontmatter {{
  background: var(--background-secondary);
  color: var(--text-faint);
  font-family: monospace;
  border-left: 3px solid var(--accent);
  padding: 1em;
  margin-bottom: 2em;
}}

:root {{
{variables}
}}
'''

def extract_root_variables(css_text):
    match = re.search(r':root\s*{([^}]+)}', css_text, re.MULTILINE | re.DOTALL)
    if not match:
        return ''
    raw_lines = match.group(1).strip().split('\n')
    variables = [line.strip() for line in raw_lines if line.strip().startswith('--')]
    return '\n'.join(variables)

def extract_theme_block(css_text, selector):
    """Extract lines inside a CSS block (e.g. .theme-dark or .theme-light)"""
    match = re.search(rf'{re.escape(selector)}\s*{{([^}}]+)}}', css_text, re.MULTILINE | re.DOTALL)
    if not match:
        return ''
    raw_lines = match.group(1).strip().split('\n')
    variables = [line.strip() for line in raw_lines if line.strip().startswith('--')]
    return '\n'.join(variables)

def process_theme_folder(folder_name):
    theme_path = os.path.join(INPUT_DIR, folder_name)
    css_path = os.path.join(theme_path, 'theme.css')

    if not os.path.isfile(css_path):
        print(f"⚠️  Skipping {folder_name} – no theme.css found.")
        return

    with open(css_path, 'r', encoding='utf-8') as f:
        css_text = f.read()

    for mode in ['dark', 'light']:
        selector = f'.theme-{mode}'
        variables = extract_theme_block(css_text, selector)
        if not variables:
            print(f"⚠️  No {selector} variables in {folder_name}/theme.css")
            continue

        output_path = os.path.join(OUTPUT_DIR, f"{folder_name.lower().replace(' ', '')}-{mode}.css")
        output_css = BASE_TEMPLATE.format(theme_name=f"{folder_name} ({mode})", variables=variables)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_css)

        print(f"✅ Processed {folder_name} ({mode}) → {output_path}")


def main():
    for folder in os.listdir(INPUT_DIR):
        folder_path = os.path.join(INPUT_DIR, folder)
        if os.path.isdir(folder_path):
            process_theme_folder(folder)

if __name__ == '__main__':
    main()
