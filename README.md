# RppRepack

rpp内の音声ファイルを一つのフォルダ・ZIPにまとめてコピーするツール

## 主な機能
- .rpp ファイルで使用されているメディアファイルを自動特定
- フォルダまたは ZIP 形式での一括コピー
- ZIP 出力時の AES-256 暗号化パスワード設定
- GUI と CLI の両方を提供

---

## GUI 版の使い方 (`RppRepack.exe`)

1. **RPP ファイルの選択**:
   - `ここに RPP ファイルをドラッグ & ドロップ` エリアにファイルをドロップするか、クリックしてファイルを選択します。
2. **保存先の指定**:
   - `📂 保存先フォルダを選択` ボタンをクリックし、出力先のディレクトリを選びます。
3. **出力形式の選択**:
   - `ZIP 出力` または `フォルダ出力` を選択します。
   - ZIP 出力の場合、`パスワードを設定する` にチェックを入れると、AES 暗号化パスワードを設定できます。
4. **実行**:
   - `実行` ボタンをクリックすると処理が開始されます。完了後、保存先フォルダが自動的に開きます。

---

## CLI 版の使い方 (`RppRepack-cli.exe`)

CLI 版は、バッチ処理やコマンドラインからの操作に適しています。

### 対話モード
引数なしで実行すると対話モードが起動します。
```bash
RppRepack-cli.exe
```
- `input <path>` : RPP ファイルを指定
- `output <path>` : 保存先を指定
- `run` : 実行 (ZIP形式)
- `run -f` : 実行 (フォルダ形式)
- `status` : 現在の設定を確認

### コマンドライン引数
引数を指定して直接実行することも可能です。
```bash
# ZIP 出力
RppRepack-cli.exe project.rpp -o ./output

# フォルダ形式で出力
RppRepack-cli.exe project.rpp -o ./output -f

# パスワード付き ZIP (パスワードを直接指定)
RppRepack-cli.exe project.rpp -o ./output -p mypassword

# パスワード付き ZIP (実行時に入力を促す)
RppRepack-cli.exe project.rpp -o ./output -P
```

---

## ビルド方法
Nuitkaでビルドするのを推奨します。

### 事前準備
- Python 3.13
- `pip install -r requirements.txt`
- `pip install nuitka`
- Visual Studio C++ Build Tools（MSVC）


`build.bat` を実行すると、`nuitka_dist\RppRepack` に GUI と CLI の両方が含まれる実行ファイルが生成されます。
