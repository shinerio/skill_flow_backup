## Prerequisites

### MCP Servers (auto-configured)

The following MCP servers are automatically configured during plugin installation:
- **markmap-mcp-server** — generates mindmap HTML from Markdown
- **chrome-devtools** — exports mindmap HTML to PNG

> No manual setup needed. The install script and plugin `.mcp.json` handle this.

### Desktop Tools (manual)
- **PicGO** — image hosting client. Download from [PicGO releases](https://github.com/Molunerfinn/PicGo/releases), enable the HTTP server (default port 36677).

## Usage

### Custom Command (bundled with plugin)

The command is bundled in the plugin's `commands/` directory and available automatically after installation.

Run in Claude Code:

`/shinerio-plugin:emb-mindmap [markdown_file_path]`
