# بنية Frontend Foundation لمنصة Visit Libya

> إعداد النشر الحالي وسياسة API موثقان في
> [`frontend-runtime-configuration.md`](frontend-runtime-configuration.md). ذلك المستند
> هو المرجع المعتمد لإعداد local وGitHub Pages وبيئة production المستقبلية.

## 1. الهدف والنطاق

توفر هذه الحزمة أساسًا معياريًا لربط Trip Planner بواجهة Visit Libya الثابتة دون
تغيير الصفحات السياحية الحالية أو إدخال build system. تشمل الحزمة الإعداد أثناء
التشغيل، عميل API، الجلسة، الأخطاء، الترجمة الديناميكية، الحالة، وأدوات واجهة
قابلة للوصول. تشمل المرحلة التالية شاشة My Trips، بينما يبقى Trip Editor خارج
النطاق ولا يتجاوز صفحة تمهيدية تتحقق من المعرّف.

## 2. لماذا ES Modules؟

تعمل ES Modules مباشرة في المتصفحات الحديثة، وتوفر imports صريحة ومسؤولية
واحدة لكل ملف، من دون dependencies أو bundler. هذا يحافظ على توافق GitHub Pages
ويتيح اختبار الوحدات لاحقًا دون إعادة بناء الموقع.

## 3. لماذا لم يُستخدم React؟

الموقع الحالي HTML/CSS/JavaScript ثابت، ولم تثبت الحاجة إلى framework. إدخال
React الآن سيضيف build pipeline وحزمة dependencies ويضاعف نطاق التغيير. يمكن
إعادة تقييم القرار بعد قياس تعقيد My Trips وTrip Editor الفعليين.

## 4. بنية المجلدات

```text
assets/js/app/
├── api/          # عميل HTTP وعقود auth وtrips
├── auth/         # دورة حياة جلسة المستخدم
├── config/       # قراءة إعداد runtime والتحقق منه
├── errors/       # AppError وربط رموز الأخطاء بالرسائل
├── i18n/         # رسائل التطبيق الديناميكية العربية والإنجليزية
├── state/        # متجر Trip Planner خفيف
├── ui/           # announcer/loading/toast/modal
├── utils/        # DOM والتحقق وquery strings
└── bootstrap.js  # إنشاء سياق التطبيق وإعلان الجاهزية

config/frontend-config.example.js
docs/frontend-architecture.md
```

## 5. مسؤولية كل وحدة

- `runtime-config.js`: تطبيع الإعداد والتحقق منه وتجميده.
- `client.js`: تنفيذ fetch، timeout، cancellation، parsing، Bearer والأخطاء.
- `auth-api.js`: login بصيغة OAuth2 الفعلية ثم التحقق عبر `/auth/me`.
- `trips-api.js`: تغليف مسارات `/api/v1/trips` الفعلية فقط.
- `session.js`: token في الذاكرة، أو sessionStorage باختيار المستخدم.
- `app-error.js`: نموذج خطأ موحد وغير مرتبط بالـDOM.
- `error-messages.js`: تحويل رمز الخطأ إلى مفتاح ترجمة.
- `translator.js`: اختيار اللغة وfallback وinterpolation النصي الآمن.
- `trip-store.js`: حالة واجهة shallow immutable دون business logic.
- `ui/*`: أدوات وصول عامة لا تعتمد على تصميم صفحة معينة.
- `utils/*`: وظائف صغيرة آمنة وقابلة لإعادة الاستخدام.
- `bootstrap.js`: يجمع السياق ولا يشغّل Trip Planner تلقائيًا.

## 6. تدفق المصادقة

```text
Login Form
  → Auth API
  → Access Token
  → In-memory/session storage
  → /auth/me
  → Authenticated Session
```

يرسل login حقلي `username` و`password` كـ
`application/x-www-form-urlencoded` إلى `/api/v1/auth/login`. بعد استلام
`access_token` تُستدعى `/api/v1/auth/me`. لا تصبح الجلسة موثقة قبل نجاح هذه
الخطوة.

