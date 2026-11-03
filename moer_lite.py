"""精简版启动入口；功能代码与 moer.py 共用。"""

from moer import login_interface


# 只保留需要开放的功能编号；删除不需要的编号即可屏蔽。
ENABLED_FEATURES = frozenset({
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
})


if __name__ == '__main__':
    login_interface('account.txt', enabled_features=ENABLED_FEATURES)
