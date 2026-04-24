import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import io
import os
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ===================== إعدادات الصفحة الأساسية =====================
st.set_page_config(page_title="نظام كاريتاس", layout="wide", page_icon="📊", initial_sidebar_state="auto")

# ===================== الثوابت والتكوين =====================

# محاولة إيجاد اللوجو بطرق مختلفة
def get_logo_path():
    """البحث عن ملف اللوجو في مسارات مختلفة"""
    possible_paths = [
        "logo.png",
        "images/logo.png",
        "static/logo.png",
        "assets/logo.png",
        Path(__file__).parent / "logo.png",
        Path(__file__).parent / "images" / "logo.png",
    ]
    
    for path in possible_paths:
        if os.path.exists(str(path)):
            return str(path)
    return None

LOGO_PATH = get_logo_path()

# تعريف جميع البرامج
PROGRAMS = {
    "active": {
        "reports": {
            "name": "سداد فوري & Opay",
            "icon": "💳📱",
            "page_title": "تقرير السدادات",
            "description": "عرض وتحليل بيانات السدادات - تقارير دقيقة ومتنوعة",
            "function": "reports_page"
        },
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

# ===================== دالة عرض اللوجو المحسنة (تظهر في كل الصفحات) =====================

def show_logo():
    """عرض اللوجو بشكل ثابت في أعلى يسار جميع الصفحات"""
    
    # استخدام base64 لعرض الصورة بشكل أفضل
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        import base64
        with open(LOGO_PATH, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        
        st.markdown(f"""
            <div style="position: fixed; top: 15px; left: 15px; z-index: 9999; background: rgba(255,255,255,0.95); 
                        padding: 5px 10px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <img src="data:image/png;base64,{img_data}" style="height: 60px; width: auto; border-radius: 8px;" alt="Caritas Logo">
            </div>
        """, unsafe_allow_html=True)
    else:
        # نص بديل إذا لم يوجد اللوجو
        st.markdown("""
            <div style="position: fixed; top: 15px; left: 15px; z-index: 9999; background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); 
                        padding: 8px 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                <div style="color: white; font-weight: bold; font-size: 18px;">📊 كاريتاس</div>
            </div>
        """, unsafe_allow_html=True)

# ===================== دالة عرض الهيدر الموحد =====================

def show_unified_header(page_title, description, show_back_button=True):
    """عرض هيدر موحد لجميع الصفحات"""
    
    # اللوجو يظهر تلقائياً من الدالة المنفصلة
    st.markdown(f"""
        <div style="margin-top: 70px;">
            <div class="main-title">
                <h1>{page_title}</h1>
                <p>{description}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if show_back_button and st.session_state.get('user'):
        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
            if st.button("🏠 العودة للرئيسية", use_container_width=True):
                st.query_params.clear()
                st.rerun()
        st.divider()

# ===================== الاتصال بـ Supabase =====================

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# ===================== الوظائف المشتركة =====================

def fetch_all_data_paginated():
    """جلب جميع البيانات من Supabase"""
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

def check_login(u, p):
    """التحقق من بيانات الدخول"""
    res = supabase.table("app_users").select("*").eq("id", u).eq("password_hash", p).execute()
    return res.data[0] if res.data else None

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

def generate_excel_single(df_display, sheet_title="التقرير", report_title="تقرير السدادات"):
    """توليد ملف Excel لشيت واحد"""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]
    ws.sheet_view.rightToLeft = True

    DARK_BLUE  = "1E3A8A"
    LIGHT_BLUE = "EFF6FF"
    ALT_ROW    = "F0F4FF"
    WHITE      = "FFFFFF"

    cols = list(df_display.columns)
    n_cols = len(cols)
    last_col = get_column_letter(n_cols)

    ws.merge_cells(f'A1:{last_col}1')
    ws['A1'].value = report_title
    ws['A1'].font = Font(bold=True, size=14, color=DARK_BLUE, name="Arial")
    ws['A1'].fill = PatternFill("solid", fgColor=LIGHT_BLUE)
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 32

    for ci, header in enumerate(cols, 1):
        c = ws.cell(row=2, column=ci, value=header)
        c.font = Font(bold=True, color=WHITE, name="Arial", size=11)
        c.fill = PatternFill("solid", fgColor=DARK_BLUE)
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = thin_border()
    ws.row_dimensions[2].height = 24

    for ri, row in enumerate(df_display.itertuples(index=False), 3):
        bg = ALT_ROW if ri % 2 == 0 else WHITE
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

def generate_excel_daily(df_display, original_df):
    """توليد ملف Excel مقسم حسب الأيام"""
    wb = Workbook()
    wb.remove(wb.active)

    DARK_BLUE  = "1E3A8A"
    LIGHT_BLUE = "EFF6FF"
    ALT_ROW    = "F0F4FF"
    TOTAL_BG   = "BFDBFE"
    WHITE      = "FFFFFF"

    def style_sheet(ws, df_part, title_text):
        ws.sheet_view.rightToLeft = True
        cols = list(df_part.columns)
        n_cols = len(cols)
        last_col = get_column_letter(n_cols)

        ws.merge_cells(f'A1:{last_col}1')
        ws['A1'].value = title_text
        ws['A1'].font = Font(bold=True, size=13, color=DARK_BLUE, name="Arial")
        ws['A1'].fill = PatternFill("solid", fgColor=LIGHT_BLUE)
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 30

        for ci, h in enumerate(cols, 1):
            c = ws.cell(row=2, column=ci, value=h)
            c.font = Font(bold=True, color=WHITE, name="Arial", size=10)
            c.fill = PatternFill("solid", fgColor=DARK_BLUE)
            c.alignment = Alignment(horizontal='center', vertical='center')
            c.border = thin_border()
        ws.row_dimensions[2].height = 22

        for ri, row in enumerate(df_part.itertuples(index=False), 3):
            bg = ALT_ROW if ri % 2 == 0 else WHITE
            for ci, val in enumerate(row, 1):
                c = ws.cell(row=ri, column=ci, value=val)
                c.fill = PatternFill("solid", fgColor=bg)
                c.alignment = Alignment(horizontal='center', vertical='center')
                c.font = Font(name="Arial", size=10)
                c.border = thin_border()
        last_data_row = 2 + len(df_part)

        write_total_row(ws, last_data_row + 1, cols, last_data_row)

        ws.freeze_panes = "A3"
        col_widths = {"اسم العميل": 28, "الفرع": 20}
        for ci, col in enumerate(cols, 1):
            ws.column_dimensions[get_column_letter(ci)].width = col_widths.get(col, 17)

    ws_sum = wb.create_sheet("ملخص يومي")
    ws_sum.sheet_view.rightToLeft = True
    summary_cols = ["التاريخ", "عدد العمليات", "إجمالي المبلغ (ج.م)"]
    n_sc = len(summary_cols)

    ws_sum.merge_cells(f'A1:{get_column_letter(n_sc)}1')
    ws_sum['A1'].value = "ملخص يومي - تقرير السدادات"
    ws_sum['A1'].font = Font(bold=True, size=14, color=DARK_BLUE, name="Arial")
    ws_sum['A1'].fill = PatternFill("solid", fgColor=LIGHT_BLUE)
    ws_sum['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws_sum.row_dimensions[1].height = 32

    for ci, h in enumerate(summary_cols, 1):
        c = ws_sum.cell(row=2, column=ci, value=h)
        c.font = Font(bold=True, color=WHITE, name="Arial")
        c.fill = PatternFill("solid", fgColor=DARK_BLUE)
        c.alignment = Alignment(horizontal='center', vertical='center')
        c.border = thin_border()
    ws_sum.row_dimensions[2].height = 22

    temp = original_df.copy()
    temp['_date'] = temp['تاريخ الدفع'].dt.date
    dates_sorted = sorted(temp['_date'].dropna().unique())

    for ri, d in enumerate(dates_sorted, 3):
        day_df = temp[temp['_date'] == d]
        bg = ALT_ROW if ri % 2 == 0 else WHITE
        for ci in range(1, n_sc + 1):
            c = ws_sum.cell(row=ri, column=ci)
            c.fill = PatternFill("solid", fgColor=bg)
            c.alignment = Alignment(horizontal='center', vertical='center')
            c.font = Font(name="Arial", size=10)
            c.border = thin_border()
        ws_sum.cell(row=ri, column=1).value = str(d)
        ws_sum.cell(row=ri, column=2).value = len(day_df)
        ws_sum.cell(row=ri, column=3).value = float(day_df['المبلغ'].sum())
        ws_sum.cell(row=ri, column=3).number_format = '#,##0.00'

    total_row_sum = 2 + len(dates_sorted) + 1
    for ci in range(1, n_sc + 1):
        c = ws_sum.cell(row=total_row_sum, column=ci)
        c.fill = PatternFill("solid", fgColor=TOTAL_BG)
        c.border = thin_border()
        c.alignment = Alignment(horizontal='center', vertical='center')
        c.font = Font(bold=True, color=DARK_BLUE, name="Arial")

    ws_sum.cell(row=total_row_sum, column=1).value = "✦ الإجمالي الكلي"
    ws_sum.cell(row=total_row_sum, column=3).value = f"=SUM(C3:C{total_row_sum - 1})"
    ws_sum.cell(row=total_row_sum, column=3).number_format = '#,##0.00'
    ws_sum.row_dimensions[total_row_sum].height = 26

    for ci, w in enumerate([18, 18, 25], 1):
        ws_sum.column_dimensions[get_column_letter(ci)].width = w
    ws_sum.freeze_panes = "A3"

    for d in dates_sorted:
        day_df_orig = temp[temp['_date'] == d].copy()
        day_display = day_df_orig.rename(columns={
            'client_code': 'كود العميل',
            'client_name': 'اسم العميل',
            'branch_name': 'الفرع'
        })
        if 'تاريخ الدفع' in day_display.columns:
            day_display['تاريخ الدفع'] = day_display['تاريخ الدفع'].dt.strftime('%Y-%m-%d')
        drop_cols = [c for c in day_display.columns if c.startswith('_') or c == 'id']
        day_display = day_display.drop(columns=drop_cols, errors='ignore')

        ws_day = wb.create_sheet(str(d)[:31])
        style_sheet(ws_day, day_display, f"تقرير سدادات يوم {d}")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

# ===================== صفحات البرامج =====================

def reports_page():
    """صفحة تقارير السدادات"""
    if 'user' not in st.session_state:
        st.warning("⚠️ يجب تسجيل الدخول أولاً")
        st.stop()
    
    show_unified_header(
        page_title="📑 سداد فوري & Opay",
        description="عرض وتحليل بيانات السدادات - تقارير دقيقة ومتنوعة",
        show_back_button=True
    )
    
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
    
    df_raw = fetch_all_data_paginated()
    
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
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">💰 إجمالي المبالغ</div>
            <div class="metric-value">{final_df['المبلغ'].sum():,.2f} ج.م</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">📊 عدد العمليات</div>
            <div class="metric-value">{len(final_df):,} حركة</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        counts = final_df['كود الخدمة'].value_counts()
        codes_html = "".join([f"<div style='font-size:13px'>• {k}: {v}</div>" for k, v in counts.items()])
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">📋 تفاصيل الأكواد</div>
            <div style="font-weight:bold; color:#1e3a8a; text-align:right;">{codes_html}</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("📅 عرض الملخص اليومي", expanded=False):
        daily_summary = (
            final_df.groupby(final_df['تاريخ الدفع'].dt.date)
            .agg(عدد_العمليات=('المبلغ', 'count'), إجمالي_المبلغ=('المبلغ', 'sum'))
            .reset_index()
        )
        daily_summary.columns = ['التاريخ', 'عدد العمليات', 'إجمالي المبلغ (ج.م)']
        st.dataframe(daily_summary, use_container_width=True, hide_index=True)
    
    display_df = final_df.copy().rename(columns={
        'client_code': 'كود العميل',
        'client_name': 'اسم العميل',
        'branch_name': 'الفرع'
    })
    drop_cols = [c for c in display_df.columns if c.startswith('_') or c == 'id']
    display_df = display_df.drop(columns=drop_cols, errors='ignore')
    if 'تاريخ الدفع' in display_df.columns:
        display_df['تاريخ الدفع'] = display_df['تاريخ الدفع'].dt.strftime('%Y-%m-%d')
    
    st.markdown("### 📋 جدول البيانات المفصل")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    split_mode = st.sidebar.radio(
        "نوع التنزيل",
        ["📄 كل البيانات في شيت واحد", "📆 تقسيم يوم يوم (شيت لكل يوم)"],
        index=0
    )
    
    if split_mode == "📆 تقسيم يوم يوم (شيت لكل يوم)":
        available_dates = sorted(final_df['تاريخ الدفع'].dropna().dt.date.unique())
        date_options = ["كل الأيام"] + [str(d) for d in available_dates]
        selected_day = st.sidebar.selectbox("اختر اليوم للتنزيل", date_options)
        
        if selected_day == "كل الأيام":
            excel_bytes = generate_excel_daily(display_df, final_df)
            file_label = f"تقرير_كل_الأيام_{datetime.now().date()}.xlsx"
        else:
            sel_date = pd.to_datetime(selected_day).date()
            day_display = display_df[
                pd.to_datetime(display_df['تاريخ الدفع'], errors='coerce').dt.date == sel_date
            ]
            excel_bytes = generate_excel_single(
                day_display,
                sheet_title=selected_day,
                report_title=f"تقرير سدادات يوم {selected_day}"
            )
            file_label = f"تقرير_{selected_day}.xlsx"
    else:
        excel_bytes = generate_excel_single(
            display_df,
            report_title=f"تقرير السدادات - {start_d} إلى {end_d}"
        )
        file_label = f"تقرير_{datetime.now().date()}.xlsx"
    
    st.sidebar.download_button(
        label="📊 تحميل Excel ملون",
        data=excel_bytes,
        file_name=file_label,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

def under_construction_page(service_icon="🔒"):
    """صفحة تحت الإنشاء"""
    if 'user' not in st.session_state:
        st.warning("⚠️ يجب تسجيل الدخول أولاً")
        st.stop()
    
    show_unified_header(
        page_title=f"{service_icon} تحت الإنشاء",
        description="هذه الخدمة قيد التطوير حالياً",
        show_back_button=True
    )
    
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
    /* الاتجاه العام */
    .main { direction: rtl; text-align: right; }
    
    /* العناوين الرئيسية */
    .main-title {
        text-align: center;
        color: #1e3a8a;
        background: linear-gradient(135deg, #eff6ff 0%, #bfdbfe 100%);
        padding: 25px;
        border-radius: 20px;
        border: none;
        margin-bottom: 30px;
        margin-top: 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-title h1 {
        margin: 0;
        font-size: 28px;
    }
    .main-title p {
        margin: 10px 0 0;
        color: #3b82f6;
        font-size: 15px;
    }
    
    /* بطاقات المقاييس */
    .metric-card {
        background-color: #ffffff;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        border-top: 4px solid #1e3a8a;
        text-align: center;
    }
    .metric-value { font-size: 26px; font-weight: bold; color: #1e3a8a; }
    .metric-label { font-size: 14px; color: #6b7280; margin-bottom: 5px; }
    
    /* أزرار الخدمات */
    .service-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        border-radius: 12px;
        padding: 18px 10px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 8px 0;
        color: white;
    }
    .service-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .service-icon {
        font-size: 32px;
        margin-bottom: 10px;
    }
    .service-title {
        font-size: 17px;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .service-badge {
        font-size: 12px;
        background: rgba(255,255,255,0.2);
        display: inline-block;
        padding: 3px 12px;
        border-radius: 15px;
    }
    .inactive-card {
        background: linear-gradient(135deg, #6b7280 0%, #9ca3af 100%);
        opacity: 0.8;
    }
    
    .stDataFrame { border: 1px solid #e5e7eb; border-radius: 10px; }
    input { text-align: right; direction: rtl; }
    
    /* إخفاء العناصر الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# ===================== الصفحة الرئيسية =====================

def main_app():
    """الصفحة الرئيسية - تسجيل الدخول"""
    
    if 'user' not in st.session_state:
        st.markdown("""
            <div style="margin-top: 70px;">
                <div class="main-title">
                    <h1>🔐 نظام كاريتاس المتكامل</h1>
                    <p>الرجاء تسجيل الدخول للوصول إلى الخدمات</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.form("login_form"):
                st.markdown("### 👤 بيانات الدخول")
                username = st.text_input("اسم المستخدم", placeholder="أدخل اسم المستخدم")
                password = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
                
                if st.form_submit_button("🚪 دخول", use_container_width=True):
                    user = check_login(username, password)
                    if user:
                        st.session_state['user'] = user
                        st.rerun()
                    else:
                        st.error("❌ خطأ في اسم المستخدم أو كلمة المرور")
        return
    
    # بعد تسجيل الدخول
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
    
    # عرض البرامج النشطة
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
    
    # عرض البرامج تحت الإنشاء
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

# ←最重要: عرض اللوجو في بداية كل صفحة (قبل أي شيء)
show_logo()

# الحصول على معامل الصفحة
query_params = st.query_params
page = query_params.get("page", "home")

# حماية الصفحات
if page != "home" and 'user' not in st.session_state:
    st.markdown("<div style='margin-top: 70px;'></div>", unsafe_allow_html=True)
    st.warning("⚠️ يجب تسجيل الدخول أولاً للوصول إلى هذه الصفحة")
    st.markdown("[🔐 الذهاب إلى صفحة تسجيل الدخول](/)")
    st.stop()

# توجيه الصفحات
if page == "home":
    main_app()
elif page in PROGRAMS["active"]:
    if page == "reports":
        reports_page()
else:
    if page in PROGRAMS["inactive"]:
        program = PROGRAMS["inactive"][page]
        under_construction_page(program['icon'])
    else:
        if 'user' in st.session_state:
            under_construction_page()
        else:
            main_app()