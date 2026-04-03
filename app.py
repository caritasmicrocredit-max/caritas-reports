import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# 1. إعدادات الأمان - قراءة الروابط من Secrets (وليس كتابتها يدوياً)
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error("خطأ في إعدادات Secrets. يرجى التأكد من ضبط SUPABASE_URL و SUPABASE_KEY في Streamlit Settings.")
    st.stop()

# إعدادات الصفحة (العنوان والشكل)
st.set_page_config(page_title="نظام تقارير كاريتاس", layout="wide")

# --- وظيفة التأكد من اسم المستخدم والباسورد ---
def check_login(username, password):
    try:
        res = supabase.table("app_users").select("*").eq("id", username).eq("password_hash", password).execute()
        return res.data[0] if res.data else None
    except:
        return None

# --- وظيفة جلب البيانات من الـ View ---
def fetch_report_data():
    try:
        # إضافة limit كبير لضمان جلب كل الحركات
        res = supabase.table("all_payments_report").select("*").limit(50000).execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return pd.DataFrame()
    
# --- نظام تسجيل الدخول ---
if 'user' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>تسجيل الدخول - نظام سدادات كاريتاس</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
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
    # --- لوحة التحكم بعد الدخول بنجاح ---
    current_user = st.session_state['user']
    user_branches = current_user.get('branches', [])
    is_admin = current_user.get('role') == 'admin'

    # شريط جانبي للمعلومات والخروج
    st.sidebar.success(f"مرحباً: {current_user['full_name']}")
    if st.sidebar.button("تسجيل الخروج"):
        del st.session_state['user']
        st.rerun()

    st.title("📊 استعراض سدادات الفروع")

    # تحميل البيانات
    df = fetch_report_data()

    if not df.empty:
        # تحويل التاريخ لنوع تاريخ لسهولة الفلترة
        df['تاريخ الدفع'] = pd.to_datetime(df['تاريخ الدفع'], dayfirst=True)

        # فلترة البيانات بناءً على فروع المستخدم (إلا إذا كان Admin)
        if not is_admin:
            df = df[df['branch_name'].isin(user_branches)]

        # --- الفلاتر الجانبية ---
        st.sidebar.header("🔍 فلاتر البحث")
        
        # فلتر التاريخ
        min_date = df['تاريخ الدفع'].min().date()
        max_date = df['تاريخ الدفع'].max().date()
        start_date = st.sidebar.date_input("من تاريخ", min_date)
        end_date = st.sidebar.date_input("إلى تاريخ", max_date)
        
        # فلتر كود الخدمة (90074, opay, إلخ)
        available_codes = ["الكل"] + sorted(df['كود الخدمة'].unique().tolist())
        selected_code = st.sidebar.selectbox("كود الخدمة", available_codes)

        # تطبيق الفلاتر على الجدول
        filtered_df = df[
            (df['تاريخ الدفع'].dt.date >= start_date) & 
            (df['تاريخ الدفع'].dt.date <= end_date)
        ]
        
        if selected_code != "الكل":
            filtered_df = filtered_df[filtered_df['كود الخدمة'] == selected_code]

        # --- عرض الإحصائيات في الأعلى ---
        st.subheader("📝 ملخص التقرير")
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي المبالغ", f"{filtered_df['المبلغ'].sum():,.2f} ج.م")
        c2.metric("عدد الحركات", f"{len(filtered_df)} حركة")
        
        # توزيع الحركات لكل كود
        with c3:
            counts = filtered_df['كود الخدمة'].value_counts()
            for code, count in counts.items():
                st.write(f"🔹 كود **{code}**: {count} حركة")

        st.divider()

        # --- عرض الجدول النهائي ---
        # تنسيق التاريخ للعرض فقط بشكل لطيف
        display_df = filtered_df.copy()
        display_df['تاريخ الدفع'] = display_df['تاريخ الدفع'].dt.strftime('%Y-%m-%d')
        st.dataframe(display_df, use_container_width=True)

        # --- زر التنزيل ---
        st.sidebar.divider()
        csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.sidebar.download_button(
            label="📥 تحميل النتائج (Excel)",
            data=csv,
            file_name=f"Report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
            use_container_width=True
        )
    else:
        st.warning("لا توجد بيانات متاحة لعرضها بناءً على صلاحياتك.")