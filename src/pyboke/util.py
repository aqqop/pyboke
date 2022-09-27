import hashlib
import os
import shutil
from pathlib import Path

from . import model
from .model import Blog_Config_Path, CWD, Templates_Folder_Name, Articles_Folder_Path, \
    Templates_Folder_Path, Output_Folder_Path, BlogConfig, Pics_Folder_Path, RSS_Atom_XML, \
    Metadata_Folder_Path, Drafts_Folder_Path, Default_Theme_Name, Themes_Folder_Path, \
    Theme_CSS_Path, MD_Suffix
from .tmpl_render import render_blog_config, tmplfile


def dir_not_empty(path):
    return True if os.listdir(path) else False


def copy_templates():
    src_folder = Path(__file__).parent.parent.joinpath(Templates_Folder_Name)
    shutil.copytree(src_folder, Templates_Folder_Path)


def copy_static_files():
    static_files = Templates_Folder_Path.glob("*")
    for src in static_files:
        if src.is_file() and src.name not in tmplfile.values():
            dst = Output_Folder_Path.joinpath(src.name)
            print(f"Copy static file to {dst}")
            shutil.copyfile(src, dst)


def copy_theme_css(name):
    name = name.lower()
    theme_css_file = Themes_Folder_Path.joinpath(f"{name}.css")
    shutil.copyfile(theme_css_file, Theme_CSS_Path)
    print(f"Using theme: {name}")


def init_blog():
    """
    在一个空文件夹中初始化一个博客。

    :return: 发生错误时返回 err_msg: str, 没有错误则返回 False 或空字符串。
    """
    if dir_not_empty(CWD):
        return f"Folder Not Empty: {CWD}"

    Drafts_Folder_Path.mkdir()
    Articles_Folder_Path.mkdir()
    Pics_Folder_Path.mkdir()
    Metadata_Folder_Path.mkdir()
    Output_Folder_Path.mkdir()
    copy_templates()
    copy_static_files()
    copy_theme_css(Default_Theme_Name)
    render_blog_config(BlogConfig.default())
    print(f"请用文本编辑器打开 {Blog_Config_Path} 填写博客名称、作者名称等。")


def blog_file_folders_exist():
    return Drafts_Folder_Path.exists()\
        and Articles_Folder_Path.exists()\
        and Pics_Folder_Path.exists()\
        and Metadata_Folder_Path.exists()\
        and Output_Folder_Path.exists()\
        and Templates_Folder_Path.exists()\
        and Blog_Config_Path.exists()


def ensure_blog_config(check_website=False):
    """
    :return: 发生错误时返回 (err_msg, None), 没有错误则返回 (False, BlogConfig)
    """
    cfg = BlogConfig.loads()
    default_cfg = BlogConfig.default()

    cfg.name = cfg.name.strip()
    if not cfg.name or cfg.name == default_cfg.name:
        return f"请用文本编辑器打开 {Blog_Config_Path} 填写博客名称", None

    cfg.author = cfg.author.strip()
    if not cfg.author or cfg.author == default_cfg.author:
        return f"请用文本编辑器打开 {Blog_Config_Path} 填写作者名称", None

    if cfg.home_recent_max <= 0:
        return f"请用文本编辑器打开 {Blog_Config_Path} 填写 home_recent_max, 必须大于零", None

    if cfg.home_recent_max <= 0:
        return f"请用文本编辑器打开 {Blog_Config_Path} 填写 title_length_max, 必须大于零", None

    cfg.website = cfg.website.strip()
    if check_website:
        if cfg.website == "" or cfg.website == default_cfg.website:
            return f"为了生成 RSS, 请用文本编辑器打开 {Blog_Config_Path} 填写博客网址(website)", None

    changed = False

    if cfg.website and cfg.website != default_cfg.website:
        cfg.website = cfg.website.removesuffix("/") + "/"
        rss_link = cfg.website + RSS_Atom_XML
        if cfg.rss_link != rss_link:
            cfg.rss_link = rss_link
            changed = True

    cfg.uuid = cfg.uuid.strip()
    if not cfg.uuid:
        cfg.uuid = hashlib.sha1(
            (cfg.name + cfg.author + str(model.now())).encode()
        ).hexdigest()
        changed = True

    if changed:
        render_blog_config(cfg)

    return False, cfg


def check_filename(file: Path, parent_dir):
    """
    确保 filepath 只包含合法字符，后缀名为 '.md', 并确保其在 parent_dir 里。

    :return: 发生错误时返回 err_msg: str, 没有错误则返回 False 或空字符串。
    """
    if file.suffix != MD_Suffix:
        return f"后缀名不是 '{MD_Suffix}': {file}"

    if file.name.lower() in ["index.md", "years.md", "title-index.md"]:
        return f"文件名不可用 {file.name}"
    if err := model.check_filename(file.name):
        return err
    if not file.parent.samefile(parent_dir):
        return f"不在 {parent_dir.name} 文件夹内: {file}"
    return False
