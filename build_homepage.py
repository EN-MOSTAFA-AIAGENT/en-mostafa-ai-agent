import paramiko, json, uuid, io

def uid():
    return uuid.uuid4().hex[:7]

def section_about():
    return {"id":uid(),"elType":"section","isInner":False,"settings":{"gap":"no","structure":"20","background_background":"classic","background_color":"#ffffff","padding":{"unit":"px","top":"80","right":"120","bottom":"80","left":"120","isLinked":False},"padding_mobile":{"unit":"px","top":"40","right":"20","bottom":"40","left":"20","isLinked":False}},"elements":[{"id":uid(),"elType":"column","settings":{"_column_size":50,"_inline_size":None,"direction_mobile":"column"},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"من نحن","header_size":"h6","title_color":"#7A51E1","typography_font_weight":"700","align":"right","title_margin":{"unit":"px","top":"0","right":"0","bottom":"10","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"منصة مقياس للاختبارات المعيارية والتقييمية","header_size":"h2","title_color":"#1A1A2E","typography_font_size":{"unit":"px","size":32},"typography_font_weight":"700","align":"right","title_margin":{"unit":"px","top":"0","right":"0","bottom":"20","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"text-editor","settings":{"editor":"<p style=\"text-align:right;color:#666;font-size:16px;line-height:1.9;\">منصة متخصصة في التدريب والتطوير والاستشارات التعليمية، تُمكّن الأفراد والمؤسسات عبر برامج مهنية متوافقة مع متطلبات سوق العمل. نؤمن بأن التميز الحقيقي يتحقق عندما تتكامل الرؤية مع جودة التنفيذ ودقة القياس.</p>","_margin":{"unit":"px","top":"0","right":"0","bottom":"30","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"button","settings":{"text":"اعرف أكثر عنّا","link":{"url":"/about-us-1/","is_external":False},"align":"right","size":"md","background_color":"#7A51E1","button_text_color":"#ffffff","border_radius":{"unit":"px","top":"8","right":"8","bottom":"8","left":"8","isLinked":True}}}]},{"id":uid(),"elType":"column","settings":{"_column_size":50,"_inline_size":None},"elements":[{"id":uid(),"elType":"widget","widgetType":"counter","settings":{"starting_number":0,"ending_number":500,"prefix":"","suffix":"+","duration":2000,"title":"مدرسة شريكة","number_color":"#7A51E1","title_color":"#1A1A2E","number_size":{"unit":"px","size":48},"title_size":{"unit":"px","size":16},"align":"center","_margin":{"unit":"px","top":"0","right":"0","bottom":"30","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"counter","settings":{"starting_number":0,"ending_number":10000,"prefix":"","suffix":"+","duration":2000,"title":"طالب تم تقييمه","number_color":"#7A51E1","title_color":"#1A1A2E","number_size":{"unit":"px","size":48},"title_size":{"unit":"px","size":16},"align":"center","_margin":{"unit":"px","top":"0","right":"0","bottom":"30","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"counter","settings":{"starting_number":0,"ending_number":98,"prefix":"","suffix":"%","duration":2000,"title":"نسبة رضا العملاء","number_color":"#7A51E1","title_color":"#1A1A2E","number_size":{"unit":"px","size":48},"title_size":{"unit":"px","size":16},"align":"center"}}]}]}

def section_how_it_works():
    steps = [
        {"num":"01","title":"تسجيل المدرسة","desc":"تتواصل المدرسة معنا ويتم إعداد حساب مخصص بسهولة وسرعة خلال 24 ساعة","icon":"fa fa-school"},
        {"num":"02","title":"تنفيذ الاختبار","desc":"يؤدي الطلاب الاختبارات المعيارية إلكترونياً بإشراف كامل وبيئة آمنة وموثوقة","icon":"fa fa-pencil-alt"},
        {"num":"03","title":"النتائج والتقارير","desc":"تحصل المدرسة على تقارير تحليلية دقيقة فور الانتهاء لاتخاذ قرارات تعليمية مدروسة","icon":"fa fa-chart-bar"},
    ]
    cols = []
    for s in steps:
        cols.append({"id":uid(),"elType":"column","settings":{"_column_size":33,"_inline_size":None},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":s["num"],"header_size":"h1","title_color":"rgba(122,81,225,0.15)","typography_font_size":{"unit":"px","size":80},"typography_font_weight":"900","align":"center","title_margin":{"unit":"px","top":"0","right":"0","bottom":"0","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":s["title"],"header_size":"h4","title_color":"#1A1A2E","typography_font_weight":"700","align":"center","title_margin":{"unit":"px","top":"10","right":"0","bottom":"15","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"text-editor","settings":{"editor":f"<p style=\"text-align:center;color:#666;font-size:15px;line-height:1.8;\">{s['desc']}</p>"}}]})
    return {"id":uid(),"elType":"section","isInner":False,"settings":{"structure":"333","background_background":"classic","background_color":"#F6F4FF","padding":{"unit":"px","top":"80","right":"120","bottom":"80","left":"120","isLinked":False}},"elements":[{"id":uid(),"elType":"column","settings":{"_column_size":100,"_inline_size":None},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"كيف تعمل منصة مقياس؟","header_size":"h2","title_color":"#1A1A2E","typography_font_size":{"unit":"px","size":36},"typography_font_weight":"700","align":"center","title_margin":{"unit":"px","top":"0","right":"0","bottom":"10","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"text-editor","settings":{"editor":"<p style=\"text-align:center;color:#666;font-size:16px;margin-bottom:50px;\">ثلاث خطوات بسيطة تفصلك عن قياس أداء طلابك بدقة واحترافية</p>"}}]}]+cols}

def section_services():
    services = [
        {"title":"الاستشارات التعليمية","desc":"تطوير الأداء المؤسسي وتحسين البيئة التعليمية وفق أحدث المعايير الدولية","icon":"fa fa-lightbulb"},
        {"title":"البرامج القيادية والإدارية","desc":"تنمية الموارد البشرية وبناء قيادات تعليمية قادرة على صناعة الأثر","icon":"fa fa-users"},
        {"title":"البرامج اللغوية","desc":"برامج متخصصة للأغراض الأكاديمية والمهنية بمعايير عالمية معتمدة","icon":"fa fa-language"},
        {"title":"التدريب التقني والرقمي","desc":"تصميم أنظمة تقييم إلكتروني متطورة تواكب متطلبات التحول الرقمي","icon":"fa fa-laptop-code"},
    ]
    cols = []
    for s in services:
        cols.append({"id":uid(),"elType":"column","settings":{"_column_size":25,"_inline_size":None},"elements":[{"id":uid(),"elType":"widget","widgetType":"icon-box","settings":{"icon":{"value":s["icon"],"library":"fa-solid"},"title_text":s["title"],"description_text":s["desc"],"position":"top","icon_color":"#7A51E1","title_color":"#1A1A2E","description_color":"#666","title_size":"h5","_background_background":"classic","_background_color":"#ffffff","_border_radius":{"unit":"px","top":"12","right":"12","bottom":"12","left":"12","isLinked":True},"_padding":{"unit":"px","top":"35","right":"30","bottom":"35","left":"30","isLinked":False},"_box_shadow_box_shadow_type":"yes","_box_shadow_box_shadow":{"horizontal":0,"vertical":8,"blur":30,"spread":0,"color":"rgba(122,81,225,0.12)"},"_margin":{"unit":"px","top":"0","right":"10","bottom":"10","left":"10","isLinked":False},"icon_size":{"unit":"px","size":40}}}]})
    return {"id":uid(),"elType":"section","isInner":False,"settings":{"background_background":"classic","background_color":"#ffffff","padding":{"unit":"px","top":"80","right":"120","bottom":"80","left":"120","isLinked":False}},"elements":[{"id":uid(),"elType":"column","settings":{"_column_size":100,"_inline_size":None},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"خدماتنا","header_size":"h6","title_color":"#7A51E1","typography_font_weight":"700","align":"center"}},{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"حلول تعليمية متكاملة لمؤسستك","header_size":"h2","title_color":"#1A1A2E","typography_font_size":{"unit":"px","size":36},"typography_font_weight":"700","align":"center","title_margin":{"unit":"px","top":"10","right":"0","bottom":"50","left":"0","isLinked":False}}}]}]+cols}

