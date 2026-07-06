import re
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pathlib import Path
from datetime import datetime
import configparser

# config
config = configparser.ConfigParser()
config.read("config.ini")

USERNAME = config["VMWARE"]["USERNAME"]
PASSWORD = config["VMWARE"]["PASSWORD"]
HEADLESS = False

# helper
def save_download(download, export_dir, filename):
    target = export_dir / filename
    download.save_as(str(target))
    print(f"[OK] Berhasil mengunduh: {filename}")

def safe_login(page, username, password):
    page.locator('input[name="username"], input[name="CastleAuthorization"], #username').first.fill(username)
    page.locator('input[name="password"], #password').first.fill(password)
    page.locator('input[name="password"], #password').first.press("Enter")
    page.get_by_role("button", name="Product navigation").wait_for(state="visible", timeout=60000)
    print("Login selesai.")

def handle_sr_login(sr_page, username, password):
    try:
        print("Mengecek potensi redirect login SSO SR...")
        username_field = sr_page.locator('input[name="username"], input[name="CastleAuthorization"], #username').first
        username_field.wait_for(state="visible", timeout=15000)
        
        print("Form login terdeteksi, memasukkan kredensial ulang...")
        username_field.fill(username)
        sr_page.locator('input[name="password"], #password').first.fill(password)
        sr_page.locator('input[name="password"], #password').first.press("Enter")
    except PlaywrightTimeoutError:
        print("Tidak ada prompt login (sudah login otomatis via SSO).")

def scan_for_sr_button(page):
    """
    Sapu bersih semua iframe di layar untuk mencari tombol OPEN Site Recovery.
    Ini adalah solusi anti-gagal untuk iframe vCenter yang urutannya suka berubah-ubah.
    """
    print("Menunggu antarmuka Site Recovery stabil (10 detik)...")
    page.wait_for_timeout(10000) 
    
    for attempt in range(2):
        # Hitung ada berapa jumlah iframe di layar saat ini
        iframe_count = page.locator("iframe").count()
        print(f"Memindai {iframe_count} iframe untuk mencari tombol OPEN...")
        
        for i in range(iframe_count):
            frame = page.frame_locator("iframe").nth(i)
            btn = frame.get_by_text(re.compile("OPEN Site Recovery", re.IGNORECASE)).first
            try:
                # Cek tiap iframe maksimal 15 detik
                btn.wait_for(state="visible", timeout=15000)
                print(f"🎯 Tombol OPEN berhasil ditemukan di iframe urutan ke-{i+1}!")
                return btn
            except PlaywrightTimeoutError:
                pass # Lanjut cari di iframe berikutnya
        
        if attempt == 0:
            print("[WARNING] Tombol tidak ditemukan di iframe manapun. Memaksa refresh halaman...")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(15000) # Tunggu vCenter loading ulang
            
    raise Exception("Gagal menemukan tombol OPEN Site Recovery setelah refresh.")

# exports
def export_vcenter1(playwright, password, export_dir):
    print("\n--- Export VC1 (10.10.40.9) ---")
    browser = playwright.chromium.launch(headless=HEADLESS)
    context = browser.new_context(ignore_https_errors=True, accept_downloads=True)
    
    try:
        page = context.new_page()
        page.goto("https://10.10.40.9/ui/", wait_until="domcontentloaded", timeout=120000)
        safe_login(page, USERNAME, password)

        btn_nav = page.get_by_role("button", name="Product navigation").first
        btn_nav.wait_for(state="visible", timeout=60000)
        btn_nav.click()
        
        # Jeda untuk membiarkan DOM sidebar terbentuk
        page.wait_for_timeout(3000)
        
        menu_sr = page.get_by_role("link", name=re.compile("Site Recovery", re.IGNORECASE)).first
        menu_sr.wait_for(state="attached", timeout=30000)
        
        print("Mencoba membuka menu Site Recovery (via JS Inject)...")
        for i in range(4):
            # [FIX 1] Eksekusi klik langsung di level DOM, mengabaikan UI blocker
            menu_sr.evaluate("node => node.click()")
            
            try:
                # [FIX 2] Jangan tunggu URL, langsung tunggu kehadiran iframe plugin
                page.locator("iframe").first.wait_for(state="attached", timeout=10000)
                print("Berhasil masuk ke halaman Site Recovery.")
                break
            except PlaywrightTimeoutError:
                print(f"Klik menu misfire (percobaan {i+1}), mencoba ulang JS Inject...")
                page.wait_for_timeout(2000)
        else:
            raise Exception("Gagal berpindah ke halaman Site Recovery setelah 4x injeksi klik.")

        # Gunakan fungsi Iframe Scanner
        btn_open = scan_for_sr_button(page)
        
        with page.expect_popup() as popup:
            btn_open.click()
        
        sr = popup.value
        sr.wait_for_load_state("domcontentloaded")
        print("Popup Site Recovery terbuka, memuat data...")

        repl_link = sr.locator('a[aria-label*="Replications within" i]').first
        repl_link.wait_for(state="visible", timeout=120000)
        repl_link.click()

        btn_export = sr.get_by_role("button", name="EXPORT")
        btn_export.wait_for(state="visible", timeout=60000)
        btn_export.click()

        with sr.expect_download() as d:
            sr.get_by_role("menuitem").first.click()

        save_download(d.value, export_dir, "VC1_10.10.40.9.csv")
        
    finally:
        context.close()
        browser.close()

