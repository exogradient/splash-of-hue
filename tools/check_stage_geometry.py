#!/usr/bin/env python3
"""Rendered browser contract for Splash of Hue stage and navigation behavior."""

from __future__ import annotations

import contextlib
import socket
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import Page, sync_playwright


MODES = ("play", "match", "picture", "call", "split")
VIEWPORTS = ((1440, 1000), (596, 1137), (573, 1137), (390, 844))


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(url: str) -> None:
    for _ in range(80):
        try:
            with urllib.request.urlopen(url, timeout=0.25) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError(f"Server did not become ready at {url}")


def rect(page: Page, selector: str) -> dict[str, float]:
    value = page.locator(selector).evaluate(
        """el => { const r = el.getBoundingClientRect();
        return {x:r.x, y:r.y, width:r.width, height:r.height}; }"""
    )
    return {key: round(float(number), 3) for key, number in value.items()}


def assert_close(first: dict[str, float], second: dict[str, float], label: str) -> None:
    for key in ("x", "y", "width", "height"):
        if abs(first[key] - second[key]) > 0.75:
            raise AssertionError(f"{label}: {key} changed from {first[key]} to {second[key]}")


def center_y(box: dict[str, float]) -> float:
    return box["y"] + box["height"] / 2


def enter_mode(page: Page, mode: str) -> None:
    page.goto(page.url.split("?")[0], wait_until="domcontentloaded")
    if mode == "play":
        page.evaluate("startGame('play'); cancelRoundTimers(); startPicking()")
    else:
        page.evaluate(f"startGame('{mode}')")
    page.wait_for_selector("#pick.active")
    page.wait_for_timeout(250)


def verify_mode(page: Page, mode: str, width: int, height: int) -> None:
    enter_mode(page, mode)
    pick_rect = rect(page, ".play-stage-row")
    exit_rect = rect(page, "#pick .round-exit-btn")
    if exit_rect["width"] < 44 or exit_rect["height"] < 44:
        raise AssertionError(f"{mode} {width}x{height}: return target is below 44px")

    vertical_anchor = {
        "play": ".play-swatch-copy",
        "match": "#matchGuessDisclosure",
        "picture": ".picture-target",
        "call": ".swatch-role-label",
        "split": ".swatch-role-label",
    }[mode]
    horizontal_anchor = {
        "play": ".play-swatch-copy",
        "match": ".match-target .swatch-role-label",
        "picture": ".picture-prompt",
        "call": ".swatch-role-label",
        "split": ".swatch-role-label",
    }[mode]
    anchor_rect = rect(page, vertical_anchor)
    anchor_center = anchor_rect["y"] + anchor_rect["height"] / 2
    exit_center = exit_rect["y"] + exit_rect["height"] / 2
    if abs(anchor_center - exit_center) > 1:
        raise AssertionError(
            f"{mode} {width}x{height}: return center is {exit_center}, copy center is {anchor_center}"
        )
    horizontal_rect = rect(page, horizontal_anchor)
    left_inset = horizontal_rect["x"] - pick_rect["x"]
    right_inset = pick_rect["x"] + pick_rect["width"] - (
        exit_rect["x"] + exit_rect["width"]
    )
    if abs(left_inset - right_inset) > 1:
        raise AssertionError(
            f"{mode} {width}x{height}: copy inset is {left_inset}, return inset is {right_inset}"
        )

    state = page.evaluate(
        """() => ({
          inactiveNotInert: [...document.querySelectorAll('.screen:not(.active)')]
            .filter(el => !el.hasAttribute('inert')).map(el => el.id),
          bodyOverflow: document.body.scrollHeight - document.documentElement.clientHeight,
          focusClass: document.activeElement?.className || '',
        })"""
    )
    if state["inactiveNotInert"]:
        raise AssertionError(f"{mode}: inactive screens are focusable: {state['inactiveNotInert']}")
    if width <= 390 and state["bodyOverflow"] > 1:
        raise AssertionError(f"{mode}: phone screen scrolls by {state['bodyOverflow']}px")

    if mode == "picture":
        prompt = page.locator(".picture-prompt")
        if prompt.inner_text() != "Choose the color":
            raise AssertionError("Picture It is missing its screen instruction")
        prompt_box = rect(page, ".picture-prompt")
        line_height = float(prompt.evaluate("el => parseFloat(getComputedStyle(el).lineHeight)"))
        if prompt_box["height"] > line_height * 1.25:
            raise AssertionError("Picture It instruction wraps into a noisy second line")
    if mode == "split" and page.locator(".split-prompt").inner_text() != "Estimate HSB":
        raise AssertionError("Split It is missing its screen instruction")
    if mode == "call" and page.locator(".call-prompt").inner_text() != "Choose a name":
        raise AssertionError("Call It is missing its screen instruction")

    page.evaluate(
        """showReveal({
          target: targetColors[0], guess: currentHSB, score: 5.7,
          call_correct_name: lastMode === 'call' ? callChoices[0].choices[callChoices[0].correctIdx].name : null,
          call_chosen_name: lastMode === 'call' ? callChoices[0].choices[0].name : null
        }, 0)"""
    )
    page.wait_for_timeout(250)
    reveal_rect = rect(page, ".reveal-card")
    assert_close(pick_rect, reveal_rect, f"{mode} {width}x{height} Pick→Reveal")
    reveal_label = rect(page, "#revealGuess .reveal-swatch-label")
    reveal_exit = rect(page, "#reveal .reveal-nav-btn.ghost")
    if abs(center_y(reveal_label) - center_y(reveal_exit)) > 1:
        raise AssertionError(
            f"{mode} {width}x{height}: Reveal return center is "
            f"{center_y(reveal_exit)}, role center is {center_y(reveal_label)}"
        )
    if page.evaluate("document.activeElement !== document.getElementById('revealScore')"):
        raise AssertionError(f"{mode}: Reveal did not own focus")


