import paramiko, json, io

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

php = b"""<?php
$db=new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');

// Get front page ID from options
$r=$db->query("SELECT option_value FROM wp_options WHERE option_name='page_on_front'");
$row=$r->fetch_row();
echo "page_on_front=" . $row[0] . "\n";

$r2=$db->query("SELECT option_value FROM wp_options WHERE option_name='show_on_front'");
$row2=$r2->fetch_row();
echo "show_on_front=" . $row2[0] . "\n";

// Get elementor data for page 13480
$r3=$db->query("SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_data'");
$row3=$r3->fetch_row();
$data=json_decode($row3[0], true);
echo "page_13480_sections=" . count($data) . "\n";

// Check first and last section IDs and titles to verify
echo "First section id: " . $data[0]['id'] . "\n";
echo "Last section id: " . $data[count($data)-1]['id'] . "\n";

// Check last section background color (should be #7A51E1 for CTA)
$last = $data[count($data)-1];
echo "Last section bg: " . ($last['settings']['background_color'] ?? 'N/A') . "\n";

// Check second to last (should be why section)
$why = $data[count($data)-2];
echo "Why section bg: " . ($why['settings']['background_color'] ?? 'N/A') . "\n";
?>"""

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(php), '/home/u634372166/check.php')
sftp.close()

i,o,e = c.exec_command('php /home/u634372166/check.php 2>&1')
o.channel.recv_exit_status()
print(o.read().decode('utf-8','ignore'))

c.exec_command('rm /home/u634372166/check.php')
c.close()
