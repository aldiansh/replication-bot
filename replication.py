import re
from playwright.sync_api import sync_playwright
# from getpass import getpass
from pathlib import Path
from datetime import datetime
import configparser

# =========================
# CONFIG
# =========================

config = configparser.ConfigParser()
config.read("config.ini")

USERNAME = config["VMWARE"]["USERNAME"]
PASSWORD = config["VMWARE"]["PASSWORD"]

SHIFT = ""

EXPORT_DIR = Path("exports")

EXPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

HEADLESS = False


# =========================
# HELPER
# =========================

def save_download(download, filename):
    target = EXPORT_DIR / filename
    download.save_as(str(target))
    print(f"[OK] {filename}")


# =========================
# VCENTER 1
# =========================

def export_vcenter1(playwright, password):
    print("Export VC1...")

    browser = playwright.chromium.launch(headless=HEADLESS)

    context = browser.new_context(
        ignore_https_errors=True,
        accept_downloads=True
    )

    page = context.new_page()

    page.goto(
        "https://10.10.40.9/ui/",
        wait_until="domcontentloaded",
        timeout=120000
    )

    page.wait_for_timeout(5000)

    page.get_by_role(
        "textbox",
        name="example@domain.local"
    ).fill(USERNAME)

    page.get_by_role(
        "textbox",
        name="Password"
    ).fill(password)

    page.get_by_role(
        "textbox",
        name="Password"
    ).press("Enter")

    page.wait_for_timeout(10000)

    print("login selesai")

    page.get_by_role(
        "button",
        name="Product navigation"
    ).click()

    print("menu diklik")

    page.get_by_role(
        "link",
        name="Site Recovery"
    ).wait_for(timeout=120000)

    print("menu Site Recovery ditemukan")

    for i in range(3):

        print(f"Percobaan klik Site Recovery ke-{i+1}")

        print("URL sebelum klik =", page.url)

        page.get_by_role(
            "link",
            name="Site Recovery"
        ).click(force=True)

        page.wait_for_timeout(5000)

        print("URL sesudah klik =", page.url)

        if "draasclientplugin" in page.url:
            print("Berhasil masuk ke Site Recovery")
            break

        print("Klik gagal, coba lagi...")

    else:
        raise Exception(
            "Tidak bisa masuk ke halaman Site Recovery"
        )

    frame = page.locator("iframe").content_frame

    print("iframe ditemukan")

    frame.get_by_role(
        "button",
        name="OPEN Site Recovery"
    ).wait_for(timeout=120000)

    print("tombol OPEN ditemukan")

    with page.expect_popup() as popup:
        frame.get_by_role(
            "button",
            name="OPEN Site Recovery"
        ).click()

    sr = popup.value

    sr.wait_for_load_state("domcontentloaded")
    sr.wait_for_timeout(10000)

    print("popup SR VC1 terbuka")

    sr.locator(
        'a[aria-label*="Replications within"]'
    ).wait_for(timeout=120000)

    sr.locator(
        'a[aria-label*="Replications within"]'
    ).click()

    print("halaman replication dibuka")

    sr.get_by_role(
        "button",
        name="EXPORT"
    ).click()

    with sr.expect_download() as d:
        sr.get_by_role("menuitem").first.click()

    download = d.value

    print("DOWNLOAD NAME =", download.suggested_filename)
    print("DOWNLOAD PATH =", download.path())

    save_download(
        download,
        "VC1_10.10.40.9.csv"
    )

    context.close()
    browser.close()


# =========================
# VCENTER 2
# =========================

