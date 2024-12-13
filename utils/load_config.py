import os
import yaml
from itertools import cycle
from loguru import logger
from models import Config, Account
from better_proxy import Proxy
from typing import List, Dict, Generator

CONFIG_PATH = os.path.join(os.getcwd(), "config")
CONFIG_DATA_PATH = os.path.join(CONFIG_PATH, "data")
CONFIG_PARAMS = os.path.join(CONFIG_PATH, "settings.yaml")

REQUIRED_DATA_FILES = ("accounts.txt", "proxies.txt")
REQUIRED_PARAMS_FIELDS = (
    "threads",
    "keepalive_interval",
    "imap_settings",
    "captcha_module",
    "delay_before_start",
    "referral_codes",
    "redirect_settings",
    "two_captcha_api_key",
    "anti_captcha_api_key",
)


def read_file(file_path: str,
              check_empty: bool = True,
              is_yaml: bool = False) -> List[str] | Dict:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件未找到: {file_path}")

    if check_empty and os.stat(file_path).st_size == 0:
        raise ValueError(f"文件为空: {file_path}")

    if is_yaml:
        with open(file_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    with open(file_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]


def get_params() -> Dict:
    data = read_file(CONFIG_PARAMS, is_yaml=True)
    missing_fields = set(REQUIRED_PARAMS_FIELDS) - set(data.keys())
    if missing_fields:
        raise ValueError(f"配置文件中缺少字段: {', '.join(missing_fields)}")
    return data


def get_proxies() -> List[Proxy]:
    try:
        proxies = read_file(os.path.join(CONFIG_DATA_PATH, "proxies.txt"),
                            check_empty=False)
        return [Proxy.from_str(line) for line in proxies] if proxies else []
    except Exception as exc:
        raise ValueError(f"代理解析失败: {exc}")


def generate_appid():
    import os
    random_bytes = os.urandom(12)
    return random_bytes.hex()


def get_accounts(
        file_name: str,
        redirect_mode: bool = False) -> Generator[Account, None, None]:
    try:
        proxies = get_proxies()
        proxy_cycle = cycle(proxies) if proxies else None
        accounts = read_file(os.path.join(CONFIG_DATA_PATH, file_name),
                             check_empty=False)

        for account in accounts:
            try:
                if not account.strip():
                    continue

                if redirect_mode:
                    splits = account.split(":", 1)
                    if len(splits) == 2:
                        email, password = splits
                        yield Account(
                            email=email.strip(),
                            password=password.strip(),
                            proxy=next(proxy_cycle) if proxy_cycle else None)
                    else:
                        yield Account(
                            email=account.strip(),
                            proxy=next(proxy_cycle) if proxy_cycle else None)
                else:
                    splits = account.split(":", 2)
                    if len(splits) < 2:
                        raise ValueError(f"账户格式无效: {account}")

                    email, password = splits[0], splits[1]
                    if len(splits) == 2:
                        appid = generate_appid()
                        logger.info(
                            f"Account: {email} | Generate appid : {appid}")
                    else:
                        appid = splits[2]
                        logger.info(f"Account: {email} | Load appid : {appid}")
                    yield Account(
                        email=email.strip(),
                        password=password.strip(),
                        proxy=next(proxy_cycle) if proxy_cycle else None,
                        app_id=appid,
                    )

            except Exception as e:
                if not redirect_mode:
                    raise ValueError(f"账户解析失败: {account}. 错误: {str(e)}")

    except Exception as e:
        raise ValueError(f"处理账户文件失败: {str(e)}")


def validate_domains(accounts: List[Account],
                     domains: Dict[str, str]) -> List[Account]:
    for account in accounts:
        domain = account.email.split("@")[1]
        if domain not in domains:
            raise ValueError(f"不支持的域名 '{domain}'，请在配置文件中添加")
        account.imap_server = domains[domain]
    return accounts


def get_app_id() -> str:
    import argparse
    parser = argparse.ArgumentParser(description="Input variables")
    parser.add_argument('--appid', type=str, default='', help="dawn appid")

    args = parser.parse_args()
    return args.appid


def load_config() -> Config:
    try:
        params = get_params()

        reg_accounts = list(
            get_accounts("register.txt",
                         redirect_mode=params["redirect_settings"]["enabled"]))
        farm_accounts = list(get_accounts("farm.txt"))
        reverify_accounts = list(get_accounts("reverify.txt"))

        if not reg_accounts and not farm_accounts and not reverify_accounts:
            raise ValueError("在数据文件中未找到账户")

        config = Config(**params,
                        accounts_to_farm=farm_accounts,
                        accounts_to_register=reg_accounts,
                        accounts_to_reverify=reverify_accounts)

        if config.redirect_settings.enabled and not config.redirect_settings.email and not config.redirect_settings.password and not config.redirect_settings.imap_server:
            raise ValueError("缺少重定向邮箱或密码或IMAP服务器")

        if reg_accounts:
            config.accounts_to_register = validate_domains(
                reg_accounts, config.imap_settings)

        if reverify_accounts:
            config.accounts_to_reverify = validate_domains(
                reverify_accounts, config.imap_settings)

        if config.captcha_module == "2captcha" and not config.two_captcha_api_key:
            raise ValueError("缺少2Captcha API密钥")
        elif config.captcha_module == "anticaptcha" and not config.anti_captcha_api_key:
            raise ValueError("缺少AntiCaptcha API密钥")

        return config

    except Exception as exc:
        logger.error(f"加载配置失败: {exc}")
        exit(1)
