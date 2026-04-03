import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# 1. إعدادات الصفحة وإخفاء معالم Streamlit و GitHub
st.set_page_config(
    page_title="نظام تقارير كاريتاس", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# كود CSS لإخفاء زر GitHub والقائمة العلوية تماماً لضمان الخصوصية
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    div.block-container {padding-top: 2rem;}
    </style>
    """, unsafe_allow_html=True)

# 2. الاتصال بـ Supabase من الـ Secrets
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error("يرجى ضبط SUPABASE_URL و SUPABASE_KEY في إعدادات Secrets على Streamlit Cloud.")
    st.stop()

# --- وظائف النظام ---

def check_login(username, password):
    """التحقق من بيانات الدخول"""
    try:
        res = supabase.table("app_users").select("*").eq("id", username).eq("password_hash", password).execute()
        return res.data[0] if res.data else None
    except:
        return None

def fetch_data():
    """جلب كافة البيانات مع تجاوز حد الـ 1000 سطر"""
    try:
        # استخدام limit(100000) لجلب كل الحركات في قاعدة البيانات
        res = supabase.table("all_payments_report").select("*").limit(100000).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            # تحويل التاريخ لنوع datetime للفلترة الصحيحة
            df['تاريخ الدفع'] = pd.to_datetime(df['تاريخ الدفع'], dayfirst=True)
        return df
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return pd.DataFrame()

# --- واجهة تسجيل الدخول ---

if 'user' not in st.session_state:
    st.markdown("<h2 style='text-align: center; color: #2c3e50;'>نظام استعراض سدادات كاريتاس</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            u = st.text_input("اسم المستخدم (ID)")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول للنظام", use_container_width=True):
                user = check_login(u, p)
                if user:
                    st.session_state['user'] = user
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
else:
    # --- لوحة التحكم (Dashboard) ---
    user = st.session_state['user']
    is_admin = user.get('role') == 'admin'
    user_branches = user.get('branches', []) # مصفوفة الفروع المسموحة

    # الشريط الجانبي
    st.sidebar.markdown(f"### مرحباً: \n **{user['full_name']}**")
    if st.sidebar.button("تسجيل الخروج", use_container_width=True):
        del st.session_state['user']
        st.rerun()

    st.sidebar.divider()
    
    # جلب البيانات
    df_raw = fetch_data()

    if not df_raw.empty:
        # 1. فلترة الفروع حسب الصلاحيات
        if is_admin:
            df_accessible = df_raw.copy()
        else:
            # عرض فقط الفروع الموجودة في مصفوفة اليوزر
            df_accessible = df_raw[df_raw['branch_name'].isin(user_branches)].copy()

        # 2. فلاتر البحث في الجانب
        st.sidebar.header("🔍 فلاتر التقارير")
        
        # فلتر التاريخ
        min_d = df_accessible['تاريخ الدفع'].min().date()
        max_d = df_accessible['تاريخ الدفع'].max().date()
        date_range = st.sidebar.date_input("اختر الفترة", [min_d, max_d])
        
        # فلتر كود الخدمة (90074, opay, إلخ)
        codes = ["الكل"] + sorted(df_accessible['كود الخدمة'].unique().tolist())
        selected_code = st.sidebar.selectbox("كود الخدمة", codes)

        # تطبيق الفلاتر النهائية
        if len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df_accessible['تاريخ الدفع'].dt.date >= start_date) & \
                   (df_accessible['تاريخ الدفع'].dt.date <= end_date)
        else:
            mask = True

        if selected_code != "الكل":
            mask = mask & (df_accessible['كود الخدمة'] == selected_code)
            
        final_df = df_accessible.loc[mask]

        # --- العرض الرئيسي ---
        st.title("📑 تقرير السدادات")
        
        # الإحصائيات العلوية
        m1, m2, m3 = st.columns(3)
        m1.metric("إجمالي المبالغ المفلترة", f"{final_df['المبلغ'].sum():,.2f} ج.م")
        m2.metric("عدد الحركات", f"{len(final_df)} حركة")
        
        with m3:
            st.markdown("**تفاصيل الأكواد:**")
            counts = final_df['كود الخدمة'].value_counts()
            for c, count in counts.items():
                st.write(f"🔹 {c}: {count} حركة")

        st.divider()

        # عرض الجدول
        # تحويل التاريخ لشكل نصي للعرض فقط
        display_df = final_df.copy()
        display_df['تاريخ الدفع'] = display_df['تاريخ الدفع'].dt.strftime('%Y-%m-%d')
        st.dataframe(display_df, use_container_width=True)

        # زر التحميل
        st.sidebar.divider()
        csv = final_df.to_csv(index=False).encode('utf-8-sig')
        st.sidebar.download_button(
            label="📥 تحميل النتائج Excel/CSV",
            data=csv,
            file_name=f"Caritas_Report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
            use_container_width=True
        )
    else:
        st.warning("لا توجد بيانات متاحة لعرضها.")

# تذييل بسيط
st.sidebar.markdown("---")
st.sidebar.caption("نظام إدارة ميكروكريديت - كاريتاس")