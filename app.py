import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import io
import os
import base64
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ===================== إعدادات الصفحة الأساسية =====================
st.set_page_config(page_title="نظام كاريتاس", layout="wide", page_icon="📊", initial_sidebar_state="auto")

# ===================== الثوابت والتكوين =====================

# مسار اللوجو
def get_logo_path():
    possible_paths = ["logo.png", "images/logo.png", "static/logo.png", "assets/logo.png"]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

LOGO_PATH = get_logo_path()

# تعريف جميع البرامج
PROGRAMS = {
    "active": {
        "reports": {
            "name": "سداد فوري & Opay",
            "icon": "💳📱",
            "icon_image": "sadad_opay",
            "page_title": "تقرير السدادات",
            "description": "عرض وتحليل بيانات السدادات - تقارير دقيقة ومتنوعة",
        },
        "installments": {
            "name": "الأقساط المستحقة",
            "icon": "📋💰",
            "icon_image": "installments",
            "page_title": "تقرير الأقساط المستحقة",
            "description": "عرض الأقساط المستحقة مع بيانات الدفع من فوري و Opay",
        }
    },
    "inactive": {
        "service_1": {"name": "تحت الإنشاء", "icon": "🏦"},
        "service_2": {"name": "تحت الإنشاء", "icon": "💰"},
        "service_3": {"name": "تحت الإنشاء", "icon": "📞"},
        "service_4": {"name": "تحت الإنشاء", "icon": "🟠"},
        "service_5": {"name": "تحت الإنشاء", "icon": "🔴"},
        "service_6": {"name": "تحت الإنشاء", "icon": "💎"},
        "service_7": {"name": "تحت الإنشاء", "icon": "💳"},
        "service_8": {"name": "تحت الإنشاء", "icon": "🏧"},
        "service_9": {"name": "تحت الإنشاء", "icon": "📱"},
        "service_10": {"name": "تحت الإنشاء", "icon": "🟢"},
        "service_11": {"name": "تحت الإنشاء", "icon": "📦"},
        "service_12": {"name": "تحت الإنشاء", "icon": "🏪"},
        "service_13": {"name": "تحت الإنشاء", "icon": "🅱️"},
        "service_14": {"name": "تحت الإنشاء", "icon": "🟡"},
        "service_15": {"name": "تحت الإنشاء", "icon": "📊"},
        "service_16": {"name": "تحت الإنشاء", "icon": "📈"},
        "service_17": {"name": "تحت الإنشاء", "icon": "👥"},
        "service_18": {"name": "تحت الإنشاء", "icon": "⚙️"},
    }
}

# ===================== دالة عرض اللوجو =====================

