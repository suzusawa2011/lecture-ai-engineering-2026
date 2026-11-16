# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：- **第1回（素のLLM / app.ask）**:
  - 講座固有のコンテキストや用語集を持っていないため、「AIE2026の講座の宿題にある3レベル」について質問した際に、一般的な機械学習のレベル分けなどを当てはめてもっともらしく答えるハルシネーションを起こすか、「分からない」と答える状態だった。
- **第3回（エージェント / app.agent）**:
  - 事前に `search_glossary` ツールを呼び出して講座の用語集（`data/glossary.json`）を検索・確認した上で回答を生成した。
  - その結果、「基礎（講義内容の確認）」「実装（自分でコードを書く）」「発展（調査や試行）」という講座独自の定義を正確に答え、どれか1つに取り組めば完了となる点や、末尾に関係する回（第1回）を示すなど、システムプロンプトの指示どおりの正確な回答を出力した。

- `--trace` で見えたツール呼び出し（ツール名と引数）：実行した質問に対して、以下のツール呼び出しと引数が確認された：
- **質問 1**: `AIE2026の口座の宿題にある「３レベル」とは何ですか？`
  - `[tool call] search_glossary({'query': '3レベル'})`
- **質問 2**: `LoRAとQLoRAの違いは？`
  - `[tool call] search_glossary({'query': 'LoRA'})`
  - `[tool call] search_glossary({'query': 'QLoRA'})`
  - （※1回の質問に対して2つの用語が別々の引数で順に検索された）
- **質問 3**: `第2回の内容から確認問題を1問出して`
  - `[tool call] make_quiz({'lecture': 2})`

- 1つの質問での LLM 呼び出し回数（`requests`）：- **質問（3レベル / 確認問題）**:
  - `requests=2`（1回目でツール呼び出しを要求し、ツールの実行結果 `tool return` を受け取った後の2回目で最終的な回答文を生成したため）。
- **質問（LoRAとQLoRAの違い）**:
  - 複数回のツール呼び出し（バッチまたは順次）と結果の返却を経て回答をまとめるため、複数回の `requests` が発生している。このようにツール呼び出しを挟むエージェントループでは、素のLLM（requests=1）と比べて呼び出し回数（requests）とトークン消費量が増加することを確認した。

- 追加したツールと、docstring に書いた説明：- **追加したツール**: `make_quiz(lecture: int) -> str`（`app/agent.py` にて `agent.tool_plain(tools.make_quiz)` として登録）
- **docstring に書いた説明**:
  ```python
  """指定した回の用語から1つを選び、確認問題と答えを返す。

  「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
  引数: {"lecture": {"type": "integer"}}
  """
  ```

## 宿題

### 選択したレベル
- **実装**: 副作用を持つツール（ファイル保存）の追加と、Human-in-the-Loop（承認フロー）の実装

### 実装内容の要約
1. **ツールの追加（`app/tools.py`）**
   - 学習した内容の要点を `learning_log/` フォルダ配下にテキストファイルとして保存する `save_learning_log(topic: str, content: str)` を実装。
2. **承認必須設定と再開処理の実装（`app/agent.py`）**
   - `Agent` の `output_type` に `[str, DeferredToolRequests]` を指定し、`agent.tool_plain(tools.save_learning_log, requires_approval=True)` で登録。
   - `main()` にて `DeferredToolRequests` が返された際、`result.output.approvals` からツール名と引数を画面に表示し、コンソール入力（`[y/N]`）で承認を得るループを実装。
   - `y` が入力された場合のみ `result.output.build_results(approve_all=True)` を生成し、`deferred_tool_results` に渡してエージェントの実行を再開するようにした。

### 動作確認ログ（`--trace` 出力）

実行コマンド:
```bash
uv run python -m app.agent --trace "今日の講義で学んだLoRAの概要を学習記録として保存して"
```

