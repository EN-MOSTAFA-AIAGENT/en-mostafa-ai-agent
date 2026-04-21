import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

# Get elementor data length
i, o, e = c.exec_command("mysql -h 127.0.0.1 -u u634372166_Xgj7D -pX4JX8XdvZf u634372166_KpQVV -e \"SHOW TABLES\" 2>&1")
o.channel.recv_exit_status()
tables = o.read().decode("utf-8", "ignore")

i2, o2, e2 = c.exec_command("mysql -h 127.0.0.1 -u u634372166_Xgj7D -pX4JX8XdvZf u634372166_KpQVV -e \"SELECT meta_key FROM wp_postmeta WHERE post_id=13480 LIMIT 20\" 2>&1")
o2.channel.recv_exit_status()
keys = o2.read().decode("utf-8", "ignore")

with open("C:/mcp-agent/db_info.txt", "w", encoding="utf-8") as f:
    f.write("=== TABLES ===\n" + tables + "\n")
    f.write("=== META KEYS for page 13480 ===\n" + keys + "\n")

c.close()
print("DONE")
