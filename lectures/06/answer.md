# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：`glossary_search_glossary`、`fetch_fetch`
- STEP 2 の [tool call]：`glossary_search_glossary({'query': '3レベル'})`
- STEP 3 の [tool call]：`fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`
- STEP 4 の [tool call]：`aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要'})` / `aws_aws___search_documentation({'search_phrase': 'Using versioning in S3 buckets Amazon Simple Storage Service'})`
- 気づき・疑問：エージェント側のコードを変更しなくても、設定ファイル（`app/mcp_servers.json`）に `command` や `url` を追加するだけで、自作サーバー・公開パッケージ（`uvx`）・外部ホストのMCPサーバーをまとめて利用できる仕組みを体感できた。一方で、外部サーバーへ質問内容が送られる点や、権限・セキュリティリスクの確認が重要だと感じた。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと（変更したファイル・設定・処理、または設計した取得方法）：サーバー側の `app/mcp_server.py` の TODO 下に `server.tool()(tools.get_lecture_summary)` を1行追加して保存し、エージェント側のコード（`app/mcp_agent.py`）や設定ファイル（`app/mcp_servers.json`）は変更せずに `--list-tools` および `--trace` で動作確認を行った。
- 比較した質問と、固定した条件（モデル・対象資料など）：質問「第2回では何を学びますか?」、MCP設定 `app/mcp_servers.json`（`glossary`・`fetch`・`aws` 接続構成）、モデル `gemini-3.1-flash-lite`（503エラー発生時の切替実行）。
- 結果（変更前後の回答・根拠、`--trace`の出力、時間・トークン数・生成API推定費用など）：`--list-tools` で `glossary_get_lecture_summary` が追加表示され、`--trace` 実行時に `[tool call] glossary_get_lecture_summary({'lecture': 2})` が呼ばれて第2回の学習内容が返った（入力5,942 tokens / 出力226 tokens / モデル応答2回）。
(aie2026-exercises) @suzusawa2011 ➜ /workspaces/lecture-ai-engineering-2026 (lec06) $ uv run pytest -q
.....................                                                                                                                                     [100%]
21 passed in 6.01s
(aie2026-exercises) @suzusawa2011 ➜ /workspaces/lecture-ai-engineering-2026 (lec06) $ 
- 改善した例と、残る失敗・制約：講義回ごとの概要照会（`get_lecture_summary`）をMCPツールとして公開できたことで、第2回の学習内容の要点を根拠付きで返せるようになった。一方で、MCPサーバー数が増えると起動時や一覧取得・入力トークンが増える点や、API側の503混雑時はモデル切替や再試行が必要になる制約がある。