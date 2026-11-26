import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

import pytest
from playwright.sync_api import sync_playwright

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_http(url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if 200 <= resp.status < 500:
                    return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError(f"Service at {url} did not become ready within {timeout}s")


@pytest.fixture(scope="module")
def live_servers():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    backend_port = 5000
    # Use a dedicated port if 5000 is already occupied
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", backend_port)) == 0:
            backend_port = _find_free_port()

    frontend_port = _find_free_port()

    backend_env = os.environ.copy()
    backend_env.update({
        "FLASK_ENV": "development",
        "FLASK_DEBUG": "0",
        "SECRET_KEY": "e2e-test-secret-key-not-for-prod",
        "PORT": str(backend_port),
        "DATABASE_PATH": db_path,
        "CORS_ORIGINS": f"http://127.0.0.1:{frontend_port},http://localhost:{frontend_port}",
    })

    backend_proc = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=BACKEND_DIR,
        env=backend_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    frontend_env = os.environ.copy()
    frontend_env.update({
        "VITE_API_BASE_URL": f"http://127.0.0.1:{backend_port}/api/v1",
    })
    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
    frontend_proc = subprocess.Popen(
        [npx_cmd, "vite", "--port", str(frontend_port), "--strictPort"],
        cwd=FRONTEND_DIR,
        env=frontend_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_http(f"http://127.0.0.1:{backend_port}/api/v1/health", timeout=25.0)
        _wait_for_http(f"http://127.0.0.1:{frontend_port}/", timeout=25.0)
        yield {
            "backend_url": f"http://127.0.0.1:{backend_port}",
            "frontend_url": f"http://127.0.0.1:{frontend_port}",
        }
    finally:
        for proc in (frontend_proc, backend_proc):
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        for ext in ("", "-wal", "-shm"):
            p = db_path + ext
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


def _attach_error_monitors(page):
    page_errors = []
    server_errors = []
    console_errors = []

    page.on("pageerror", lambda err: page_errors.append(str(err)))
    page.on(
        "response",
        lambda resp: server_errors.append(f"{resp.status} {resp.url}") if resp.status >= 500 else None,
    )
    page.on(
        "console",
        lambda msg: console_errors.append(msg.text)
        if msg.type == "error" and "401 (UNAUTHORIZED)" not in msg.text
        else None,
    )
    return page_errors, server_errors, console_errors


def _register_in_ui(page, base_url, *, full_name, username, email, password="Password123!", skills="Python, React"):
    page.goto(base_url, wait_until="domcontentloaded")
    page.get_by_role("button", name="Create an Account").click()
    page.locator('input[name="full_name"]').fill(full_name)
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="email"]').fill(email)
    page.locator('input[name="password"]').fill(password)
    page.locator('input[name="skills"]').fill(skills)
    page.get_by_role("button", name="Create Account").click()
    page.get_by_role("button", name="Feed").first.wait_for(state="visible", timeout=10000)


def test_complete_campusconnect_e2e_journeys(live_servers):
    base_url = live_servers["frontend_url"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Context A: User A
        ctx_a = browser.new_context(viewport={"width": 1280, "height": 800})
        page_a = ctx_a.new_page()
        page_errors_a, server_errors_a, console_errors_a = _attach_error_monitors(page_a)

        # Journey 1: Auth error + Register + Reload + Logout + Login
        page_a.goto(base_url, wait_until="domcontentloaded")
        page_a.locator('input[placeholder*="alex_cs"]').fill("nonexistent_user")
        page_a.locator('input[placeholder*="Enter your password"]').fill("wrongpass")
        page_a.get_by_role("button", name="Sign In").click()
        page_a.locator("text=Invalid").first.wait_for(state="visible", timeout=5000)

        _register_in_ui(
            page_a,
            base_url,
            full_name="Alice Student",
            username="alice_e2e",
            email="alice_e2e@university.edu",
        )

        # Reload persistence
        page_a.reload(wait_until="domcontentloaded")
        page_a.get_by_role("button", name="Feed").first.wait_for(state="visible", timeout=10000)

        # Logout & verify protected UI is gone
        page_a.get_by_role("button", name="Sign Out").or_(page_a.get_by_role("button", name="Logout")).first.click()
        page_a.get_by_role("button", name="Sign In").wait_for(state="visible", timeout=10000)

        # Login back in
        page_a.locator('input[placeholder*="alex_cs"]').fill("alice_e2e")
        page_a.locator('input[placeholder*="Enter your password"]').fill("Password123!")
        page_a.get_by_role("button", name="Sign In").click()
        page_a.get_by_role("button", name="Feed").first.wait_for(state="visible", timeout=10000)

        # Journey 2: Profile view + edit + reload persistence
        page_a.get_by_role("button", name="Profile").first.click()
        page_a.get_by_role("button", name="Edit Profile").click()
        page_a.locator("#edit-skills").fill("Algorithms, Playwright, Graph")
        page_a.locator("#edit-bio").fill("E2E verified bio.")
        with page_a.expect_response(lambda r: "/users/me" in r.url and r.request.method == "PUT", timeout=8000) as resp_info:
            page_a.get_by_role("button", name="Save Changes").click()
        put_resp = resp_info.value
        assert put_resp.status == 200, f"PUT /users/me failed: {put_resp.status} {put_resp.text()}"
        page_a.get_by_role("button", name="Edit Profile").wait_for(state="visible", timeout=5000)
        page_a.locator("text=E2E verified bio.").wait_for(state="visible", timeout=5000)
        page_a.reload(wait_until="domcontentloaded")
        page_a.locator("text=E2E verified bio.").wait_for(state="visible", timeout=10000)

        # Journey 3: Posts & Feed (create + verify + delete)
        page_a.get_by_role("button", name="Feed").first.click()
        post_text = "E2E integration test post from Alice"
        page_a.locator("#feed-post-composer").fill(post_text)
        page_a.get_by_role("button", name="Publish Post").click()
        page_a.locator(f"text={post_text}").wait_for(state="visible", timeout=5000)

        page_a.once("dialog", lambda dialog: dialog.accept())
        page_a.get_by_role("button", name="Delete").first.click()
        page_a.locator(f"text={post_text}").wait_for(state="detached", timeout=5000)

        # Register User B and User C in separate contexts
        ctx_b = browser.new_context(viewport={"width": 1280, "height": 800})
        page_b = ctx_b.new_page()
        page_errors_b, server_errors_b, console_errors_b = _attach_error_monitors(page_b)
        _register_in_ui(
            page_b,
            base_url,
            full_name="Bob Researcher",
            username="bob_e2e",
            email="bob_e2e@university.edu",
        )

        ctx_c = browser.new_context(viewport={"width": 1280, "height": 800})
        page_c = ctx_c.new_page()
        page_errors_c, server_errors_c, console_errors_c = _attach_error_monitors(page_c)
        _register_in_ui(
            page_c,
            base_url,
            full_name="Charlie Graph",
            username="charlie_e2e",
            email="charlie_e2e@university.edu",
        )

        # Journey 4 & 5: Search & Connections
        page_a.get_by_role("button", name="Discover").first.click()
        search_input = page_a.locator('input[type="search"], input[placeholder*="Search"]').first
        with page_a.expect_response(lambda r: "/search/users" in r.url and r.status == 200, timeout=5000):
            search_input.fill("bob_e2e")
        page_a.locator("text=Bob Researcher").first.wait_for(state="visible", timeout=5000)
        with page_a.expect_response(lambda r: "/connections/requests" in r.url and r.request.method == "POST", timeout=5000) as req_a:
            page_a.get_by_role("button", name="Connect", exact=True).first.click()
        assert req_a.value.status == 201

        # User B accepts User A's request
        page_b.get_by_role("button", name="Connections").first.click()
        page_b.get_by_role("button", name="Requests Received").click()
        page_b.locator("text=Alice Student").first.wait_for(state="visible", timeout=5000)
        with page_b.expect_response(lambda r: "/accept" in r.url and r.request.method == "POST", timeout=5000) as acc_a:
            page_b.get_by_role("button", name="Accept", exact=True).first.click()
        assert acc_a.value.status == 200

        # User C connects to User B so Alice <-> Bob <-> Charlie forms a 2-hop path
        page_c.get_by_role("button", name="Discover").first.click()
        with page_c.expect_response(lambda r: "/search/users" in r.url and r.status == 200, timeout=5000):
            page_c.locator('input[type="search"], input[placeholder*="Search"]').first.fill("bob_e2e")
        page_c.locator("text=Bob Researcher").first.wait_for(state="visible", timeout=5000)
        with page_c.expect_response(lambda r: "/connections/requests" in r.url and r.request.method == "POST", timeout=5000) as req_c:
            page_c.get_by_role("button", name="Connect", exact=True).first.click()
        assert req_c.value.status == 201

        page_b.reload(wait_until="domcontentloaded")
        page_b.get_by_role("button", name="Connections").first.click()
        page_b.get_by_role("button", name="Requests Received").click()
        page_b.locator("text=Charlie Graph").first.wait_for(state="visible", timeout=5000)
        with page_b.expect_response(lambda r: "/accept" in r.url and r.request.method == "POST", timeout=5000) as acc_c:
            page_b.get_by_role("button", name="Accept", exact=True).first.click()
        assert acc_c.value.status == 200

        # Journey 6: Network degree, recommendations & BFS shortest path
        page_a.get_by_role("button", name="Network").first.click()
        page_a.locator("text=Charlie Graph").first.wait_for(state="visible", timeout=5000)

        # Journey 7: Mobile viewport check (375x812)
        page_a.set_viewport_size({"width": 375, "height": 812})
        page_a.get_by_role("button", name="Feed").first.click()
        page_a.locator("#feed-post-composer").wait_for(state="visible", timeout=5000)

        assert not page_errors_a and not page_errors_b and not page_errors_c, (
            page_errors_a + page_errors_b + page_errors_c
        )
        assert not server_errors_a and not server_errors_b and not server_errors_c, (
            server_errors_a + server_errors_b + server_errors_c
        )
        assert not console_errors_a and not console_errors_b and not console_errors_c, (
            console_errors_a + console_errors_b + console_errors_c
        )

        browser.close()
