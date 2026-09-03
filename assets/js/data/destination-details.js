/* Visitor-facing presentation data only. Atlas/GIS remains authoritative. */
(function () {
  const bi = (en, ar) => ({ en, ar });
  const img = (root, file, en, ar, width, height) => ({
    src: `../imges/Destination Detail/${root}/${file}`,
    alt: bi(en, ar), width, height,
  });
  const atlas = (image) => ({ href: "../atlas.html", image,
    title: bi("Continue in the Tourist Atlas", "تابع الاستكشاف في الأطلس السياحي"),
    description: bi("Open the authoritative tourism map to explore Libya’s governed destination information.", "افتح الخريطة السياحية المعتمدة لاستكشاف معلومات الوجهات الليبية الموثوقة.") });
  const practical = (styleEn, styleAr, environmentEn, environmentAr) => [
    { label: bi("Visit style", "أسلوب الزيارة"), value: bi(styleEn, styleAr) },
    { label: bi("Environment", "البيئة"), value: bi(environmentEn, environmentAr) },
    { label: bi("Prepare", "الاستعداد"), value: bi("Check current local guidance before travelling; carry sun protection and water.", "تحقق من الإرشادات المحلية السارية قبل السفر، واصطحب وسائل الوقاية من الشمس والماء.") },
    { label: bi("Visitor care", "آداب الزيارة"), value: bi("Respect heritage, communities and natural settings; leave no trace.", "احترم التراث والمجتمعات والبيئات الطبيعية، ولا تترك أثراً خلفك.") },
  ];
  const roots = {
    leptis: "liptes", tripoli: "Tripoli_Cinematic_Preserved_HQ", acacus: "acacus",
    rock: "VisitLibya_Akakus_RockArt_Processed_Only", sabratha: "subrita",
    ghadames: "VisitLibya_Ghadames_Hero_Batch01", awjila: "awijla",
    ras: "Ras_Al_Hilal_Cinematic_Preserved_HQ",
    ubari: "Ubari_Lakes",
    cyrene: "Cyrene",
  };
  const records = {
    "leptis-magna": {
      slug: "leptis-magna", name: bi("Leptis Magna", "لبدة الكبرى"),
      tagline: bi("A monumental city beside the Mediterranean", "مدينة أثرية شامخة على ضفاف المتوسط"),
      region: bi("Al Khums · Northwest Coast", "الخمس · الساحل الشمالي الغربي"), type: bi("Archaeological destination", "وجهة أثرية"),
      heritageStatus: bi("UNESCO World Heritage Site", "موقع تراث عالمي لليونسكو"),
      hero: img(roots.leptis,"ChatGPT Image Sep 2, 2026, 03_14_06 AM (6).png","Ancient theatre at Leptis Magna overlooking the Mediterranean","المسرح الأثري في لبدة الكبرى المطل على البحر المتوسط",1448,1086),
      introduction: { title: bi("An ancient city shaped on a grand scale", "مدينة قديمة صيغت على نطاق مهيب"), body: bi("Leptis Magna brings streets, forums, arches and public buildings into one remarkable Mediterranean setting. Its surviving urban fabric allows visitors to read the rhythm of an ancient city while moving through it.", "تجمع لبدة الكبرى بين الشوارع والساحات والأقواس والمباني العامة في مشهد متوسطي متكامل. ويتيح نسيجها العمراني الباقي للزائر قراءة إيقاع المدينة القديمة أثناء التجول فيها."), image: img(roots.leptis,"ChatGPT Image Sep 2, 2026, 03_14_05 AM (3).png","Colonnaded architecture at Leptis Magna","عمارة معمدة في لبدة الكبرى",1448,1086) },
      highlights: [
        ["Monumental urban fabric","نسيج عمراني ضخم","Forums, streets and civic spaces reveal the scale of the ancient city.","تكشف الساحات والشوارع والفضاءات العامة عن اتساع المدينة القديمة.","ChatGPT Image Sep 2, 2026, 03_14_05 AM (4).png"],
        ["Theatre and sea","المسرح والبحر","Performance architecture opens toward a distinctly Mediterranean horizon.","تنفتح عمارة المسرح على أفق متوسطي مميز.","ChatGPT Image Sep 2, 2026, 03_14_06 AM (5).png"],
        ["Arches and processional ways","الأقواس والمسارات","Stone gateways frame long views through the archaeological landscape.","تؤطر البوابات الحجرية مشاهد ممتدة عبر الموقع الأثري.","ChatGPT Image Sep 2, 2026, 03_20_52 AM (1).png"],
        ["Architectural detail","تفاصيل معمارية","Columns, carving and layered masonry reward close observation.","تدعو الأعمدة والزخارف وطبقات البناء إلى التأمل الدقيق.","ChatGPT Image Sep 2, 2026, 03_20_54 AM (4).png"]
      ].map(x=>({title:bi(x[0],x[1]),description:bi(x[2],x[3]),image:img(roots.leptis,x[4],x[0],x[1],1448,1086)})),
      visualStory: { eyebrow: bi("Stone and horizon", "الحجر والأفق"), title: bi("A city revealed along the ancient road", "مدينة تتكشف على امتداد الطريق القديم"), description: bi("Monumental arches turn a walk through Leptis Magna into a sequence of framed views, changing light and architectural discovery.", "تحول الأقواس المهيبة السير في لبدة الكبرى إلى تتابع من المشاهد المؤطرة والضوء المتغير والاكتشاف المعماري."), image: img(roots.leptis,"ChatGPT Image Sep 2, 2026, 03_20_53 AM (2).png","Monumental arch and pathway at Leptis Magna","قوس أثري ومسار في لبدة الكبرى",1672,941) },
      experiences: [bi("Walk the ancient streets", "التجول في الشوارع القديمة"),bi("Study arches and colonnades", "تأمل الأقواس والأروقة"),bi("Photograph the Mediterranean setting", "تصوير المشهد المتوسطي"),bi("Explore theatre architecture", "استكشاف عمارة المسرح")],
      context: { title: bi("Heritage in a coastal landscape", "تراث في مشهد ساحلي"), body: bi("The relationship between city and sea is essential to Leptis Magna. Aerial views reveal how its monuments, routes and coastline form one connected archaeological landscape.", "تُعد العلاقة بين المدينة والبحر جزءاً أساسياً من لبدة الكبرى؛ إذ تكشف المشاهد الجوية ترابط المعالم والمسارات والساحل في مشهد أثري واحد."), image: img(roots.leptis,"ChatGPT Image Sep 2, 2026, 03_20_54 AM (5).png","Aerial view of the theatre and coast at Leptis Magna","مشهد جوي لمسرح لبدة الكبرى وساحلها",1448,1086) },
      gallery: ["ChatGPT Image Sep 2, 2026, 03_14_05 AM (3).png","ChatGPT Image Sep 2, 2026, 03_14_05 AM (4).png","ChatGPT Image Sep 2, 2026, 03_14_06 AM (5).png","ChatGPT Image Sep 2, 2026, 03_14_06 AM (6).png","ChatGPT Image Sep 2, 2026, 03_20_52 AM (1).png","ChatGPT Image Sep 2, 2026, 03_20_53 AM (2).png","ChatGPT Image Sep 2, 2026, 03_20_54 AM (4).png","ChatGPT Image Sep 2, 2026, 03_20_54 AM (5).png","ChatGPT Image Sep 2, 2026, 03_20_55 AM (6).png"].map((f,i)=>img(roots.leptis,f,`Leptis Magna archaeological view ${i+1}`,`مشهد أثري من لبدة الكبرى ${i+1}`,i===4?1672:1448,i===4?941:1086)),
      practical: practical("A spacious walking visit with time for close architectural viewing.","زيارة سيراً على الأقدام مع وقت كافٍ لتأمل العمارة.","Open archaeological terrain beside the Mediterranean.","موقع أثري مفتوح بمحاذاة البحر المتوسط."),
      atlas: atlas(img(roots.leptis,"ChatGPT Image Sep 2, 2026, 03_20_55 AM (6).png","Wide aerial view of Leptis Magna","مشهد جوي واسع للبدة الكبرى",1672,941)), continueExploring:["tripoli","sabratha","ghadames"]
    },
  };

  function simple(slug, name, arName, tagline, arTagline, region, arRegion, type, arType, heritage, root, prefix, count, copy) {
    const files = Array.from({length:count},(_,i)=> prefix(i+1));
    const image = (i, enAlt, arAlt) => img(root, files[i%files.length], enAlt, arAlt, copy.dims?.[i]?.[0]||1448, copy.dims?.[i]?.[1]||1086);
    records[slug] = { slug, name:bi(name,arName), tagline:bi(tagline,arTagline), region:bi(region,arRegion), type:bi(type,arType), heritageStatus: heritage?bi(heritage[0],heritage[1]):null,
      hero:image(0,`${name} landscape`,`${arName} في مشهدها المميز`),
      introduction:{title:bi(copy.introTitle[0],copy.introTitle[1]),body:bi(copy.intro[0],copy.intro[1]),image:image(1,`${name} identity`,`${arName} وهويتها`)},
      highlights:copy.highlights.map((h,i)=>({title:bi(h[0],h[1]),description:bi(h[2],h[3]),image:image(i+2,`${name}: ${h[0]}`,`${arName}: ${h[1]}`)})),
      visualStory:{eyebrow:bi(copy.eyebrow[0],copy.eyebrow[1]),title:bi(copy.storyTitle[0],copy.storyTitle[1]),description:bi(copy.story[0],copy.story[1]),image:image(5,`${name} visual story`,`${arName} في حكاية بصرية`)},
      experiences:copy.experiences.map(x=>bi(x[0],x[1])),
      context:{title:bi(copy.contextTitle[0],copy.contextTitle[1]),body:bi(copy.context[0],copy.context[1]),image:image(6,`${name} context`,`${arName} وسياقها`)},
      gallery:(count<=7?files:files.slice(Math.max(1,count-12))).map((f,i)=>img(root,f,`${name} view ${i+1}`,`مشهد من ${arName} ${i+1}`,1448,1086)),
      practical:practical(copy.visit[0],copy.visit[1],copy.environment[0],copy.environment[1]), atlas:atlas(image(Math.min(count-1,7),`${name} spatial setting`,`${arName} في محيطها`)), continueExploring:copy.continue };
  }
  const common = {
    tripoli:{slug:"tripoli",name:"Tripoli",ar:"طرابلس",tag:"A living capital between old city and sea",artag:"عاصمة حية بين المدينة القديمة والبحر",region:"Tripoli · Mediterranean Coast",arregion:"طرابلس · الساحل المتوسطي",type:"Urban cultural destination",artype:"وجهة حضرية ثقافية",root:roots.tripoli,count:18,p:i=>{const n=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,17,18,19][i-1];return `Tripoli_${String(n).padStart(2,"0")}_Cinematic_Preserved_HQ.jpg`},dims:[[4096,3072],[1536,1024],[1024,1130],[2560,1414],[4096,2720],[3960,2160],[3960,2160],[3556,1992]],c:{introTitle:["The Mediterranean capital","العاصمة المتوسطية"],intro:["Tripoli layers a historic medina, civic landmarks, markets and a working waterfront into a city best understood at street level.","تجمع طرابلس بين المدينة القديمة والمعالم المدنية والأسواق والواجهة البحرية في مدينة تُكتشف تفاصيلها على مستوى الشارع."],highlights:[["Old City lanes","أزقة المدينة القديمة","Historic streets hold markets, courtyards and everyday urban life.","تحتضن الشوارع التاريخية الأسواق والأفنية وإيقاع الحياة اليومية."],["Mediterranean waterfront","الواجهة البحرية","The coast gives the capital an open horizon and maritime character.","يمنح الساحل العاصمة أفقاً مفتوحاً وطابعاً بحرياً."],["Historic architecture","العمارة التاريخية","Mosques, arches and civic buildings trace layered periods of the city.","تروي المساجد والأقواس والمباني العامة طبقات من تاريخ المدينة."],["Markets and culture","الأسواق والثقافة","Craft, food and conversation animate Tripoli’s central quarters.","تمنح الحرف والطعام واللقاءات أحياء طرابلس المركزية حيويتها."]],eyebrow:["City in motion","مدينة نابضة"],storyTitle:["Where heritage remains part of daily life","حيث يبقى التراث جزءاً من الحياة اليومية"],story:["Tripoli’s character is found in the transitions—from shaded lanes to bright squares and from historic walls to the sea.","تتجلى شخصية طرابلس في الانتقال من الأزقة المظللة إلى الساحات المضيئة، ومن الأسوار التاريخية إلى البحر."],experiences:[["Walk the Old City","التجول في المدينة القديمة"],["Explore urban architecture","استكشاف العمارة الحضرية"],["Discover markets and crafts","اكتشاف الأسواق والحرف"],["See the waterfront","زيارة الواجهة البحرية"]],contextTitle:["A living urban culture","ثقافة حضرية حية"],context:["Tripoli is not a preserved tableau but a contemporary capital whose heritage continues through neighbourhoods, commerce and social life.","طرابلس ليست مشهداً محفوظاً فحسب، بل عاصمة معاصرة يستمر تراثها في الأحياء والتجارة والحياة الاجتماعية."],visit:["Best explored on foot in focused neighbourhood walks.","تُستكشف بشكل أفضل عبر جولات مشي مركزة في الأحياء."],environment:["Dense historic quarters, open squares and a coastal urban edge.","أحياء تاريخية كثيفة وساحات مفتوحة وامتداد حضري ساحلي."],continue:["leptis-magna","sabratha","ghadames"]}},
    acacus:{slug:"acacus",name:"Acacus",ar:"أكاكوس",tag:"Rock art and sandstone horizons in the Sahara",artag:"فن صخري وآفاق من الحجر الرملي في الصحراء",region:"Fezzan · Southwest Libya",arregion:"فزان · جنوب غرب ليبيا",type:"Saharan cultural landscape",artype:"مشهد ثقافي صحراوي",heritage:["UNESCO World Heritage Site","موقع تراث عالمي لليونسكو"],root:roots.acacus,count:10,p:i=>`ChatGPT Image Sep 2, 2026, 02_26_${i<3?'50':i<6?'51':i<10?'52':'53'} AM (${i}).png`,dims:[[1448,1086],[1086,1448],[1448,1086],[1823,863],[1448,1086],[1448,1086],[1672,941],[1536,1024]],c:{introTitle:["A Saharan archive in stone","سجل صحراوي محفور في الصخر"],intro:["Acacus combines sandstone massifs, valleys and rock art in a cultural landscape shaped across deep time.","يجمع أكاكوس بين كتل الحجر الرملي والوديان والفن الصخري في مشهد ثقافي تشكل عبر أزمنة بعيدة."],highlights:[["Desert formations","تشكيلات صحراوية","Erosion has formed towers, arches and sculptural ridges.","شكّل النحت الطبيعي أبراجاً وأقواساً وحواف صخرية مميزة."],["Rock art","الفن الصخري","Images preserved on stone record changing lives and environments.","تحفظ الرسوم على الصخر شواهد على تحولات الحياة والبيئة."],["Saharan scale","رحابة الصحراء","Wide valleys place each formation within an immense horizon.","تضع الوديان الواسعة كل تشكيل ضمن أفق ممتد."],["Cultural landscape","مشهد ثقافي","Natural form and human memory remain inseparable here.","يتداخل التكوين الطبيعي والذاكرة الإنسانية في هذا المكان."]],eyebrow:["Deep desert","عمق الصحراء"],storyTitle:["Landforms that hold memory","تضاريس تحفظ الذاكرة"],story:["Light moves across sandstone walls and reveals a landscape valued for both its geology and its record of human presence.","يتحرك الضوء فوق جدران الحجر الرملي ليكشف مشهداً يجمع قيمة التكوين الجيولوجي وسجل الحضور الإنساني."],experiences:[["Observe rock art respectfully","مشاهدة الفن الصخري باحترام"],["Explore desert landforms","استكشاف التكوينات الصحراوية"],["Landscape photography","تصوير المشاهد الطبيعية"],["Read the Saharan horizon","تأمل الأفق الصحراوي"]],contextTitle:["A fragile Saharan heritage","تراث صحراوي حساس"],context:["Acacus asks for careful, low-impact visitation. Rock surfaces and archaeological traces must never be touched or disturbed.","يتطلب أكاكوس زيارة واعية قليلة الأثر؛ فلا ينبغي لمس الأسطح الصخرية أو الآثار أو العبث بها."],visit:["A planned desert journey with suitable local guidance.","رحلة صحراوية مخططة مع إرشاد محلي مناسب."],environment:["Remote, exposed Saharan terrain with large temperature shifts.","تضاريس صحراوية نائية ومكشوفة مع تفاوت ملحوظ في الحرارة."],continue:["ghadames","awjila","tripoli"]}},
  };
  Object.values(common).forEach(d=>simple(d.slug,d.name,d.ar,d.tag,d.artag,d.region,d.arregion,d.type,d.artype,d.heritage,d.root,d.p,d.count,{...d.c,dims:d.dims}));
  records.acacus.highlights[1].image = img(roots.rock,"akakus_rockart_04_processed.jpg","Rock art preserved on stone in Acacus","فن صخري محفوظ على الحجر في أكاكوس",1280,720);
  records.acacus.gallery[1] = img(roots.rock,"akakus_rockart_08_processed.jpg","Rock art detail in the Acacus cultural landscape","تفصيل من الفن الصخري في المشهد الثقافي لأكاكوس",2048,1365);

  const more = [
    ["sabratha","Sabratha","صبراتة","A theatre city facing the Mediterranean","مدينة المسرح المواجهة للمتوسط","Sabratha · Northwest Coast","صبراتة · الساحل الشمالي الغربي","Archaeological destination","وجهة أثرية",["UNESCO World Heritage Site","موقع تراث عالمي لليونسكو"],roots.sabratha,18,i=> i===1?"ChatGPT Image Sep 2, 2026, 05_08_41 PM (1).png":`ChatGPT Image Sep 2, 2026, 05_${i<11?'08':'16'}_${i<3?'41':i<5?'42':i<7?'43':i<9?'44':i<11?'45':i===11?'06':i===12?'11':i<15?'12':i<17?'13':'14'} PM${i===11?'':i===1?' (1)':` (${i>10?i-10:i})`}.png`,
    {introTitle:["Theatre, city and sea","المسرح والمدينة والبحر"],intro:["Sabratha’s theatre anchors an archaeological city whose streets and monuments meet the Mediterranean coast.","يتصدر مسرح صبراتة مدينة أثرية تتلاقى شوارعها ومعالمها مع ساحل البحر المتوسط."],highlights:[["The Roman theatre","المسرح الروماني","Its stage architecture creates the site’s defining composition.","تشكّل عمارة واجهة المسرح المشهد الأبرز في الموقع."],["Archaeological city","المدينة الأثرية","Streets and public buildings extend beyond the theatre.","تمتد الشوارع والمباني العامة إلى ما وراء المسرح."],["Coastal setting","الموقع الساحلي","Sea and stone remain in constant visual dialogue.","يدخل البحر والحجر في حوار بصري متواصل."],["Monumental heritage","تراث معماري","Columns, arches and masonry reward careful viewing.","تكافئ الأعمدة والأقواس والبناء الحجري التأمل المتأني."]],eyebrow:["Stage by the sea","مسرح بجوار البحر"],storyTitle:["Architecture open to the horizon","عمارة تنفتح على الأفق"],story:["From elevated viewpoints, Sabratha reads as a complete coastal city rather than a single monument.","من المشاهد المرتفعة تبدو صبراتة مدينة ساحلية متكاملة لا معلماً منفرداً."],experiences:[["Explore the theatre","استكشاف المسرح"],["Walk the ancient city","التجول في المدينة القديمة"],["Study monumental architecture","تأمل العمارة الضخمة"],["Photograph coast and ruins","تصوير الساحل والآثار"]],contextTitle:["An archaeological coast","ساحل أثري"],context:["Sabratha’s significance lies in the relationship between its celebrated theatre, wider urban remains and maritime setting.","تكمن أهمية صبراتة في العلاقة بين مسرحها الشهير وبقايا المدينة الأوسع وموقعها البحري."],visit:["A walking archaeological visit with time beyond the theatre.","زيارة أثرية سيراً على الأقدام مع وقت لاستكشاف ما وراء المسرح."],environment:["Open coastal archaeological terrain.","موقع أثري ساحلي مفتوح."],continue:["tripoli","leptis-magna","ghadames"]}],
    ["ghadames","Ghadames","غدامس","An oasis city of shade, craft and earthen architecture","مدينة واحة من الظلال والحرف والعمارة الترابية","Ghadames · Western Desert","غدامس · الصحراء الغربية","Historic oasis city","مدينة واحة تاريخية",["UNESCO World Heritage Site","موقع تراث عالمي لليونسكو"],roots.ghadames,10,i=>`ghadames_hero_${String(i).padStart(2,"0")}_1920x1080.jpg`,
    {introTitle:["A city designed for desert life","مدينة صممت لحياة الصحراء"],intro:["Ghadames is known for a compact old town of earthen homes, covered passages and carefully moderated light.","تشتهر غدامس بمدينتها القديمة المتماسكة وبيوتها الترابية وممراتها المسقوفة وضوئها المدروس."],highlights:[["Covered passages","الممرات المسقوفة","Shade shapes movement through the old town.","يشكل الظل مسارات الحركة في المدينة القديمة."],["Traditional architecture","العمارة التقليدية","Earthen construction responds directly to the oasis climate.","تستجيب العمارة الترابية مباشرة لمناخ الواحة."],["Oasis setting","بيئة الواحة","Palms and water support the city’s desert identity.","تدعم النخيل والمياه هوية المدينة الصحراوية."],["Living craft","الحرف الحية","Pattern, textile and decoration continue local visual traditions.","تواصل الزخارف والمنسوجات تقاليد بصرية محلية."]],eyebrow:["Light and shade","الضوء والظل"],storyTitle:["Inside the architecture of an oasis","داخل عمارة الواحة"],story:["The old town turns climate into architecture through thick walls, narrow routes and covered communal spaces.","تحول المدينة القديمة المناخ إلى عمارة عبر الجدران السميكة والمسارات الضيقة والفضاءات المشتركة المسقوفة."],experiences:[["Walk covered passages","التجول في الممرات المسقوفة"],["Observe earthen architecture","تأمل العمارة الترابية"],["Discover local craft","اكتشاف الحرف المحلية"],["Experience the oasis setting","التعرف على بيئة الواحة"]],contextTitle:["Oasis knowledge made visible","معرفة الواحة متجسدة في العمارة"],context:["Ghadames expresses generations of adaptation to desert climate through settlement form, social space and material craft.","تجسد غدامس خبرة أجيال في التكيف مع المناخ الصحراوي من خلال شكل العمران والفضاء الاجتماعي والحرف المادية."],visit:["A slow walking visit through shaded historic spaces.","زيارة هادئة سيراً عبر الفضاءات التاريخية المظللة."],environment:["Hot desert oasis with cool, enclosed historic passages.","واحة صحراوية حارة وممرات تاريخية داخلية أكثر اعتدالاً."],continue:["acacus","awjila","tripoli"]}],
    ["awjila","Awjila","أوجلة","An eastern oasis shaped by earth, palms and tradition","واحة شرقية صاغتها الأرض والنخيل والتقاليد","Al Wahat · Eastern Libya","الواحات · شرق ليبيا","Oasis heritage destination","وجهة تراثية واحية",null,roots.awjila,7,i=>`ChatGPT Image Sep 2, 2026, 03_01_44 AM (${i}).png`,
    {introTitle:["A vernacular oasis landscape","مشهد واحة بعمارة محلية"],intro:["Awjila’s identity emerges through palm cultivation, earthen building traditions and the close relationship between settlement and oasis.","تتجلى هوية أوجلة في زراعة النخيل وتقاليد البناء الترابي والعلاقة الوثيقة بين العمران والواحة."],highlights:[["Oasis identity","هوية الواحة","Palm landscapes frame local settlement and daily life.","تؤطر مشاهد النخيل العمران المحلي والحياة اليومية."],["Vernacular architecture","العمارة المحلية","Earth, timber and shade shape distinctive spaces.","تشكّل الأرض والأخشاب والظل فضاءات مميزة."],["Desert heritage","التراث الصحراوي","Local knowledge reflects long adaptation to arid conditions.","تعكس المعرفة المحلية تكيفاً ممتداً مع البيئة الجافة."],["Traditional fabric","النسيج التقليدي","Compact routes reveal a human-scaled urban character.","تكشف المسارات المتقاربة طابعاً عمرانياً إنسانياً."]],eyebrow:["Oasis rhythms","إيقاع الواحة"],storyTitle:["Architecture rooted in place","عمارة متجذرة في المكان"],story:["Awjila rewards attentive observation of materials, shade and the transitions between built space and palms.","تكافئ أوجلة التأمل في المواد والظلال والانتقال بين الفضاء المبني والنخيل."],experiences:[["Observe oasis architecture","تأمل عمارة الواحة"],["Walk traditional routes","التجول في المسارات التقليدية"],["Photograph material details","تصوير التفاصيل المادية"],["Learn about oasis life","التعرف على حياة الواحة"]],contextTitle:["Eastern oasis heritage","تراث الواحات الشرقية"],context:["Awjila contributes a distinct eastern expression to Libya’s diverse oasis cultures and desert building traditions.","تقدم أوجلة تعبيراً شرقياً مميزاً ضمن تنوع ثقافات الواحات وتقاليد البناء الصحراوي في ليبيا."],visit:["A respectful cultural visit at an unhurried pace.","زيارة ثقافية هادئة تراعي خصوصية المكان."],environment:["Desert oasis, palm landscapes and earthen historic spaces.","واحة صحراوية ومشاهد نخيل وفضاءات تاريخية ترابية."],continue:["ghadames","acacus","ras-al-hilal"]}],
    ["ras-al-hilal","Ras Al Hilal","رأس الهلال","A quiet meeting of green slopes and Mediterranean blue","لقاء هادئ بين السفوح الخضراء وزرقة المتوسط","Jebel Akhdar · Northeast Coast","الجبل الأخضر · الساحل الشمالي الشرقي","Natural coastal destination","وجهة طبيعية ساحلية",null,roots.ras,6,i=>`Ras_Al_Hilal_${String(i).padStart(2,"0")}_Cinematic_Preserved_HQ.jpg`,
    {introTitle:["The Green Mountain reaches the sea","حين يصل الجبل الأخضر إلى البحر"],intro:["Ras Al Hilal brings wooded slopes, pale cliffs and clear Mediterranean water into one layered coastal landscape.","يجمع رأس الهلال بين السفوح المشجرة والمنحدرات الفاتحة ومياه المتوسط الصافية في مشهد ساحلي متعدد الطبقات."],highlights:[["Mediterranean coast","الساحل المتوسطي","Curving bays open toward broad sea views.","تنفتح الخلجان المنحنية على مشاهد بحرية واسعة."],["Cliffs and slopes","المنحدرات والسفوح","Rocky relief gives the coast its strong profile.","تمنح التضاريس الصخرية الساحل ملامحه القوية."],["Forest and sea","الغابة والبحر","Green vegetation meets blue water at close range.","تلتقي الخضرة بالمياه الزرقاء على مسافة قريبة."],["Quiet scenery","مشاهد هادئة","Natural viewpoints invite slow observation and photography.","تدعو الإطلالات الطبيعية إلى التأمل والتصوير بهدوء."]],eyebrow:["Blue and green","الأزرق والأخضر"],storyTitle:["A coastline with depth","ساحل متعدد الأبعاد"],story:["From elevated ground, the shoreline unfolds as a sequence of coves, forested ridges and open Mediterranean water.","من المرتفعات يتكشف الساحل في تتابع من الخلجان والحواف المشجرة والمياه المتوسطية المفتوحة."],experiences:[["Take in coastal viewpoints","الاستمتاع بالإطلالات الساحلية"],["Landscape photography","تصوير المشاهد الطبيعية"],["Enjoy the shoreline","قضاء وقت على الساحل"],["Observe forest and cliff ecology","تأمل بيئة الغابة والمنحدرات"]],contextTitle:["A natural coastal transition","انتقال طبيعي نحو الساحل"],context:["Ras Al Hilal is defined by the meeting of Jebel Akhdar terrain and the Mediterranean, a relationship that changes with every viewpoint.","يتحدد رأس الهلال بلقاء تضاريس الجبل الأخضر بالبحر المتوسط، وهي علاقة تتغير مع كل إطلالة."],visit:["A scenic coastal visit with time for viewpoints and quiet pauses.","زيارة ساحلية هادئة مع وقت للإطلالات والتوقفات المتأنية."],environment:["Exposed coast, rocky slopes and Mediterranean conditions.","ساحل مكشوف وسفوح صخرية وظروف متوسطية."],continue:["awjila","tripoli","leptis-magna"]}]
  ,

    ["ubari-lakes","Ubari Lakes","بحيرات أوباري",
      "Desert lakes between dunes and palm-fringed oases",
      "بحيرات صحراوية بين الكثبان وواحات النخيل",
      "Fezzan · Southwest Libya",
      "فزان · جنوب غرب ليبيا",
      "Natural desert destination",
      "وجهة طبيعية صحراوية",
      null,
      roots.ubari,
      10,
      i=>`Ubari_${String(i).padStart(2,"0")}_Cinematic_Preserved_HQ.jpg`,
      {
        introTitle:["Water in the heart of the Sahara","الماء في قلب الصحراء"],
        intro:[
          "The Ubari lake landscapes create one of Libya’s most distinctive Saharan scenes, where water, dunes, palms and open desert meet in striking contrast.",
          "تشكل بحيرات أوباري أحد أكثر المشاهد الصحراوية تميزاً في ليبيا، حيث تلتقي المياه بالكثبان والنخيل والفضاء الصحراوي المفتوح في تباين بصري لافت."
        ],
        highlights:[
          ["Desert lakes","البحيرات الصحراوية","Still water forms an unexpected oasis landscape among the dunes.","تصنع المياه الهادئة مشهداً واحاتياً غير متوقع بين الكثبان."],
          ["Golden dunes","الكثبان الذهبية","Sweeping sand formations frame the lakes and change with light and wind.","تؤطر التكوينات الرملية البحيرات وتتغير ملامحها مع الضوء والرياح."],
          ["Palm oases","واحات النخيل","Palm clusters mark historic points of life and shade in the desert.","تشكل تجمعات النخيل علامات للحياة والظل في البيئة الصحراوية."],
          ["Saharan horizons","آفاق الصحراء","Wide views reveal the scale and quiet character of Fezzan.","تكشف المشاهد الواسعة اتساع فزان وطابعها الهادئ."]
        ],
        eyebrow:["Water and sand","الماء والرمال"],
        storyTitle:["A rare contrast in the Sahara","تباين نادر في قلب الصحراء"],
        story:[
          "At Ubari, deep desert scenery is transformed by reflective water and palm-lined edges, creating a landscape that feels both remote and intimate.",
          "في أوباري يتغير المشهد الصحراوي العميق بوجود المياه العاكسة وحواف النخيل، فتتشكل بيئة تجمع بين العزلة والحميمية."
        ],
        experiences:[
          ["Photograph lakes and dunes","تصوير البحيرات والكثبان"],
          ["Watch changing desert light","متابعة تغير الضوء الصحراوي"],
          ["Explore oasis landscapes","استكشاف مشاهد الواحات"],
          ["Experience the scale of Fezzan","استشعار اتساع فزان"]
        ],
        contextTitle:["A fragile desert landscape","مشهد صحراوي حساس"],
        context:[
          "The Ubari lake area is part of a delicate Saharan environment where water, sand, vegetation and local communities are closely connected.",
          "تقع بحيرات أوباري ضمن بيئة صحراوية حساسة ترتبط فيها المياه والرمال والنبات والمجتمعات المحلية بعلاقة وثيقة."
        ],
        visit:[
          "A scenic desert visit best approached with local guidance and careful preparation.",
          "زيارة صحراوية ذات طابع طبيعي يفضل القيام بها بتنسيق محلي واستعداد مناسب."
        ],
        environment:[
          "Arid Sahara, exposed dunes, oasis vegetation and remote desert conditions.",
          "صحراء جافة وكثبان مكشوفة ونباتات واحات وظروف صحراوية بعيدة."
        ],
        continue:["ghadames","acacus","tripoli"]
      }
    ],

    ["cyrene","Cyrene","قورينا – شحات",
      "Ancient terraces overlooking the landscapes of Jebel Akhdar",
      "مدرجات أثرية تطل على مشاهد الجبل الأخضر",
      "Shahat · Jebel Akhdar",
      "شحات · الجبل الأخضر",
      "Archaeological and cultural destination",
      "وجهة أثرية وثقافية",
      "UNESCO World Heritage Site",
      roots.cyrene,
      8,
      i=>`shahat_${String(i).padStart(2,"0")}_cinematic_preserved.jpg`,
      {
        introTitle:[
          "An ancient city shaped by landscape",
          "مدينة أثرية شكلتها الطبيعة"
        ],
        intro:[
          "Cyrene combines monumental archaeological remains with the elevated landscapes of Jebel Akhdar, creating one of Libya’s most distinctive heritage settings.",
          "تجمع قورينا بين المعالم الأثرية الكبرى والمشاهد المرتفعة للجبل الأخضر، لتشكل أحد أكثر المواقع التراثية تميزاً في ليبيا."
        ],
        highlights:[
          [
            "Ancient terraces",
            "المدرجات الأثرية",
            "The site unfolds across layered slopes and monumental archaeological spaces.",
            "يمتد الموقع عبر سفوح متدرجة وفضاءات أثرية واسعة."
          ],
          [
            "Temple landscapes",
            "مشاهد المعابد",
            "Classical structures remain closely connected to the surrounding terrain.",
            "ترتبط المباني الكلاسيكية ارتباطاً وثيقاً بالتضاريس المحيطة."
          ],
          [
            "Jebel Akhdar setting",
            "بيئة الجبل الأخضر",
            "Green uplands give the archaeological site a distinctive natural frame.",
            "تمنح مرتفعات الجبل الأخضر الموقع الأثري إطاراً طبيعياً مميزاً."
          ],
          [
            "Historic perspectives",
            "إطلالات تاريخية",
            "Elevated viewpoints reveal the scale and structure of the ancient city.",
            "تكشف الإطلالات المرتفعة حجم المدينة القديمة وتنظيمها."
          ]
        ],
        eyebrow:[
          "Heritage on the highlands",
          "تراث فوق المرتفعات"
        ],
        storyTitle:[
          "Where archaeology meets the Green Mountain",
          "حين يلتقي الأثر بالجبل الأخضر"
        ],
        story:[
          "Cyrene is experienced through movement between architecture, terraces and open landscapes, where history and topography remain inseparable.",
          "تكتشف قورينا عبر الانتقال بين العمارة والمدرجات والمشاهد المفتوحة، حيث يبقى التاريخ والطبوغرافيا جزءاً من تجربة واحدة."
        ],
        experiences:[
          ["Explore archaeological remains","استكشاف المعالم الأثرية"],
          ["Walk through historic terraces","التجول بين المدرجات التاريخية"],
          ["Photograph classical architecture","تصوير العمارة الكلاسيكية"],
          ["Observe Jebel Akhdar landscapes","مشاهدة مناظر الجبل الأخضر"]
        ],
        contextTitle:[
          "A major heritage landscape",
          "مشهد تراثي رئيسي"
        ],
        context:[
          "The archaeological setting of Cyrene reflects the close relationship between ancient urban development and the natural geography of northeastern Libya.",
          "يعكس المشهد الأثري لقورينا العلاقة الوثيقة بين تطور المدينة القديمة والجغرافيا الطبيعية لشمال شرق ليبيا."
        ],
        visit:[
          "Allow time to move between the different archaeological zones and elevated viewpoints.",
          "يفضل تخصيص وقت كافٍ للتنقل بين المناطق الأثرية المختلفة ونقاط الإطلالة المرتفعة."
        ],
        environment:[
          "Elevated Mediterranean highlands, archaeological terrain and changing seasonal conditions.",
          "مرتفعات متوسطية وتضاريس أثرية وظروف موسمية متغيرة."
        ],
        continue:[
          "ras-al-hilal",
          "leptis-magna",
          "sabratha"
        ]
      }
    ]];
  more.forEach(d=>simple(d[0],d[1],d[2],d[3],d[4],d[5],d[6],d[7],d[8],d[9],d[10],d[12],d[11],d[13]));
  window.VISITLIBYA_DESTINATION_DETAILS = Object.freeze(records);
}());