def verify_target_alignment(page: Page, width: int, height: int) -> None:
    page.goto(page.url.split("?")[0], wait_until="domcontentloaded")
    page.evaluate("startGame('play'); cancelRoundTimers(); startMemorize(); cancelRoundTimers()")
    label = rect(page, "#memorizeLabel")
    memorize_exit = rect(page, "#memorize .round-exit-btn")
    screen = rect(page, "#memorize")
    if abs(center_y(label) - center_y(memorize_exit)) > 1:
        raise AssertionError(
            f"Target {width}x{height}: return center is {center_y(memorize_exit)}, "
            f"role center is {center_y(label)}"
        )
    if abs((label["x"] - screen["x"]) - (screen["width"] - memorize_exit["x"] - memorize_exit["width"])) > 1:
        raise AssertionError("Target return control does not share the role-label inset")


def verify_embed_fill(page: Page, width: int, height: int) -> None:
    page.goto(f"{page.url.split('?')[0]}?embed=play", wait_until="load")
    countdown = page.locator("#countdown")
    countdown_rect = rect(page, "#countdown")
    countdown_style = countdown.evaluate(
        "el => ({background:getComputedStyle(el).backgroundColor, color:getComputedStyle(el.querySelector('.countdown-num')).color})"
    )
    if abs(countdown_rect["height"] - height) > 1 or abs(countdown_rect["width"] - width) > 1:
        raise AssertionError(
            f"Embed Countdown {width}x{height}: surface is "
            f"{countdown_rect['width']}x{countdown_rect['height']}"
        )
    if countdown_style["background"] in ("rgba(0, 0, 0, 0)", "transparent"):
        raise AssertionError(f"Embed Countdown {width}x{height}: surface is transparent")
    if countdown_style["background"] == countdown_style["color"]:
        raise AssertionError(f"Embed Countdown {width}x{height}: numeral is invisible")
    if page.evaluate("document.activeElement === document.getElementById('countdownNum')"):
        raise AssertionError(
            f"Embed Countdown {width}x{height}: non-interactive numeral owns focus"
        )
    if countdown.locator("#countdownNum").get_attribute("role") != "status":
        raise AssertionError(
            f"Embed Countdown {width}x{height}: updates lack a semantic status region"
        )
    page.evaluate("cancelRoundTimers(); startMemorize(); cancelRoundTimers()")
    memorize_rect = rect(page, "#memorize")
    timer_rect = rect(page, ".timer-bar")
    timer_left = timer_rect["x"] - memorize_rect["x"]
    timer_right = memorize_rect["x"] + memorize_rect["width"] - (
        timer_rect["x"] + timer_rect["width"]
    )
    if abs(timer_left - timer_right) > 1:
        raise AssertionError(
            f"Embed Memory {width}x{height}: timer insets differ "
            f"({timer_left}px left, {timer_right}px right)"
        )
    if timer_rect["width"] < memorize_rect["width"] - 80:
        raise AssertionError(
            f"Embed Memory {width}x{height}: timer is shortchanged at "
            f"{timer_rect['width']}px inside a {memorize_rect['width']}px stage"
        )
    page.evaluate("cancelRoundTimers(); startPicking()")
    page.wait_for_selector("#pick.active")
    stage = rect(page, ".play-stage-row")
    if abs(stage["height"] - height) > 1 or abs(stage["width"] - width) > 1:
        raise AssertionError(
            f"Embed {width}x{height}: stage is {stage['width']}x{stage['height']}"
        )


