import paramiko, json, io, uuid

def uid():
    return uuid.uuid4().hex[:7]

def section_about():
    return {"id":uid(),"elType":"section","isInner":False,"settings":{"gap":"no","structure":"20","background_background":"classic","background_color":"#ffffff","padding":{"unit":"px","top":"80","right":"120","bottom":"80","left":"120","isLinked":False}},"elements":[{"id":uid(),"elType":"column","settings":{"_column_size":50},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"من نحن","header_size":"h6","title_color":"#7A51E1","typography_font_weight":"700","align":"right"}},{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"منصة مقياس للاختبارات المعيارية والتقييمية","header_size":"h2","title_color":"#1A1A2E","typography_font_weight":"700","align":"right","title_margin":{"unit":"px","top":"10","right":"0","bottom":"20","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"text-editor","settings":{"editor":"<p style=\"text-align:right;color:#666;font-size:16px;line-height:1.9;\">منصة متخصصة في التدريب والتطوير والاستشارات التعليمية، تُمكّن الأفراد والمؤسسات عبر برامج مهنية متوافقة مع متطلبات سوق العمل. نؤمن بأن التميز الحقيقي يتحقق عندما تتكامل الرؤية مع جودة التنفيذ ودقة القياس.</p>","_margin":{"unit":"px","top":"0","right":"0","bottom":"30","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"button","settings":{"text":"اعرف أكثر عنّا","link":{"url":"/about-us-1/"},"align":"right","size":"md","background_color":"#7A51E1","button_text_color":"#ffffff","border_radius":{"unit":"px","top":"8","right":"8","bottom":"8","left":"8","isLinked":True}}}]},{"id":uid(),"elType":"column","settings":{"_column_size":50},"elements":[{"id":uid(),"elType":"widget","widgetType":"counter","settings":{"starting_number":0,"ending_number":500,"suffix":"+","duration":2000,"title":"مدرسة شريكة","number_color":"#7A51E1","title_color":"#1A1A2E","align":"center","_margin":{"unit":"px","top":"0","right":"0","bottom":"25","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"counter","settings":{"starting_number":0,"ending_number":10000,"suffix":"+","duration":2000,"title":"طالب تم تقييمه","number_color":"#7A51E1","title_color":"#1A1A2E","align":"center","_margin":{"unit":"px","top":"0","right":"0","bottom":"25","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"counter","settings":{"starting_number":0,"ending_number":98,"suffix":"%","duration":2000,"title":"نسبة رضا العملاء","number_color":"#7A51E1","title_color":"#1A1A2E","align":"center"}}]}]}

def section_how():
    steps=[{"num":"01","title":"تسجيل المدرسة","desc":"تتواصل المدرسة معنا ويتم إعداد حساب مخصص بسهولة خلال 24 ساعة"},{"num":"02","title":"تنفيذ الاختبار","desc":"يؤدي الطلاب الاختبارات إلكترونياً بإشراف كامل في بيئة آمنة وموثوقة"},{"num":"03","title":"النتائج والتقارير","desc":"تقارير تحليلية دقيقة فور الانتهاء لاتخاذ قرارات تعليمية مدروسة"}]
    cols=[{"id":uid(),"elType":"column","settings":{"_column_size":100},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"كيف تعمل منصة مقياس؟","header_size":"h2","title_color":"#1A1A2E","typography_font_size":{"unit":"px","size":36},"typography_font_weight":"700","align":"center","title_margin":{"unit":"px","top":"0","right":"0","bottom":"10","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"text-editor","settings":{"editor":"<p style=\"text-align:center;color:#666;margin-bottom:50px;\">ثلاث خطوات بسيطة تفصلك عن قياس أداء طلابك بدقة واحترافية</p>"}}]}]
    for s in steps:
        cols.append({"id":uid(),"elType":"column","settings":{"_column_size":33},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":s["num"],"header_size":"h1","title_color":"rgba(122,81,225,0.2)","typography_font_size":{"unit":"px","size":72},"typography_font_weight":"900","align":"center"}},{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":s["title"],"header_size":"h4","title_color":"#1A1A2E","typography_font_weight":"700","align":"center","title_margin":{"unit":"px","top":"5","right":"0","bottom":"15","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"text-editor","settings":{"editor":f"<p style=\"text-align:center;color:#666;font-size:15px;line-height:1.8;\">{s['desc']}</p>"}}]})
    return {"id":uid(),"elType":"section","isInner":False,"settings":{"background_background":"classic","background_color":"#F6F4FF","padding":{"unit":"px","top":"80","right":"120","bottom":"80","left":"120","isLinked":False}},"elements":cols}

