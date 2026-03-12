"""
人社部企业年金运行数据定期下载工具
数据来源：https://www.mohrss.gov.cn/shbxjjjds/SHBXJDSzhengcewenjian/
"""

import os
import re
import time
import logging
import hashlib
import schedule
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# ──────────────────────────────────────────
# 配置区
# ──────────────────────────────────────────
BASE_URL = "https://www.mohrss.gov.cn"
LIST_URL = "https://www.mohrss.gov.cn/shbxjjjds/SHBXJDSzhengcewenjian/"
KEYWORDS = ["企业年金", "年金基金", "年金运行"]   # 匹配目标文章的关键词
DOWNLOAD_DIR = Path("mohrss_annuity_data")        # 下载目录
INTERVAL_HOURS = 24                                # 检查间隔（小时）
REQUEST_TIMEOUT = 30                               # 请求超时秒数

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("downloader.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────
def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_filename(name: str) -> str:
    """去除文件名中的非法字符"""
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


def load_downloaded_set(record_file: Path) -> set:
    if not record_file.exists():
        return set()
    return set(record_file.read_text(encoding="utf-8").splitlines())


def save_downloaded_set(record_file: Path, downloaded: set):
    record_file.write_text("\n".join(sorted(downloaded)), encoding="utf-8")


# ──────────────────────────────────────────
# 核心爬取逻辑
# ──────────────────────────────────────────
def fetch_article_links(session: requests.Session) -> list[dict]:
    """从列表页提取含关键词的文章链接"""
    try:
        resp = session.get(LIST_URL, timeout=REQUEST_TIMEOUT)
        resp.encoding = resp.apparent_encoding or "utf-8"
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error("获取列表页失败: %s", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []

    for a_tag in soup.find_all("a", href=True):
        title = a_tag.get_text(strip=True)
        if not any(kw in title for kw in KEYWORDS):
            continue
        href = a_tag["href"]
        full_url = urljoin(BASE_URL, href) if not href.startswith("http") else href
        articles.append({"title": title, "url": full_url})
        log.debug("找到文章: %s → %s", title, full_url)

    log.info("列表页共找到 %d 篇目标文章", len(articles))
    return articles


def fetch_download_links(session: requests.Session, article_url: str) -> list[dict]:
    """从文章页提取附件下载链接（PDF / Excel 等）"""
    try:
        resp = session.get(article_url, timeout=REQUEST_TIMEOUT)
        resp.encoding = resp.apparent_encoding or "utf-8"
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error("获取文章页失败 %s: %s", article_url, e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if re.search(r"\.(pdf|xls|xlsx|doc|docx|zip)$", href, re.I):
            full_url = urljoin(article_url, href)
            label = a_tag.get_text(strip=True) or Path(urlparse(href).path).name
            links.append({"label": label, "url": full_url})

    return links


def download_file(session: requests.Session, url: str, dest_dir: Path, label: str) -> Path | None:
    """下载单个文件，返回保存路径；跳过已存在且内容相同的文件"""
    ext = Path(urlparse(url).path).suffix or ".pdf"
    filename = safe_filename(label) + ext
    dest = dest_dir / filename

    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT, stream=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error("下载失败 %s: %s", url, e)
        return None

    # 写入临时文件，对比 MD5 后决定是否替换
    tmp = dest.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)

    if dest.exists() and file_md5(dest) == file_md5(tmp):
        tmp.unlink()
        log.info("文件未变化，跳过: %s", filename)
        return dest

    tmp.rename(dest)
    log.info("已保存: %s", dest)
    return dest


# ──────────────────────────────────────────
# 主任务
# ──────────────────────────────────────────
def run_download_task():
    log.info("========== 开始检查人社部年金数据 ==========")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    record_file = DOWNLOAD_DIR / ".downloaded_urls.txt"
    downloaded = load_downloaded_set(record_file)

    session = make_session()
    articles = fetch_article_links(session)
    new_files = 0

    for article in articles:
        if article["url"] in downloaded:
            log.debug("已处理过，跳过: %s", article["title"])
            continue

        log.info("处理文章: %s", article["title"])
        # 按文章标题建子目录
        sub_dir = DOWNLOAD_DIR / safe_filename(article["title"])
        sub_dir.mkdir(parents=True, exist_ok=True)

        dl_links = fetch_download_links(session, article["url"])
        if not dl_links:
            log.warning("  未找到附件，页面可能需要登录或结构不同: %s", article["url"])
        for link in dl_links:
            path = download_file(session, link["url"], sub_dir, link["label"])
            if path:
                new_files += 1

        downloaded.add(article["url"])
        time.sleep(1)  # 礼貌性等待，避免请求过于密集

    save_downloaded_set(record_file, downloaded)
    log.info("本次任务完成，新下载文件 %d 个", new_files)
    log.info("下次检查时间: %s 小时后", INTERVAL_HOURS)


# ──────────────────────────────────────────
# 入口
# ──────────────────────────────────────────
if __name__ == "__main__":
    log.info("启动人社部年金数据定时下载器（间隔 %d 小时）", INTERVAL_HOURS)

    # 首次立即运行
    run_download_task()

    # 注册定时任务
    schedule.every(INTERVAL_HOURS).hours.do(run_download_task)

    while True:
        schedule.run_pending()
        time.sleep(60)
