import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# 1. إعدادات الصفحة واللغة (يمين إلى يسار)
st.set_page_config(page_title="نظام تقارير كاريتاس", layout="wide")

# كود CSS لتحويل الاتجاه للعربية وتحسين الألوان وإخفاء معالم Streamlit
st.markdown("""
    <style>
    /* تحويل الصفحة لليمين */
    .main { direction: rtl; text-align: right; }
    .stSidebar { direction: rtl; }
    [data-testid="stMetricValue"] { text-align: right; color: #1f77b4; }
    
    /* إخفاء القوائم غير الضرورية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* تنسيق الجداول والخانات */
    .stDataFrame { direction: rtl; }
    input { text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# 2. الاتصال بـ Supabase
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- وظائف النظام المطورة ---

def check_login(username, password):
    try:
        res = supabase.table("app_users").select("*").eq("id", username).eq("password_hash", password).execute()
        return res.data[0] if res.data else None
    except: return None

def fetch_all_data_paginated():
    """وظيفة تجلب كل البيانات مهما كان عددها (تتخطى حاجز الـ 1000)"""
    all_data = []
    limit = 1000
    offset = 0
    
    while True:
        res = supabase.table("all_payments_report").select("*").range(offset, offset + limit - 1).execute()
        data = res.data
        all_data.extend(data)
        if len(data) < limit: # إذا رجع أقل من 1000 يعني مفيش بيانات تانية
            break
        offset += limit
        
    df = pd.DataFrame(all_data)
    if not df.empty:
        df['تاريخ الدفع'] = pd.to_datetime(df['تاريخ الدفع'], dayfirst=True)
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
                else:
                    st.error("خطأ في البيانات")
else:
    # --- لوحة التحكم ---
    user = st.session_state['user']
    is_admin = user.get('role') == 'admin'
    user_branches = user.get('branches', [])

    st.sidebar.markdown(f"### أهلاً: {user['full_name']}")
    if st.sidebar.button("خروج"):
        del st.session_state['user']
        st.rerun()

    # جلب كافة البيانات (بدون ليميت)
    with st.spinner('جاري تحديث البيانات...'):
        df_raw = fetch_all_data_paginated()

    if not df_raw.empty:
        # فلترة الفروع
        df_accessible = df_raw if is_admin else df_raw[df_raw['branch_name'].isin(user_branches)]

        # --- الفلاتر الجانبية ---
        st.sidebar.header("🔍 فلاتر البحث")
        
        # البحث بالاسم أو الكود (يحتوي على)
        search_query = st.sidebar.text_input("بحث باسم العميل أو الكود:")

        # فلاتر التاريخ
        min_date = df_accessible['تاريخ الدفع'].min().date()
        max_date = df_accessible['تاريخ الدفع'].max().date()
        start_date = st.sidebar.date_input("من تاريخ", min_date)
        end_date = st.sidebar.date_input("إلى تاريخ", max_date)
        
        # فلتر الكود
        codes = ["الكل"] + sorted(df_accessible['كود الخدمة'].unique().tolist())
        selected_code = st.sidebar.selectbox("كود الخدمة", codes)

        # تطبيق الفلاتر
        mask = (df_accessible['تاريخ الدفع'].dt.date >= start_date) & \
               (df_accessible['تاريخ الدفع'].dt.date <= end_date)
        
        if selected_code != "الكل":
            mask &= (df_accessible['كود الخدمة'] == selected_code)
            
        if search_query:
            # البحث في عمود 'اسم العميل' و 'كود العميل'
            mask &= (df_accessible['اسم العميل'].astype(str).str.contains(search_query, na=False)) | \
                    (df_accessible['كود العميل'].astype(str).str.contains(search_query, na=False))

        final_df = df_accessible.loc[mask]

        # --- العرض ---
        st.title("📋 استعراض السدادات")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي المبالغ", f"{final_df['المبلغ'].sum():,.2f} ج.م")
        c2.metric("عدد العمليات", f"{len(final_df)}")
        with c3:
            st.write("**تفاصيل الأكواد:**")
            for c, count in final_df['كود الخدمة'].value_counts().items():
                st.write(f"🔹 {c}: {count}")

        st.divider()

        # عرض الجدول بتنسيق عربي
        display_df = final_df.copy()
        display_df['تاريخ الدفع'] = display_df['تاريخ الدفع'].dt.strftime('%Y-%m-%d')
        st.dataframe(display_df, use_container_width=True)

        # تحميل البيانات
        csv = final_df.to_csv(index=False).encode('utf-8-sig')
        st.sidebar.download_button("📥 تحميل إكسيل", csv, f"Report_{datetime.now().date()}.csv", "text/csv", use_container_width=True)
    else:
        st.warning("لا توجد بيانات.")
