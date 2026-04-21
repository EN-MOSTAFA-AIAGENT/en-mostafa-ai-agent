import paramiko, json, re

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

# Get current elementor data
i, o, e = c.exec_command("mysql -h 127.0.0.1 -u u634372166_Xgj7D -pX4JX8XdvZf u634372166_KpQVV -se \"SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_data'\" 2>&1")
o.channel.recv_exit_status()
current_data = o.read().decode("utf-8", "ignore")
err = e.read().decode("utf-8", "ignore")

with open("C:/mcp-agent/current_el_data.txt", "w", encoding="utf-8") as f:
    f.write(current_data[:2000])

print("Current data length:", len(current_data))
print("First 300 chars:", current_data[:300])
c.close()