def section_why():
    features = [
        {"title":"اختبارات معيارية دقيقة","desc":"اختبارات مصممة وفق معايير دولية معتمدة لقياس المستوى الحقيقي للطلاب"},
        {"title":"تصحيح تلقائي فوري","desc":"نتائج فورية بمجرد إنهاء الاختبار بدون انتظار مع دقة 100% في التصحيح"},
        {"title":"تقارير تحليلية شاملة","desc":"تقارير تفصيلية لكل طالب وصف ومدرسة لاتخاذ قرارات تعليمية مدروسة"},
        {"title":"سهولة الاستخدام","desc":"واجهة سلسة للمعلمين والطلاب دون الحاجة لأي خبرة تقنية مسبقة"},
        {"title":"دعم كامل ومتواصل","desc":"فريق متخصص يدعمك في كل خطوة من الإعداد حتى الحصول على النتائج"},
        {"title":"تقييم فردي متخصص","desc":"تحليل أداء كل طالب بشكل منفرد لمتابعة التقدم وتحديد نقاط التطوير"},
    ]
    cols = []
    for f in features:
        cols.append({"id":uid(),"elType":"column","settings":{"_column_size":33,"_inline_size":None},"elements":[{"id":uid(),"elType":"widget","widgetType":"icon-box","settings":{"icon":{"value":"fa fa-check-circle","library":"fa-solid"},"title_text":f["title"],"description_text":f["desc"],"position":"left","icon_color":"#7A51E1","title_color":"#1A1A2E","description_color":"#666","title_size":"h5","icon_size":{"unit":"px","size":28},"_margin":{"unit":"px","top":"0","right":"0","bottom":"30","left":"0","isLinked":False}}}]})
    return {"id":uid(),"elType":"section","isInner":False,"settings":{"structure":"333","background_background":"classic","background_color":"#F6F4FF","padding":{"unit":"px","top":"80","right":"120","bottom":"80","left":"120","isLinked":False}},"elements":[{"id":uid(),"elType":"column","settings":{"_column_size":100,"_inline_size":None},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"لماذا تختار منصة مقياس؟","header_size":"h2","title_color":"#1A1A2E","typography_font_size":{"unit":"px","size":36},"typography_font_weight":"700","align":"center","title_margin":{"unit":"px","top":"0","right":"0","bottom":"10","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"text-editor","settings":{"editor":"<p style=\"text-align:center;color:#666;font-size:16px;margin-bottom:50px;\">نقدم لك كل ما تحتاجه لقياس وتطوير الأداء التعليمي في مكان واحد</p>"}}]}]+cols}

