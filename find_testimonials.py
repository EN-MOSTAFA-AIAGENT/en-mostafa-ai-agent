import paramiko, json, io

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

php = b"""<?php
$db=new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$r=$db->query("SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_data'");
$row=$r->fetch_row();
echo $row[0];
?>"""

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(php), '/home/u634372166/g.php')
sftp.close()

i,o,e = c.exec_command('php /home/u634372166/g.php 2>/dev/null')
o.channel.recv_exit_status()
chunks=[]
while True:
    ch=o.read(65536)
    if not ch: break
    chunks.append(ch)
data = json.loads(b''.join(chunks).decode('utf-8','ignore'))

c.exec_command('rm /home/u634372166/g.php')
c.close()

# Find testimonials section
for i, section in enumerate(data):
    sec_str = json.dumps(section, ensure_ascii=False)
    if 'testimonial' in sec_str.lower() or 'Bob' in sec_str or 'Robert Lane' in sec_str or 'edublink-testimonial' in sec_str:
        print(f"Found testimonials in section {i} (id={section['id']})")
        print(json.dumps(section, ensure_ascii=False, indent=2)[:3000])
        print("---")
