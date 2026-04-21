import json, paramiko, io

# Arabic replacements for all text content
REPLACEMENTS = {
    # Headings
    "Top Categories": "خدماتنا الرئيسية",
    "Consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore": "نقدم حلولاً تعليمية متكاملة تلبي احتياجات مؤسستك وتطوّر أداء طلابك",
    "Personal Development": "الاستشارات التعليمية",
    "Arts & Design": "البرامج القيادية",
    "Business Management": "التدريب التقني",
    "Marketing": "البرامج اللغوية",
    "Data Science": "تصميم الاختبارات",
    "Health & Fitness": "تقارير الأداء",
    "Video & Photography": "التقييم الإلكتروني",
    "Computer Science": "تطوير المناهج",
    "Business & Finance": "الشهادات المعتمدة",
    # About section
    "ABOUT US": "من نحن",
    "Learn & Grow Your Skills": "قِس وطوّر أداء",
    "From <span": "طلابك مع <span",
    "Anywhere": "مقياس",
    "Lorem ipsum dolor sit amet consectetur adipiscing elit sed eiusmod ex tempor incididunt labore dolore magna aliquaenim minim veniam quis nostrud exercitation ullamco laboris": "منصة مقياس متخصصة في التدريب والتطوير والاستشارات التعليمية. نُمكّن الأفراد والمؤسسات عبر برامج مهنية متوافقة مع متطلبات سوق العمل ونحول المعرفة إلى مهارات قابلة للقياس.",
    "Lorem ipsum dolor sit amet consectetur adipiscing elit sed eiusmod ex tempor incididunt labore dolore magna aliquaenim minim veniam quis .nostrud exercitation ullamco laboris": "منصة مقياس متخصصة في التدريب والتطوير والاستشارات التعليمية. نُمكّن الأفراد والمؤسسات عبر برامج مهنية متوافقة مع متطلبات سوق العمل ونحول المعرفة إلى مهارات قابلة للقياس.",
    "Expert Trainers": "اختبارات معيارية دقيقة",
    "Online Remote Learning": "تصحيح تلقائي فوري",
    "Lifetime Access": "تقارير تحليلية شاملة",
    # Courses section
    "POPULAR COURSES": "اختباراتنا المعيارية",
    "Pick A Course To Get Started": "اختر الاختبار المناسب لمدرستك",
    "Browse more courses": "استعرض جميع الاختبارات",
    # Stats section
    "COURSES CREATED": "اختبار معياري",
    "ACTIVE STUDENTS": "طالب مُقيَّم",
    "CERTIFIED STUDENTS": "مدرسة شريكة",
    "INSTRUCTORS": "خبير تربوي",
    # Testimonials
    "TESTIMONIALS": "آراء شركائنا",
    "What Our Students Have To Say": "ماذا يقول شركاؤنا عن مقياس؟",
    "View All": "عرض الكل",
    # Call Us
    "CALL US NOW": "تواصل معنا",
    "GET IN TOUCH": "راسلنا",
    "Info@edublink": "info@askmbt.com",
    # Instructors
    "INSTRUCTORS": "فريقنا",
    "Course Instructors": "فريق خبراء مقياس",
    # Certificate CTA
    "Get Your Quality Skills Certificate": "ابدأ رحلة التقييم المعياري",
    "Through EduBlink": "مع منصة مقياس",
    "Get Started Now": "تواصل معنا الآن",
    # Partners
    "OUR PARTNERS": "شركاؤنا",
    "Learn with Our Partners": "شركاؤنا في التميز التعليمي",
    "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua": "نفخر بشراكتنا مع مؤسسات تعليمية رائدة تشاركنا رؤيتنا في تطوير التعليم وقياس الجودة",
    # News/Blog
    "LATEST ARTICLES": "أحدث أخبارنا",
    "Get News with EduBlink": "أحدث أخبار منصة مقياس",
    # Footer newsletter
    "Media world": "عالم التعليم",
    "Your email address": "بريدك الإلكتروني",
    "Subscribe": "اشترك",
    # Common lorem ipsum
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt": "منصة مقياس - رائدة في الاختبارات المعيارية والتقييم الإلكتروني",
    "lorem ipsum dolor sit amet consectetur": "تواصل معنا للحصول على عرض مخصص لمدرستك",
    # Button texts
    "Read More": "اقرأ المزيد",
    "Learn More": "اعرف أكثر",
    "Enroll Now": "سجّل الآن",
    "Start Learning": "ابدأ التقييم",
    "Become A Teacher": "انضم لفريقنا",
    "Find Courses": "استعرض الاختبارات",
    # Numbers stats  
    "6,000+": "+500",
    "Membership": "مدرسة",
    "Online Courses": "اختبار معياري",
    "Top Instructors": "خبير تربوي",
    "Students World Wide": "طالب مُقيَّم",
    "4000": "+10,000",
    "453": "+98%",
    "K4.23": "500+",
    "K2.54": "10,000+",
    "%9.99": "98%",
    # Names - replace with MBT team
    "John Travolta": "د. جمال عبدالحميد",
    "Penelope Cruz": "أ. محمد طلعت",
    "Edward Norton": "د. أحمد السيد",
    "Jane Seymour": "أ. سارة محمد",
    # Titles
    "Wordpress Expert": "رئيس تنفيذي",
    "Graphic Designer": "مدير تطوير الأعمال",
    "Web Developer": "خبير تربوي",
    "UX Designer": "مستشارة تعليمية",
    # Blog articles
    "Crafting Effective Learning Guide One": "دليل التقييم المعياري الشامل",
    "Exploring Learning Landscapes in Academia": "كيف تختار نظام الاختبارات لمدرستك؟",
}