لا توجد endpoints للـlogout أوrefresh أوregistration في Backend الحالي، لذلك
لم تُنشأ عقود وهمية لها.

## 7. سياسة token

- الذاكرة هي التخزين الافتراضي.
- يستخدم `sessionStorage` فقط عند اختيار التذكر داخل جلسة المتصفح.
- يمنع استخدام `localStorage`.
- لا يُفك JWT لاتخاذ قرارات صلاحيات؛ `/auth/me` هو مصدر هوية المستخدم.
- لا يُسجل token أو request body في console.
- عند 401 تُنظف الجلسة ويطلق `visitlibya:auth-expired`.
- التصميم يسمح باستبدال التخزين مستقبلًا بتدفق HttpOnly cookie.

## 8. تدفق API

```text
Static HTML Page
  → Page Controller
  → Store
  → Trips API
  → Shared API Client
  → FastAPI Backend
```

لا يفترض runtime config عنوان API افتراضيًا، وتكون API معطلة بأمان حتى يتم
تفعيلها صراحة بعنوان صالح. يدعم العميل GET وPOST
وPATCH وPUT وDELETE، JSON وtext و204، timeout وAbortSignal خارجيًا، وrequest ID
إذا أعاده Backend. retry معطل افتراضيًا ومتاح اختياريًا لـGET فقط.

## 9. Error model

`AppError` يحتوي:

- `status`
- `code`
- `message`
- `details`
- `fieldErrors`
- `requestId`
- `retryable`
- `cause`

تتحول أخطاء الشبكة والمهلة والإلغاء و400 و401 و403 و404 و409 و422 و429 و500+
إلى هذا النموذج. تستخرج أخطاء FastAPI 422 من `detail[].loc` و`detail[].msg`
ولا تُعرض الاستجابة الخام للمستخدم.

## 10. معالجة 409

عند الرسالة الفعلية `Trip was modified by another request` يستخدم الرمز
`TRIP_VERSION_CONFLICT`. الرسالة العربية:

> تم تعديل الرحلة من جلسة أخرى. حمّل أحدث نسخة قبل إعادة المحاولة.

والإنجليزية:

> This trip was updated in another session. Load the latest version before trying again.

لا يحدث retry أوmerge تلقائي. يجب على Page Controller إيقاف الحفظ وعرض الرسالة
وتوفير إجراء صريح لتحميل أحدث نسخة.

## 11. Localization

القواميس مخصصة للرسائل الديناميكية فقط؛ المحتوى السياحي يبقى داخل HTML.
تُستنتج اللغة من `document.documentElement.lang` مع fallback إلى
`defaultLocale`. تدعم `t(key, params)` interpolation نصيًا دون HTML أو`eval`.

## 12. Accessibility primitives

- Announcer واحد يدعم polite وassertive ويمنع التكرار.
- Loading يضبط `aria-busy` ويوفر status نصيًا.
- Toast يستخدم status/alert وإغلاقًا يدويًا.
- Modal يستخدم `<dialog>`، focus trap، Escape، استعادة التركيز ووضع critical.
- جميع الرسائل الديناميكية تدخل عبر `textContent`.

## 13. قواعد الأمن

- لا أسرار أو عناوين production في المصدر.
- لا `localStorage` للـtoken.
- لا `innerHTML` في الوحدات الجديدة.
- لا تُبنى redirects من query parameters.
- لا تُسجل credentials أو tokens أو request bodies.
- صلاحيات المستخدم تأتي من Backend ولا تُستنتج من JWT.
- يجب ضبط CORS للـorigin الفعلي في بيئة النشر.

## 14. إعداد runtime config

انسخ المثال خارج عملية commit الخاصة بالأسرار إلى ملف إعداد للبيئة، ثم حمّله
قبل ES module:

```html
<script src="config/frontend-config.js"></script>
<script type="module" src="assets/js/app/bootstrap.js"></script>
```

الشكل:

```js
window.VISIT_LIBYA_CONFIG = Object.freeze({
  apiBaseUrl: "http://127.0.0.1:8000/api/v1",
  requestTimeoutMs: 10000,
  defaultLocale: "en",
  debug: false,
});
```

