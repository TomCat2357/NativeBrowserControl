# Workflow Schema

`run_native_browser_workflow.py` は `--spec-json` または `--spec-file` で次の JSON を受け取る。

```json
{
  "browser": "chrome",
  "connect": {
    "window_index": 0
  },
  "artifact_dir": "optional/output/dir",
  "steps": [
    {
      "action": "summary"
    }
  ]
}
```

## Top-Level Fields

| field | required | description |
| --- | --- | --- |
| `browser` | yes | `chrome` または `edge`。未指定はエラー |
| `connect` | yes | `window_index` か `launch: true` を指定 |
| `artifact_dir` | no | 画像や保存物の出力先。未指定時は一時ディレクトリ |
| `steps` | yes | 実行順に並べた step 配列 |

## `connect`

```json
{
  "window_index": 0,
  "require_visible": false,
  "exclude_minimized": false,
  "retries": 3
}
```

または:

```json
{
  "launch": true,
  "retries": 5,
  "start_delay": 1.0
}
```

- `window_index` と `launch` は同時に指定しない。
- `browser` と接続先ブラウザは常に一致させる。

## Step Actions

| action | main fields |
| --- | --- |
| `summary` | `max_text_len` |
| `navigate` | `url`, `timeout_s`, `interval_s` |
| `wait` | `seconds` |
| `screenshot` | `fmt`, `quality`, `prefer`, `allow_fallback`, `prepare_window`, `maximize_before`, `foreground_before`, `settle_ms`, `file_path` |
| `full_screenshot` | `monitor`, `fmt`, `quality`, `file_path` |
| `page_text` | なし |
| `page_source` | `wait_seconds`, `close_after`, `save_file`, `save_path` |
| `scan` | `control_type`, `title`, `max_elements`, `foreground`, `maximize`, `settle_ms`, `update_mode` |
| `filter` | `class_names`, `control_types`, `name_regex`, `value_regex`, `only_visible`, `require_enabled`, `min_width`, `min_height`, `only_focusable`, `automation_id_regex`, `omit_no_name`, `min_separator_count`, `update_mode`, `output` |
| `get_index` | `class_names`, `control_types`, `name_regex`, `value_regex`, `only_visible`, `require_enabled`, `min_width`, `min_height`, `only_focusable`, `automation_id_regex`, `omit_no_name`, `min_separator_count` |
| `click_index` | `index` |
| `set_text` | `index`, `text` |
| `type_text` | `text`, `method` |
| `find_text` | `text` or `search_text`, `method` |
| `scroll` | `direction`, `amount` |
| `tab` | `operation=new|close|next|previous` |
| `history` | `operation=back|forward|refresh` |
| `zoom` | `operation=in|out|reset` |
| `clipboard` | `operation=copy_selected|cut_text|paste` |
| `click_at` | `x`, `y`, `button=left|double|right` |
| `move_mouse` | `index` or `x`,`y` |

## State Rules

- `filter`
- `get_index`
- `click_index`
- `set_text`
- `move_mouse` with `index`

上記は同一 invocation 内で先に `scan` が必要。

## Output Shape

```json
{
  "ok": true,
  "browser": "chrome",
  "window": {
    "handle": 12345,
    "pid": 67890,
    "title": "Example - Google Chrome"
  },
  "results": [],
  "artifacts": []
}
```

- `results` は step ごとの実行結果
- `artifacts` は保存ファイルの絶対パス一覧
- エラー時は `ok: false` で `error` を返し、可能なら `results` と `artifacts` に途中結果を残す