def export_vcenter2(playwright, password, export_dir):
    print("\n--- Export VC2 (10.10.40.14) ---")
    browser = playwright.chromium.launch(headless=HEADLESS)
    context = browser.new_context(ignore_https_errors=True, accept_downloads=True)
    
    try:
        page = context.new_page()
        page.goto("https://10.10.40.14/", wait_until="domcontentloaded", timeout=120000)
        
        launch_btn = page.get_by_role("link", name="Launch vSphere Client (HTML5)")
        if launch_btn.is_visible():
            launch_btn.click()

        safe_login(page, USERNAME, password)

        btn_nav = page.get_by_role("button", name="Product navigation").first
        btn_nav.wait_for(state="visible", timeout=60000)
        btn_nav.click()
        
        # [FIX 1] Jeda 3 detik
        page.wait_for_timeout(3000)
        
        menu_sr = page.get_by_role("link", name="Site Recovery").first
        menu_sr.wait_for(state="visible", timeout=30000)
        
        print("Mencoba membuka menu Site Recovery...")
        for i in range(4):
            try:
                menu_sr.hover(timeout=3000)
                menu_sr.click(timeout=3000)
            except Exception:
                menu_sr.click(force=True)

            try:
                # [FIX 3] Waktu respons 10 detik
                page.wait_for_url("**/*draasclientplugin*", timeout=10000)
                print("Berhasil masuk ke halaman Site Recovery.")
                break
            except PlaywrightTimeoutError:
                print(f"Klik menu misfire (percobaan {i+1}), menunggu respon vCenter...")
                page.wait_for_timeout(2000)
        else:
            raise Exception("Gagal berpindah ke halaman Site Recovery setelah 4x percobaan.")

        # Gunakan fungsi Iframe Scanner
        btn_open = scan_for_sr_button(page)
        
        with page.expect_popup() as popup:
            btn_open.click()
            
        sr = popup.value
        sr.wait_for_load_state("domcontentloaded")
        print("Popup Site Recovery terbuka, memuat data...")

        repl_link = sr.locator('a[aria-label*="Replications within" i]').first
        repl_link.wait_for(state="visible", timeout=120000)
        repl_link.click()

        btn_export = sr.get_by_role("button", name="EXPORT")
        btn_export.wait_for(state="visible", timeout=60000)
        btn_export.click()

        with sr.expect_download() as d:
            sr.get_by_role("menuitem").first.click()

        save_download(d.value, export_dir, "VC2_10.10.40.14.csv")

    finally:
        context.close()
        browser.close()

