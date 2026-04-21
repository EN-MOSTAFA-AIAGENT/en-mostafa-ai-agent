import paramiko, json

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

# Use PHP to get clean elementor data
php = """<?php
define('ABSPATH', '/home/u634372166/domains/askmbt.com/public_html/');
$db = new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$r = $db->query("SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_data'");
$row = $r->fetch_row();
echo $row[0];
?>"""

sftp = c.open_sftp()
import io
sftp.putfo(io.BytesIO(php.encode()), '/home/u634372166/getdata.php')
sftp.close()

i,o,e = c.exec_command('php /home/u634372166/getdata.php 2>&1')
o.channel.recv_exit_status()

chunks = []
while True:
    chunk = o.read(65536)
    if not chunk:
        break
    chunks.append(chunk)

raw = b''.join(chunks).decode('utf-8','ignore')
c.close()

with open("C:/mcp-agent/current.json", "w", encoding="utf-8") as f:
    f.write(raw)

print(f"len={len(raw)}")

try:
    data = json.loads(raw)
    print(f"sections={len(data)}")
except Exception as ex:
    print(f"JSON error: {ex}")
    print(f"Last 100 chars: {repr(raw[-100:])}")
