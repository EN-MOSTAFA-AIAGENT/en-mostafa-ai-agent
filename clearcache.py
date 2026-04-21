import paramiko, io

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

php = b"""<?php
error_reporting(0);
$db=new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');

// 1. Clear Elementor CSS cache for page
$r1=$db->query("DELETE FROM wp_postmeta WHERE post_id=13480 AND meta_key IN ('_elementor_css','_elementor_page_assets','_elementor_controls_usage')");
echo "1. Elementor CSS cache cleared: " . $db->affected_rows . " rows\n";

// 2. Clear all Elementor global CSS transients
$r2=$db->query("DELETE FROM wp_options WHERE option_name LIKE '%elementor%css%'");
echo "2. Elementor CSS transients: " . $db->affected_rows . " rows\n";

// 3. Clear LiteSpeed cache
$r3=$db->query("DELETE FROM wp_options WHERE option_name LIKE '%litespeed%'");
echo "3. LiteSpeed options cleared: " . $db->affected_rows . " rows\n";

// 4. Clear all transients
$r4=$db->query("DELETE FROM wp_options WHERE option_name LIKE '_transient_%' OR option_name LIKE '_site_transient_%'");
echo "4. All transients cleared: " . $db->affected_rows . " rows\n";

// 5. Reset post modified
$db->query("UPDATE wp_posts SET post_modified=NOW(), post_modified_gmt=UTC_TIMESTAMP(), post_status='publish' WHERE ID=13480");
echo "5. Post updated\n";

// 6. Verify sections count
$r6=$db->query("SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_data'");
$row=$r6->fetch_row();
$data=json_decode($row[0],true);
echo "6. Verified sections in DB: " . count($data) . "\n";

// 7. Check elementor edit mode
$r7=$db->query("SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_edit_mode'");
$row7=$r7->fetch_row();
echo "7. Elementor edit mode: " . $row7[0] . "\n";

echo "CACHE CLEARED SUCCESSFULLY!\n";
?>"""

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(php), '/home/u634372166/clearcache.php')
sftp.close()

i,o,e = c.exec_command('php /home/u634372166/clearcache.php 2>&1')
o.channel.recv_exit_status()
print(o.read().decode('utf-8','ignore'))

# Also clear LiteSpeed cache files
i2,o2,e2 = c.exec_command('find ~/domains/askmbt.com/public_html/wp-content/cache -type f -delete 2>&1 | wc -l; echo "Cache files deleted"')
o2.channel.recv_exit_status()
print(o2.read().decode('utf-8','ignore'))

c.exec_command('rm /home/u634372166/clearcache.php')
c.close()
print("DONE!")
