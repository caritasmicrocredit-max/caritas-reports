import streamlit as st
import base64
import os

# ============================================================
#  تحميل اللوجو — ضع الصورة بجانب app.py باسم: logo.png
#  (أو غيّر الاسم هنا ليناسب اسم ملفك)
# ============================================================
LOGO_FILENAME = "logo.png"   # ← غيّر الاسم هنا لو احتجت

def load_logo(filename):
    """يحمّل الصورة ويحوّلها base64 لتظهر داخل HTML"""
    path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext = filename.rsplit(".", 1)[-1].lower()
        mime = "image/png" if ext == "png" else f"image/{ext}"
        return f'<img src="data:{mime};base64,{data}" style="width:60px;height:60px;object-fit:contain;border-radius:10px;">'
    # لو مفيش لوجو يظهر placeholder
    return '<span style="font-size:36px;">⛪</span>'

LOGO_HTML = load_logo(LOGO_FILENAME)

st.set_page_config(
    page_title="بوابة كاريتاس",
    page_icon="📑",
    layout="wide"
)

# ============================================================
#  قائمة البرامج الـ 15
# ============================================================
PROGRAMS = [
    # ===== البرامج الفعّالة =====
    {
        "icon": "💳",
        "title": "سداد فورى و opay",
        "desc": "75146 + 90074",
        "url": "/sadad_fori",
        "active": True,
        "color": "#3b82f6",
    },
    # ===== تحت الإنشاء =====
    {"icon": "🏥", "title": "الخدمات الصحية",    "desc": "إدارة ملفات المرضى",        "url": "#", "active": False, "color": "#64748b"},
    {"icon": "🎓", "title": "الدعم التعليمي",    "desc": "المنح والمساعدات",           "url": "#", "active": False, "color": "#64748b"},
    {"icon": "🏠", "title": "الإسكان والمأوى",   "desc": "طلبات السكن الطارئ",        "url": "#", "active": False, "color": "#64748b"},
    {"icon": "👨‍👩‍👧", "title": "دعم الأسرة",       "desc": "برامج الرعاية الأسرية",     "url": "#", "active": False, "color": "#64748b"},
    {"icon": "♿", "title": "ذوو الاحتياجات",    "desc": "خدمات الإعاقة والتأهيل",   "url": "#", "active": False, "color": "#64748b"},
    {"icon": "👴", "title": "رعاية كبار السن",   "desc": "برامج المسنين والرعاية",    "url": "#", "active": False, "color": "#64748b"},
    {"icon": "🍽️", "title": "الأمن الغذائي",     "desc": "توزيع المساعدات الغذائية", "url": "#", "active": False, "color": "#64748b"},
    {"icon": "💼", "title": "دعم التشغيل",       "desc": "برامج التدريب والتوظيف",   "url": "#", "active": False, "color": "#64748b"},
    {"icon": "🌊", "title": "الطوارئ والأزمات",  "desc": "الاستجابة السريعة",         "url": "#", "active": False, "color": "#64748b"},
    {"icon": "📦", "title": "المستودعات",        "desc": "إدارة المخزون والتوزيع",    "url": "#", "active": False, "color": "#64748b"},
    {"icon": "📋", "title": "التقارير الإدارية", "desc": "التقارير والإحصاءات",       "url": "#", "active": False, "color": "#64748b"},
    {"icon": "💰", "title": "الحسابات المالية",  "desc": "المصروفات والميزانيات",     "url": "#", "active": False, "color": "#64748b"},
    {"icon": "🤝", "title": "الشراكات",          "desc": "إدارة المتبرعين والشركاء", "url": "#", "active": False, "color": "#64748b"},
    {"icon": "📊", "title": "لوحة الإدارة",      "desc": "إحصاءات شاملة للإدارة",    "url": "#", "active": False, "color": "#64748b"},
]

# ============================================================
#  CSS التصميم العصري
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&family=Tajawal:wght@300;400;700;900&display=swap');

:root {
    --bg-deep:    #060b18;
    --bg-mid:     #0d1628;
    --bg-card:    rgba(255,255,255,0.04);
    --bg-card-h:  rgba(255,255,255,0.08);
    --border:     rgba(255,255,255,0.08);
    --border-act: rgba(59,130,246,0.6);
    --blue:       #3b82f6;
    --blue-glow:  rgba(59,130,246,0.3);
    --gold:       #f59e0b;
    --text-pri:   #f1f5f9;
    --text-sec:   #94a3b8;
    --text-dim:   #475569;
    --active-grad: linear-gradient(135deg,#1d4ed8,#3b82f6,#0ea5e9);
    --radius:     16px;
}

* { font-family: 'Cairo', 'Tajawal', sans-serif !important; box-sizing: border-box; }

/* إزالة كل عناصر Streamlit الزيادة */
#MainMenu, footer, header, .stDeployButton { display: none !important; visibility: hidden !important; }
[data-testid="stToolbar"]          { display: none !important; }
[data-testid="stDecoration"]       { display: none !important; }
[data-testid="stStatusWidget"]     { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"]   { display: none !important; }

/* خلفية الصفحة */
.stApp {
    background: var(--bg-deep) !important;
    min-height: 100vh;
}
.main .block-container {
    padding: 0 !important;
}

/* ===== الحاوية الرئيسية ===== */
.portal-wrap {
    direction: rtl;
    min-height: 100vh;
    background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(59,130,246,0.15), transparent),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(14,165,233,0.08), transparent),
        var(--bg-deep);
    padding: 0 0 60px;
}

