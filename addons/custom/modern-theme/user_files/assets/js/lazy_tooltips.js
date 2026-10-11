/**
 * lazy_tooltips.js
 *
 * ה-HTML מכיל רק data-tt="key" ולא שום טקסט טולטיפ.
 * div אחד (#global_tooltip) עוקב אחרי הסמן — נוצר/מוסר דינמית.
 */
(function () {

    var TT = {
        'nav-write':    'לייג צו א פראגע און אן ענטפער',
        'nav-menu':     'מעניו "טעקע"',
        'nav-home':     'גיי צום הויפט עקראן',
        'nav-browse':   'עפנט דעם דורכבלעטערער פענסטער',
        'nav-filter':   'שאף א פעקל מיט פראגעס געפילטערט לויט א געוויסער איינשטעלונג',
        'nav-stats':    'עפנט דעם סטאטיסטיק פענסטער',
        'nav-help':     'מעניו "הילף"',
        'btn-add-deck': 'שאף א נייעם נושא ווי ש״ס, הלכה.',
        'btn-write':    'שרייבט א פראגע',
        'btn-browse':   'בלעטערט דורכן פעקל',
        'btn-subdeck':  'לייג צו אן אונטערפעקל',
        'btn-test':     'הייב אן א חזרה',
        'st-total':     'דריקט דא צו אנהייבן א חזרה אויף<br>אלע פראגעס וואס ווארטן פאר חזרה.',
        'st-added':     'נייע פראגעס<br>וואס זענען היינט געשריבן אדער צוגעלייגט געווארן',
        'st-studied':   'דריקט דא צו ווייזן<br>אלע פראגעס וואס מען האט היינט געלערנט.',
        'st-today':     'דריקט דא צו אנהייבן א חזרה אויף<br>אלע פראגעס וואס זענען געפלאנט פאר היינט.',
        'st-overdue':   'דריקט דא צו אנהייבן א חזרה אויף<br>אלע פארשפעטיגטע פראגעס.',
        'st-new':       'דריקט דא צו אנהייבן א חזרה אויף<br>אלע נייע פראגעס.',
        'st-beyond-cap': 'חזרה קארטלעך וואס זענען איבער דער טעגליכער חזרה גרעניץ<br>און וועלן היינט נישט צוגעשטעלט ווערן צום לערנען.',
        'db-tomorrow':  'איר האט פארענדיגט פאר היינט!<br>דריקט דא צו פריער חזרן קארטלעך פון מארגן.',
        'ov-studied':   'היינט געלערנט',
        'ov-sched':     'געפלאנט פאר היינט',
        'ov-overdue':   'פארשפעטיגט',
        'ov-new':       'נייע (אויך אפגעשטעלטע)'
    };

    var ICON_TIPS = {
        'empty':    'קיין פראגעס געהערן נאך נישט צו דעם פעקל',
        'done':     'אין דעם פעקל זענען נישט דא קיין פראגעס וואס ווארטן פאר חזרה היינט',
        'filtered': 'דאס איז א געפילטערטער פעקל',
        'overdue':  'עס זענען נאך געבליבן {n} פראגעס וואס זענען געפלאנט געווען פאר פריערדיגע טעג',
        'due':      'עס זענען נאך געבליבן פראגעס געפלאנט פאר היינט',
        'buried':   'פארענדיגט, אבער עס זענען דא {n} באזייטיגטע קארטלעך'
    };

    // #280 — האבחון החי הוכיח שמסמך ה-WebView עצמו נגלל (HTML.scrollTop=87.2)
    // בזמן שמיכל החפיסות נשאר ב-scrollTop=0. במסך החפיסות הגלילה התקינה היא רק
    // בתוך .deck-tree-container/עמודת הסטטיסטיקות, ולכן כל גלילה של שורש המסמך
    // מוחזרת מיד לאפס. הבדיקה לנוכחות עץ החפיסות מונעת השפעה על מבחן/Overview.
    function resetDeckBrowserRootScroll() {
        if (!document.querySelector('.deck-tree-container')) return;
        var root = document.scrollingElement || document.documentElement;
        if (root && root.scrollTop !== 0) {
            root.scrollTop = 0;
        }
    }

    // #280 — מתקינים פעם אחת על ה-WebView. גם אם אותו WebView משמש אחר כך
    // למסך אחר, הפונקציה אינה פועלת כשאין בו .deck-tree-container.
    if (!window.__hafDeckBrowserRootScrollGuardInstalled) {
        window.__hafDeckBrowserRootScrollGuardInstalled = true;
        window.addEventListener('scroll', resetDeckBrowserRootScroll, { passive: true });
        window.addEventListener('pageshow', resetDeckBrowserRootScroll, false);
    }
    resetDeckBrowserRootScroll();
    requestAnimationFrame(resetDeckBrowserRootScroll);
    setTimeout(resetDeckBrowserRootScroll, 0);
    setTimeout(resetDeckBrowserRootScroll, 100);

    function buildText(el) {
        var d = el.dataset, key = d.tt;
        if (!key) return null;

        if (TT[key]) return TT[key];

        if (key === 'db-pb') {
            var lines = [d.nLabel + (d.n && d.n !== '0' && d.n !== '' ? ': ' + d.n : '')];
            for (var i = 1; i <= 4; i++) {
                var en = d['nE' + i], el2 = d['nE' + i + 'l'];
                if (en && el2 && en !== '0') lines.push('(' + en + ' ' + el2 + ')');
            }
            return lines.join('<br>');
        }

        if (key === 'db-time') {
            return 'חשבון: דורכשניטליכע צייט פאר א פראגע (' + d.nAvg + ' סעקונדעס)<br>מאל די פראגעס וואס ווארטן (' + d.nExp + ')';
        }

        if (key === 'db-count') {
            var txt = 'סך הכל פראגעס אין דעם פעקל: ' + d.n;
            if (d.nS && d.nS !== '0') txt += '<br><span style="color:rgb(154,229,229)">אפגעשטעלטע: ' + d.nS + '</span>';
            return txt;
        }

        if (key === 'db-icon') {
            var tmpl = ICON_TIPS[d.nType] || '';
            return d.n && d.n !== '0' ? tmpl.replace('{n}', d.n) : tmpl;
        }

        return null;
    }

    // div אחד בלבד — נוצר אם לא קיים כבר
    // הצגת פונט יפה בטולטיפ גם במבחן
    var tip = document.getElementById('global_tooltip');
    if (!tip) {
        tip = document.createElement('div');
        tip.id = 'global_tooltip';
        tip.style.cssText = 'position:fixed;display:none;background:#333;color:#fff;border:1px solid #555;padding:5px 10px;border-radius:5px;font-size:0.9rem;font-family: var(--bs-body-font-family);z-index:99999;pointer-events:none;box-shadow:0 4px 6px rgba(0,0,0,.3);max-width:300px;text-align:center;direction:rtl;';
        document.body.appendChild(tip);
    }

    document.addEventListener('mouseover', function (e) {
        var el = e.target.closest && e.target.closest('[data-tt]');
        if (!el) return;
        var text = buildText(el);
        if (!text) return;
        tip.innerHTML = text;
        tip.style.display = 'block';
    }, false);

    document.addEventListener('mousemove', function (e) {
        if (tip.style.display === 'none') return;
        var x = e.clientX + 15, y = e.clientY + 15;
        if (x + 310 > window.innerWidth) x = e.clientX - 175;
        if (y + tip.offsetHeight + 10 > window.innerHeight) y = e.clientY - tip.offsetHeight - 10;
        tip.style.left = x + 'px';
        tip.style.top = y + 'px';
    }, false);

    document.addEventListener('mouseout', function (e) {
        var el = e.target.closest && e.target.closest('[data-tt]');
        if (!el) return;
        if (e.relatedTarget && el.contains(e.relatedTarget)) return;
        tip.style.display = 'none';
    }, false);

})();
