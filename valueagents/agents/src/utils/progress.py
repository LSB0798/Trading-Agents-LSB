from datetime import datetime, timezone
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.style import Style
from rich.text import Text
from typing import Dict, Optional, Callable, List

console = Console()


class AgentProgress:
    """Manages progress tracking for multiple agents."""

    def __init__(self):
        print(' -class AgentProgress: def __init__(self):- ')
        self.agent_status: Dict[str, Dict[str, str]] = {}
        self.table = Table(show_header=False, box=None, padding=(0, 1))
        self.live = Live(self.table, console=console, refresh_per_second=4)
        self.started = False
        self.update_handlers: List[Callable[[str, Optional[str], str], None]] = []

    def register_handler(self, handler: Callable[[str, Optional[str], str], None]):
        print(' -class AgentProgress: def register_handler(self):- ')
        """Register a handler to be called when agent status updates."""
        self.update_handlers.append(handler)
        return handler  # Return handler to support use as decorator

    def unregister_handler(self, handler: Callable[[str, Optional[str], str], None]):
        print(' -class AgentProgress: def unregister_handler(self):- ')
        """Unregister a previously registered handler."""
        if handler in self.update_handlers:
            self.update_handlers.remove(handler)

    def start(self):
        print(' -class AgentProgress: def start(self):- ')
        """Start the progress display."""
        print('self.started : {}'.format(self.started))
        if not self.started:
            self.live.start()
            self.started = True

    def stop(self):
        print(' -class AgentProgress: def stop(self):- ')
        """Stop the progress display."""
        if self.started:
            self.live.stop()
            self.started = False

    def update_status(self, agent_name: str, ticker: Optional[str] = None, status: str = "", analysis: Optional[str] = None):
        """
        作用：更新某个 Agent 的状态信息。
        做的事情：
            将传入的 agent_name、ticker、status、analysis 存储到内部的 self.agent_status 字典中。
            记录当前时间戳（UTC）。
            通知所有已注册的回调处理器（self.update_handlers）。
            调用 _refresh_display() 刷新终端表格。
        你看到的多次调用：说明工作流中有多个 Agent（如 Ben Graham、Warren Buffett 等）在并行执行，每个 Agent 在执行的不同阶段（开始、进行中、完成）都会调用 update_status，因此日志中反复出现该方法。"""
        # print(' -class AgentProgress: def update_status(self):- ')
        """Update the status of an agent."""
        if agent_name not in self.agent_status:
            self.agent_status[agent_name] = {"status": "", "ticker": None}

        if ticker:
            self.agent_status[agent_name]["ticker"] = ticker
        if status:
            self.agent_status[agent_name]["status"] = status
        if analysis:
            self.agent_status[agent_name]["analysis"] = analysis
        
        # Set the timestamp as UTC datetime
        timestamp = datetime.now(timezone.utc).isoformat()
        self.agent_status[agent_name]["timestamp"] = timestamp

        # Notify all registered handlers
        for handler in self.update_handlers:
            handler(agent_name, ticker, status, analysis, timestamp)

        self._refresh_display()

    def get_all_status(self):
        print(' -class AgentProgress: def get_all_status(self):- ')
        """Get the current status of all agents as a dictionary."""
        return {agent_name: {"ticker": info["ticker"], "status": info["status"], "display_name": self._get_display_name(agent_name)} for agent_name, info in self.agent_status.items()}

    def _get_display_name(self, agent_name: str) -> str:
        """
        作用：将 Agent 的内部名称（例如 "ben_graham_agent"）转换为用户友好的显示名称（例如 "Ben Graham"）。
        做的事情：
            移除 "_agent" 后缀，将下划线替换为空格，然后调用 .title() 将每个单词首字母大写。
            例如："risk_management_agent" → "Risk Management"。
        你看到的多次调用：在 _refresh_display 中，为每个 Agent 生成显示名称时会调用该方法；由于表格每刷新一次就要为所有 Agent 重新生成显示名称，所以日志中会出现多次（尤其是当多个 Agent 状态更新引起多次刷新时）。"""
        # print(' -class AgentProgress: def _get_display_name(self):- ')
        """Convert agent_name to a display-friendly format."""
        return agent_name.replace("_agent", "").replace("_", " ").title()

    def _refresh_display(self):
        """
        作用：重新构建并刷新终端中的进度表格。
        做的事情：
            清空当前表格的所有列。
            根据 self.agent_status 中保存的最新状态，重新生成每一行（每个 Agent 一行）。
            根据状态（"done"、"error"、其他）设置不同的颜色和符号（✓、✗、⋯）。
            调用 self.live.update(self.table) 更新终端显示。
        你看到的多次调用：每当任何 Agent 状态变化（update_status 被调用），就会触发一次 _refresh_display，确保表格实时反映最新进度。 """
        # print(' -class AgentProgress: def _refresh_display(self):- ')
        """Refresh the progress display."""
        self.table.columns.clear()
        self.table.add_column(width=100)

        # Sort agents with Risk Management and Portfolio Management at the bottom
        def sort_key(item):
            agent_name = item[0]
            if "risk_management" in agent_name:
                return (2, agent_name)
            elif "portfolio_management" in agent_name:
                return (3, agent_name)
            else:
                return (1, agent_name)

        for agent_name, info in sorted(self.agent_status.items(), key=sort_key):
            status = info["status"]
            ticker = info["ticker"]
            # Create the status text with appropriate styling
            if status.lower() == "done":
                style = Style(color="green", bold=True)
                symbol = "✓"
            elif status.lower() == "error":
                style = Style(color="red", bold=True)
                symbol = "✗"
            else:
                style = Style(color="yellow")
                symbol = "⋯"

            agent_display = self._get_display_name(agent_name)
            status_text = Text()
            status_text.append(f"{symbol} ", style=style)
            status_text.append(f"{agent_display:<20}", style=Style(bold=True))

            if ticker:
                status_text.append(f"[{ticker}] ", style=Style(color="cyan"))
            status_text.append(status, style=style)

            self.table.add_row(status_text)


# Create a global instance
progress = AgentProgress() # 初始化