def section_cta():
    return {"id":uid(),"elType":"section","isInner":False,"settings":{"background_background":"classic","background_color":"#7A51E1","padding":{"unit":"px","top":"100","right":"120","bottom":"100","left":"120","isLinked":False}},"elements":[{"id":uid(),"elType":"column","settings":{"_column_size":100,"_inline_size":None},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"ابدأ رحلتك التعليمية مع مقياس اليوم","header_size":"h2","title_color":"#ffffff","typography_font_size":{"unit":"px","size":40},"typography_font_weight":"700","align":"center","title_margin":{"unit":"px","top":"0","right":"0","bottom":"20","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"text-editor","settings":{"editor":"<p style=\"text-align:center;color:rgba(255,255,255,0.85);font-size:18px;line-height:1.8;margin-bottom:40px;\">انضم إلى مئات المدارس التي تثق في منصة مقياس لتقييم طلابها وتطوير أدائها التعليمي</p>"}},{"id":uid(),"elType":"widget","widgetType":"button","settings":{"text":"تواصل معنا الآن","link":{"url":"/contact-us/","is_external":False},"align":"center","size":"xl","background_color":"#ffffff","button_text_color":"#7A51E1","hover_color":"#F6F4FF","border_radius":{"unit":"px","top":"8","right":"8","bottom":"8","left":"8","isLinked":True},"_margin":{"unit":"px","top":"0","right":"15","bottom":"0","left":"15","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"button","settings":{"text":"استعرض خدماتنا","link":{"url":"/courses/","is_external":False},"align":"center","size":"xl","background_color":"transparent","button_text_color":"#ffffff","hover_color":"rgba(255,255,255,0.1)","border_border":"solid","border_width":{"unit":"px","top":"2","right":"2","bottom":"2","left":"2","isLinked":True},"border_color":"#ffffff","border_radius":{"unit":"px","top":"8","right":"8","bottom":"8","left":"8","isLinked":True}}}]}]}

# Connect SSH
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

# Get current data via PHP
php_get = """<?php
$db = new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$r = $db->query("SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_data'");
$row = $r->fetch_row();
echo $row[0];
?>"""

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(php_get.encode('utf-8')), '/home/u634372166/getdata.php')
sftp.close()

i,o,e = c.exec_command('php /home/u634372166/getdata.php 2>/dev/null')
o.channel.recv_exit_status()

chunks = []
while True:
    chunk = o.read(65536)
    if not chunk:
        break
    chunks.append(chunk)

current_raw = b''.join(chunks).decode('utf-8','ignore')
current_sections = json.loads(current_raw)
print(f"Got {len(current_sections)} current sections")

# Build new sections
new_sections = [
    section_about(),
    section_how_it_works(),
    section_services(),
    section_why(),
    section_cta(),
]

# Merge
all_sections = current_sections + new_sections
new_json = json.dumps(all_sections, ensure_ascii=False)
print(f"Total {len(all_sections)} sections, JSON size: {len(new_json)}")

# Upload JSON via SFTP
sftp2 = c.open_sftp()
sftp2.putfo(io.BytesIO(new_json.encode('utf-8')), '/home/u634372166/new_data.json')
sftp2.close()
print("JSON uploaded to server")

# PHP script to update DB
php_update = """<?php
$db = new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$json = file_get_contents('/home/u634372166/new_data.json');
$json = wp_slash($json);
// Use raw update without wp_slash since we're direct
$db2 = new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db2->set_charset('utf8mb4');
$json2 = file_get_contents('/home/u634372166/new_data.json');
$escaped = $db2->real_escape_string($json2);
$result = $db2->query("UPDATE wp_postmeta SET meta_value='$escaped' WHERE post_id=13480 AND meta_key='_elementor_data'");
echo $result ? 'SUCCESS affected='.$db2->affected_rows : 'ERROR: '.$db2->error;
// Also update post modified
$db2->query("UPDATE wp_posts SET post_modified=NOW(), post_modified_gmt=UTC_TIMESTAMP() WHERE ID=13480");
// Clear elementor cache
$db2->query("DELETE FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_css'");
echo ' | Cache cleared';
?>"""

sftp3 = c.open_sftp()
sftp3.putfo(io.BytesIO(php_update.encode('utf-8')), '/home/u634372166/update.php')
sftp3.close()

i2,o2,e2 = c.exec_command('php /home/u634372166/update.php 2>&1')
o2.channel.recv_exit_status()
result = o2.read().decode('utf-8','ignore')
print(f"Update result: {result}")

# Cleanup
c.exec_command('rm /home/u634372166/getdata.php /home/u634372166/update.php /home/u634372166/new_data.json 2>/dev/null')

c.close()
print("DONE!")
