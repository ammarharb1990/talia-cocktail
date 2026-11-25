# Talia Cocktail — دليل المشروع لـ Claude Code

نظام إدارة محل كوكتيل وعصائر (مجموعة تاليا). الواجهة عربية (RTL) والعملة شيقل (₪). صاحب المشروع يتواصل بالعربية: اكتب له الردود والنصوص في الواجهة بالعربية.

## الملفات
- `index.html`: النظام كله في ملف واحد (HTML + CSS + JS). الكود مضغوط في أسطر طويلة، فعدّل بالبحث عن نص محدد، لا بأرقام الأسطر.
- `manifest.webmanifest` و`sw.js` والأيقونات: للتثبيت كتطبيق (PWA). **ارفع اسم الكاش في `sw.js`** (`talia-fakh-monthly-vN`) مع كل تعديل على `index.html`، حتى يصل التحديث للأجهزة المثبّت عليها التطبيق.
- `CHANGES.md`: سجل الإصلاحات والمتبقي.
- `tests/test_app.py`: اختبار تلقائي (Playwright) للحسابات الأساسية.

## التشغيل والاختبار
- فتح سريع: افتح `index.html` في المتصفح مباشرة.
- كخادم محلي: `npx serve .` أو `python -m http.server 8000`، ثم افتح `http://localhost:8000`.
- الدخول التجريبي (ظاهر على شاشة الدخول بطلب صاحب المشروع، اتركه كما هو): المدير `admin / Talia@2026`، الموظف `employee / 123456`.
- الاختبار: `pip install playwright && python -m playwright install chromium`، ثم `python tests/test_app.py`.
- **بعد أي تعديل على JS:** افحص الصياغة (استخرج محتوى `<script>` الرئيسي وشغّل `node --check`)، ثم شغّل الاختبار.

## البنية التقنية
- كل البيانات في `localStorage` على جهاز واحد. لا خادم ولا مزامنة.
- مصفوفات عامة تُقرأ بـ`get(key,default)` وتُحفظ بـ`set(key,value)`:

| المفتاح | المحتوى |
|---|---|
| `tc_sales` | `{id,type:'cash'|'visa'|'credit',date:'YYYY-MM-DDT12:00',amount,employee,note,dailyTotal}`، سجل واحد لكل نوع في اليوم (`upsertDailySale`) |
| `tc_purchases` | `{id,section:'main'|'secondary',category,name,qty,date,price,paid,paymentStatus:'paid'|'unpaid'|'company',supplier,sourceCompany?,fromDaily?,supplierInvoiceId?}` |
| `tc_expenses` | `{id,section:'fixed'|'operating',type,date,amount,fromDaily?}` |
| `tc_suppliers` | حركات الموردين `{id,date,name,previous,invoice,payment,remaining,items,source,paymentStatus?,purchaseId?}`، الرصيد يُعاد حسابه بـ`recalcSupplierAccount` |
| `tc_daily_withdrawals` | مسحوبات الصندوق `{id,date,amount,note}` |
| `tc_workers` | `{id(timestamp الإضافة),name,due,notes,advances:[{id,date,time,amount,cashPaid,note}],salaryHistory?:[{from:'YYYY-MM',due}]}` |
| `tc_collections` | تحصيل ديون الزبائن `{id,date,client,amount,method:'cash'|'bank',note}` |
| `tc_company_entries` | حركات حساب الشركة اليدوية `{id,type:'opening_debt'|'paid'|'credit'|'supply'|'received'...,date,amount,description,reference,notes,appliesToOldDebt?}` |
| `tc_company_month_closures` | `{month:'YYYY-MM',mode:'carry'|'zero',at}` |
| `tc_due_entries` | المستحقات والشيكات (مع `payments`) |
| `tc_external_obligations` | الالتزامات الخارجية (لا تؤثر على حسابات المحل) |
| `tc_employees` | موظف واحد حالياً، كلمة مروره نص عادي |
| `tc_admin_auth` | `{salt,hash}` لكلمة مرور المدير (SHA-256 عبر `tcSha256`)؛ غيابه يعني أن كلمة المرور الافتراضية فعّالة |
| `tc_manager_profile`, `tc_worker_goods` | ملف المدير، بضاعة العمال |

- **التنقل:** `page(id)` يُظهر `<section class="page" id=...>`. الصفحات: home, dailyEntry, sales, salesYearDetail, purchases, expenses, suppliers, supplierDetail, cashbox, workers, workerDetail, reports, fakh, dues, externalObligations, admin.
- **العرض:** `render()` معاد تعريفها 4 مرات، وكل نسخة تلفّ السابقة (`renderOriginal`, `renderBeforeDues`, `renderBeforeDailyEntry`, `renderBeforeExternal`). لا تعرّفها مرة خامسة بنفس الطريقة: أضف استدعاءك داخل آخر غلاف أو رتّبها في دالة واحدة.
- **الصلاحيات:** العنصر الذي يحمل `data-a` يظهر للمدير فقط، و`data-p="sales|purchases|expenses"` حسب صلاحية الموظف. التحقق كله في المتصفح، ولا يُعتبر أماناً حقيقياً.

