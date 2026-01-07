---
name: Native Browser Usage
description: This skill should be used when the user asks about "NativeBrowserControl", "browser automation", "Chrome automation", "Edge automation", "UI Automation", "scan elements", "click element", or needs help with browser control workflows without Selenium.
version: 0.1.0
---

# Native Browser Control

NativeBrowserControl is an MCP server that controls Chrome and Edge browsers on Windows using UI Automation (pywinauto/pywin32) without Selenium. It provides direct window manipulation, element scanning, and browser interaction capabilities.

## Core Concepts

### Browser Connection Model

NativeBrowserControl operates on already-running browser windows or can launch new ones:

1. **List available windows**: Use `/browser:list-windows` to see all running browser instances
2. **Connect to specific window**: Use `/browser:connect` with window index (0=first, -1=last)
3. **Auto-launch if needed**: Connection automatically launches browser if none running

### Element Interaction Pattern

The recommended workflow for reliable element interaction:

1. **Scan elements**: `/browser:scan-elements` updates `current_elements` (use `/browser:list-elements` to inspect)
2. **Filter if needed**: `/browser:filter-elements` narrows the scan results
3. **Identify target**: Find element by name, type, or automation_id in the list
4. **Interact by index**: Use `/browser:click-element <index>` or `/browser:set-element-text <index> <text>`
5. **Re-scan as needed**: Element indices change when page updates

**Critical**: Always scan before clicking elements. Indices are session-specific.

### Browser Selection

All tools accept optional `browser` parameter:
- `chrome` (default): Control Chrome browser
- `edge`: Control Microsoft Edge

Pass browser type in command arguments when needed.

## Common Workflows

### Basic Navigation Workflow

```
1. /browser:connect
2. /browser:navigate https://example.com
3. /browser:screenshot
4. /browser:get-page-text
```

### Element Interaction Workflow

```
1. /browser:scan-elements
2. /browser:list-elements
3. Identify target element index from results
4. /browser:click-element <index>
5. /browser:wait 2
6. /browser:screenshot
```

### Form Filling Workflow

```
1. /browser:scan-elements control_type="Edit"
2. /browser:set-element-text <index> "text to input"
3. /browser:scan-elements control_type="Button"
4. /browser:click-element <button_index>
```

### File Dialog Handling

File open dialogs require special handling:

```
1. Trigger dialog (e.g., click upload button)
2. /browser:wait 2
3. /browser:scan-elements
4. Find <Edit> element for filename field
5. /browser:set-element-text <index> "C:\\full\\path\\to\\file.txt"
6. Find "開く(O)" or "Open" button
7. /browser:click-element <button_index>
```

**Note**: File paths must be absolute Windows paths with backslashes.

### Tab Management Workflow

```
1. /browser:new-tab
2. /browser:navigate <url>
3. /browser:switch-tab direction="previous"
4. /browser:close-tab
```

## Scanning and Filtering

`/browser:scan-elements` populates `current_elements`. Use `/browser:list-elements` or
`/browser:elements-summary` to inspect, then `/browser:filter-elements` to narrow.

**Scan with simple constraints**:

```
/browser:scan-elements control_type="Button"
/browser:scan-elements control_type="Edit"
/browser:scan-elements title="Login"
```

**Filter after scan**:
```
/browser:filter-elements control_types="Button" name_regex="^Login"
/browser:filter-elements class_names=["Edit", "ComboBox"]
/browser:filter-elements automation_id_regex="^user_"
/browser:filter-elements value_regex="^admin"
/browser:filter-elements only_visible=true require_enabled=true
/browser:filter-elements min_width=100 min_height=30
/browser:filter-elements index_ranges="0:50" output="summary"
/browser:filter-elements omit_no_name=false update_mode="preserve"
/browser:filter-elements min_separator_count=1 update_mode="add"
```

Use `max_elements` on `scan-elements` to limit the initial scan size.

## Screenshot Modes

### Window Screenshot

Captures only the browser window:
```
/browser:screenshot
/browser:screenshot format="JPEG" quality=90
```

Returns base64-encoded image. Supports PNG (default) and JPEG.

### Full Screen Screenshot

Captures entire screen or specific monitor:
```
/browser:full-screenshot
/browser:full-screenshot monitor=1
/browser:full-screenshot monitor=2 format="PNG"
```

Monitor options:
- `0`: All monitors
- `1`: Primary monitor
- `2+`: Secondary monitors

## Text Input Methods

### Type Text Tool

For focused elements:
```
/browser:type-text text="Hello World"
/browser:type-text text="Hello" method="paste"
/browser:type-text text="Hello" method="type"
```

Methods:
- `paste` (default): Clipboard-based, fast
- `type`: Character-by-character, slower but more reliable for some inputs

### Set Element Text Tool

For specific elements (recommended):
```
1. /browser:scan-elements
2. /browser:set-element-text <index> "text content"
```

Directly sets text on Edit controls without focus concerns.

## Scrolling Patterns

```
/browser:scroll direction="down"
/browser:scroll direction="up"
/browser:scroll direction="page_down"
/browser:scroll direction="page_up"
/browser:scroll direction="top"
/browser:scroll direction="bottom"
/browser:scroll direction="down" amount=1000
```

Use `amount` parameter (pixels) only with `down` or `up` directions.

## Timing and Waits

Page load and dynamic content require explicit waits:

```
/browser:navigate https://example.com
/browser:wait 3
/browser:scan-elements
```

Common wait scenarios:
- After navigation: 2-3 seconds
- After dialog open: 1-2 seconds
- After form submission: 3-5 seconds
- After element click: 1-2 seconds

