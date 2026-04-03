import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# 1. إعدادات الصفحة واللغة
st.set_page_config(page_title="نظام تقارير كاريتاس", layout="wide")

# كود CSS لتنسيق الواجهة (RTL) وتحسين الألوان
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    .stSidebar { direction: rtl; }
    [data-testid="stMetricValue"] { text-align: right; color: #1f77b4; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    input { text-align: right; }
    .stDataFrame div { direction: rtl; }
    /* تحسين شكل خانات الإدخال */
    div[data-baseweb="input"] { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# 2. الاتصال بـ Supabase
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- وظائف النظام ---

def check_login(username, password):
    try:
        res = supabase.table("app_users").select("*").eq("id", username).eq("password_hash", password).execute()
        return res.data[0] if res.data else None
    except: return None

def fetch_all_data_paginated():
    """جلب كل البيانات مع تخطي حاجز الـ 1000 سطر"""
    all_data = []
    limit = 1000
    offset = 0
    while True:
        res = supabase.table("all_payments_report").select("*").range(offset, offset + limit - 1).execute()
        data = res.data
        if not data: break
        all_data.extend(data)
        if len(data) < limit: break
        offset += limit
    df = pd.DataFrame(all_data)
    if not df.empty:
        # تحويل التاريخ مع معالجة الأخطاء
        df['تاريخ الدفع'] = pd.to_datetime(df['تاريخ الدفع'], dayfirst=True, errors='coerce')
    return df

# --- واجهة تسجيل الدخول ---
if 'user' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>نظام سدادات كاريتاس - تسجيل الدخول</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول", use_container_width=True):
                user = check_login(u, p)
                if user:
                    st.session_state['user'] = user
                    st.rerun()
                else: st.error("بيانات الدخول غير صحيحة")
else:
    user = st.session_state['user']
    is_admin = user.get('role') == 'admin'
    user_branches = user.get('branches', [])

    st.sidebar.markdown(f"### أهلاً بك: \n**{user['full_name']}**")
    if st.sidebar.button("تسجيل الخروج"):
        del st.session_state['user']
        st.rerun()

    with st.spinner('جاري تحميل البيانات المحدثة...'):
        df_raw = fetch_all_data_paginated()

    if not df_raw.empty:
        # فلترة الفروع بناءً على الصلاحية
        df_acc = df_raw if is_admin else df_raw[df_raw['branch_name'].isin(user_branches)]

        # --- الفلاتر الجانبية ---
        st.sidebar.header("🔍 أدوات البحث")
        
        # خانات بحث مستقلة
        search_name = st.sidebar.text_input("بحث باسم العميل:")
        search_code = st.sidebar.text_input("بحث بكود العميل:")

        # فلاتر التاريخ
        valid_dates = df_acc['تاريخ الدفع'].dropna()
        if not valid_dates.empty:
            start_date = st.sidebar.date_input("من تاريخ", valid_dates.min().date())
            end_date = st.sidebar.date_input("إلى تاريخ", valid_dates.max().date())
        else:
            start_date, end_date = None, None

        codes = ["الكل"] + sorted(df_acc['كود الخدمة'].unique().tolist())
        sel_code = st.sidebar.selectbox("كود الخدمة", codes)

        # --- تطبيق الفلترة المنطقية ---
        mask = pd.Series([True] * len(df_acc), index=df_acc.index)
        
        # فلتر التاريخ
        if start_date and end_date:
            mask &= (df_acc['تاريخ الدفع'].dt.date >= start_date) & (df_acc['تاريخ الدفع'].dt.date <= end_date)
        
        # فلتر كود الخدمة
        if sel_code != "الكل":
            mask &= (df_acc['كود الخدمة'] == sel_code)
            
        # بحث بالاسم (يحتوي على جزء من النص)
        if search_name:
            mask &= df_acc['client_name'].astype(str).str.contains(search_name, na=False, case=False)
            
        # بحث بكود العميل (يحتوي على جزء من النص)
        if search_code:
            mask &= df_acc['client_code'].astype(str).str.contains(search_code, na=False, case=False)

        final_df = df_acc.loc[mask]

        # --- العرض الرئيسي ---
        st.title("📑 استعراض تقارير السدادات")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي المبالغ", f"{final_df['المبلغ'].sum():,.2f} ج.م")
        c2.metric("عدد العمليات", f"{len(final_df)}")
        with c3:
            st.write("**إحصائيات الأكواد:**")
            counts = final_df['كود الخدمة'].value_counts()
            for c, count in counts.items():
                st.write(f"🔹 {c}: {count} حركة")

        st.divider()
        
        # تنسيق الجدول النهائي للعرض
        display_df = final_df.copy()
        # إعادة تسمية الأعمدة لتظهر بالعربي في الجدول
        display_df = display_df.rename(columns={
            'client_code': 'كود العميل',
            'client_name': 'اسم العميل',
            'branch_name': 'الفرع'
        })
        
        if 'تاريخ الدفع' in display_df.columns:
            display_df['تاريخ الدفع'] = display_df['تاريخ الدفع'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(display_df, use_container_width=True)

        # زر التحميل
        csv = final_df.to_csv(index=False).encode('utf-8-sig')
        st.sidebar.download_button("📥 تحميل التقرير (Excel)", csv, f"Caritas_Report_{datetime.now().date()}.csv", "text/csv", use_container_width=True)
    else:
        st.warning("لا توجد بيانات حالياً.")

st.sidebar.markdown("---")
st.sidebar.caption("نظام كاريتاس 2026")