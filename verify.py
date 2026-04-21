import paramiko, json, io

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

# Verify by checking sections count after update
php_verify = """<?php
$db = new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$r = $db->query("SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_data'");
$row = $r->fetch_row();
$data = json_decode($row[0], true);
echo 'sections=' . count($data) . ' | len=' . strlen($row[0]);
?>"""

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(php_verify.encode('utf-8')), '/home/u634372166/verify.php')
sftp.close()

i,o,e = c.exec_command('php /home/u634372166/verify.php 2>&1')
o.channel.recv_exit_status()
print("Verify:", o.read().decode('utf-8','ignore'))

# If still 12, do direct update
php_update = """<?php
error_reporting(E_ALL);
ini_set('display_errors',1);
$db = new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
if($db->connect_error){ die('Connect error: '.$db->connect_error); }
$db->set_charset('utf8mb4');
$json = file_get_contents('/home/u634372166/new_data.json');
if(!$json){ die('File not found!'); }
$stmt = $db->prepare("UPDATE wp_postmeta SET meta_value=? WHERE post_id=13480 AND meta_key='_elementor_data'");
$stmt->bind_param('s', $json);
$result = $stmt->execute();
echo $result ? 'SUCCESS rows='.$stmt->affected_rows : 'ERROR:'.$stmt->error;
$stmt->close();

// Update post modified time
$db->query("UPDATE wp_posts SET post_modified=NOW(), post_modified_gmt=UTC_TIMESTAMP() WHERE ID=13480");

// Clear all caches
$db->query("DELETE FROM wp_postmeta WHERE post_id=13480 AND meta_key IN ('_elementor_css','_elementor_page_assets')");

// Also delete transients
$db->query("DELETE FROM wp_options WHERE option_name LIKE '%elementor%' AND option_name LIKE '%css%'");

echo ' | Done';
?>"""

sftp2 = c.open_sftp()
sftp2.putfo(io.BytesIO(php_update.encode('utf-8')), '/home/u634372166/update2.php')

# Also re-upload the JSON in case it was deleted
with open("C:/mcp-agent/new_el_sections.json", "r", encoding="utf-8") as f:
    new_json = f.read()
sftp2.putfo(io.BytesIO(new_json.encode('utf-8')), '/home/u634372166/new_data.json')
sftp2.close()

i2,o2,e2 = c.exec_command('php /home/u634372166/update2.php 2>&1')
o2.channel.recv_exit_status()
print("Update:", o2.read().decode('utf-8','ignore'))

# Verify again
i3,o3,e3 = c.exec_command('php /home/u634372166/verify.php 2>&1')
o3.channel.recv_exit_status()
print("Final verify:", o3.read().decode('utf-8','ignore'))

c.exec_command('rm /home/u634372166/verify.php /home/u634372166/update2.php /home/u634372166/new_data.json 2>/dev/null')
c.close()
