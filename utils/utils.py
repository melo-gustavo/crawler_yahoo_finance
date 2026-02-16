def detect_browser(browser: str) -> str:
    browser_lower = browser.lower()

    if "edg/" in browser_lower:
        return "Edge"
    if "opr/" in browser_lower or "opera" in browser_lower:
        return "Opera"
    if "chrome/" in browser_lower and "chromium" not in browser_lower:
        return "Chrome"
    if "firefox/" in browser_lower:
        return "Firefox"
    if "safari/" in browser_lower and "chrome/" not in browser_lower:
        return "Safari"

    return "Unknown"
