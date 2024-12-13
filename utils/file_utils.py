import asyncio
import aiofiles
from pathlib import Path
from aiocsv import AsyncWriter
from models import ModuleType, OperationResult, StatisticData


class FileOperations:
    def __init__(self, base_path: str = "./results"):
        self.base_path = Path(base_path)
        self.lock = asyncio.Lock()
        self.module_paths: dict[ModuleType, dict[str, Path]] = {
            "register": {
                "success": self.base_path / "注册成功.txt",
                "failed": self.base_path / "注册失败.txt",
            },
            "tasks": {
                "success": self.base_path / "任务成功.txt",
                "failed": self.base_path / "任务失败.txt",
            },
            "stats": {
                "base": self.base_path / "账户统计.csv",
            },
            "accounts": {
                "unverified": self.base_path / "未验证账户.txt",
                "banned": self.base_path / "被封禁账户.txt",
            },
            "re-verify": {
                "success": self.base_path / "重新验证成功.txt",
                "failed": self.base_path / "重新验证失败.txt",
            }
        }

    async def setup_files(self):
        self.base_path.mkdir(exist_ok=True)
        for module_paths in self.module_paths.values():
            for path in module_paths.values():
                path.touch(exist_ok=True)

        async with aiofiles.open(self.module_paths["stats"]["base"], "w", encoding="utf-8") as f:
            writer = AsyncWriter(f)
            await writer.writerow(
                [
                    "邮箱",
                    "推荐码",
                    "积分",
                    "推荐积分",
                    "总积分",
                    "注册日期",
                    "完成任务",
                ]
            )

    async def export_result(self, result: OperationResult, module: ModuleType):
        if module not in self.module_paths:
            raise ValueError("未知模块: {}".format(module))

        file_path = self.module_paths[module][
            "success" if result["status"] else "failed"
        ]
        async with self.lock:
            try:
                async with aiofiles.open(file_path, "a", encoding="utf-8") as file:
                    await file.write(f"{result['identifier']}:{result['data']}\n")
            except IOError as e:
                print(f"写入文件时出错: {e}")

    async def export_unverified_email(self, email: str, password: str):
        file_path = self.module_paths["accounts"]["unverified"]
        async with self.lock:
            try:
                async with aiofiles.open(file_path, "a", encoding="utf-8") as file:
                    await file.write(f"{email}:{password}\n")
            except IOError as e:
                print(f"写入文件时出错: {e}")

    async def export_banned_email(self, email: str, password: str):
        file_path = self.module_paths["accounts"]["banned"]
        async with self.lock:
            try:
                async with aiofiles.open(file_path, "a", encoding="utf-8") as file:
                    await file.write(f"{email}:{password}\n")
            except IOError as e:
                print(f"写入文件时出错: {e}")

    async def export_stats(self, data: StatisticData):
        file_path = self.module_paths["stats"]["base"]
        async with self.lock:
            try:
                async with aiofiles.open(file_path, mode="a", newline="", encoding="utf-8") as f:
                    writer = AsyncWriter(f)

                    if not data or not data["referralPoint"] or not data["rewardPoint"]:
                        return

                    await writer.writerow(
                        [
                            data["referralPoint"]["email"],
                            data["referralPoint"]["referralCode"],
                            data["rewardPoint"]["points"],
                            data["referralPoint"]["commission"],
                            float(data["rewardPoint"]["points"])
                            + float(data["referralPoint"]["commission"]),
                            data["rewardPoint"]["registerpointsdate"],
                            (
                                True
                                if data["rewardPoint"]["twitter_x_id_points"] == 5000
                                and data["rewardPoint"]["discordid_points"] == 5000
                                and data["rewardPoint"]["telegramid_points"] == 5000
                                else False
                            ),
                        ]
                    )

            except IOError as e:
                print(f"写入文件时出错: {e}")
