---
name: embed-mindmap
description: Generate a mind map based on a Markdown file and embed it into the Markdown document
allowed-tools: Bash(mv *), Bash(uv run *), Bash(sleep *)
---

# steps

1. generate mindmap
2. export html to png
3. upload image
4. embed mindmap
5. cleanup temporary files

## generate mindmap

1. try to install the mcp named "markmap-mcp-server" if not exist.
2. Use mcp tools named "markmap-mcp-server" to generate mindmap. Record the output HTML file path as `{html_path}`.

## export html to png

1. Open the generated HTML in chrome-devtools via `navigate_page` with `url` set to `file://{html_path}`.
2. Wait for the page to fully load using `wait_for` with a reasonable timeout (e.g., 2000ms) to ensure the markmap is rendered.
3. Click the "Export PNG" button using the `click` tool with selector `button:has-text("Export PNG")`. This triggers the browser's export functionality, producing a cleaner PNG without unwanted text selections.
4. Wait for the download to complete (use a short delay or wait for the file to appear in the Downloads folder).
5. Move the downloaded PNG file from the Downloads folder to `{html_path}.png`. The downloaded file is typically named based on the HTML filename or "markmap.png".
6. Rename the png file with pattern `{markdown_file_name}_YYYY_MM_DD_HHMMSS.png`.

## upload image

Important! Note that you must run picgo_client.py by `uv run` first.

Use `uv run scripts/picgo_client.py {html_path}.png` to upload image to picgo and get the image url.

Only if uv is not available, you can also run the script with python directly:

```bash
python scripts/picgo_client.py {html_path}.png`
```

## embed mindmap

Add a mind map section titled "# 🧠 Overview" at the beginning of the Markdown file and embed the image url. `![mindmap](image_url)`

## cleanup temporary files

Delete the two temporary files created during the process:

```bash
rm -f "{html_path}" "{html_path}.png"
```