def section_services():
    svcs=[{"title":"الاستشارات التعليمية","desc":"تطوير الأداء المؤسسي وتحسين البيئة التعليمية وفق أحدث المعايير الدولية","icon":"fa fa-lightbulb"},{"title":"البرامج القيادية والإدارية","desc":"تنمية الموارد البشرية وبناء قيادات تعليمية قادرة على صناعة الأثر","icon":"fa fa-users"},{"title":"البرامج اللغوية","desc":"برامج متخصصة للأغراض الأكاديمية والمهنية بمعايير عالمية معتمدة","icon":"fa fa-language"},{"title":"التدريب التقني والرقمي","desc":"تصميم أنظمة تقييم إلكتروني متطورة تواكب التحول الرقمي","icon":"fa fa-laptop"}]
    cols=[{"id":uid(),"elType":"column","settings":{"_column_size":100},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"خدماتنا","header_size":"h6","title_color":"#7A51E1","align":"center"}},{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"حلول تعليمية متكاملة لمؤسستك","header_size":"h2","title_color":"#1A1A2E","typography_font_size":{"unit":"px","size":36},"typography_font_weight":"700","align":"center","title_margin":{"unit":"px","top":"10","right":"0","bottom":"50","left":"0","isLinked":False}}}]}]
    for s in svcs:
        cols.append({"id":uid(),"elType":"column","settings":{"_column_size":25},"elements":[{"id":uid(),"elType":"widget","widgetType":"icon-box","settings":{"icon":{"value":s["icon"],"library":"fa-solid"},"title_text":s["title"],"description_text":s["desc"],"position":"top","icon_color":"#7A51E1","title_color":"#1A1A2E","description_color":"#666","title_size":"h5","_background_background":"classic","_background_color":"#fff","_border_radius":{"unit":"px","top":"12","right":"12","bottom":"12","left":"12","isLinked":True},"_padding":{"unit":"px","top":"35","right":"25","bottom":"35","left":"25","isLinked":False},"icon_size":{"unit":"px","size":40}}}]})
    return {"id":uid(),"elType":"section","isInner":False,"settings":{"background_background":"classic","background_color":"#ffffff","padding":{"unit":"px","top":"80","right":"120","bottom":"80","left":"120","isLinked":False}},"elements":cols}

def section_why():
    features=[{"title":"اختبارات معيارية دقيقة","desc":"مصممة وفق معايير دولية لقياس المستوى الحقيقي للطلاب"},{"title":"تصحيح تلقائي فوري","desc":"نتائج فورية بمجرد إنهاء الاختبار بدقة 100%"},{"title":"تقارير تحليلية شاملة","desc":"تقارير تفصيلية لكل طالب وصف ومدرسة"},{"title":"سهولة الاستخدام","desc":"واجهة سلسة للمعلمين والطلاب بدون خبرة تقنية"},{"title":"دعم كامل ومتواصل","desc":"فريق متخصص يدعمك في كل خطوة"},{"title":"تقييم فردي متخصص","desc":"تحليل أداء كل طالب بشكل منفرد لمتابعة التقدم"}]
    cols=[{"id":uid(),"elType":"column","settings":{"_column_size":100},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"لماذا تختار منصة مقياس؟","header_size":"h2","title_color":"#1A1A2E","typography_font_size":{"unit":"px","size":36},"typography_font_weight":"700","align":"center","title_margin":{"unit":"px","top":"0","right":"0","bottom":"50","left":"0","isLinked":False}}}]}]
    for f in features:
        cols.append({"id":uid(),"elType":"column","settings":{"_column_size":33},"elements":[{"id":uid(),"elType":"widget","widgetType":"icon-box","settings":{"icon":{"value":"fa fa-check-circle","library":"fa-solid"},"title_text":f["title"],"description_text":f["desc"],"position":"left","icon_color":"#7A51E1","title_color":"#1A1A2E","description_color":"#666","title_size":"h5","icon_size":{"unit":"px","size":28},"_margin":{"unit":"px","top":"0","right":"0","bottom":"30","left":"0","isLinked":False}}}]})
    return {"id":uid(),"elType":"section","isInner":False,"settings":{"background_background":"classic","background_color":"#F6F4FF","padding":{"unit":"px","top":"80","right":"120","bottom":"80","left":"120","isLinked":False}},"elements":cols}

