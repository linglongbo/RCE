# 定义MD5函数
import hashlib


def get_md5(url):
    """
    :param url: 图片的url
    """
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()  # 抽取m的钥


if __name__ == '__main__':
    print(get_md5('http://www.baidu.com'.encode("utf-8")))  # 报错Unicode-objects must be encoded before hashing：【x.encode(utf8)】
