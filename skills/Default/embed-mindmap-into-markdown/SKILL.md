---
name: embed-mindmap-into-markdown
description: Generate a mind map based on a Markdown file and embed it into the Markdown document
skills: generate-mindmap, upload-mindmap, embed-mindmap
---

# steps

1. generate mindmap
2. export html to png
3. upload imagesd
4. embed mindmap
5. clear local html and png

## generate mindmap

Use mcp tools named "markmap-mcp-server" to generate mindmap. 

## export html to png

Use mcp tools named "chrome-devtools" to export the html to png format. You should click the "Export png" button in the chrome-devtools.

## upload images

1. Use the following command to find the latest png file in the Downloads folder.

```bash
cd ~/Downloads && ls -lt *.png 2>/dev/null | head -1 || ls -lt *.png 2>/dev/null | head -1
```

2. Use `python scripts/picgo_client.py [image_absolute_path]` to upload image to picgo and get the image url.

## embed mindmap

Add a mind map section if not exist at the end of the Markdown file and embed the image url. ![image_name](image_url)

## clear local html and png

After all, you should delete the local html and png files.