/* ===== خطوط الشبكة الخلفية ===== */
.portal-wrap::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(59,130,246,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(59,130,246,0.04) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 0;
}

/* ===== الهيدر ===== */
.portal-hero {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 36px 56px 32px;
    border-bottom: 1px solid var(--border);
    background: rgba(13,22,40,0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}

/* منطقة اللوجو */
.logo-zone {
    display: flex;
    align-items: center;
    gap: 18px;
}
.logo-box {
    width: 72px;
    height: 72px;
    border-radius: 18px;
    border: 2px dashed rgba(59,130,246,0.4);
    background: rgba(59,130,246,0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s;
}
.logo-box::after {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 18px;
    background: linear-gradient(135deg,rgba(59,130,246,0.3),transparent,rgba(14,165,233,0.2));
    pointer-events: none;
}
.logo-text-area { text-align: right; }
.logo-name {
    font-size: 26px;
    font-weight: 900;
    color: var(--text-pri);
    margin: 0;
    letter-spacing: -0.5px;
    line-height: 1.2;
}
.logo-name span { color: var(--blue); }
.logo-tagline {
    font-size: 13px;
    color: var(--text-sec);
    margin: 3px 0 0;
    font-weight: 400;
}

/* شارة الإصدار */
.version-badge {
    background: rgba(59,130,246,0.12);
    border: 1px solid rgba(59,130,246,0.25);
    color: var(--blue);
    font-size: 11px;
    font-weight: 700;
    padding: 5px 14px;
    border-radius: 20px;
    letter-spacing: 0.5px;
}

/* ===== شريط المعلومات ===== */
.info-bar {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 48px;
    padding: 18px 56px;
    background: rgba(59,130,246,0.06);
    border-bottom: 1px solid var(--border);
    direction: rtl;
}
.info-item {
    display: flex;
    align-items: center;
    gap: 10px;
}
.info-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 8px #22c55e;
    animation: pulse-dot 2s infinite;
}
.info-dot-dim { background: var(--text-dim); box-shadow: none; animation: none; }
@keyframes pulse-dot {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.6; transform:scale(1.3); }
}
.info-label { font-size: 12px; color: var(--text-sec); }
.info-value { font-size: 13px; font-weight: 700; color: var(--text-pri); }

/* ===== عنوان القسم ===== */
.section-header {
    position: relative;
    z-index: 1;
    padding: 40px 56px 24px;
    direction: rtl;
}
.section-title {
    font-size: 15px;
    font-weight: 700;
    color: var(--text-sec);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 0 0 6px;
}
.section-title::before {
    content: '';
    display: inline-block;
    width: 20px;
    height: 2px;
    background: var(--blue);
    margin-left: 10px;
    vertical-align: middle;
}
.section-count {
    font-size: 13px;
    color: var(--text-dim);
}
.section-count span { color: var(--blue); font-weight: 700; }

/* ===== شبكة البطاقات ===== */
.programs-grid {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 18px;
    padding: 0 56px 40px;
    direction: rtl;
}

/* ===== بطاقة البرنامج ===== */
.prog-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 28px 20px 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform 0.25s, box-shadow 0.25s, border-color 0.25s, background 0.25s;
    cursor: default;
}
.prog-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
}

/* بطاقة فعّالة */
.prog-card.active {
    border-color: var(--border-act);
    background: linear-gradient(145deg, rgba(29,78,216,0.12), rgba(59,130,246,0.06));
    cursor: pointer;
}
.prog-card.active::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--radius);
    box-shadow: 0 0 30px rgba(59,130,246,0.15) inset;
    pointer-events: none;
}
.prog-card.active:hover {
    transform: translateY(-4px);
    border-color: var(--blue);
    box-shadow: 0 16px 48px rgba(59,130,246,0.2), 0 0 0 1px rgba(59,130,246,0.3);
    background: linear-gradient(145deg, rgba(29,78,216,0.2), rgba(59,130,246,0.1));
}

/* بطاقة غير فعّالة */
.prog-card.inactive { opacity: 0.55; }
.prog-card.inactive:hover {
    opacity: 0.75;
    border-color: rgba(255,255,255,0.12);
    transform: translateY(-2px);
}

/* شارة الحالة في الزاوية */
.status-badge {
    position: absolute;
    top: 12px;
    left: 12px;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.3px;
}
.status-active {
    background: rgba(59,130,246,0.2);
    color: #93c5fd;
    border: 1px solid rgba(59,130,246,0.3);
}
.status-wip {
    background: rgba(245,158,11,0.15);
    color: #fbbf24;
    border: 1px solid rgba(245,158,11,0.25);
}