def show_logo():
    """عرض اللوجو في أعلى يسار الصفحة"""
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <div style="position: fixed; top: 15px; left: 15px; z-index: 9999; background: rgba(255,255,255,0.95); 
                        padding: 5px 10px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <img src="data:image/png;base64,{img_data}" style="height: 60px; width: auto; border-radius: 8px;" alt="Caritas Logo">
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="position: fixed; top: 15px; left: 15px; z-index: 9999; background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); 
                        padding: 8px 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                <div style="color: white; font-weight: bold; font-size: 18px;">📊 كاريتاس</div>
            </div>
        """, unsafe_allow_html=True)

# ===================== الاتصال بـ Supabase =====================

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

def check_login(u, p):
    """التحقق من بيانات الدخول"""
    res = supabase.table("app_users").select("*").eq("id", u).eq("password_hash", p).execute()
    return res.data[0] if res.data else None

# ===================== دوال جلب البيانات =====================

def fetch_reports_data():
    """جلب بيانات تقارير السدادات"""
    all_data = []
    limit, offset = 1000, 0
    while True:
        res = supabase.table("all_payments_report").select("*").range(offset, offset + limit - 1).execute()
        if not res.data:
            break
        all_data.extend(res.data)
        if len(res.data) < limit:
            break
        offset += limit
    df = pd.DataFrame(all_data)
    if not df.empty:
        df['تاريخ الدفع'] = pd.to_datetime(df['تاريخ الدفع'], dayfirst=True, errors='coerce')
    return df

def fetch_outstanding_data():
    """جلب بيانات الأقساط المستحقة من الـ View"""
    all_data = []
    limit, offset = 1000, 0
    while True:
        res = supabase.table("outstanding_with_payments").select("*").range(offset, offset + limit - 1).execute()
        if not res.data:
            break
        all_data.extend(res.data)
        if len(res.data) < limit:
            break
        offset += limit
    df = pd.DataFrame(all_data)
    return df

# ===================== دوال توليد Excel =====================

def thin_border():
    s = Side(border_style="thin", color="D1D5DB")
    return Border(left=s, right=s, top=s, bottom=s)

def write_total_row(ws, total_row, cols, last_data_row):
    """كتابة صف الإجمالي"""
    DARK_BLUE = "1E3A8A"
    TOTAL_BG  = "BFDBFE"
    n_cols = len(cols)

    for ci in range(1, n_cols + 1):
        c = ws.cell(row=total_row, column=ci)
        c.fill = PatternFill("solid", fgColor=TOTAL_BG)
        c.border = thin_border()
        c.alignment = Alignment(horizontal='center', vertical='center')
        c.font = Font(bold=True, color=DARK_BLUE, name="Arial", size=11)

    ws.cell(row=total_row, column=1).value = "✦ الإجمالي"

    if 'المبلغ' in cols:
        amt_ci = cols.index('المبلغ') + 1
        col_letter = get_column_letter(amt_ci)
        ws.cell(row=total_row, column=amt_ci).value = f"=SUM({col_letter}3:{col_letter}{last_data_row})"
        ws.cell(row=total_row, column=amt_ci).number_format = '#,##0.00'

    ws.row_dimensions[total_row].height = 26

def generate_outstanding_excel(df, title="تقرير الأقساط المستحقة"):
    """توليد ملف Excel لتقرير الأقساط المستحقة مع تنسيق ملون"""
    wb = Workbook()
    ws = wb.active
    ws.title = "الأقساط المستحقة"
    ws.sheet_view.rightToLeft = True

    # تحضير الأعمدة
    cols = list(df.columns)
    n_cols = len(cols)
    last_col = get_column_letter(n_cols)

    # عنوان رئيسي
    ws.merge_cells(f'A1:{last_col}1')
    ws['A1'].value = title
    ws['A1'].font = Font(bold=True, size=16, color="1E3A8A", name="Arial")
    ws['A1'].fill = PatternFill("solid", fgColor="EFF6FF")
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 35

    # الرؤوس
    headers = ['اسم المسؤول', 'كود الفرع', 'اسم الفرع', 'تاريخ استحقاق القسط', 'تاريخ حالة القسط',
               'كود العميل', 'اسم العميل', 'الرقم القومي', 'رقم القرض', 'حالة القسط', 'قيمة القسط',
               'نوع الفاتورة', 'تاريخ التحويل', 'وقت التحويل', 'مبلغ فوري', 'رقم حساب الفوترة',
               'رقم تحويل فوري', 'الرقم المرجعي', 'مبلغ Opay', 'تاريخ الدفع Opay', 'وقت الدفع Opay']
    
    for ci, header in enumerate(headers[:len(cols)], 1):
        c = ws.cell(row=2, column=ci, value=header)
        c.font = Font(bold=True, color="FFFFFF", name="Arial", size=11)
        c.fill = PatternFill("solid", fgColor="1E3A8A")
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = thin_border()
    ws.row_dimensions[2].height = 30

    # البيانات مع التلوين
    for ri, row in enumerate(df.itertuples(index=False), 3):
        for ci, val in enumerate(row, 1):
            c = ws.cell(row=ri, column=ci, value=val)
            c.alignment = Alignment(horizontal='center', vertical='center')
            c.font = Font(name="Arial", size=10)
            c.border = thin_border()
            
            # تلوين حسب حالة القسط
            status = str(row[9]) if len(row) > 9 else ""
            if "مسدد جزئي" in status:
                c.fill = PatternFill("solid", fgColor="FFCCCC")
                c.font = Font(color="9C0006", bold=True)
            elif "غير مدفوع" in status or status == "":
                c.fill = PatternFill("solid", fgColor="FFE699")
                c.font = Font(color="7F4A00")
            else:
                c.fill = PatternFill("solid", fgColor="E2EFDA")
                c.font = Font(color="375623")
    
    # ضبط عرض الأعمدة
    col_widths = {'اسم العميل': 25, 'اسم الفرع': 20, 'اسم المسؤول': 18, 'الرقم القومي': 15}
    for ci, col in enumerate(headers[:len(cols)], 1):
        width = col_widths.get(col, 15)
        ws.column_dimensions[get_column_letter(ci)].width = width

    ws.freeze_panes = "A3"
    
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

def generate_reports_excel_single(df_display, sheet_title="التقرير", report_title="تقرير السدادات"):
    """توليد ملف Excel لتقارير السدادات"""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]
    ws.sheet_view.rightToLeft = True

    cols = list(df_display.columns)
    n_cols = len(cols)
    last_col = get_column_letter(n_cols)

    ws.merge_cells(f'A1:{last_col}1')
    ws['A1'].value = report_title
    ws['A1'].font = Font(bold=True, size=14, color="1E3A8A", name="Arial")
    ws['A1'].fill = PatternFill("solid", fgColor="EFF6FF")
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 32

    for ci, header in enumerate(cols, 1):
        c = ws.cell(row=2, column=ci, value=header)
        c.font = Font(bold=True, color="FFFFFF", name="Arial", size=11)
        c.fill = PatternFill("solid", fgColor="1E3A8A")
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = thin_border()
    ws.row_dimensions[2].height = 24

    for ri, row in enumerate(df_display.itertuples(index=False), 3):
        bg = "F0F4FF" if ri % 2 == 0 else "FFFFFF"
        for ci, val in enumerate(row, 1):
            c = ws.cell(row=ri, column=ci, value=val)
            c.fill = PatternFill("solid", fgColor=bg)
            c.alignment = Alignment(horizontal='center', vertical='center')
            c.font = Font(name="Arial", size=10)
            c.border = thin_border()
    last_data_row = 2 + len(df_display)

    write_total_row(ws, last_data_row + 1, cols, last_data_row)

    col_widths = {"اسم العميل": 28, "الفرع": 20}
    for ci, col in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(ci)].width = col_widths.get(col, 18)

    ws.freeze_panes = "A3"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

# ===================== الصفحات =====================

def reports_page():
    """صفحة تقارير السدادات"""
    if 'user' not in st.session_state:
        st.warning("⚠️ يجب تسجيل الدخول أولاً")
        st.stop()
    
    st.markdown('<div style="margin-top: 70px;"></div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="main-title">
            <h1>📑 سداد فوري & Opay</h1>
            <p>عرض وتحليل بيانات السدادات - تقارير دقيقة ومتنوعة</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🏠 العودة للرئيسية", use_container_width=False):
        st.query_params.clear()
        st.rerun()
    
    st.divider()
    
    user = st.session_state['user']
    is_admin = user.get('role') == 'admin'
    user_branches = user.get('branches', [])
    
    with st.sidebar:
        st.markdown(f"### 👤 مرحباً: {user['full_name']}")
        if st.button("🚪 خروج", use_container_width=True):
            del st.session_state['user']
            st.query_params.clear()
            st.rerun()
        st.divider()
        st.markdown("### 🔍 أدوات البحث")
        s_name = st.text_input("🔎 بحث باسم العميل")
        s_code = st.text_input("🔢 بحث بكود العميل")
        st.divider()
        st.markdown("### 📥 تحميل التقرير")
    
    df_raw = fetch_reports_data()
    
    if df_raw.empty:
        st.info("📭 لا توجد بيانات متاحة حالياً")
        return
    
    df_acc = df_raw if is_admin else df_raw[df_raw['branch_name'].isin(user_branches)]
    v_dates = df_acc['تاريخ الدفع'].dropna()
    
    if v_dates.empty:
        st.info("📭 لا توجد تواريخ متاحة")
        return
    
    start_d = st.sidebar.date_input("📅 من تاريخ", v_dates.min().date())
    end_d = st.sidebar.date_input("📅 إلى تاريخ", v_dates.max().date())
    codes = ["الكل"] + sorted(df_acc['كود الخدمة'].unique().tolist())
    sel_code = st.sidebar.selectbox("🏷️ كود الخدمة", codes)
    
    mask = (df_acc['تاريخ الدفع'].dt.date >= start_d) & (df_acc['تاريخ الدفع'].dt.date <= end_d)
    if sel_code != "الكل":
        mask &= (df_acc['كود الخدمة'] == sel_code)
    if s_name:
        mask &= df_acc['client_name'].astype(str).str.contains(s_name, na=False, case=False)
    if s_code:
        mask &= df_acc['client_code'].astype(str).str.contains(s_code, na=False, case=False)
    
    final_df = df_acc.loc[mask]
    
    if final_df.empty:
        st.warning("⚠️ لا توجد بيانات تطابق معايير البحث")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">💰 إجمالي المبالغ</div>
                    <div class="metric-value">{final_df['المبلغ'].sum():,.2f} ج.م</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">📊 عدد العمليات</div>
                    <div class="metric-value">{len(final_df):,} حركة</div></div>""", unsafe_allow_html=True)
    with col3:
        counts = final_df['كود الخدمة'].value_counts()
        codes_html = "".join([f"<div style='font-size:13px'>• {k}: {v}</div>" for k, v in counts.items()])
        st.markdown(f"""<div class="metric-card"><div class="metric-label">📋 تفاصيل الأكواد</div>
                    <div style="font-weight:bold; color:#1e3a8a; text-align:right;">{codes_html}</div></div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("📅 عرض الملخص اليومي", expanded=False):
        daily_summary = final_df.groupby(final_df['تاريخ الدفع'].dt.date).agg(
            عدد_العمليات=('المبلغ', 'count'), إجمالي_المبلغ=('المبلغ', 'sum')).reset_index()
        daily_summary.columns = ['التاريخ', 'عدد العمليات', 'إجمالي المبلغ (ج.م)']
        st.dataframe(daily_summary, use_container_width=True, hide_index=True)
    
    display_df = final_df.copy().rename(columns={
        'client_code': 'كود العميل', 'client_name': 'اسم العميل', 'branch_name': 'الفرع'
    })
    drop_cols = [c for c in display_df.columns if c.startswith('_') or c == 'id']
    display_df = display_df.drop(columns=drop_cols, errors='ignore')
    if 'تاريخ الدفع' in display_df.columns:
        display_df['تاريخ الدفع'] = display_df['تاريخ الدفع'].dt.strftime('%Y-%m-%d')
    
    st.markdown("### 📋 جدول البيانات المفصل")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    excel_bytes = generate_reports_excel_single(display_df, report_title=f"تقرير السدادات - {start_d} إلى {end_d}")
    
    st.sidebar.download_button(
        label="📊 تحميل Excel",
        data=excel_bytes,
        file_name=f"تقرير_{datetime.now().date()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
def outstanding_page():
    """صفحة الأقساط المستحقة"""
    if 'user' not in st.session_state:
        st.warning("⚠️ يجب تسجيل الدخول أولاً")
        st.stop()
    
    st.markdown('<div style="margin-top: 70px;"></div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="main-title">
            <h1>📋💰 الأقساط المستحقة</h1>
            <p>عرض الأقساط المستحقة مع بيانات الدفع من فوري و Opay</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🏠 العودة للرئيسية", use_container_width=False):
        st.query_params.clear()
        st.rerun()
    
    st.divider()
    
    user = st.session_state['user']
    is_admin = user.get('role') == 'admin'
    user_role = user.get('role', '')
    branches_list = user.get('branches', [])
    
    # تحويل branches إلى قائمة إذا كانت string
    if isinstance(branches_list, str):
        import json
        try:
            branches_list = json.loads(branches_list)
        except:
            branches_list = [branches_list]
    
    officer_name = user.get('full_name', '')
    
    with st.sidebar:
        st.markdown(f"### 👤 مرحباً: {user['full_name']}")
        st.markdown(f"**الدور:** {user_role}")
        if branches_list:
            st.markdown(f"**الفروع المسموح بها:** {', '.join(branches_list)}")
        if st.button("🚪 خروج", use_container_width=True):
            del st.session_state['user']
            st.query_params.clear()
            st.rerun()
        st.divider()
        st.markdown("### 🔍 أدوات البحث")
    
    df_raw = fetch_outstanding_data()
    
    if df_raw.empty:
        st.info("📭 لا توجد بيانات متاحة حالياً")
        return
    
    # تحديد اسم عمود الفرع الصحيح
    branch_column = None
    possible_branch_names = ['branch_name', 'Branch_name', 'اسم الفرع', 'branch', 'Branch']
    for col in possible_branch_names:
        if col in df_raw.columns:
            branch_column = col
            break
    
    # تحديد اسم عمود المسؤول الصحيح
    officer_column = None
    possible_officer_names = ['officer_name', 'Officer_name', 'اسم المسؤول', 'officer', 'Officer']
    for col in possible_officer_names:
        if col in df_raw.columns:
            officer_column = col
            break
    
    # تحديد أعمدة المبالغ
    inst_col = None
    for col in ['inst_amount', 'قيمة القسط', 'amount', 'inst_amt']:
        if col in df_raw.columns:
            inst_col = col
            break
    
    fawry_col = None
    for col in ['fawry_amount', 'amount', 'fawry_amt', 'Amount']:
        if col in df_raw.columns:
            fawry_col = col
            break
    
    opay_col = None
    for col in ['opay_amount', 'opay_amt', 'opayAmount']:
        if col in df_raw.columns:
            opay_col = col
            break
    
    if branch_column is None:
        st.error("❌ لم يتم العثور على عمود الفرع في البيانات")
        return
    
    # ========== الفلترة حسب الصلاحيات ==========
    
    # الفلترة الأساسية: حسب الفروع المسموح بها للمستخدم العادي
    if not is_admin and branches_list:
        df_acc = df_raw[df_raw[branch_column].astype(str).isin(branches_list)].copy()
        st.info(f"📌 يتم عرض الفروع: {', '.join(branches_list)}")
    else:
        df_acc = df_raw.copy()
    
    # ========== الفلاتر الإضافية في الشريط الجانبي ==========
    st.sidebar.markdown("### 🎯 فلاتر إضافية")
    
    # فلتر اسم الاخصائي (للكل، ولكن الخيارات تأتي من النتائج الحالية)
    if officer_column and officer_column in df_acc.columns:
        # جلب قائمة الاخصائيين من النتائج الحالية (بعد فلترة الفروع)
        officers_list = sorted(df_acc[officer_column].dropna().unique().tolist())
        if officers_list:
            selected_officer = st.sidebar.selectbox("👤 فلترة حسب الاخصائي", ["الكل"] + officers_list)
            if selected_officer != "الكل":
                df_acc = df_acc[df_acc[officer_column] == selected_officer]
    
    # فلتر اسم العميل
    search_name = st.sidebar.text_input("🔎 بحث باسم العميل")
    
    # فلتر الرقم القومي
    search_nation = st.sidebar.text_input("🆔 بحث بالرقم القومي")
    
    # البحث في أعمدة العميل
    client_col = None
    for col in ['client_name', 'اسم العميل', 'client', 'name']:
        if col in df_acc.columns:
            client_col = col
            break
    
    nation_col = None
    for col in ['nation_id', 'الرقم القومي', 'nation', 'national_id']:
        if col in df_acc.columns:
            nation_col = col
            break
    
    if search_name and client_col:
        df_acc = df_acc[df_acc[client_col].astype(str).str.contains(search_name, na=False, case=False)]
    if search_nation and nation_col:
        df_acc = df_acc[df_acc[nation_col].astype(str).str.contains(search_nation, na=False, case=False)]
    
    # ========== فلترة إضافية للمدير فقط ==========
    if is_admin:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔧 فلترة المدير")
        
        # فلتر الفرع (للمدير)
        branches_in_data = sorted(df_acc[branch_column].dropna().unique().tolist())
        if branches_in_data:
            selected_branch = st.sidebar.selectbox("🏢 فلترة حسب الفرع", ["الكل"] + branches_in_data)
            if selected_branch != "الكل":
                df_acc = df_acc[df_acc[branch_column] == selected_branch]
    
    if df_acc.empty:
        st.warning("⚠️ لا توجد بيانات تطابق معايير البحث")
        with st.expander("🔍 بيانات للمساعدة في التشخيص"):
            st.write("عدد الصفوف في البيانات الأصلية:", len(df_raw))
            st.write("قيم عمود الفرع الفريدة:", df_raw[branch_column].unique().tolist())
            if branches_list:
                st.write(f"الفروع المسموح بها للمستخدم: {branches_list}")
            if officer_column:
                st.write(f"قيم عمود الاخصائي الفريدة:", df_raw[officer_column].dropna().unique().tolist()[:10])
        return
    
    # تحويل المبالغ إلى numeric
    if inst_col:
        df_acc[inst_col] = pd.to_numeric(df_acc[inst_col], errors='coerce').fillna(0)
    if fawry_col:
        df_acc[fawry_col] = pd.to_numeric(df_acc[fawry_col], errors='coerce').fillna(0)
    if opay_col:
        df_acc[opay_col] = pd.to_numeric(df_acc[opay_col], errors='coerce').fillna(0)
    
    # حساب الإحصائيات
    total_inst_amount = df_acc[inst_col].sum() if inst_col else 0
    total_fawry_amount = df_acc[fawry_col].sum() if fawry_col else 0
    total_opay_amount = df_acc[opay_col].sum() if opay_col else 0
    total_paid = total_fawry_amount + total_opay_amount
    total_remaining = total_inst_amount - total_paid
    
    # عرض الإحصائيات
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">💰 إجمالي المستحق</div>
                    <div class="metric-value">{total_inst_amount:,.2f} ج.م</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">💳 إجمالي المدفوع</div>
                    <div class="metric-value">{total_paid:,.2f} ج.م</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">📊 إجمالي المتبقي</div>
                    <div class="metric-value">{total_remaining:,.2f} ج.م</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">📋 عدد الأقساط</div>
                    <div class="metric-value">{len(df_acc):,} قسط</div></div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # عرض الجدول بالألوان
    st.markdown("### 📋 جدول الأقساط المستحقة")
    
    # إضافة عمود حالة الدفع
    def get_payment_status(row):
        fawry_amt = row.get(fawry_col, 0) if fawry_col else 0
        opay_amt = row.get(opay_col, 0) if opay_col else 0
        total_paid_row = (fawry_amt if pd.notna(fawry_amt) else 0) + (opay_amt if pd.notna(opay_amt) else 0)
        inst_amt = row.get(inst_col, 0) if inst_col and pd.notna(row.get(inst_col)) else 0
        
        if total_paid_row >= inst_amt and inst_amt > 0:
            return "✅ مدفوع بالكامل"
        elif total_paid_row > 0:
            return "⚠️ مسدد جزئي"
        else:
            return "❌ غير مدفوع"
    
    df_acc['حالة الدفع'] = df_acc.apply(get_payment_status, axis=1)
    
    # تحديد أعمدة العرض
    display_cols = []
    display_names = []
    
    # الأعمدة الأساسية
    col_mapping = [
        ('حالة الدفع', '📊 حالة الدفع'),
        (branch_column, '🏢 اسم الفرع'),
        (client_col, '👤 اسم العميل'),
        (nation_col, '🆔 الرقم القومي'),
        ('inst_mat_date', '📅 تاريخ الاستحقاق'),
        (inst_col, '💰 قيمة القسط'),
        (fawry_col, '💳 مبلغ فوري'),
        (opay_col, '📱 مبلغ Opay'),
        (officer_column, '👨‍💼 المسؤول'),
        ('loan_number', '🔢 رقم القرض'),
        ('inst_status', '📌 حالة القسط'),
    ]
    
    for col, name in col_mapping:
        if col and col in df_acc.columns:
            display_cols.append(col)
            display_names.append(name)
    
    if display_cols:
        df_display = df_acc[display_cols].copy()
        df_display.columns = display_names
        
        # تنسيق التاريخ
        if '📅 تاريخ الاستحقاق' in df_display.columns:
            df_display['📅 تاريخ الاستحقاق'] = pd.to_datetime(df_display['📅 تاريخ الاستحقاق'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # تنسيق الأرقام
        for col in ['💰 قيمة القسط', '💳 مبلغ فوري', '📱 مبلغ Opay']:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) and x > 0 else "0.00")
        
        # دالة لتلوين الصفوف حسب حالة الدفع
        def color_rows(row):
            status = row['📊 حالة الدفع']
            if 'مسدد جزئي' in status:
                return ['background-color: #FFCCCC; color: #9C0006; font-weight: bold'] * len(row)
            elif 'غير مدفوع' in status:
                return ['background-color: #FFE699; color: #7F4A00; font-weight: bold'] * len(row)
            else:
                return ['background-color: #E2EFDA; color: #375623'] * len(row)
        
        styled_df = df_display.style.apply(color_rows, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=500)
    
    # ملخص حسب حالة الدفع (بشكل جميل)
    if inst_col:
        st.markdown("### 📊 ملخص حسب حالة الدفع")
        
        summary_df = df_acc.groupby('حالة الدفع').agg({
            inst_col: 'sum',
        }).reset_index()
        
        # إضافة أعمدة إضافية
        summary_df['عدد الأقساط'] = df_acc.groupby('حالة الدفع').size().values
        if fawry_col:
            summary_df['إجمالي فوري'] = df_acc.groupby('حالة الدفع')[fawry_col].sum().values
        else:
            summary_df['إجمالي فوري'] = 0
        if opay_col:
            summary_df['إجمالي Opay'] = df_acc.groupby('حالة الدفع')[opay_col].sum().values
        else:
            summary_df['إجمالي Opay'] = 0
        
        summary_df['إجمالي المدفوع'] = summary_df['إجمالي فوري'] + summary_df['إجمالي Opay']
        summary_df['المتبقي'] = summary_df[inst_col] - summary_df['إجمالي المدفوع']
        summary_df.columns = ['حالة الدفع', 'إجمالي المستحق', 'عدد الأقساط', 'إجمالي فوري', 'إجمالي Opay', 'إجمالي المدفوع', 'المتبقي']
        
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # ملخص حسب المسؤول (يظهر للجميع)
    if officer_column and officer_column in df_acc.columns and len(df_acc[officer_column].unique()) > 1:
        st.markdown("### 👥 ملخص حسب المسؤول")
        officer_summary = df_acc.groupby(officer_column).agg({
            inst_col: 'sum' if inst_col else 'count',
            client_col: 'count' if client_col else 'count'
        }).reset_index()
        
        # حساب نسبة التحصيل
        officer_summary['عدد الأقساط'] = officer_summary[client_col] if client_col else officer_summary[inst_col]
        officer_summary['متوسط القسط'] = officer_summary[inst_col] / officer_summary['عدد الأقساط']
        officer_summary.columns = ['اسم المسؤول', 'إجمالي المستحق', 'عدد الأقساط', 'متوسط القسط']
        officer_summary['متوسط القسط'] = officer_summary['متوسط القسط'].apply(lambda x: f"{x:,.2f}")
        
        st.dataframe(officer_summary, use_container_width=True, hide_index=True)
    
    # تحميل Excel
    st.sidebar.divider()
    st.sidebar.markdown("### 📥 تحميل التقرير")
    
    excel_bytes = generate_outstanding_excel(df_acc)
    st.sidebar.download_button(
        label="📊 تحميل Excel ملون",
        data=excel_bytes,
        file_name=f"الاقساط_المستحقة_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

def under_construction_page(service_name, service_icon="🔒"):
    """صفحة تحت الإنشاء"""
    if 'user' not in st.session_state:
        st.warning("⚠️ يجب تسجيل الدخول أولاً")
        st.stop()
    
    st.markdown('<div style="margin-top: 70px;"></div>', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="main-title">
            <h1>{service_icon} {service_name}</h1>
            <p>هذه الخدمة قيد التطوير حالياً</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🏠 العودة للرئيسية", use_container_width=False):
        st.query_params.clear()
        st.rerun()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/7439/7439576.png", width=150)
        st.markdown("""
            <div style="text-align: center; padding: 40px; background: #fef3c7; border-radius: 20px; margin-top: 20px;">
                <h2 style="color: #d97706;">🚧 قيد التطوير</h2>
                <p style="font-size: 18px; color: #78350f;">هذه الخدمة تحت الإنشاء حالياً</p>
                <p style="margin-top: 20px; color: #92400e;">سيتم إطلاقها قريباً إن شاء الله</p>
            </div>
        """, unsafe_allow_html=True)

# ===================== CSS التنسيقات =====================

st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    .main-title {
        text-align: center;
        color: #1e3a8a;
        background: linear-gradient(135deg, #eff6ff 0%, #bfdbfe 100%);
        padding: 25px;
        border-radius: 20px;
        margin-bottom: 30px;
        margin-top: 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-title h1 { margin: 0; font-size: 28px; }
    .main-title p { margin: 10px 0 0; color: #3b82f6; font-size: 15px; }
    .metric-card {
        background-color: #ffffff;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-top: 4px solid #1e3a8a;
        text-align: center;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: #1e3a8a; }
    .metric-label { font-size: 13px; color: #6b7280; margin-bottom: 5px; }
    .service-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        border-radius: 12px;
        padding: 15px 10px;
        text-align: center;
        transition: all 0.3s ease;
        margin: 8px 0;
        color: white;
    }
    .service-card:hover { transform: translateY(-3px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .service-icon { font-size: 28px; margin-bottom: 8px; }
    .service-title { font-size: 16px; font-weight: bold; margin-bottom: 6px; }
    .service-badge { font-size: 11px; background: rgba(255,255,255,0.2); display: inline-block; padding: 2px 10px; border-radius: 15px; }
    .inactive-card { background: linear-gradient(135deg, #6b7280 0%, #9ca3af 100%); opacity: 0.8; }
    .stDataFrame { border: 1px solid #e5e7eb; border-radius: 10px; }
    input { text-align: right; direction: rtl; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

# ===================== الصفحة الرئيسية =====================

def main_app():
    """الصفحة الرئيسية"""
    
    if 'user' not in st.session_state:
        st.markdown('<div style="margin-top: 70px;"></div>', unsafe_allow_html=True)
        st.markdown("""
            <div class="main-title">
                <h1>🔐 نظام كاريتاس المتكامل</h1>
                <p>الرجاء تسجيل الدخول للوصول إلى الخدمات</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.form("login_form"):
                st.markdown("### 👤 بيانات الدخول")
                username = st.text_input("اسم المستخدم")
                password = st.text_input("كلمة المرور", type="password")
                if st.form_submit_button("🚪 دخول", use_container_width=True):
                    user = check_login(username, password)
                    if user:
                        st.session_state['user'] = user
                        st.rerun()
                    else:
                        st.error("❌ خطأ في اسم المستخدم أو كلمة المرور")
        return
    
    show_logo()
    
    user = st.session_state['user']
    
    st.markdown(f"""
        <div style="margin-top: 70px;">
            <div class="main-title">
                <h1>🏠 مرحباً بك {user['full_name']}</h1>
                <p>اختر الخدمة التي ترغب في استخدامها</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚪 خروج", use_container_width=True):
            del st.session_state['user']
            st.rerun()
    
    st.markdown("---")
    
    # الخدمات النشطة
    if PROGRAMS["active"]:
        st.markdown("### ✅ الخدمات المتاحة")
        for program_id, program in PROGRAMS["active"].items():
            cols = st.columns([1, 3])
            with cols[0]:
                st.markdown(f"""
                    <div class="service-card">
                        <div class="service-icon">{program['icon']}</div>
                        <div class="service-title">{program['name']}</div>
                        <div class="service-badge">✅ متاح</div>
                    </div>
                """, unsafe_allow_html=True)
            with cols[1]:
                if st.button(f"فتح {program['name']}", key=f"active_{program_id}", use_container_width=True):
                    st.query_params["page"] = program_id
                    st.rerun()
    
    # خدمات تحت الإنشاء
    if PROGRAMS["inactive"]:
        st.markdown("### 🚧 خدمات تحت الإنشاء")
        inactive_items = list(PROGRAMS["inactive"].items())
        for i in range(0, len(inactive_items), 4):
            cols = st.columns(4)
            for j, (program_id, program) in enumerate(inactive_items[i:i+4]):
                with cols[j]:
                    st.markdown(f"""
                        <div class="service-card inactive-card">
                            <div class="service-icon">{program['icon']}</div>
                            <div class="service-title">{program['name']}</div>
                            <div class="service-badge">🚧 تحت الإنشاء</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"فتح", key=f"inactive_{program_id}", use_container_width=True):
                        st.query_params["page"] = program_id
                        st.rerun()

# ===================== تشغيل التطبيق =====================

show_logo()

query_params = st.query_params
page = query_params.get("page", "home")

if page != "home" and 'user' not in st.session_state:
    st.markdown("<div style='margin-top: 70px;'></div>", unsafe_allow_html=True)
    st.warning("⚠️ يجب تسجيل الدخول أولاً للوصول إلى هذه الصفحة")
    st.markdown("[🔐 الذهاب إلى صفحة تسجيل الدخول](/)")
    st.stop()

if page == "home":
    main_app()
elif page == "reports":
    reports_page()
elif page == "installments":
    outstanding_page()
elif page in PROGRAMS["inactive"]:
    program = PROGRAMS["inactive"][page]
    under_construction_page(program['name'], program['icon'])
else:
    if 'user' in st.session_state:
        under_construction_page("الخدمة المطلوبة")
    else:
        main_app()