def export_vcenter2(playwright, password):

    print("Export VC2...")

    browser = playwright.chromium.launch(headless=HEADLESS)
    context = browser.new_context(ignore_https_errors=True)

    page = context.new_page()

    page.goto("https://10.10.40.14/")
    page.get_by_role("link", name="Launch vSphere Client (HTML5)").click()

    page.get_by_role("textbox", name="example@domain.local").fill(USERNAME)
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("textbox", name="Password").press("Enter")

    page.wait_for_timeout(5000)

    print("login VC2 selesai")

    page.get_by_role(
        "button",
        name="Product navigation"
    ).click()

    print("menu VC2 diklik")

    page.get_by_role(
        "link",
        name="Site Recovery"
    ).click()

    print("site recovery VC2 diklik")

    page.wait_for_timeout(5000)

    frame = page.locator("iframe").content_frame

    print("iframe VC2 ditemukan")

    frame.get_by_role(
        "button",
        name="OPEN Site Recovery"
    ).wait_for()

    print("tombol OPEN VC2 ditemukan")

    with page.expect_popup() as popup:
        frame.get_by_role(
            "button",
            name="OPEN Site Recovery"
        ).click()

    sr = popup.value

    sr.wait_for_load_state("domcontentloaded")
    sr.wait_for_timeout(10000)

    print("popup SR VC2 terbuka")

    sr.locator(
        'a[aria-label*="Replications within"]'
    ).wait_for(timeout=120000)

    sr.locator(
        'a[aria-label*="Replications within"]'
    ).click()

    print("halaman replication VC2 dibuka")

    sr.get_by_role("button", name="EXPORT").click()

    with sr.expect_download() as d:
        sr.get_by_role("menuitem").first.click()

    save_download(
        d.value,
        "VC2_10.10.40.14.csv"
    )

    context.close()
    browser.close()


# =========================
# VCENTER 4
# =========================

def export_vcenter4(playwright, password):

    print("Export VC4...")

    browser = playwright.chromium.launch(headless=HEADLESS)
    context = browser.new_context(ignore_https_errors=True)

    page = context.new_page()

    page.goto("https://192.168.193.250/")

    page.get_by_role("link", name="Launch vSphere Client (HTML5)").click()

    page.get_by_role("textbox", name="example@domain.local").fill(USERNAME)
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("textbox", name="Password").press("Enter")

    page.wait_for_timeout(5000)

    print("login VC4 selesai")

    page.get_by_role(
        "button",
        name="Product navigation"
    ).click()

    print("menu VC4 diklik")

    page.get_by_role(
        "link",
        name="Site Recovery"
    ).click()

    print("site recovery VC4 diklik")

    page.wait_for_timeout(5000)

    frame = page.locator("iframe").content_frame

    print("iframe VC4 ditemukan")

    # ======================
    # 192.168.191.25
    # ======================

    try:

        with page.expect_popup() as popup1:
            page.locator(
                'iframe[title="Site Recovery"]'
            ).content_frame.get_by_role(
                "button",
                name="OPEN Site Recovery"
            ).first.click()

        sr1 = popup1.value

        sr1.get_by_role(
            "textbox",
            name="example@domain.local"
        ).fill(USERNAME)

        sr1.get_by_role(
            "textbox",
            name="Password"
        ).fill(password)

        sr1.get_by_role(
            "textbox",
            name="Password"
        ).press("Enter")

        # tunggu redirect selesai
        sr1.wait_for_url(
            lambda url: "/dr/" in url,
            timeout=60000
        )

        print("URL SR1 =", sr1.url)

        sr1.wait_for_timeout(5000)

        print("Login SR1 selesai")

        # buka outgoing replication
        sr1.get_by_label(
            "Outgoing Replications"
        ).click()

        print("Outgoing SR1 diklik")

        # tunggu halaman replication terbuka
        sr1.get_by_role(
            "button",
            name="EXPORT"
        ).wait_for(timeout=30000)

        print("Halaman replication SR1 terbuka")

        # export outgoing
        sr1.get_by_role(
            "button",
            name="EXPORT"
        ).click()

        with sr1.expect_download() as d:
            sr1.get_by_role("menuitem").first.click()

        save_download(
            d.value,
            "VC4_19125_Outgoing.csv"
        )

        print("Outgoing SR1 exported")

        # ======================
        # WITHIN SR1
        # ======================

        sr1.goto(
            "https://192.168.191.26/dr/#/home"
        )

        sr1.wait_for_timeout(5000)

        print("Kembali ke Home SR1")

        sr1.get_by_label(
            "15 Replications within the"
        ).click()

        print("Within SR1 diklik")

        sr1.get_by_role(
            "button",
            name="EXPORT"
        ).wait_for(timeout=30000)

        # export within
        sr1.get_by_role(
            "button",
            name="EXPORT"
        ).click()

        with sr1.expect_download() as d:
            sr1.get_by_role("menuitem").first.click()

        save_download(
            d.value,
            "VC4_19125_Within.csv"
        )

        print("Within SR1 exported")

    except Exception as e:
        print("=" * 60)
        print("SR1 gagal")
        print(e)
        print("=" * 60)

    # ======================
    # 192.168.193.250
    # ======================

    with page.expect_popup() as popup2:
        page.locator(
        'iframe[title="Site Recovery"]'
    ).content_frame.get_by_role(
        "button",
        name="OPEN Site Recovery"
    ).nth(1).click()

    sr2 = popup2.value

    # tunggu redirect SSO selesai
    for i in range(12):
        print("URL SR2 =", sr2.url)

        if "/dr/" in sr2.url:
            break

        sr2.wait_for_timeout(5000)

    print("FINAL URL SR2 =", sr2.url)

    sr2.wait_for_timeout(10000)

    print("URL setelah tunggu =", sr2.url)

    # buka outgoing replication
    print("Mau klik Outgoing SR2")

    sr2.get_by_label(
        "Outgoing Replications"
    ).click()

    print("Outgoing SR2 diklik")

    # tunggu halaman replication terbuka
    sr2.get_by_role(
        "button",
        name="EXPORT"
    ).wait_for(timeout=30000)

    print("Halaman replication SR2 terbuka")

    # export outgoing
    sr2.get_by_role(
        "button",
        name="EXPORT"
    ).click()

    with sr2.expect_download() as d:
        sr2.get_by_role("menuitem").first.click()

    save_download(
        d.value,
        "VC4_193250_Outgoing.csv"
    )

    print("Outgoing SR2 exported")

    sr2.goto(
        "https://192.168.193.251/dr/#/home"
    )

    sr2.wait_for_timeout(5000)

    print("Kembali ke Home SR2")

    # buka replication within
    sr2.get_by_label(
        "89 Replications within the"
    ).click()

    print("Within SR2 diklik")

    print("Within SR2 diklik")

    sr2.get_by_role(
        "button",
        name="EXPORT"
    ).wait_for(timeout=30000)

    # export within
    sr2.get_by_role(
        "button",
        name="EXPORT"
    ).click()

    with sr2.expect_download() as d:
        sr2.get_by_role("menuitem").first.click()

    save_download(
        d.value,
        "VC4_193250_Within.csv"
    )

    print("Within SR2 exported")

    context.close()
    browser.close()