Adjust based on page complexity and network speed.

## Clipboard Operations

### Copy Selected Text

```
1. /browser:scan-elements
2. /browser:click-element <text_start_index>
3. Select text manually or use Ctrl+A
4. /browser:copy-selected
```

Returns copied text content.

### Paste Content

```
/browser:paste
```

Pastes current clipboard content to focused element.

## Important Limitations

### Window Visibility

Browser window must be:
- Foreground (front-most)
- Not minimized
- Visible on screen

The driver attempts auto-restore if window is minimized.

### DPI and Scaling

Coordinate-based operations depend on:
- Standard DPI settings (100%)
- Single monitor or primary monitor use
- No virtual desktop complications

If coordinates are misaligned, check display scaling settings.

### Element Stability

Element indices from scan results are:
- Valid only for current page state
- Invalidated by page changes, reloads, dynamic content
- Session-specific (not persistent across scans)

Always re-scan after page updates.

### Manual Intervention

During automation:
- Avoid manual mouse/keyboard input
- Browser window loses focus → operations may fail
- Clicking outside browser → need to re-focus

## Troubleshooting

### Cannot Find Element

```
1. /browser:screenshot to verify page loaded
2. /browser:wait <seconds> for dynamic content
3. /browser:scan-elements then /browser:filter-elements with specific filters
4. Check element name, type, and visibility
5. Try broader filters or no filters
```

### Click Not Working

```
1. Verify element enabled: filter with require_enabled=true
2. Verify element visible: filter with only_visible=true
3. Try filtering with only_focusable=true
4. Wait longer before clicking
5. Check browser window is foreground
```

### Coordinate Misalignment

```
1. Check Windows display scaling (should be 100%)
2. Verify single monitor or primary monitor use
3. Ensure browser window is maximized
4. Use element-based clicking instead of coordinate clicking
```

### Browser Not Responding

```
1. /browser:list-windows to check browser state
2. /browser:connect to reconnect
3. Close and reopen browser manually
4. Verify browser not in fullscreen mode
```

## Best Practices

1. **Always scan before interact**: Element indices are not stable
2. **Use specific filters**: Reduce scan results to relevant elements
3. **Prefer element operations over coordinates**: More reliable across DPI settings
4. **Add explicit waits**: Don't assume instant page loads
5. **Take screenshots for debugging**: Visual confirmation of state
6. **Handle file dialogs carefully**: Use absolute paths, verify element indices
7. **Re-scan after page changes**: Dynamic content invalidates indices
8. **Keep browser in foreground**: Automation requires window visibility
9. **Use set-element-text for inputs**: More reliable than type-text for forms
10. **Check browser parameter**: Specify `edge` when needed, default is `chrome`

## Available Commands

### Browser Connection & Management
- `/browser:list-windows` - List running browser windows
- `/browser:connect` - Connect to browser (launch if needed)
- `/browser:wait` - Wait for specified seconds

### Navigation
- `/browser:navigate` - Navigate to URL
- `/browser:get-url` - Get current URL
- `/browser:get-title` - Get page title
- `/browser:get-browser-summary` - Get browser summary (URL/title/state)
- `/browser:back` - Go back
- `/browser:forward` - Go forward
- `/browser:refresh` - Reload page

### Screenshots
- `/browser:screenshot` - Capture browser window
- `/browser:full-screenshot` - Capture entire screen

### Content
- `/browser:get-page-text` - Get all page text
- `/browser:get-page-source` - Get HTML source

### Input & Search
- `/browser:type-text` - Type text to focused element
- `/browser:find-text` - Find text on page

### Scrolling
- `/browser:scroll` - Scroll page

### Tabs
- `/browser:new-tab` - Open new tab
- `/browser:close-tab` - Close current tab
- `/browser:switch-tab` - Switch to next/previous tab

### Zoom
- `/browser:zoom` - Zoom in/out/reset

### Clicking
- `/browser:click` - Click at coordinates

### Element Operations (Recommended)
- `/browser:scan-elements` - Scan page elements
- `/browser:filter-elements` - Filter scanned elements
- `/browser:list-elements` - List scanned elements
- `/browser:elements-summary` - Show element statistics
- `/browser:click-element` - Click element by index
- `/browser:set-element-text` - Set text on element by index

### Clipboard
- `/browser:copy-selected` - Copy selected text
- `/browser:paste` - Paste clipboard content

### Configuration
- `/browser:add-to-config` - Add MCP server to config file

## Quick Reference

| Task | Command |
|------|---------|
| Connect browser | `/browser:connect` |
| Navigate to URL | `/browser:navigate <url>` |
| Take screenshot | `/browser:screenshot` |
| Scan elements | `/browser:scan-elements` |
| Click element | `/browser:click-element <index>` |
| Type text | `/browser:type-text <text>` |
| Set element text | `/browser:set-element-text <index> <text>` |
| Scroll page | `/browser:scroll direction="down"` |
| Wait | `/browser:wait <seconds>` |
| New tab | `/browser:new-tab` |
| Get page text | `/browser:get-page-text` |

Use these commands through Claude Code's slash command interface to control Chrome and Edge browsers efficiently.

## Additional Resources

### Reference Files

For advanced techniques and detailed patterns (when added):
- **`references/advanced-patterns.md`** - Complex automation workflows
- **`references/troubleshooting.md`** - Detailed error resolution

### Example Files

Working examples for common scenarios:
- **`examples/approval-system-download.md`** - Approval system file batch download workflow
- **`examples/table-extraction.md`** - Browser table data extraction and JSON conversion

Future additions will expand documentation while keeping this core guide comprehensive.
