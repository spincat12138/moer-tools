import logging
import random
import struct
import time

from moer import clearbag, get_account, getname, getpetlist, login_taomi


# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def battle_loop(s2, str2):
    """海滩刷怪逻辑。战斗专用协议仍保留在本模块。"""
    battle_times = 0
    battle_load_wait = 0.1
    skill_time = 8

    a, i = getpetlist(s2, str2)
    pet_flag = False
    for x in range(i):
        if a[x][67] == 3:
            pet_id = a[x][0:4]
            pet_flag = True
            print(f"找到主战宠物{getname(a[x][13:31])}")
    if not pet_flag:
        pet_id = [0, 0, 0, 0]
        print("没有主战宠物！")

    while True:
        # 1. 传送至新生巨石蟹
        packet = [0, 0, 0, 0x26, 3, 0xec, *str2, 0, 0, random.randint(5, 6),
                  random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0x75, 0xfb, 0,
                  0, 0, 0, 0, 0, 0, 0x8b, 0, 0, 0x01, 0x5d, 0, 0, 0, 0]
        s2.send(struct.pack('38B', *packet))
        time.sleep(0.1)

        # 2. 刷明雷战斗
        packet = [0, 0, 0, 0x1a, 0x05, 0x18, *str2, 0, 0, random.randint(5, 6),
                  random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0x09, 0xc8, 0, 0, 0, 0]
        s2.send(struct.pack('26B', *packet))
        time.sleep(0.1)

        # 3. 进入战斗读秒（0-100）
        for battle_load_percent in range(5, 101, 5):
            packet = [0, 0, 0, 22, 5, 26, *str2, 0, 0, random.randint(5, 6),
                      random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, battle_load_percent]
            s2.send(struct.pack('22B', *packet))
            time.sleep(battle_load_wait)

        # 进入战斗
        packet = [0, 0, 0, 22, 5, 37, *str2, 0, 0, 6, random.randint(0, 255),
                  0, 0, 0, 0, 0, 0, 0, 1]
        s2.send(struct.pack('22B', *packet))
        time.sleep(0.1)

        # 自动释放技能
        for _ in range(skill_time):
            # 人物自动攻击
            packet = [0, 0, 0, 38, 5, 28, *str2, 0, 0, 6, random.randint(0, 255),
                      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 255, 255, 255,
                      0, 15, 66, 64, 0, 0, 0, 1]
            s2.send(struct.pack('38B', *packet))
            time.sleep(0.05)

            # 宠物自动攻击
            packet = [0, 0, 0, 38, 5, 28, *str2, 0, 0, 6, random.randint(0, 255),
                      0, 0, 0, 0, *pet_id, 0, 0, 0, 0, 255, 255, 255, 255,
                      0, 15, 66, 64, 0, 0, 0, 1]
            s2.send(struct.pack('38B', *packet))
            time.sleep(0.05)

        # 结束战斗（1a0406）
        packet = [0, 0, 0, 26, 4, 6, *str2, 0, 0, 6, random.randint(0, 255),
                  0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1]
        s2.send(struct.pack('26B', *packet))
        time.sleep(0.1)

        # 星豆治疗
        packet = [0, 0, 0, 22, 4, 1, *str2, 0, 0, 5, random.randint(0, 255),
                  0, 0, 0, 0, 0, 0, 0, 5]
        s2.send(struct.pack('22B', *packet))

        battle_times += 1
        if battle_times % 10 == 0:
            clearbag(s2, str2)
        logging.info(f"成功完成第 {battle_times} 次战斗")
        time.sleep(0.5)


def run_bot():
    try:
        # 账号解析、登录和背包清理统一复用 moer.py 实现。
        accounts = get_account()
    except Exception as exc:
        logging.error(f"读取账号文件失败: {exc}")
        return
    if not accounts:
        logging.error("没有可用账号，请检查 account.txt")
        return

    uid_str = next(iter(accounts))
    pwd_md5 = accounts[uid_str]

    # model=1、fwq=0 表示经典模式并随机选择服务器。
    login_result = login_taomi(int(uid_str), pwd_md5, model=1, fwq=0)
    if not login_result:
        logging.error(f"账号 {uid_str} 登录失败")
        return

    s, s2, str2 = login_result
    try:
        battle_loop(s2, str2)
    finally:
        s.close()
        s2.close()


if __name__ == '__main__':
    while True:
        try:
            logging.info("服务启动中...")
            run_bot()
        except Exception as e:
            logging.warning(f"发生致命错误，5秒后重启: {e}")
            time.sleep(5)
