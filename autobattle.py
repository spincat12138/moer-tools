import hashlib
import logging
import os
import time

from moer import battle, get_account, get_battle_wait_defaults, login_taomi


# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def _read_config_from_env():
    """读取 Docker 配置；返回 None 表示未配置任何环境变量。"""
    # MOER_* 是推荐写法，UID/PWD/POSITION 仅作为兼容别名。
    uid_raw = os.getenv('MOER_UID') or os.getenv('UID')
    pwd_raw = os.getenv('MOER_PWD') or os.getenv('PWD')
    position_raw = os.getenv('MOER_POSITION') or os.getenv('POSITION')

    values = (uid_raw, pwd_raw, position_raw)
    if not any(value is not None for value in values):
        return None

    missing = [name for name, value in zip(('MOER_UID', 'MOER_PWD', 'MOER_POSITION'), values)
               if not value]
    if missing:
        raise ValueError('环境变量配置不完整，缺少: %s' % ', '.join(missing))

    try:
        uid = int(uid_raw)
        position = int(position_raw)
    except ValueError as exc:
        raise ValueError('MOER_UID 和 MOER_POSITION 必须是整数') from exc

    if uid < 0:
        raise ValueError('MOER_UID 不能为负数')
    if position not in (1, 2, 3, 4, 5, 6, 7):
        raise ValueError('MOER_POSITION 必须是 1、2、3 或 4')

    # 与 get_account() 保持一致：环境变量中的密码填写明文。
    pwd_md5 = hashlib.md5(pwd_raw.encode('utf-8')).hexdigest()
    return uid, pwd_md5, position


def _read_account_config():
    """兼容未配置环境变量时的旧 account.txt 方式。"""
    try:
        accounts = get_account()
    except Exception as exc:
        raise ValueError(f'读取账号文件失败: {exc}') from exc
    if not accounts:
        raise ValueError('没有可用账号，请检查 account.txt')

    uid_str = next(iter(accounts))
    return int(uid_str), accounts[uid_str], 4


def run_battle():
    try:
        config = _read_config_from_env() or _read_account_config()
    except (ValueError, OSError) as exc:
        logging.error(str(exc))
        return

    uid, pwd_md5, position = config

    # model=1、fwq=0 表示经典模式并随机选择服务器。
    login_result = login_taomi(uid, pwd_md5, model=1, fwq=0)
    if not login_result:
        logging.error(f"账号 {uid} 登录失败")
        return

    s, s2, str2 = login_result
    turn_wait, end_wait = get_battle_wait_defaults(position)
    battle(s2, str2, position=position, turn_wait=turn_wait, end_wait=end_wait, login_socket=s,
           reconnect_uid=uid, reconnect_pwd=pwd_md5)


if __name__ == '__main__':
    while True:
        try:
            logging.info("服务启动中...")
            run_battle()
        except Exception as e:
            logging.warning(f"发生致命错误，5秒后重启: {e}")
            time.sleep(5)
