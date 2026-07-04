"""DOM 结构提取与截断.

D014: 通过 page.evaluate() 执行 JS 从 DOM 提取 role/name/children,
深度 ≤ 4, 元素数 ≤ max_elements.
"""

from typing import List
from typing import Tuple

from playwright.sync_api import Page


_JS_EXTRACT = """
({maxDepth, maxElements}) => {
  const elements = [];
  let count = 0;
  let truncated = false;

  function getRole(el) {
    const ariaRole = el.getAttribute('role');
    if (ariaRole) return ariaRole;
    return el.tagName.toLowerCase();
  }

  function getName(el) {
    const ariaLabel = el.getAttribute('aria-label');
    if (ariaLabel) return ariaLabel.substring(0, 50);
    const text = (el.textContent || '').trim().substring(0, 50);
    return text;
  }

  function walk(el, depth) {
    if (truncated) return null;
    if (depth > maxDepth) return null;

    count++;
    if (count > maxElements) {
      truncated = true;
      return null;
    }

    const elem = {
      role: getRole(el),
      name: getName(el),
    };

    const children = [];
    for (const child of el.children) {
      if (truncated) break;
      const childElem = walk(child, depth + 1);
      if (childElem !== null) {
        children.push(childElem);
      }
    }
    if (children.length > 0) {
      elem.children = children;
    }

    return elem;
  }

  if (document.body) {
    for (const child of document.body.children) {
      if (truncated) break;
      const childElem = walk(child, 1);
      if (childElem !== null) {
        elements.push(childElem);
      }
    }
  }

  return { elements, truncated };
}
"""


def extract_structure(
    page: Page,
    max_depth: int = 4,
    max_elements: int = 500,
) -> Tuple[List[dict], bool]:
    """通过 page.evaluate() 执行 JS 从 DOM 提取页面结构.

    Args:
        page: Playwright Page 对象.
        max_depth: 最大嵌套深度, 默认 4.
        max_elements: 最大元素总数, 超出时截断并标记 truncated.

    Returns:
        (elements, truncated) 元组.
        elements 为 List[dict], 每个元素含 role, name, 可能含 children.
        truncated 为 True 表示触发了元素数截断.
    """
    result = page.evaluate(
        _JS_EXTRACT,
        {"maxDepth": max_depth, "maxElements": max_elements},
    )
    return result["elements"], result["truncated"]
