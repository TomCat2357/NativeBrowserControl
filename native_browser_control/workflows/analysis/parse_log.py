#%%
import argparse
import json
import sys

from native_browser_control.utils.output import add_output_argument, route_output

def get_text_from_content(content):
    """
    contentフィールドからテキストを抽出するジェネレータ
    """
    if isinstance(content, dict):
        for key, value in content.items():
            if key == 'text':
                yield value  # 見つけたらその場で値を「産出」する
            elif isinstance(value, (dict, list)):
                # 再帰先のジェネレータから値を中継する
                yield from get_text_from_content(value)
    elif isinstance(content, list):
        for item in content:
            yield from get_text_from_content(item)


def parse_chat_log(log_data):
    """
    ログデータから会話部分（UserとAssistant）のみを抽出して表示する
    """
    parsed_log = []
    # 各行を分割して処理
    for line in log_data.strip().split('\n'):
        if not line.strip():
            continue

        try:
            entry = json.loads(line)  # 各行をJSONとしてパース
            entry_type = entry.get('type')
            
            # --- ユーザーのメッセージ抽出 ---
            if entry_type == 'user':
                message = entry.get('message', {})
                text = list(get_text_from_content(message))
                if text:
                    # 修正: f-string内のクォート競合を回避するためシングルクォートを使用
                    parsed_log.append(f"👤 [User]: {''.join(text)}")

            # --- アシスタントのメッセージ抽出 ---
            elif entry_type == 'assistant':
                message = entry.get('message', {})
                text = list(get_text_from_content(message))
                if text:
                    parsed_log.append(f"🤖 [Assistant]: {''.join(text)}")
                    
        except json.JSONDecodeError:
            print(f"⚠ JSONパースエラー: {line[:20]}...", file=sys.stderr)
            continue
    return parsed_log
        

def reconstruct_tree(data):
    if isinstance(data, dict):
        return {key: reconstruct_tree(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [reconstruct_tree(item) for item in data]
    else:
        return type(data).__name__


def main(file_path):
    """
    ファイルを読み込み、パース結果をリストとして返すメイン関数
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_log = f.read()
        
        parsed_log = parse_chat_log(raw_log)
        return parsed_log
        
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません -> {file_path}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)
        return []
def run_log_parser(file_path: str, output: str = "stdout") -> str:
    """ログファイルをパースし、結果を指定出力先に返す。"""

    def _task() -> None:
        sys.stdout.reconfigure(encoding="utf-8")
        result = main(file_path)
        for line in result:
            print(line)

    return route_output(_task, output)


#%%
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chatログファイルをパースして表示します")
    parser.add_argument("file_path", help="パースしたいログファイルのパス")
    add_output_argument(parser)
    args = parser.parse_args()
    run_log_parser(args.file_path, args.output)
# %%