def deep_replace(obj, replacements):
    """Recursively replace text in Elementor JSON"""
    if isinstance(obj, str):
        for old, new in replacements.items():
            if old in obj:
                obj = obj.replace(old, new)
        return obj
    elif isinstance(obj, dict):
        return {k: deep_replace(v, replacements) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_replace(item, replacements) for item in obj]
    return obj

# Load original backup
with open("C:/mcp-agent/current.json", "r", encoding="utf-8") as f:
    original = json.load(f)

print(f"Original sections: {len(original)}")

# Apply replacements to sections 1-11 (keep Hero section 0 UNTOUCHED)
hero = original[0]  # Section 0 = Hero, DON'T TOUCH
rest = original[1:]  # Sections 1-11

# Apply Arabic replacements
arabized = deep_replace(rest, REPLACEMENTS)

# Combine: Hero + Arabized sections
final = [hero] + arabized

final_json = json.dumps(final, ensure_ascii=False)
print(f"Final: {len(final)} sections, {len(final_json)} bytes")

# Save locally
with open("C:/mcp-agent/arabized.json", "w", encoding="utf-8") as f:
    f.write(final_json)

# Upload to server and update DB
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(final_json.encode('utf-8')), '/home/u634372166/arabized.json')
sftp.close()

php_upd = b"""<?php
error_reporting(0);
$db=new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$json=file_get_contents('/home/u634372166/arabized.json');
$stmt=$db->prepare("UPDATE wp_postmeta SET meta_value=? WHERE post_id=13480 AND meta_key='_elementor_data'");
$stmt->bind_param('s',$json);
$ok=$stmt->execute();
echo $ok?"SUCCESS rows=".$stmt->affected_rows:"FAIL:".$db->error;
$stmt->close();
$db->query("UPDATE wp_posts SET post_modified=NOW(),post_modified_gmt=UTC_TIMESTAMP() WHERE ID=13480");
$db->query("DELETE FROM wp_postmeta WHERE post_id=13480 AND meta_key IN ('_elementor_css','_elementor_page_assets')");
$db->query("DELETE FROM wp_options WHERE option_name LIKE '%elementor%css%' OR option_name LIKE '_transient_%' OR option_name LIKE '%litespeed%'");
echo " | cache_cleared";

// Verify
$r=$db->query("SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_data'");
$row=$r->fetch_row();
$d=json_decode($row[0],true);
echo " | sections=".count($d);
?>"""

sftp2 = c.open_sftp()
sftp2.putfo(io.BytesIO(php_upd), '/home/u634372166/upd.php')
sftp2.close()

i,o,e = c.exec_command('php /home/u634372166/upd.php 2>&1')
o.channel.recv_exit_status()
print(f"Update: {o.read().decode('utf-8','ignore')}")

# Clear file cache
i2,o2,e2 = c.exec_command('find ~/domains/askmbt.com/public_html/wp-content/cache/ -type f -delete 2>/dev/null; echo "cache_files_cleared"')
o2.channel.recv_exit_status()
print(o2.read().decode())

c.exec_command('rm /home/u634372166/upd.php /home/u634372166/arabized.json 2>/dev/null')
c.close()
print("DONE!")
