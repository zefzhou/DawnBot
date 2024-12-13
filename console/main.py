import os
import sys
import inquirer

from inquirer.themes import GreenPassion
from art import text2art
from colorama import Fore
from loader import config

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

sys.path.append(os.path.realpath("."))


class Console:
    MODULES = (
        "注册",
        "农业",
        "任务",
        "重新验证账户",
        "导出统计",
        "退出",
    )
    MODULES_DATA = {
        "注册": "register",
        "农业": "farm",
        "退出": "exit",
        "导出统计": "export_stats",
        "任务": "complete_tasks",
        "重新验证账户": "re_verify_accounts",
    }

    def __init__(self):
        self.rich_console = RichConsole()

    def show_dev_info(self):
        os.system("cls" if os.name == "nt" else "clear")

        title = text2art("JamBit", font="small")
        styled_title = Text(title, style="bold cyan")

        version = Text("版本: 1.6", style="blue")
        telegram = Text("我的频道: https://t.me/xuegaoz", style="green")
        github = Text("原作者GitHub: https://github.com/Jaammerr", style="green")

        dev_panel = Panel(
            Text.assemble(styled_title, "\n", version, "\n", telegram, "\n", github),
            border_style="yellow",
            expand=False,
            title="[bold green]欢迎[/bold green]",
            subtitle="[italic]由Jammer提供支持 雪糕战神@Hy78516012汉化[/italic]",
        )

        self.rich_console.print(dev_panel)
        print()

    @staticmethod
    def prompt(data: list):
        answers = inquirer.prompt(data, theme=GreenPassion())
        return answers

    def get_module(self):
        questions = [
            inquirer.List(
                "module",
                message=Fore.LIGHTBLACK_EX + "选择模块",
                choices=self.MODULES,
            ),
        ]

        answers = self.prompt(questions)
        return answers.get("module")

    def display_info(self):
        table = Table(title="Dawn 配置", box=box.ROUNDED)
        table.add_column("参数", style="cyan")
        table.add_column("值", style="magenta")

        if config.redirect_settings.enabled:
            table.add_row("重定向模式", "已启用")
            table.add_row("重定向邮箱", config.redirect_settings.email)

        table.add_row("等待注册的账户", str(len(config.accounts_to_register)))
        table.add_row("等待农业的账户", str(len(config.accounts_to_farm)))
        table.add_row("等待重新验证的账户", str(len(config.accounts_to_reverify)))
        table.add_row("线程", str(config.threads))
        table.add_row(
            "开始前的延迟",
            f"{config.delay_before_start.min} - {config.delay_before_start.max} 秒",
        )

        panel = Panel(
            table,
            expand=False,
            border_style="green",
            title="[bold yellow]系统信息[/bold yellow]",
            subtitle="[italic]使用箭头键导航[/italic]",
        )
        self.rich_console.print(panel)

    def build(self) -> None:
        self.show_dev_info()
        self.display_info()

        module = self.get_module()
        config.module = self.MODULES_DATA[module]

        if config.module == "exit":
            exit(0)