# =========================
# MAIN
# =========================

bulan = [
    "Januari", "Februari", "Maret", "April",
    "Mei", "Juni", "Juli", "Agustus",
    "September", "Oktober", "November", "Desember"
]

def main():

    global SHIFT
    global EXPORT_DIR

    print("\nPilih Shift:")
    print("1. Pagi")
    print("2. Siang")
    print("3. Malam")

    pilihan = input("Masukkan pilihan (1-3): ")

    if pilihan == "1":
        SHIFT = "Pagi"
    elif pilihan == "2":
        SHIFT = "Siang"
    elif pilihan == "3":
        SHIFT = "Malam"
    else:
        print("Shift tidak valid")
        return

    now = datetime.now()

    EXPORT_DIR = (
        Path("exports")
        / f"{bulan[now.month - 1]}-{now.year}"
        / f"{now.strftime('%d-%m-%Y')} ({SHIFT})"
    )

    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print(f"\nShift dipilih: {SHIFT}")
    print(f"Folder export: {EXPORT_DIR}")

    with sync_playwright() as playwright:

        try:
            export_vcenter1(playwright, PASSWORD)
        except Exception as e:
            print("=" * 60)
            print("VC1 gagal")
            print(e)
            print("=" * 60)

        try:
            export_vcenter2(playwright, PASSWORD)
        except Exception as e:
            print("=" * 60)
            print("VC2 gagal")
            print(e)
            print("=" * 60)

        try:
            export_vcenter4(playwright, PASSWORD)
        except Exception as e:
            print("=" * 60)
            print("VC4 gagal")
            print(e)
            print("=" * 60)

    print("\nSELESAI")


if __name__ == "__main__":
    main()