/* أيقونة البطاقة */
.card-icon-wrap {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    margin: 0 auto 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    position: relative;
}
.card-icon-wrap.active-icon {
    background: linear-gradient(135deg, rgba(29,78,216,0.3), rgba(59,130,246,0.2));
    border: 1px solid rgba(59,130,246,0.4);
    box-shadow: 0 4px 20px rgba(59,130,246,0.2);
}
.card-icon-wrap.dim-icon {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.07);
}

.card-title-active {
    font-size: 14px;
    font-weight: 800;
    color: var(--text-pri);
    margin: 0 0 6px;
    line-height: 1.4;
}
.card-title-inactive {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-sec);
    margin: 0 0 6px;
    line-height: 1.4;
}
.card-desc {
    font-size: 11px;
    color: var(--text-dim);
    margin: 0 0 18px;
    line-height: 1.6;
}

/* زرار الفتح */
.open-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--active-grad);
    color: white !important;
    text-decoration: none !important;
    padding: 9px 22px;
    border-radius: 30px;
    font-size: 12px;
    font-weight: 700;
    box-shadow: 0 4px 16px rgba(59,130,246,0.35);
    transition: opacity 0.2s, transform 0.2s;
    letter-spacing: 0.3px;
}
.open-link:hover {
    opacity: 0.9;
    transform: scale(1.03);
    color: white !important;
    text-decoration: none !important;
}
.soon-tag {
    display: inline-block;
    background: rgba(255,255,255,0.05);
    color: var(--text-dim);
    padding: 7px 20px;
    border-radius: 30px;
    font-size: 11px;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.07);
}

/* ===== الفوتر ===== */
.portal-footer {
    position: relative;
    z-index: 1;
    text-align: center;
    padding: 24px 56px;
    border-top: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 12px;
    direction: rtl;
}
.portal-footer span { color: var(--text-sec); }

/* ===== ريسبونسيف ===== */
@media (max-width: 1200px) {
    .programs-grid { grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 900px) {
    .programs-grid { grid-template-columns: repeat(3, 1fr); padding: 0 24px 40px; }
    .portal-hero { padding: 24px; }
    .section-header { padding: 30px 24px 16px; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
#  بناء HTML الصفحة الكاملة
# ============================================================

# --- شبكة البطاقات ---
cards_html = ""
active_count = sum(1 for p in PROGRAMS if p["active"])
wip_count    = len(PROGRAMS) - active_count

for p in PROGRAMS:
    if p["active"]:
        cards_html += f"""
        <div class="prog-card active">
            <div class="status-badge status-active">● متاح الآن</div>
            <div class="card-icon-wrap active-icon">{p['icon']}</div>
            <div class="card-title-active">{p['title']}</div>
            <div class="card-desc">{p['desc']}</div>
            <a class="open-link" href="{p['url']}" target="_blank">▶ فتح البرنامج</a>
        </div>
        """
    else:
        cards_html += f"""
        <div class="prog-card inactive">
            <div class="status-badge status-wip">⏳ قريباً</div>
            <div class="card-icon-wrap dim-icon">{p['icon']}</div>
            <div class="card-title-inactive">{p['title']}</div>
            <div class="card-desc">{p['desc']}</div>
            <div class="soon-tag">تحت الإنشاء</div>
        </div>
        """

full_page = f"""
<div class="portal-wrap">

    <!-- ===== الهيدر ===== -->
    <div class="portal-hero">
        <div class="logo-zone">
            <div class="logo-box">{LOGO_HTML}</div>
            <div class="logo-text-area">
                <p class="logo-name">بوابة <span>كاريتاس</span></p>
                <p class="logo-tagline">منظومة البرامج والخدمات الاجتماعية</p>
            </div>
        </div>
        <div class="version-badge">v 2.0 · 2025</div>
    </div>

    <!-- ===== شريط المعلومات ===== -->
    <div class="info-bar">
        <div class="info-item">
            <div class="info-dot"></div>
            <span class="info-label">البرامج النشطة</span>
            <span class="info-value">{active_count}</span>
        </div>
        <div class="info-item">
            <div class="info-dot info-dot-dim"></div>
            <span class="info-label">تحت الإنشاء</span>
            <span class="info-value">{wip_count}</span>
        </div>
        <div class="info-item">
            <span class="info-label">إجمالي البرامج</span>
            <span class="info-value">{len(PROGRAMS)}</span>
        </div>
    </div>

    <!-- ===== عنوان القسم ===== -->
    <div class="section-header">
        <div class="section-title">البرامج والخدمات</div>
        <div class="section-count">
            <span>{active_count}</span> برنامج نشط من أصل {len(PROGRAMS)} —
            اختر البرنامج لفتحه في تبويب جديد
        </div>
    </div>

    <!-- ===== الشبكة ===== -->
    <div class="programs-grid">
        {cards_html}
    </div>

    <!-- ===== الفوتر ===== -->
    <div class="portal-footer">
        <span>نظام كاريتاس © 2025</span> — جميع الحقوق محفوظة · تطوير الفريق التقني
    </div>

</div>
"""

st.markdown(full_page, unsafe_allow_html=True)