def export_vcenter4(playwright, password, export_dir):
    print("\n--- Export VC4 (192.168.193.250) ---")
    browser = playwright.chromium.launch(headless=HEADLESS)
    context = browser.new_context(ignore_https_errors=True, accept_downloads=True)
    
    try:
        page = context.new_page()
        page.goto("https://192.168.193.250/", wait_until="domcontentloaded", timeout=120000)
        
        launch_btn = page.get_by_role("link", name="Launch vSphere Client (HTML5)")
        if launch_btn.is_visible():
            launch_btn.click()

        safe_login(page, USERNAME, password)

        page.get_by_role("button", name="Product navigation").click()
        menu_sr = page.get_by_role("link", name="Site Recovery")
        for i in range(4):
            menu_sr.click(force=True)
            try:
                page.wait_for_url("**/*draasclientplugin*", timeout=5000)
                break
            except PlaywrightTimeoutError:
                pass

        frame = page.frame_locator("iframe").last

        # SR1 (192.168.191.25)
        try:
            print("Membuka SR1 (192.168.191.25)...")
            btn_open_1 = frame.get_by_text(re.compile("OPEN Site Recovery", re.IGNORECASE)).first
            btn_open_1.wait_for(state="visible", timeout=60000)
            
            with page.expect_popup() as popup1:
                btn_open_1.click()
            sr1 = popup1.value
            
            handle_sr_login(sr1, USERNAME, password)
            sr1.wait_for_url(lambda url: "/dr/" in url, timeout=90000)
            sr1.wait_for_load_state("domcontentloaded")

            out_link1 = sr1.locator('a[aria-label*="Outgoing Replications" i]').first
            out_link1.wait_for(state="visible", timeout=60000)
            out_link1.click()

            btn_export = sr1.get_by_role("button", name="EXPORT")
            btn_export.wait_for(state="visible", timeout=60000)
            btn_export.click()
            with sr1.expect_download() as d:
                sr1.get_by_role("menuitem").first.click()
            save_download(d.value, export_dir, "VC4_19125_Outgoing.csv")

            sr1.goto("https://192.168.191.26/dr/#/home", wait_until="domcontentloaded", timeout=120000)
            sr1.wait_for_load_state("domcontentloaded")
            
            within_link1 = sr1.locator('a[aria-label*="Replications within" i]').first
            within_link1.wait_for(state="visible", timeout=60000)
            within_link1.click()
            
            btn_export.wait_for(state="visible", timeout=60000)
            btn_export.click()
            with sr1.expect_download() as d:
                sr1.get_by_role("menuitem").first.click()
            save_download(d.value, export_dir, "VC4_19125_Within.csv")
            sr1.close()
        except Exception as e:
            print(f"[ERROR] SR1 gagal dieksekusi: {e}")

        # SR2 (192.168.193.250)
        try:
            print("Membuka SR2 (192.168.193.250)...")
            btn_open_2 = frame.get_by_text(re.compile("OPEN Site Recovery", re.IGNORECASE)).nth(1)
            btn_open_2.wait_for(state="visible", timeout=60000)

            with page.expect_popup() as popup2:
                btn_open_2.click()
            sr2 = popup2.value

            handle_sr_login(sr2, USERNAME, password)
            sr2.wait_for_url(lambda url: "/dr/" in url, timeout=90000)
            sr2.wait_for_load_state("domcontentloaded")

            out_link2 = sr2.locator('a[aria-label*="Outgoing Replications" i]').first
            out_link2.wait_for(state="visible", timeout=60000)
            out_link2.click()

            btn_export2 = sr2.get_by_role("button", name="EXPORT")
            btn_export2.wait_for(state="visible", timeout=60000)
            btn_export2.click()
            with sr2.expect_download() as d:
                sr2.get_by_role("menuitem").first.click()
            save_download(d.value, export_dir, "VC4_193250_Outgoing.csv")

            sr2.goto("https://192.168.193.251/dr/#/home", wait_until="domcontentloaded", timeout=120000)
            sr2.wait_for_load_state("domcontentloaded")
            
            within_link2 = sr2.locator('a[aria-label*="Replications within" i]').first
            within_link2.wait_for(state="visible", timeout=60000)
            within_link2.click()
            
            btn_export2.wait_for(state="visible", timeout=60000)
            btn_export2.click()
            with sr2.expect_download() as d:
                sr2.get_by_role("menuitem").first.click()
            save_download(d.value, export_dir, "VC4_193250_Within.csv")
            sr2.close()
        except Exception as e:
            print(f"[ERROR] SR2 gagal dieksekusi: {e}")

    finally:
        context.close()
        browser.close()

# main
BULAN = [
    "Januari", "Februari", "Maret", "April",
    "Mei", "Juni", "Juli", "Agustus",
    "September", "Oktober", "November", "Desember"
]

def main():
    print("\nPilih Shift:")
    print("1. Pagi")
    print("2. Siang")
    print("3. Malam")

    pilihan = input("Masukkan pilihan (1-3): ")
    shift_map = {"1": "Pagi", "2": "Siang", "3": "Malam"}
    
    if pilihan not in shift_map:
        print("Shift tidak valid")
        return
    shift = shift_map[pilihan]

    now = datetime.now()
    export_dir = (
        Path("exports")
        / f"{BULAN[now.month - 1]}-{now.year}"
        / f"{now.strftime('%d-%m-%Y')} ({shift})"
    )
    export_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nShift dipilih: {shift}")
    print(f"Folder export: {export_dir}")

    with sync_playwright() as playwright:
        print("\nMemulai Scraping...")
        
        for name, func in [("VC1", export_vcenter1), ("VC2", export_vcenter2), ("VC4", export_vcenter4)]:
            try:
                func(playwright, PASSWORD, export_dir)
            except Exception as e:
                print("=" * 60)
                print(f"{name} mengalami kendala: {e}")
                print("=" * 60)
        
    print("\n✅ SEMUA PROSES SELESAI")

if __name__ == "__main__":
    main()