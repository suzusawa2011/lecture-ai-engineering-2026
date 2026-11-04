"""第3回: Pydantic AI で作る学習支援エージェント。"""

import argparse
import inspect
import json
from pathlib import Path

from pydantic_ai import Agent, DeferredToolRequests
from pydantic_ai.exceptions import ModelHTTPError
from fastmcp import Client
from pydantic_ai.mcp import MCPToolset, StdioTransport
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.google import GoogleProvider

from app import tools
from app.config import MODEL, api_error_message, get_api_key

INSTRUCTIONS = """\
あなたはAIエンジニアリング講座（AIE2026）の学習支援エージェントです。
- 用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。
- 回の内容を聞かれたら get_lecture_summary を使う。
- 確認問題や復習問題を求められたら make_quiz を使う。回が指定されていない場合は、何回の問題か確認する。
- 学習した内容の記録や保存を求められたら save_learning_log を使う。
- 用語集に見つからないことは、推測で断定せず「用語集にはない」と伝える。
- 回答の最後に、関係する回（第N回）を示す。
- 宿題の答えそのものは書かず、考え方のヒントで導く。
"""

# 宿題（実装）：DeferredToolRequests を output_type に許容
agent = Agent(instructions=INSTRUCTIONS, output_type=[str, DeferredToolRequests])
agent.tool_plain(tools.search_glossary)
agent.tool_plain(tools.get_lecture_summary)
agent.tool_plain(tools.make_quiz)
# 宿題（実装）：承認が必要なツールとして登録
agent.tool_plain(tools.save_learning_log, requires_approval=True)

# 第5回: 使う MCP サーバーの設定ファイル
MCP_CONFIG = Path(__file__).resolve().parent / "mcp_servers.json"


def load_mcp_servers(config_path: Path = MCP_CONFIG) -> list[MCPToolset]:
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))["mcpServers"]
    toolsets = []
    for name, spec in config.items():
        if "url" in spec:
            transport = spec["url"]
        else:
            transport = StdioTransport(spec["command"], spec.get("args", []), env=spec.get("env"))
        toolsets.append(MCPToolset(Client(transport, mode="legacy")).prefixed(name))
    return toolsets


def build_mcp_agent(config_path: Path = MCP_CONFIG) -> Agent:
    return Agent(instructions=INSTRUCTIONS, toolsets=load_mcp_servers(config_path))


def build_model() -> GoogleModel:
    return GoogleModel(MODEL, provider=GoogleProvider(api_key=get_api_key()))


def print_tools(target: Agent) -> None:
    model = TestModel(call_tools=[])
    target.run_sync("ツール一覧", model=model)
    tools_seen = model.last_model_request_parameters.function_tools
    print(f"モデルに見えているツール: {len(tools_seen)} 個")
    for tool in tools_seen:
        print(f"\n[{tool.name}]")
        print("  " + inspect.cleandoc(tool.description or "").replace("\n", "\n  "))
        params = tool.parameters_json_schema.get("properties", {})
        print(f"  引数: {json.dumps(params, ensure_ascii=False)}")


def print_trace(result) -> None:
    print("\n--- trace ---")
    for message in result.all_messages():
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                print(f"[tool call]   {part.tool_name}({part.args})")
            elif isinstance(part, ToolReturnPart):
                print(f"[tool return] {part.tool_name} -> {str(part.content)[:120]}…")
    print(f"[usage] {result.usage}")


def main() -> None:
    parser = argparse.ArgumentParser(description="学習支援エージェントに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--trace", action="store_true", help="ツール呼び出しを表示する")
    parser.add_argument("--mcp", action="store_true", help="第5回: ツールを MCP サーバーから受け取る")
    parser.add_argument("--list-tools", action="store_true", help="モデルに見えるツール一覧を表示して終了する")
    args = parser.parse_args()

    target = build_mcp_agent() if args.mcp else agent
    if args.list_tools:
        print_tools(target)
        return
    if not args.question:
        parser.error("質問を指定してください")

    print(f"[model] {MODEL}")
    if args.mcp:
        print("[tools] MCP サーバー（app/mcp_servers.json）")

    model = build_model()
    try:
        result = target.run_sync(args.question, model=model)

        # 宿題（実装）：承認待ちツールのハンドリング（Human-in-the-Loop）
        while isinstance(result.output, DeferredToolRequests):
            print("\n[承認要求] 以下の操作を実行しようとしています:")
            for req in result.output.approvals:
                print(f"  - ツール名: {req.tool_name}")
                print(f"  - 引数: {req.args}")

            choice = input("この操作を実行してよろしいですか？ [y/N]: ").strip().lower()
            if choice == "y":
                # build_results(approve_all=True) で承認して処理を再開
                tool_results = result.output.build_results(approve_all=True)
                result = target.run_sync(
                    message_history=result.all_messages(),
                    model=model,
                    deferred_tool_results=tool_results,
                )
            else:
                print("操作を拒否しました。")
                break

    except ModelHTTPError as e:
        print(api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)

    print(result.output)
    if args.trace:
        print_trace(result)
        
if __name__ == "__main__":
    main()