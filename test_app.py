"""اختبار تلقائي لنظام Talia Cocktail.
التشغيل: pip install playwright && python -m playwright install chromium && python tests/test_app.py
"""
import sys, json, pathlib, os
from playwright.sync_api import sync_playwright

target = sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parent.parent / 'index.html')
CHROME = os.environ.get('CHROME_PATH')
errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox']) if CHROME else p.chromium.launch()
    pg = b.new_page(viewport={'width': 1280, 'height': 900})
    pg.on('pageerror', lambda e: errors.append('PAGEERROR ' + str(e)))
    pg.on('dialog', lambda d: (errors.append('PAGEERROR native dialog used: ' + d.message), d.dismiss()))
    pg.on('console', lambda m: errors.append('CONSOLE ' + m.text) if m.type == 'error' else None)
    pg.route('**/cdn.jsdelivr.net/**', lambda r: r.fulfill(body='window.Tesseract={}', content_type='text/javascript'))
    pg.set_default_timeout(8000)
    pg.goto(pathlib.Path(target).as_uri())
    pg.evaluate("localStorage.clear();sessionStorage.clear()")
    pg.reload()
    # wrong password
    pg.fill('#lu', 'admin'); pg.fill('#lp', 'wrong'); pg.click('#login button.pri')
    assert pg.is_visible('#login'), 'wrong pw must fail'
    pg.fill('#lp', 'Talia@2026'); pg.click('#login button.pri')
    pg.wait_for_timeout(300)
    assert pg.is_visible('#app'), 'login failed'
    r = pg.evaluate("""()=>{
      const out={};
      const d=isoLocalDate();
      // daily cash/visa + credit via upsert
      upsertDailySale('cash',d,1200,'t','');upsertDailySale('visa',d,300,'t','');upsertDailySale('credit',d,500,'t','');
      purchases.unshift({id:entryUniqueId(),section:'secondary',category:'x',name:'<img src=x onerror=window.__xss=1>',qty:1,date:d,price:200,paid:200,paymentStatus:'paid',supplier:''});set('tc_purchases',purchases);
      expenses.unshift({id:1,section:'fixed',type:'كهرباء',date:d,amount:100});expenses.unshift({id:2,section:'operating',type:'op',date:d,amount:50});set('tc_expenses',expenses);
      dailyWithdrawals.unshift({id:3,date:d,amount:80,note:'n'});set('tc_daily_withdrawals',dailyWithdrawals);
      workers.unshift({id:Date.now()-86400000*400,name:'w',due:3000,advances:[{id:4,date:d,amount:70,cashPaid:true}]});set('tc_workers',workers);
      render();
      out.netBefore=cashSummaryFor(x=>String(x.date).slice(0,10)===d).netCash; // 700
      collections.unshift({id:5,date:d,client:'c',amount:150,method:'cash'});collections.unshift({id:6,date:d,client:'c',amount:50,method:'bank'});set('tc_collections',collections);render();
      out.netAfterCollect=cashSummaryFor(x=>String(x.date).slice(0,10)===d).netCash; // 850
      out.todayTotal=G('st').textContent;
      out.xss=!!window.__xss;
      // salary change from next month only
      const w=workers[0];selectedWorkerId=w.id;const cur=d.slice(0,7);
      const [y,m]=cur.split('-').map(Number);const next=m===12?(y+1)+'-01':y+'-'+String(m+1).padStart(2,'0');
      setWorkerMonth(next);openWorkerEdit();G('workerEditDue').value=3500;saveWorkerEdit({preventDefault(){}});
      out.wageCur=monthlyWorkerWages(y,m);out.wageNext=monthlyWorkerWages(+next.slice(0,4),+next.slice(5));
      // unpaid main purchase -> linked supplier row, deletable
      G('mainFromCompany').checked=false;toggleMainSupplier();G('mainPaymentStatus').value='unpaid';toggleMainSupplier();G('mainSupplierName').value='مورد1';G('mainName').value='سكر';G('mainQty').value=1;G('mainDate').value=d;G('mainPrice').value=400;
      saveMainP({preventDefault(){},target:{reset(){}}});
      const sup=suppliers.find(s=>s.name==='مورد1');out.supLinked=!!(sup&&sup.purchaseId);out.supBal=lastDebt('مورد1');
      // supplier invoice edit syncs purchase
      G('supDate').value=d;G('supName').value='مورد2';G('supPrev').value=0;G('supInv').value=1000;G('supPay').value=1000;G('supRem').value=0;G('supItem').value='فواكه';G('supQty').value=1;
      saveSupplier({preventDefault(){},target:{reset(){}}});
      const s2=suppliers.find(s=>s.name==='مورد2');selectedSupplierName='مورد2';openSupplierInvoiceEdit(s2.id);G('editSupplierPayment').value=600;saveSupplierInvoiceEdit({preventDefault(){}});
      const p2=purchases.find(q=>Number(q.supplierInvoiceId)===s2.id);out.p2paid=p2.paid;out.p2status=p2.paymentStatus;
      out.backupKeys=TC_BACKUP_KEYS.length;
      out.ym=ym('2026-11-01');
      return out}""")
    print(json.dumps(r, ensure_ascii=False))
    assert r['netBefore'] == 700, r
    assert r['netAfterCollect'] == 850, r
    assert '2,000' in r['todayTotal'], r
    assert not r['xss']
    assert r['wageCur'] == 3000 and r['wageNext'] == 3500, r
    assert r['supLinked'] and r['supBal'] == 400, r
    assert r['p2paid'] == 600 and r['p2status'] == 'unpaid', r
    # change admin password
    pg.evaluate("page('admin')")
    assert pg.is_visible('#adminPwNotice')
    pg.fill('#adminPwCurrent', 'Talia@2026'); pg.fill('#adminPwNew', 'NewPass#2027'); pg.fill('#adminPwConfirm', 'NewPass#2027')
    pg.click('#admin form[onsubmit*=changeAdminPassword] button')
    assert not pg.is_visible('#adminPwNotice')
    pg.evaluate("logout()"); pg.wait_for_timeout(500)
    pg.fill('#lu', 'admin'); pg.fill('#lp', 'Talia@2026'); pg.click('#login button.pri')
    assert pg.is_visible('#login'), 'old pw must fail'
    pg.fill('#lp', 'NewPass#2027'); pg.click('#login button.pri'); pg.wait_for_timeout(300)
    assert pg.is_visible('#app')
    # visit every page
    for pid in ['home','dailyEntry','sales','purchases','expenses','suppliers','cashbox','workers','reports','fakh','dues','externalObligations','admin']:
        pg.evaluate(f"page('{pid}');render()")
    pg.evaluate("page('home')")
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.evaluate("page('cashbox')")
    # company share on net profit + in-page dialogs
    r2 = pg.evaluate("""()=>{const t=mt(+isoLocalDate().slice(0,4),+isoLocalDate().slice(5,7));return {net:t.net,share:t.companyShare,after:t.netAfterCompany}}""")
    print('profit', r2)
    assert abs(r2['share'] - max(0, r2['net']) * 0.10) < 0.01 and abs(r2['after'] - (r2['net'] - r2['share'])) < 0.01
    pg.evaluate("()=>{dailyWithdrawals.unshift({id:991,date:isoLocalDate(),amount:5,note:'t'});set('tc_daily_withdrawals',dailyWithdrawals);render();deleteDailyWithdrawal(991)}")
    pg.wait_for_timeout(200); pg.click('#tcDlgOk'); pg.wait_for_timeout(200)
    assert pg.evaluate("dailyWithdrawals.every(x=>x.id!==991)")
    b.close()
print('ERRORS:', errors)
print('ALL TESTS PASSED' if not [e for e in errors if 'PAGEERROR' in e] else 'PAGE ERRORS')
