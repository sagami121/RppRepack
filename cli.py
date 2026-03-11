import sys
import os
import argparse
import pyzipper
import shutil
import traceback
import getpass
from datetime import datetime

def log_msg(msg):
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    print(f"{timestamp} {msg}")

def parse_rpp_files(rpp_path):
    try:
        if not os.path.isfile(rpp_path):
            return []
        encodings = ["utf-8", "cp932", "latin1"]
        file_lines = None
        for enc in encodings:
            try:
                with open(rpp_path, "r", encoding=enc) as f:
                    file_lines = f.readlines()
                break
            except Exception:
                continue
        if file_lines is None:
            return []

        project_dir = os.path.dirname(os.path.abspath(rpp_path))
        file_set = set()
        for line in file_lines:
            if "FILE \"" in line:
                start = line.find("\"") + 1
                end = line.rfind("\"")
                if start < end:
                    file_path = line[start:end]
                    if not os.path.isabs(file_path):
                        file_path = os.path.join(project_dir, file_path)
                    file_set.add(os.path.abspath(file_path))
        return list(file_set)
    except Exception:
        print(traceback.format_exc())
        return []

def make_zip(rpp_path, save_dir, password=None):
    project_name = os.path.splitext(os.path.basename(rpp_path))[0]
    zip_path = os.path.join(save_dir, f"{project_name}.zip")
    
    if os.path.exists(zip_path):
        counter = 1
        while True:
            zip_path = os.path.join(save_dir, f"{project_name}_{counter}.zip")
            if not os.path.exists(zip_path):
                break
            counter += 1

    encryption = pyzipper.WZ_AES if password else None
    files_to_add = [os.path.abspath(rpp_path)] + [f for f in parse_rpp_files(rpp_path) if os.path.isfile(f)]
    
    log_msg(f"ZIP作成開始: {zip_path}")
    added_files = set()
    files_added = 0

    with pyzipper.AESZipFile(zip_path, "w", compression=pyzipper.ZIP_DEFLATED, encryption=encryption) as zipf:
        if password:
            zipf.setpassword(password.encode("utf-8"))

        for f in files_to_add:
            if f not in added_files:
                zipf.write(f, os.path.basename(f))
                log_msg(f"コピー: {os.path.basename(f)}")
                files_added += 1
                added_files.add(f)

    log_msg(f"完了: {files_added} 個のファイルをまとめました。")

def make_folder(rpp_path, save_dir):
    project_name = os.path.splitext(os.path.basename(rpp_path))[0]
    folder_path = os.path.join(save_dir, project_name)
    
    if os.path.exists(folder_path):
        counter = 1
        while True:
            folder_path = os.path.join(save_dir, f"{project_name}_{counter}")
            if not os.path.exists(folder_path):
                break
            counter += 1
    
    os.makedirs(folder_path, exist_ok=True)
    files_to_copy = [os.path.abspath(rpp_path)] + [f for f in parse_rpp_files(rpp_path) if os.path.isfile(f)]
    
    log_msg(f"フォルダ出力開始: {folder_path}")
    files_copied = 0
    for f in files_to_copy:
        dest = os.path.join(folder_path, os.path.basename(f))
        shutil.copy2(f, dest)
        log_msg(f"コピー: {os.path.basename(f)}")
        files_copied += 1

    log_msg(f"完了: {files_copied} 個のファイルをコピーしました。")

def interactive_mode():
    print("RppRepack CLI v1.0")
    print("'exit' または 'quit' で終了します。'help' でヘルプを表示。")
    
    current_input = ""
    current_output = "."
    
    while True:
        try:
            cmd_line = input("RppRepack> ").strip()
            if not cmd_line:
                continue
                
            parts = cmd_line.split()
            cmd = parts[0].lower()

            if cmd in ["exit", "quit"]:
                break
            elif cmd == "help":
                print("コマンド:")
                print("  input <path>   : RPPファイルを指定")
                print("  output <path>  : 保存先ディレクトリを指定")
                print("  run            : ZIP形式で実行")
                print("  run -f         : フォルダ形式で実行")
                print("  status         : 現在の設定を確認")
                continue
            elif cmd == "status":
                print(f"  入力: {current_input if current_input else '(未設定)'}")
                print(f"  出力: {current_output}")
                continue
            elif cmd == "input":
                if len(parts) > 1:
                    path = " ".join(parts[1:]).strip('\"')
                    if os.path.isfile(path):
                        current_input = path
                        print(f"入力ファイルを設定しました: {path}")
                    else:
                        print("エラー: ファイルが見つかりません。")
                else:
                    print("使い方: input <file_path>")
                continue
            elif cmd == "output":
                if len(parts) > 1:
                    current_output = " ".join(parts[1:]).strip('\"')
                    print(f"出力先を設定しました: {current_output}")
                else:
                    print("使い方: output <dir_path>")
                continue
            elif cmd == "run":
                if not current_input:
                    print("エラー: 先に 'input <path>' でファイルを指定してください。")
                    continue
                
                is_folder = "-f" in parts
                
                if not os.path.exists(current_output):
                    os.makedirs(current_output, exist_ok=True)
                
                if is_folder:
                    make_folder(current_input, current_output)
                else:
                    pwd = None
                    ans = input("パスワードを設定しますか？ (y/N): ").lower()
                    if ans == 'y':
                        pwd = getpass.getpass("Enter password: ")
                    make_zip(current_input, current_output, pwd)
                print("処理が完了しました。")
            else:
                # 入力されたものがファイルパスなら、それをinputとして扱う
                path = cmd_line.strip('\"')
                if os.path.isfile(path) and path.lower().endswith(".rpp"):
                    current_input = path
                    print(f"入力ファイルを設定しました: {path}")
                    print("実行するには 'run' と入力してください。")
                else:
                    print(f"未知のコマンドです: {cmd}")
        except KeyboardInterrupt:
            print("\n終了します。")
            break
        except Exception as e:
            print(f"エラーが発生しました: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="RppRepack CLI - Reaper Project Assets Packager",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input", nargs="?", help="入力する .rpp ファイルのパス")
    parser.add_argument("-o", "--output", help="出力先フォルダのパス")
    parser.add_argument("-f", "--folder", action="store_true", help="ZIPではなくフォルダとして出力する")
    parser.add_argument("-p", "--password", help="ZIP出力時のパスワード設定 (引数として直接指定)")
    parser.add_argument("-P", "--ask-password", action="store_true", help="パスワードをセキュアに入力する (画面に表示されません)")

    # 引数がない場合は対話モードへ
    if len(sys.argv) == 1:
        interactive_mode()
        sys.exit(0)

    args = parser.parse_args()

    if not args.input or not os.path.isfile(args.input):
        print(f"エラー: 有効な入力ファイルが指定されていません: {args.input}")
        parser.print_usage()
        sys.exit(1)

    save_dir = args.output
    if not save_dir:
        save_dir = input("保存先フォルダのパスを入力してください (デフォルト: .): ").strip()
        if not save_dir:
            save_dir = "."

    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    password = args.password
    if args.ask_password:
        password = getpass.getpass("Enter password: ")

    try:
        if args.folder:
            make_folder(args.input, save_dir)
        else:
            make_zip(args.input, save_dir, password)
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
