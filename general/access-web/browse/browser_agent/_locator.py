"""三级回退元素定位策略.

D010: accessible name → 文本内容 → CSS selector
"""

from typing import Optional
from typing import Tuple

from playwright.sync_api import Locator
from playwright.sync_api import Page


def locate(page: Page, description: str) -> Tuple[Optional[Locator], Optional[str]]:
    """按三级回退策略定位元素.

    Args:
        page: Playwright Page 对象.
        description: agent 传入的语义描述 (如 "submit button", "search box").

    Returns:
        (locator, strategy) 元组. locator 为 None 表示全部策略未命中
        (含空 description).
        strategy 为命中所用策略标签 (如 "role=button,name=submit").
    """
    if not description or not description.strip():
        return None, None

    # 提取潜在名称: 去除常见 role 后缀词
    role_suffixes = [
        " button", " link", " input", " box", " field",
        " checkbox", " radio", " menu", " dropdown", " select",
        " textarea", " toggle", " icon", " image", " img",
    ]
    names = [description]
    lower_desc = description.lower()
    for suffix in role_suffixes:
        if lower_desc.endswith(suffix):
            stripped = description[: -len(suffix)].strip()
            if stripped:
                names.append(stripped)

    common_roles = [
        "button", "link", "textbox", "checkbox", "radio",
        "combobox", "menuitem", "option", "tab", "heading",
        "listitem", "img", "navigation", "banner", "main", "region",
    ]

    # ---- Level 1: accessible name ----

    # 1a: get_by_role
    for role in common_roles:
        for name in names:
            loc = _try_get_by_role(page, role, name)
            if loc is not None:
                return loc, f"role={role},name={name}"

    # 1b: get_by_label (aria-label / <label>)
    for name in names:
        loc = _try_get_by_label(page, name)
        if loc is not None:
            return loc, f"label={name}"

    # 1c: get_by_placeholder
    for name in names:
        loc = _try_get_by_placeholder(page, name)
        if loc is not None:
            return loc, f"placeholder={name}"

    # ---- Level 2: text content ----
    for name in names:
        loc = _try_get_by_text(page, name)
        if loc is not None:
            return loc, f"text={name}"

    # ---- Level 3: CSS selector ----
    loc = _try_css(page, description)
    if loc is not None:
        return loc, f"css={description}"

    return None, None


def _try_get_by_role(page: Page, role: str, name: str) -> Optional[Locator]:
    try:
        loc = page.get_by_role(role, name=name)
        if loc.count() > 0:
            return loc.first
    except Exception:
        pass
    return None


def _try_get_by_label(page: Page, name: str) -> Optional[Locator]:
    try:
        loc = page.get_by_label(name)
        if loc.count() > 0:
            return loc.first
    except Exception:
        pass
    return None


def _try_get_by_placeholder(page: Page, name: str) -> Optional[Locator]:
    try:
        loc = page.get_by_placeholder(name)
        if loc.count() > 0:
            return loc.first
    except Exception:
        pass
    return None


def _try_get_by_text(page: Page, name: str) -> Optional[Locator]:
    try:
        loc = page.get_by_text(name)
        if loc.count() > 0:
            return loc.first
    except Exception:
        pass
    return None


def _try_css(page: Page, selector: str) -> Optional[Locator]:
    try:
        loc = page.locator(selector)
        if loc.count() > 0:
            return loc.first
    except Exception:
        pass
    return None
