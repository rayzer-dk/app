from playwright.sync_api import sync_playwright, expect
import time, urllib.request
url='http://127.0.0.1:8765/'
for _ in range(50):
    try:
        with urllib.request.urlopen(url,timeout=2) as response:
            if response.status==200: break
    except OSError:
        time.sleep(.2)
else:
    raise RuntimeError('Local HTTP server did not start')
with sync_playwright() as playwright:
    browser=playwright.chromium.launch()
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(url)
    expect(page.locator('.hero')).to_be_visible()
    page.wait_for_function('!!navigator.serviceWorker.controller',timeout=90000)
    expect(page.locator('.az-install small')).to_contain_text('готовы',timeout=90000)
    page.locator('[data-action="nav"][data-to="math"]:visible').first.click()
    page.locator('[data-action="open-lesson"][data-id="m-count-2"]:visible').first.click()
    expect(page.locator('.az-apple')).to_have_count(3)
    apple=page.locator('.az-apple').first
    apple.click()
    expect(page.locator('.az-count output')).to_have_text('1 / 3')
    apple.click()
    expect(page.locator('.az-count output')).to_have_text('1 / 3')
    page.locator('[data-action="count-reset"]').click()
    expect(page.locator('.az-count output')).to_have_text('0 / 3')
    page.locator('[data-action="nav"][data-to="home"]:visible').first.click()
    page.locator('[data-action="nav"][data-to="write"]:visible').first.click()
    page.locator('[data-action="writing-open"]:visible').first.click()
    expect(page.locator('.writing-board')).to_be_visible()
    page.locator('[data-action="writing-trace"]').click()
    expect(page.locator('.writing-board.is-drawable')).to_be_visible()
    page.locator('[data-action="nav"][data-to="home"]:visible').first.click()
    context.set_offline(True)
    page.reload()
    expect(page.locator('.hero')).to_be_visible()
    for width in [320,390,768,1280]:
        page.set_viewport_size({'width':width,'height':900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), f'Horizontal overflow at {width}px'
    assert not errors,errors
    context.close()
    browser.close()
print('PASS: browser shell, service worker, count, writing and offline reload')