يحتوي المستودع على `frontend-config.js` بقيم static-host آمنة: API معطلة وعنوانها
فارغ. أما `frontend-config.example.js` فهو مثال للتطوير المحلي فقط. راجع دليل
runtime configuration لمعرفة إعداد GitHub Pages وHTTPS وCORS وحالة كل ميزة.

## 15. My Trips

تم إنشاء `trips.html` و`ar/trips.html` دون تغيير صفحتي الإرشاد `plan.html`.
تستخدم الصفحتان `trips-page.js` و`trips-renderer.js` و`trips-form.js` لتوفير:

1. استعادة الجلسة والتحقق عبر `/auth/me`.
2. تسجيل الدخول باسم المستخدم أو البريد الإلكتروني.
3. قائمة رحلات مع loading/empty/error/offline states.
4. pagination باستخدام `skip/limit/total` وحفظ الصفحة في query string.
5. إنشاء رحلة بالحقول الفعلية فقط.
6. حذف مؤكد دون optimistic deletion.
7. فتح صفحة تمهيدية لـTrip Editor بمعرّف موجب.
8. logout محلي عبر حذف Bearer token؛ لا يُستدعى endpoint غير موجود.

لا تستخدم صفحات My Trips بيانات mock ولا تخزن الرحلات محليًا.

## 16. إضافة Trip Editor لاحقًا

1. قراءة `trip` id كعدد موجب من URLSearchParams.
2. جلب `TripDetailResponse` وحفظ `version`.
3. مطابقة الحقول مع schemas الفعلية.
4. تنفيذ item CRUD دون retry تلقائي.
5. إعادة ترتيب المجموعة كاملة باستخدام:
   `expected_version` و`items[{item_id, day_number}]`.
6. فرض حد 100 في الواجهة مع بقاء Backend المصدر النهائي للتحقق.
7. عند 409، عدم overwrite أوmerge؛ تحميل النسخة الأحدث بإذن المستخدم.
8. حماية التغييرات غير المحفوظة وإتاحة reorder بلوحة المفاتيح.

## 17. سياسة الاختبارات المستقبلية

- Unit tests: config، session، error mapping، validation، translator، store.
- API contract tests: method/path/body/headers و204/401/409/422/timeout.
- DOM tests: modal، focus، announcer، toast، loading.
- Integration tests: login→me، list، CRUD، reorder conflict.
- Browser tests: العربية/الإنجليزية والهاتف ولوحة المفاتيح.
- لا تُضاف أداة اختبار قبل اختيار موثق يعتمد على حاجة المرحلة التطبيقية.

## 18. القيود الحالية

- My Trips هي الصفحة التطبيقية الوحيدة التي تحمل bootstrap حاليًا.
- لا توجد آلية refresh token أو HttpOnly cookie في Backend.
- token المستعاد غير موثوق حتى نجاح `/auth/me`.
- لا يوجد test runner أو build/lint/typecheck.
- CSS الحالية مخصصة لـMy Trips ولا تمثل design system عامًا.
- Trip Editor وitem CRUD وreorder غير منفذة.

## 19. القرارات المؤجلة

- اختيار test runner.
- آلية production config والنشر.
- سياسة refresh/HttpOnly cookie.
- Trip Editor وأسلوب reorder مع بديل لوحة مفاتيح.
- cache policy وoffline behavior.
- تقسيم `main.js` و`style.css` القائمين.
- إزالة أو اعتماد `partials.js`.

## 20. Definition of Done للـFoundation

- جميع الوحدات المطلوبة موجودة بمسؤولية واحدة.
- imports وsyntax سليمة.
- العقود تطابق FastAPI الحالي.
- 401 و409 و422 مركزية.
- token لا يدخل localStorage أوstore.
- لا secrets أوproduction URLs.
- runtime config قابل للتبديل ومجمد.
- لا dependencies أوpackage.json.
- لا تعديل Backend أوالمحتوى الرسمي لصفحتي `plan.html`.
- توثيق التدفقات والقيود والمرحلة التالية مكتمل.
