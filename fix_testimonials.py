import paramiko, json, io

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

# Get current data
php_get = b"""<?php
$db=new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$r=$db->query("SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_data'");
$row=$r->fetch_row(); echo $row[0];
?>"""
sftp = c.open_sftp()
sftp.putfo(io.BytesIO(php_get), '/home/u634372166/g.php')
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

# ============================================================
# New testimonials content - Arabic MBT
# ============================================================
new_testimonials = [
    {
        "_id": "f39b7d1",
        "name": "د. محمد السيد",
        "designation": "مدير تعليمي - مدرسة الرواد",
        "testimonial": "منصة مقياس غيّرت طريقة تقييمنا للطلاب بشكل كامل. التقارير الفورية والتحليلات الدقيقة ساعدتنا على اتخاذ قرارات تعليمية أكثر فاعلية. أنصح بها كل مؤسسة تعليمية.",
        "thumb": {
            "url": "https://devsedu.softatomic.com/wp-content/uploads/2023/06/testimonial-01.png",
            "id": 7429, "alt": "", "source": "library", "size": ""
        },
        "logo": {"url": "", "id": "", "alt": "", "source": "library", "size": ""},
        "rating": "5"
    },
    {
        "_id": "a12b3c4",
        "name": "أ. فاطمة العمري",
        "designation": "رائدة أعمال تعليمية - أبوظبي",
        "testimonial": "الاختبارات المعيارية التي تقدمها مقياس تتميز بالدقة والاحترافية. النتائج الفورية والتقارير المفصّلة جعلت متابعة أداء الطلاب أمراً سهلاً وممتعاً.",
        "thumb": {
            "url": "https://devsedu.softatomic.com/wp-content/uploads/2023/06/testimonial-02.png",
            "id": 7430, "alt": "", "source": "library", "size": ""
        },
        "logo": {"url": "", "id": "", "alt": "", "source": "library", "size": ""},
        "rating": "5"
    },
    {
        "_id": "d56e7f8",
        "name": "م. خالد المنصوري",
        "designation": "مشرف تربوي - وزارة التعليم",
        "testimonial": "تجربتنا مع مقياس كانت استثنائية. سهولة الاستخدام والدعم المتواصل من الفريق جعلا عملية التقييم سلسة للغاية. المنصة تستحق كل التوصية.",
        "thumb": {
            "url": "https://devsedu.softatomic.com/wp-content/uploads/2023/06/testimonial-03.png",
            "id": 7431, "alt": "", "source": "library", "size": ""
        },
        "logo": {"url": "", "id": "", "alt": "", "source": "library", "size": ""},
        "rating": "5"
    }
]

new_sub_heading = "<p>نفخر بثقة شركائنا في مقياس. اقرأ ما يقوله مديرو المدارس والمشرفون التربويون عن تجربتهم مع منصتنا.</p>"

# ============================================================
# Update section with id "review" (section index 6, id=c621e0c)
# ============================================================
updated = False
for section in data:
    # Check if this is the review section
    if section.get('settings', {}).get('_element_id') == 'review' or section.get('id') == 'c621e0c':
        print(f"Found review section: {section['id']}")
        for col in section.get('elements', []):
            for widget in col.get('elements', []):
                # Update heading sub_heading
                if widget.get('widgetType') == 'edublink-heading':
                    widget['settings']['sub_heading'] = new_sub_heading
                    print(f"  Updated heading sub_heading")
                # Update testimonials
                if widget.get('widgetType') == 'edublink-testimonial':
                    widget['settings']['testimonials'] = new_testimonials
                    print(f"  Updated {len(new_testimonials)} testimonials")
                    updated = True

print(f"Updated: {updated}")

# Save and upload
final_json = json.dumps(data, ensure_ascii=False)
sftp2 = c.open_sftp()
sftp2.putfo(io.BytesIO(final_json.encode('utf-8')), '/home/u634372166/upd.json')
sftp2.close()

php_upd = b"""<?php
error_reporting(0);
$db=new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$json=file_get_contents('/home/u634372166/upd.json');
$stmt=$db->prepare("UPDATE wp_postmeta SET meta_value=? WHERE post_id=13480 AND meta_key='_elementor_data'");
$stmt->bind_param('s',$json);
$ok=$stmt->execute();
echo $ok?"SUCCESS rows=".$stmt->affected_rows:"FAIL:".$db->error;
$stmt->close();
$db->query("UPDATE wp_posts SET post_modified=NOW(),post_modified_gmt=UTC_TIMESTAMP() WHERE ID=13480");
$db->query("DELETE FROM wp_postmeta WHERE post_id=13480 AND meta_key IN ('_elementor_css','_elementor_page_assets')");
$db->query("DELETE FROM wp_options WHERE option_name LIKE '%elementor%css%' OR option_name LIKE '_transient_%' OR option_name LIKE '%litespeed%'");
echo " | done";
?>"""

sftp3 = c.open_sftp()
sftp3.putfo(io.BytesIO(php_upd), '/home/u634372166/upd.php')
sftp3.close()

i2,o2,e2 = c.exec_command('php /home/u634372166/upd.php 2>&1')
o2.channel.recv_exit_status()
print(f"DB Update: {o2.read().decode('utf-8','ignore')}")

# Clear file cache
i3,o3,e3 = c.exec_command('find ~/domains/askmbt.com/public_html/wp-content/cache/ -type f -delete 2>/dev/null; echo cache_cleared')
o3.channel.recv_exit_status()
print(o3.read().decode())

c.exec_command('rm /home/u634372166/upd.json /home/u634372166/upd.php 2>/dev/null')
c.close()
print("DONE!")
