import configparser
import time
import atexit
import ssl
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

# config
config = configparser.ConfigParser()
config.read("config.ini")

USERNAME = config["VMWARE"]["USERNAME"]
PASSWORD = config["VMWARE"]["PASSWORD"]

# test
VCENTER_IP = "10.10.40.9" 

def test_api_connection():
    print(f"Mengirim request API ke {VCENTER_IP}...")
    
    start_time = time.time()
    
    try:
        context = ssl._create_unverified_context()

        si = SmartConnect(
            host=VCENTER_IP,
            user=USERNAME,
            pwd=PASSWORD,
            sslContext=context
        )
        
        atexit.register(Disconnect, si)
        
        about_info = si.content.about
        
        print("\n✅ KONEKSI BERHASIL!")
        print("-" * 40)
        print(f"Produk      : {about_info.fullName}")
        print(f"Versi API   : {about_info.apiVersion}")
        print(f"Vendor      : {about_info.vendor}")
        print(f"OS Tipe     : {about_info.osType}")
        print("-" * 40)
        
    except vim.fault.InvalidLogin:
        print("\n❌ GAGAL: Username atau Password salah!")
    except Exception as e:
        print(f"\n❌ KONEKSI GAGAL: {e}")
        
    finally:
        end_time = time.time()
        durasi = round(end_time - start_time, 2)
        print(f"\n⏱️ Total Waktu Eksekusi: {durasi} detik.")

if __name__ == "__main__":
    test_api_connection()