## قواعد إلزامية عند التعديل
- **لا تستخدم `alert/confirm/prompt`.** استعمل `await askConfirm(msg)` و`await askPrompt(msg,def,type)` و`tcDialog({...})`، والدالة المستدعية تصير `async`. السبب: الصفحة تعمل داخل إطار يمنع هذه الأوامر.
- **التصدير:** استعمل `tcExport(name,text,mime)`، فهو يعرض المحتوى مع زر نسخ إذا مُنع التنزيل.
- أي نص من المستخدم يدخل `innerHTML` يمر عبر `escapeText()`.
- المعرّفات الجديدة من `entryUniqueId()`. التواريخ المحلية من `isoLocalDate()` / `today()`، لا `toISOString()` مباشرة.
- أي مفتاح `localStorage` جديد يُضاف إلى `TC_BACKUP_KEYS` وإلى `confirmResetAllData`.

## القواعد المحاسبية (قرارات صاحب المشروع، لا تغيّرها دون سؤاله)
- **صافي الربح** (`mt(y,m).net`) = المبيعات (نقدي + فيزا + دين) − المشتريات الرئيسية (ومعها توريدات الشركة اليدوية) − الثانوية − المصاريف الثابتة − رواتب الشهر − التشغيلية.
- **حصة شركة فخفخينا** = 10% من صافي ربح الشهر، وصفر إذا كان الشهر خسارة. حصة المحل 90% من الصافي. يعرض النظام `companyShare` و`netAfterCompany`.
- **المواد الرئيسية من الشركة** خارج النسبة، وتُسجَّل بقيمتها الكاملة ديناً على المحل في حساب الشركة، ولا تُخصم من الصندوق.
- **رصيد حساب الشركة** = − المواد − حصة الشركة (حركة بتاريخ آخر يوم في الشهر، وحصة الشهر الحالي تقديرية) + الدفعات للشركة. السالب مستحق للشركة.
- **الدين القديم للشركة:** دفتر منفصل (`opening_debt` ودفعات `appliesToOldDebt`) لا يدخل كشف الشهر.
- **الأشهر المغلقة** في حساب الشركة: لا إضافة ولا تعديل ولا حذف لحركاتها اليدوية قبل إلغاء الإغلاق.
- **صافي الصندوق** (`cashSummaryFor`) = المبيعات النقدية + تحصيل الديون نقداً − المشتريات المدفوعة نقداً − المصاريف الثابتة والتشغيلية (كلها تُعتبر نقداً حالياً) − المسحوبات − سلف العمال. الفيزا والآجل والتوريدات لا تُعتبر نقداً.
- **الراتب:** تكلفة الشهر = الراتب كاملاً، والسلف تُخصم من المتبقي للعامل فقط ولا تُخصم من الربح مرة ثانية. تعديل الراتب يسري من الشهر المحدد عبر `salaryHistory`.

## الموقع العام (GitHub Pages)
- الرابط لصاحب المحل: https://ammarharb1990.github.io/talia-cocktail/ ، من الـrepo العام `ammarharb1990/talia-cocktail` (فرع `main`، الجذر).
- **طريقة التحديث:** عدّل الملفات، وارفع `version.json` برقم جديد (وغيّر `APP_VERSION` في `index.html` لنفس الرقم)، وارفع اسم الكاش في `sw.js`، ثم ادفع للفرع `main`. يظهر عند المستخدمين شريط «في تحديث جديد».
- الآيفون: Safari ← مشاركة ← Add to Home Screen.

## النسخة التجريبية على Claude
- الرابط: https://claude.ai/artifact/H6C8rc6wuend5qDr5EmBvd (artifact slug `824bccc4-0193-4e40-ae2b-13dc7cd87efe`). صاحب المشروع يشاركه مع صاحب المحل للتجربة.
- أي نشر جديد على نفس الـslug يصل لكل من يفتح الرابط. بيانات كل مستخدم تبقى في متصفحه، ولا تُمسح عند التحديث.
- الصفحة تعمل داخل إطار يمنع `alert/confirm/prompt` والتنزيل وService Worker، لذلك استعمل أدوات الحوار والتصدير الداخلية.

## الخطة القادمة: التحويل لموقع احترافي
مقترح للنقاش مع صاحب المشروع قبل البدء:
1. فصل الكود: `index.html` + `css/` + `js/` (وحدات حسب القسم)، وتوحيد `render`.
2. قاعدة بيانات سحابية (مثل Supabase أو Firebase) مع تسجيل دخول حقيقي وصلاحيات على الخادم، ومزامنة الآيفون والكمبيوتر، وأداة استيراد من ملف النسخة الاحتياطية JSON الحالي.
3. نشر على استضافة HTTPS (مثل Netlify أو Vercel أو Cloudflare Pages).
4. نواقص معروفة: طريقة دفع لكل مصروف، أكثر من موظف مع تشفير كلمات المرور، تعديل وحذف المشتريات والمصاريف من صفحاتها، دفتر دين لكل زبون، جرد وتكلفة بضاعة، وعدم احتساب الرواتب على الأشهر المستقبلية في الجدول السنوي.
