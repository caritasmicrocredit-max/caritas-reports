import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام تقارير كاريتاس", layout="wide")

# 2. كود التنسيق الاحترافي (CSS) - لجعل الواجهة يمين والشكل مربعات
st.markdown("""
    <style>
    /* جعل الصفحة بالكامل من اليمين للشمال */
    .main { direction: rtl; text-align: right; }
    [data-testid="stSidebar"] { direction: rtl; background-color: #f8f9fa; }
    
    /* تنسيق العنوان في المنتصف */
    .main-title {
        text-align: center;
        color: #1e3a8a;
        background-color: #eff6ff;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #bfdbfe;
        margin-bottom: 30px;
    }

    /* تنسيق مربعات الإحصائيات */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-top: 5px solid #1e3a8a;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1e3a8a;
    }
    .metric-label {
        font-size: 16px;
        color: #6b7280;
    }

    /* إخفاء معالم ستريمليت وجيت هاب */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* تحسين شكل الجدول */
    .stDataFrame { border: 1px solid #e5e7eb; border-radius: 10px; }
    
    /* ضبط خانات البحث في اليمين */
    input { text-align: right; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# 3. الاتصال بـ Supabase
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- الوظائف ---
def fetch_all_data_paginated():
    all_data = []
    limit, offset = 1000, 0
    while True:
        res = supabase.table("all_payments_report").select("*").range(offset, offset + limit - 1).execute()
        if not res.data: break
        all_data.extend(res.data)
        if len(res.data) < limit: break
        offset += limit
    df = pd.DataFrame(all_data)
    if not df.empty:
        df['تاريخ الدفع'] = pd.to_datetime(df['تاريخ الدفع'], dayfirst=True, errors='coerce')
    return df

def check_login(u, p):
    res = supabase.table("app_users").select("*").eq("id", u).eq("password_hash", p).execute()
    return res.data[0] if res.data else None

# --- واجهة الدخول ---
if 'user' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>تسجيل دخول الموظفين</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.form("login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول", use_container_width=True):
                user = check_login(u, p)
                if user:
                    st.session_state['user'] = user
                    st.rerun()
                else: st.error("خطأ في البيانات")
else:
    # --- لوحة التحكم ---
    user = st.session_state['user']
    is_admin = user.get('role') == 'admin'
    user_branches = user.get('branches', [])

    # البحث في الشريط الجانبي (اليمين)
    st.sidebar.markdown(f"<h3 style='text-align:right;'>أهلاً بك: {user['full_name']}</h3>", unsafe_allow_html=True)
    if st.sidebar.button("خروج", use_container_width=True):
        del st.session_state['user']
        st.rerun()

    st.sidebar.divider()
    st.sidebar.header("🔍 أدوات البحث")
    s_name = st.sidebar.text_input("بحث باسم العميل")
    s_code = st.sidebar.text_input("بحث بكود العميل")
    
    df_raw = fetch_all_data_paginated()
    if not df_raw.empty:
        df_acc = df_raw if is_admin else df_raw[df_raw['branch_name'].isin(user_branches)]
        
        # فلاتر التاريخ والخدمة
        v_dates = df_acc['تاريخ الدفع'].dropna()
        start_d = st.sidebar.date_input("من تاريخ", v_dates.min().date())
        end_d = st.sidebar.date_input("إلى تاريخ", v_dates.max().date())
        
        codes = ["الكل"] + sorted(df_acc['كود الخدمة'].unique().tolist())
        sel_code = st.sidebar.selectbox("كود الخدمة", codes)

        # تطبيق الفلترة
        mask = (df_acc['تاريخ الدفع'].dt.date >= start_d) & (df_acc['تاريخ الدفع'].dt.date <= end_d)
        if sel_code != "الكل": mask &= (df_acc['كود الخدمة'] == sel_code)
        if s_name: mask &= df_acc['client_name'].astype(str).str.contains(s_name, na=False, case=False)
        if s_code: mask &= df_acc['client_code'].astype(str).str.contains(s_code, na=False, case=False)
        
        final_df = df_acc.loc[mask]

        # --- العرض الرئيسي ---
        st.markdown('<div class="main-title"><h1>📑 استعراض تقارير السدادات</h1></div>', unsafe_allow_html=True)

        # المربعات العلوية
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">إجمالي المبالغ</div>
                        <div class="metric-value">{final_df['المبلغ'].sum():,.2f} ج.م</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">عدد العمليات</div>
                        <div class="metric-value">{len(final_df)} حركة</div></div>""", unsafe_allow_html=True)
        with col3:
            counts = final_df['كود الخدمة'].value_counts()
            codes_html = "".join([f"<div>{k}: {v}</div>" for k, v in counts.items()])
            st.markdown(f"""<div class="metric-card"><div class="metric-label">تفاصيل الأكواد</div>
                        <div style="font-weight:bold; color:#1e3a8a;">{codes_html}</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # الجدول
        display_df = final_df.copy().rename(columns={'client_code': 'كود العميل', 'client_name': 'اسم العميل', 'branch_name': 'الفرع'})
        if 'تاريخ الدفع' in display_df.columns:
            display_df['تاريخ الدفع'] = display_df['تاريخ الدفع'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(display_df, use_container_width=True)

        # تحميل
        csv = final_df.to_csv(index=False).encode('utf-8-sig')
        st.sidebar.download_button("📥 تحميل التقرير (Excel)", csv, f"Report_{datetime.now().date()}.csv", use_container_width=True)