def section_cta():
    return {"id":uid(),"elType":"section","isInner":False,"settings":{"background_background":"classic","background_color":"#7A51E1","padding":{"unit":"px","top":"100","right":"120","bottom":"100","left":"120","isLinked":False}},"elements":[{"id":uid(),"elType":"column","settings":{"_column_size":100},"elements":[{"id":uid(),"elType":"widget","widgetType":"heading","settings":{"title":"ابدأ رحلتك التعليمية مع مقياس اليوم","header_size":"h2","title_color":"#ffffff","typography_font_size":{"unit":"px","size":40},"typography_font_weight":"700","align":"center","title_margin":{"unit":"px","top":"0","right":"0","bottom":"20","left":"0","isLinked":False}}},{"id":uid(),"elType":"widget","widgetType":"text-editor","settings":{"editor":"<p style=\"text-align:center;color:rgba(255,255,255,0.85);font-size:18px;line-height:1.8;margin-bottom:35px;\">انضم إلى مئات المدارس التي تثق في منصة مقياس لتقييم طلابها وتطوير أدائها التعليمي</p>"}},{"id":uid(),"elType":"widget","widgetType":"button","settings":{"text":"تواصل معنا الآن","link":{"url":"/contact-us/"},"align":"center","size":"xl","background_color":"#ffffff","button_text_color":"#7A51E1","border_radius":{"unit":"px","top":"8","right":"8","bottom":"8","left":"8","isLinked":True}}}]}]}

# ============================================================
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("187.124.60.115", port=65002, username="u634372166", password="Miqyas85@gmail.com", timeout=15)

# Step 1: Get current data and extract ONLY the hero section (first section)
php_get = b"""<?php
$db=new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$r=$db->query("SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_data'");
$row=$r->fetch_row();
echo $row[0];
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
current_json = b''.join(chunks).decode('utf-8','ignore')
current_data = json.loads(current_json)
print(f"Total sections currently: {len(current_data)}")

# Step 2: Keep ONLY the first section (Hero)
hero_section = current_data[0]
print(f"Hero section ID: {hero_section['id']}")
print(f"Hero bg: {hero_section['settings'].get('background_background','')}")

# Step 3: Build new sections
new_sections = [
    hero_section,         # Keep Hero intact
    section_about(),
    section_how(),
    section_services(),
    section_why(),
    section_cta(),
]

final_json = json.dumps(new_sections, ensure_ascii=False)
print(f"Final: {len(new_sections)} sections, {len(final_json)} bytes")

# Step 4: Upload and update
sftp2 = c.open_sftp()
sftp2.putfo(io.BytesIO(final_json.encode('utf-8')), '/home/u634372166/final.json')
sftp2.close()

php_upd = b"""<?php
error_reporting(0);
$db=new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$json=file_get_contents('/home/u634372166/final.json');
$stmt=$db->prepare("UPDATE wp_postmeta SET meta_value=? WHERE post_id=13480 AND meta_key='_elementor_data'");
$stmt->bind_param('s',$json);
$ok=$stmt->execute();
echo $ok?"SUCCESS rows=".$stmt->affected_rows:"FAIL:".$db->error;
$stmt->close();
$db->query("UPDATE wp_posts SET post_modified=NOW(),post_modified_gmt=UTC_TIMESTAMP() WHERE ID=13480");
$db->query("DELETE FROM wp_postmeta WHERE post_id=13480 AND meta_key IN ('_elementor_css','_elementor_page_assets')");
$db->query("DELETE FROM wp_options WHERE option_name LIKE '%elementor%css%' OR option_name LIKE '_transient_%' OR option_name LIKE '%litespeed%'");
?>"""

sftp3 = c.open_sftp()
sftp3.putfo(io.BytesIO(php_upd), '/home/u634372166/upd.php')
sftp3.close()

i2,o2,e2 = c.exec_command('php /home/u634372166/upd.php 2>&1')
o2.channel.recv_exit_status()
print(f"Update: {o2.read().decode('utf-8','ignore')}")

# Step 5: Also clear LiteSpeed file cache
i3,o3,e3 = c.exec_command('find ~/domains/askmbt.com/public_html/wp-content/cache/ -type f -delete 2>/dev/null; echo done')
o3.channel.recv_exit_status()
print(f"LS Cache: {o3.read().decode()}")

# Step 6: Verify
php_ver = b"""<?php
$db=new mysqli('127.0.0.1','u634372166_Xgj7D','X4JX8XdvZf','u634372166_KpQVV');
$db->set_charset('utf8mb4');
$r=$db->query("SELECT meta_value FROM wp_postmeta WHERE post_id=13480 AND meta_key='_elementor_data'");
$row=$r->fetch_row();
$d=json_decode($row[0],true);
echo "FINAL sections=".count($d)." | len=".strlen($row[0])."\n";
foreach($d as $i=>$s){
    $bg=$s['settings']['background_color']??'no-color';
    echo "Section $i: id=".$s['id']." bg=$bg\n";
}
?>"""
sftp4 = c.open_sftp()
sftp4.putfo(io.BytesIO(php_ver), '/home/u634372166/v.php')
sftp4.close()
i4,o4,e4 = c.exec_command('php /home/u634372166/v.php 2>&1')
o4.channel.recv_exit_status()
print(o4.read().decode('utf-8','ignore'))

c.exec_command('rm /home/u634372166/g.php /home/u634372166/upd.php /home/u634372166/final.json /home/u634372166/v.php 2>/dev/null')
c.close()
print("ALL DONE!")
