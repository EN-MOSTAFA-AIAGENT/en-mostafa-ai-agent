import paramiko, json, io, re

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

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
# الأسماء الصحيحة الوحيدة
# ============================================================
TEAM = [
    {
        "name": "أ. محمد طلعت",
        "designation": "مدير تطوير الأعمال",
        "phone": "+971 54 538 7535"
    },
    {
        "name": "د. جمال عبد الحميد",
        "designation": "الرئيس التنفيذي (CEO)",
        "phone": "+971 55 516 9149"
    }
]

# أسماء يجب استبدالها
WRONG_NAMES = [
    "Bob Limones", "Robert Lane", "John Travolta", "Penelope Cruz",
    "Edward Norton", "Jane Seymour", "Tom Harley", "د. محمد السيد",
    "أ. فاطمة العمري", "م. خالد المنصوري", "Robert Lune",
    "Wordpress Expert", "Graphic Designer", "Web Developer", "UX Designer",
    "Student", "Developer", "Content Creator", "Instructor"
]

changes = []

def fix_names_deep(obj, path=""):
    """Traverse and fix all name/designation fields"""
    if isinstance(obj, dict):
        # Fix testimonials list
        if 'testimonials' in obj:
            for idx, t in enumerate(obj['testimonials']):
                old_name = t.get('name', '')
                if old_name and old_name not in [tm['name'] for tm in TEAM]:
                    member = TEAM[idx % len(TEAM)]
                    t['name'] = member['name']
                    t['designation'] = member['designation']
                    t['testimonial'] = get_testimonial(idx)
                    changes.append(f"Testimonial: '{old_name}' → '{member['name']}'")

        # Fix team members list
        if 'team_members' in obj or 'members' in obj:
            members_key = 'team_members' if 'team_members' in obj else 'members'
            for idx, m in enumerate(obj[members_key]):
                old_name = m.get('name', '')
                if old_name and old_name not in [tm['name'] for tm in TEAM]:
                    member = TEAM[idx % len(TEAM)]
                    m['name'] = member['name']
                    if 'designation' in m: m['designation'] = member['designation']
                    if 'position' in m: m['position'] = member['designation']
                    if 'description' in m: m['description'] = f"خبير متخصص في مجال التقييم التعليمي والتطوير المؤسسي"
                    changes.append(f"Team member: '{old_name}' → '{member['name']}'")

        # Fix individual name/designation fields
        for key in ['name', 'author_name', 'member_name']:
            if key in obj and isinstance(obj[key], str):
                val = obj[key]
                if val and val not in [tm['name'] for tm in TEAM] and any(w in val for w in ['Bob', 'Robert', 'John', 'Penelope', 'Edward', 'Jane', 'Tom', 'Lorem']):
                    new_name = TEAM[0]['name']
                    changes.append(f"Field '{key}': '{val}' → '{new_name}'")
                    obj[key] = new_name

        for key in ['designation', 'position', 'job_title', 'role']:
            if key in obj and isinstance(obj[key], str):
                val = obj[key]
                if val in ['Student', 'Developer', 'Instructor', 'Wordpress Expert', 'Graphic Designer', 'Web Developer', 'UX Designer', 'Content Creator']:
                    obj[key] = TEAM[0]['designation']
                    changes.append(f"Field '{key}': '{val}' → '{TEAM[0]['designation']}'")

        return {k: fix_names_deep(v, path+'.'+k) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [fix_names_deep(item, path+f'[{i}]') for i, item in enumerate(obj)]

    elif isinstance(obj, str):
        result = obj
        for wrong in WRONG_NAMES:
            if wrong in result:
                # Smart replacement based on context
                if 'Bob' in wrong or 'Robert' in wrong:
                    result = result.replace(wrong, TEAM[0]['name'])
                    changes.append(f"String replace: '{wrong}' → '{TEAM[0]['name']}'")
                elif 'John' in wrong or 'Edward' in wrong:
                    result = result.replace(wrong, TEAM[1]['name'])
                    changes.append(f"String replace: '{wrong}' → '{TEAM[1]['name']}'")
                elif wrong in ['Student', 'Developer']:
                    result = result.replace(wrong, TEAM[0]['designation'])
                elif wrong in ['Instructor', 'Wordpress Expert']:
                    result = result.replace(wrong, TEAM[1]['designation'])
        return result

    return obj

def get_testimonial(idx):
    testimonials = [
        "منصة مقياس غيّرت طريقة تقييمنا للطلاب بشكل كامل. التقارير الفورية والتحليلات الدقيقة ساعدتنا على اتخاذ قرارات تعليمية أكثر فاعلية. أنصح بها كل مؤسسة تعليمية.",
        "الاختبارات المعيارية التي تقدمها مقياس تتميز بالدقة والاحترافية. النتائج الفورية والتقارير المفصّلة جعلت متابعة أداء الطلاب أمراً سهلاً ومثمراً.",
        "تجربتنا مع مقياس كانت استثنائية. سهولة الاستخدام والدعم المتواصل من الفريق جعلا عملية التقييم سلسة للغاية. المنصة تستحق كل التوصية."
    ]
    return testimonials[idx % len(testimonials)]

# Apply fixes
print("Scanning page for wrong names...")
fixed_data = fix_names_deep(data)

if changes:
    print(f"\nFound and fixed {len(changes)} issues:")
    for ch in changes:
        print(f"  ✅ {ch}")
else:
    print("No issues found!")

# Upload and update
final_json = json.dumps(fixed_data, ensure_ascii=False)
sftp2 = c.open_sftp()
sftp2.putfo(io.BytesIO(final_json.encode('utf-8')), '/home/u634372166/fixed.json')
sftp2.close()

php_upd = b"""<?php
error_reporting(0);
$db=new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$json=file_get_contents('/home/u634372166/fixed.json');
$stmt=$db->prepare("UPDATE wp_postmeta SET meta_value=? WHERE post_id=13480 AND meta_key='_elementor_data'");
$stmt->bind_param('s',$json);
$ok=$stmt->execute();
echo $ok?"SUCCESS rows=".$stmt->affected_rows:"FAIL:".$db->error;
$stmt->close();
$db->query("UPDATE wp_posts SET post_modified=NOW(),post_modified_gmt=UTC_TIMESTAMP() WHERE ID=13480");
$db->query("DELETE FROM wp_postmeta WHERE post_id=13480 AND meta_key IN ('_elementor_css','_elementor_page_assets')");
$db->query("DELETE FROM wp_options WHERE option_name LIKE '%elementor%css%' OR option_name LIKE '_transient_%' OR option_name LIKE '%litespeed%'");
echo " | cache_cleared";
?>"""

sftp3 = c.open_sftp()
sftp3.putfo(io.BytesIO(php_upd), '/home/u634372166/upd.php')
sftp3.close()

i2,o2,e2 = c.exec_command('php /home/u634372166/upd.php 2>&1')
o2.channel.recv_exit_status()
print(f"\nDB: {o2.read().decode('utf-8','ignore')}")

i3,o3,e3 = c.exec_command('find ~/domains/askmbt.com/public_html/wp-content/cache/ -type f -delete 2>/dev/null; echo cache_files_cleared')
o3.channel.recv_exit_status()
print(o3.read().decode())

c.exec_command('rm /home/u634372166/fixed.json /home/u634372166/upd.php 2>/dev/null')
c.close()
print("ALL DONE!")
