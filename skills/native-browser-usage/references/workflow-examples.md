# Workflow Examples

## Chrome で概要取得してスクリーンショット

```json
{
  "browser": "chrome",
  "connect": {
    "window_index": 0
  },
  "steps": [
    {
      "action": "summary"
    },
    {
      "action": "navigate",
      "url": "https://example.com"
    },
    {
      "action": "wait",
      "seconds": 2
    },
    {
      "action": "screenshot",
      "fmt": "PNG"
    }
  ]
}
```

## Edge で要素をスキャンしてクリック

```json
{
  "browser": "edge",
  "connect": {
    "window_index": 0
  },
  "steps": [
    {
      "action": "scan",
      "control_type": "Button",
      "max_elements": 200
    },
    {
      "action": "get_index",
      "control_types": "Button",
      "name_regex": "^(検索|Search)$",
      "only_visible": true
    },
    {
      "action": "click_index",
      "index": 0
    }
  ]
}
```

## フォーム入力

```json
{
  "browser": "chrome",
  "connect": {
    "window_index": 0
  },
  "steps": [
    {
      "action": "scan",
      "control_type": "Edit",
      "max_elements": 200
    },
    {
      "action": "set_text",
      "index": 3,
      "text": "sample text"
    },
    {
      "action": "tab",
      "operation": "next"
    }
  ]
}
```

## HTML ソースを保存

```json
{
  "browser": "edge",
  "connect": {
    "window_index": 0
  },
  "steps": [
    {
      "action": "page_source",
      "save_file": true
    }
  ]
}
```