def verify_instrument_continuity(page: Page) -> None:
    page.goto(page.url.split("?")[0], wait_until="domcontentloaded")
    page.evaluate("startGame('play'); cancelRoundTimers(); startPicking()")
    field = page.locator(".spectrum-field")
    normal_style = field.evaluate(
        "el => ({boxShadow:getComputedStyle(el).boxShadow, borderStyle:getComputedStyle(el).borderStyle})"
    )
    if normal_style["boxShadow"] != "none" or normal_style["borderStyle"] != "none":
        raise AssertionError(
            f"Inner field has a permanent separator contour: {normal_style}"
        )
    field.focus()
    focus_style = field.evaluate(
        "el => ({style:getComputedStyle(el).outlineStyle, width:parseFloat(getComputedStyle(el).outlineWidth)})"
    )
    if focus_style["style"] == "none" or focus_style["width"] < 2:
        raise AssertionError(f"Inner field keyboard focus is not visible: {focus_style}")
    field.press("ArrowRight")
    page.wait_for_timeout(3000)
    if page.locator(".spectrum-control").get_attribute("data-active") != "true":
        raise AssertionError("Continuous instrument quiets before perceptual confirmation")
    page.wait_for_timeout(2300)
    if page.locator(".spectrum-control").get_attribute("data-active") != "false":
        raise AssertionError("Continuous instrument does not return to its quiet state")


