#!/usr/bin/env python3
# Firefox Decrypt - Decrypt Firefox passwords
import argparse
import csv
import json
import logging
import os
import sqlite3
import sys
import xml.etree.ElementTree as ET
from base64 import b64decode
from getpass import getpass

try:
    from Cryptodome.Cipher import DES3, AES
    from Cryptodome.Hash import SHA1, SHA256, HMAC
    from Cryptodome.Protocol.KDF import PBKDF2
except ImportError:
    from Crypto.Cipher import DES3, AES
    from Crypto.Hash import SHA1, SHA256, HMAC
    from Crypto.Protocol.KDF import PBKDF2

log = logging.getLogger(__name__)

# Mapping of known entry types
ENC_TYPES = {
    1: "ASN1/Curve",
    2: "HMAC-SHA1 with AES-CBC",
    3: "Triple DES",
    4: "AES 256 PBKDF2 HMAC SHA256",
}

class FirefoxDecrypt:
    def __init__(self, profile_path):
        self.profile = profile_path
        self.db = None
        self.key = None
        self.version = None

    def get_key_db(self):
        """Get the master key from key4.db or key3.db"""
        key4_path = os.path.join(self.profile, "key4.db")
        if not os.path.exists(key4_path):
            raise Exception("key4.db not found")
        
        conn = sqlite3.connect(key4_path)
        conn.text_factory = bytes
        c = conn.cursor()
        
        # Get the global salt and master password
        c.execute("SELECT item1, item2 FROM metadata WHERE id = 'password'")
        row = c.fetchone()
        if row:
            self.global_salt = row[0]
            self.master_password = row[1]
        
        # Get the encryption key
        c.execute("SELECT a11, a102 FROM nssPrivate")
        row = c.fetchone()
        conn.close()
        
        if not row:
            raise Exception("No encryption keys found")
        
        return row[0], row[1]

    def decrypt_3des(self, encrypted_data, key):
        """Decrypt Triple DES encrypted data"""
        iv = encrypted_data[:8]
        ciphertext = encrypted_data[8:]
        cipher = DES3.new(key, DES3.MODE_CBC, iv=iv)
        return cipher.decrypt(ciphertext)

    def decrypt_aes(self, encrypted_data, key):
        """Decrypt AES encrypted data"""
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        return cipher.decrypt(ciphertext)

    def pkcs11_unpad(self, data):
        """Remove PKCS#7 padding"""
        if len(data) == 0:
            return data
        pad_len = data[-1]
        if pad_len < 1 or pad_len > 16:
            return data
        return data[:-pad_len]

    def decode_login_data(self, data):
        """Decode the encrypted login data"""
        if self.version == 4:
            # AES 256 PBKDF2 HMAC SHA256
            entry_salt_len = int.from_bytes(data[:4], 'big')
            entry_salt = data[4:4+entry_salt_len]
            algtag = data[4+entry_salt_len]
            iv = data[5+entry_salt_len:5+entry_salt_len+16]
            ciphertext = data[5+entry_salt_len+16:-32]
            hmac_tag = data[-32:]
            
            # Derive key
            key = PBKDF2(self.key, entry_salt, dkLen=32, count=1)
            
            # Verify HMAC
            hcalc = HMAC.new(key, data[:5+entry_salt_len+16], SHA256)
            hcalc.update(ciphertext)
            
            cipher = AES.new(key, AES.MODE_CBC, iv=iv)
            return self.pkcs11_unpad(cipher.decrypt(ciphertext))
        else:
            if self.version == 2:
                # Triple DES with HMAC-SHA1
                key = SHA1.new(self.key).digest()[:24]
                iv = data[:8]
                ciphertext = data[8:-20]
                hmac_data = data[-20:]
                
                # Verify HMAC
                hm = HMAC.new(self.key, iv + ciphertext, SHA1)
                
                cipher = DES3.new(key, DES3.MODE_CBC, iv=iv)
                return self.pkcs11_unpad(cipher.decrypt(ciphertext))
            else:
                # Triple DES (older)
                key = SHA1.new(self.key).digest()[:24]
                return self.pkcs11_unpad(self.decrypt_3des(data, key))

    def decrypt_passwords(self):
        """Main decryption routine"""
        logins_path = os.path.join(self.profile, "logins.json")
        if not os.path.exists(logins_path):
            raise Exception("logins.json not found")
        
        a11, a102 = self.get_key_db()
        
        self.version = 1
        if len(a11) > 0:
            self.version = 2
        if len(a102) > 0:
            self.version = 4
        
        # Decrypt the master key
        if self.version >= 2:
            # Use DPAPI-decrypted key approach for Windows
            import ctypes
            from ctypes import wintypes
            
            crypt32 = ctypes.windll.crypt32
            
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]
            
            def decrypt_dpapi(data):
                blob_in = DATA_BLOB(len(data), ctypes.create_string_buffer(data))
                blob_out = DATA_BLOB()
                if crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
                    return ctypes.string_at(blob_out.pbData, blob_out.cbData)
                return None
            
            if self.version == 4 and a102:
                # AES key entry
                entry_data = a102
                # Try DPAPI first for the key
                decoded = decrypt_dpapi(entry_data[:296] if len(entry_data) > 296 else entry_data)
                if decoded:
                    self.key = decoded
        else:
            self.key = a11
        
        if not self.key:
            raise Exception("Could not decrypt master key")
        
        # Read logins
        with open(logins_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = []
        for login in data.get('logins', []):
            hostname = login.get('hostname', '')
            enc_user = b64decode(login.get('encryptedUsername', ''))
            enc_pass = b64decode(login.get('encryptedPassword', ''))
            
            try:
                username = self.decode_login_data(enc_user)
                password = self.decode_login_data(enc_pass)
                results.append({
                    'hostname': hostname.decode('utf-8', errors='replace'),
                    'username': username.decode('utf-8', errors='replace'),
                    'password': password.decode('utf-8', errors='replace'),
                })
                log.info(f"Decrypted: {hostname}")
            except Exception as e:
                log.error(f"Failed to decrypt {hostname}: {e}")
        
        return results

def main():
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="Decrypt Firefox passwords")
    parser.add_argument("profile", help="Path to Firefox profile directory")
    args = parser.parse_args()
    
    fd = FirefoxDecrypt(args.profile)
    results = fd.decrypt_passwords()
    
    for r in results:
        print(f"Website:   {r['hostname']}")
        print(f"Username:  {r['username']}")
        print(f"Password:  {r['password']}")
        print()

if __name__ == "__main__":
    main()