出力結果:
```text
[model] gemini-3.5-flash-lite

[承認要求] 以下の操作を実行しようとしています:
  - ツール名: save_learning_log
  - 引数: {'topic': 'LoRAの概要', 'content': 'LoRAは、事前学習済みの重みを固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法です。学習パラメータが少なく、アダプタとして小さなファイルサイズで保存できる特徴があります。'}
この操作を実行してよろしいですか？ [y/N]: y
今日の講義で学んだLoRAの概要を学習記録として `learning_log/LoRAの概要.txt` に保存しました。

【記録した内容】
LoRAは、事前学習済みの重みを固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法です。学習パラメータが少なく、アダプタとして小さなファイルサイズで保存できる特徴があります。

（第2回）

--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[tool call]   save_learning_log({'topic': 'LoRAの概要', 'content': 'LoRAは、事前学習済みの重みを固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法です。学習パラメータが少なく、アダプタとして小さなファイルサイズで保存できる特徴があります。'})
[tool return] save_learning_log -> 学習記録を learning_log/LoRAの概要.txt に保存しました。…
[usage] RunUsage(cost=Decimal('0.0005648'), details={'text_prompt_tokens': 991}, input_text_tokens=991, input_tokens=991, output_tokens=107, requests=1, tool_calls=1)
```

生成されたファイルの確認:
```bash
$ cat "learning_log/LoRAの概要.txt"
LoRAは、事前学習済みの重みを固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法です。学習パラメータが少なく、アダプタとして小さなファイルサイズで保存できる特徴があります。
```

## 気づき・疑問

### 1. `pydantic-ai` の `DeferredToolRequests` の仕様調査と試行錯誤
- Human-in-the-Loop の承認処理を実装する際、当初 `result.output.approve()` を呼び出したところ `AttributeError` となり、次に `result.output.remaining` をループしようとして `TypeError: 'method' object is not iterable` や引数不足エラーに直面した。
- AIフレームワークはバージョンによるAPIの差異が大きいため、当て推量でコードを書き換えるのではなく、`dir(DeferredToolRequests)`、`inspect.signature(DeferredToolRequests.build_results)`、`__dataclass_fields__` をワンライナーで実行して実環境のオブジェクト構造を直接調査した。
- その結果、データフィールドとして `calls`, `approvals`, `metadata` を持ち、承認結果は `build_results(approve_all=True)` メソッドで生成する仕様であることが正確に分かり、確実に動作させることができた。未知のライブラリ仕様に詰まった際、Python のリフレクション機能（`inspect` 等）で一次情報を確認する重要性を実感した。

### 2. CLI実行時の「無音終了」バグの切り分けプロセス
- コード修正後、`uv run python -m app.agent` を実行してもエラーすら出ずに終了コード `0` で即座に終わってしまう現象が起きた。
- 原因を切り分けるため、① `import app.agent` で構文エラーがないことを確認、② `python -c "from app.agent import main; main()" --list-tools` で関数単体は正常に動くことを確認した。これにより「`main()` 自体は正しいがエントリポイントが呼ばれていない」と絞り込むことができ、末尾の `if __name__ == "__main__":` が `if args.trace:` のブロック内にインデントされてしまっていたミスを特定できた。

### 3. エージェントの自律的なツール連鎖と承認タイミング
- `--trace` のログを見ると、「LoRAの概要を学習記録として保存して」という1つの指示に対し、エージェントはまず `INSTRUCTIONS` のルールに従って `search_glossary({'query': 'LoRA'})` を自動実行し、用語集の正確な定義を取得した上で `save_learning_log` の引数（`content`）を組み立ててから承認要求を出していた。
- 読み取り専用の安全なツール（`search_glossary`）は承認なしで自動実行され、副作用のある書き込みツール（`save_learning_log`）の直前でのみ人間の承認（HITL）が挟まるという、実用的なエージェント制御の動きを体感できた。

### 4. 外部APIの混雑（503エラー）と例外ハンドリング
- テスト実行中に Gemini API の `503` エラー（モデル混雑）に遭遇したが、`ModelHTTPError` の例外処理によって「モデルが混み合っています（503）。少し待ってから再実行してください。」と分かりやすく表示され、再実行ですぐに成功した。LLMを組み込むシステムでは外部APIの一時的な失敗が日常的に起きるため、ユーザーに次の行動を示すエラーハンドリングやリトライ設計が不可欠だと感じた。