def verify_navigation_and_results(page: Page) -> None:
    page.goto(page.url.split("?")[0], wait_until="domcontentloaded")
    page.get_by_role("button", name="Match It — Tune beside the target").click()
    page.keyboard.press("Escape")
    page.wait_for_function("document.body.dataset.screen === 'menu'")
    if page.evaluate("document.activeElement?.dataset.mode") != "match":
        raise AssertionError("Escape did not restore focus to the initiating mode")

    page.get_by_role("button", name="Call It — Choose its closest word").click()
    page.go_back()
    page.wait_for_function("document.body.dataset.screen === 'menu'")
    if page.evaluate("document.activeElement?.dataset.mode") != "call":
        raise AssertionError("Browser Back did not restore the menu and initiating focus")

    page.get_by_role("button", name="Match It — Tune beside the target").click()
    page.locator("#confirmBtn").click()
    page.wait_for_selector("#reveal.active")
    page.locator(".reveal-nav-btn:not(.ghost)").click()
    page.wait_for_selector("#pick.active")
    page.wait_for_timeout(50)
    if page.evaluate("!document.activeElement?.classList.contains('spectrum-hue')"):
        raise AssertionError("Next left focus on a hidden Reveal control")
    page.get_by_role("button", name="Return to games").click()
    page.wait_for_function("document.body.dataset.screen === 'menu'")

    page.get_by_role("button", name="History").click()
    page.wait_for_selector("#historyScreen.active")
    for selector in ("#historyScreen .icon-btn", "#historyScreen .history-tab:first-child"):
        target = rect(page, selector)
        if target["width"] < 44 or target["height"] < 44:
            raise AssertionError(f"History target is below 44px: {selector} {target}")
    page.go_back()
    page.wait_for_function("document.body.dataset.screen === 'menu'")
    if page.evaluate("document.activeElement?.getAttribute('aria-label')") != "History":
        raise AssertionError("Browser Back from History did not restore History focus")

    page.get_by_role("button", name="Picture It — Pick the color from HSB").click()
    page.evaluate(
        """showResults({total_score: 28.5, results: targetColors.map(target => ({
          target, guess: {...target}, score: 5.7, target_name: 'target', guess_name: 'guess'
        }))})"""
    )
    disclosure = page.locator("#resultsDisclosure")
    disclosure_rect = rect(page, "#resultsDisclosure")
    if disclosure_rect["height"] < 44 or not disclosure.is_visible():
        raise AssertionError("Results breakdown is not a visible 44px disclosure")
    if page.locator(".result-card[role='button']").count():
        raise AssertionError("Results still contains invisible card-level interactions")
    disclosure.click()
    if disclosure.get_attribute("aria-expanded") != "true":
        raise AssertionError("Results breakdown did not expose its expanded state")
    if not page.locator(".result-detail-wrap.visible").first.is_visible():
        raise AssertionError("Results breakdown did not reveal analysis")


def main() -> int:
    port = free_port()
    url = f"http://127.0.0.1:{port}/"
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.app:app", "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_server(url)
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(channel="chrome", headless=True)
            except Exception:
                browser = playwright.chromium.launch(headless=True)
            try:
                errors: list[str] = []
                page = browser.new_page()
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(url, wait_until="domcontentloaded")
                page.emulate_media(reduced_motion="reduce")
                for width, height in VIEWPORTS:
                    page.set_viewport_size({"width": width, "height": height})
                    for mode in MODES:
                        verify_mode(page, mode, width, height)
                    verify_target_alignment(page, width, height)
                    verify_embed_fill(page, width, height)
                page.set_viewport_size({"width": 390, "height": 844})
                verify_instrument_continuity(page)
                verify_navigation_and_results(page)
                if errors:
                    raise AssertionError(f"Browser errors: {errors}")

                touch_context = browser.new_context(
                    viewport={"width": 390, "height": 844}, has_touch=True
                )
                try:
                    touch_page = touch_context.new_page()
                    touch_page.goto(url, wait_until="domcontentloaded")
                    touch_page.get_by_role(
                        "button", name="Call It — Choose its closest word"
                    ).tap()
                    touch_page.locator(".call-choice").first.tap()
                    touch_page.wait_for_selector("#reveal.active")
                finally:
                    touch_context.close()

                no_script_context = browser.new_context(java_script_enabled=False)
                try:
                    no_script_page = no_script_context.new_page()
                    no_script_page.goto(url, wait_until="domcontentloaded")
                    if "needs JavaScript" not in no_script_page.locator("body").inner_text():
                        raise AssertionError("No-JavaScript fallback is not visible")
                finally:
                    no_script_context.close()
            finally:
                browser.close()
    finally:
        server.terminate()
        with contextlib.suppress(subprocess.TimeoutExpired):
            server.wait(timeout=3)
        if server.poll() is None:
            server.kill()
    print("Rendered stage, focus, navigation, and disclosure contracts pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
