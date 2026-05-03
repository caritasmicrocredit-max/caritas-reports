import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import io
import os
import base64
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ===================== إعدادات الصفحة =====================
st.set_page_config(
    page_title="نظام كاريتاس",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="collapsed"
)

# ===================== إخفاء الـ Sidebar نهائياً =====================
st.markdown("""
<style>
[data-testid="collapsedControl"]    { display: none !important; }
[data-testid="stSidebar"]           { display: none !important; }
section[data-testid="stSidebarNav"] { display: none !important; }
#MainMenu        { visibility: hidden; }
footer           { visibility: hidden; }
header           { visibility: hidden; }
.stDeployButton  { display: none; }

html, body, .main, .block-container { direction: rtl; }

/* ======= هيدر ======= */
.sys-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 60%, #2563eb 100%);
    padding: 14px 28px;
    border-radius: 18px;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px rgba(30,58,138,0.25);
}
.sys-header-logo { display:flex; align-items:center; gap:14px; }
.sys-header-logo img { height:52px; border-radius:10px; }
.sys-header-title { color:#fff; font-size:22px; font-weight:800; letter-spacing:-0.5px; }
.sys-header-sub   { color:#93c5fd; font-size:12px; margin-top:2px; }
.sys-header-user  { text-align:left; color:#bfdbfe; font-size:13px; line-height:1.7; }

/* ======= كروت البرامج ======= */
.prog-card {
    background:#fff;
    border-radius:20px;
    padding:30px 26px;
    box-shadow:0 4px 24px rgba(30,58,138,0.10);
    border:2px solid #e0e7ff;
    position:relative;
    overflow:hidden;
}
.prog-card::before {
    content:'';
    position:absolute;
    top:0; right:0;
    width:6px; height:100%;
    background:linear-gradient(180deg,#2563eb,#06b6d4);
    border-radius:0 18px 18px 0;
}
.prog-card-icon { font-size:44px; margin-bottom:14px; display:block; }
.prog-card-name { font-size:20px; font-weight:800; color:#1e3a8a; margin-bottom:8px; }
.prog-card-desc { font-size:13px; color:#64748b; line-height:1.6; margin-bottom:18px; }
.prog-card-badge {
    display:inline-block;
    background:linear-gradient(90deg,#2563eb,#06b6d4);
    color:#fff; font-size:11px; font-weight:700;
    padding:4px 14px; border-radius:20px;
}

/* ======= KPIs ======= */
.kpi-card {
    background:#fff;
    border-radius:14px;
    padding:18px 20px;
    box-shadow:0 2px 12px rgba(30,58,138,0.09);
    border-top:4px solid #2563eb;
    text-align:center;
    margin-bottom:16px;
}
.kpi-val { font-size:22px; font-weight:800; color:#1e3a8a; }
.kpi-lbl { font-size:12px; color:#64748b; margin-top:4px; }

/* ======= فلاتر ======= */
.filter-bar {
    background:#f1f5f9;
    border-radius:14px;
    padding:18px 20px;
    margin-bottom:20px;
    border:1px solid #e2e8f0;
}
.filter-bar-title { font-size:14px; font-weight:700; color:#1e3a8a; margin-bottom:12px; }

/* ======= عنوان قسم ======= */
.sec-title {
    font-size:17px; font-weight:800; color:#1e3a8a;
    border-right:4px solid #2563eb;
    padding-right:12px;
    margin:22px 0 12px;
}

/* ======= أزرار ======= */
.stButton > button {
    background:linear-gradient(90deg,#1e3a8a,#2563eb) !important;
    color:white !important;
    border:none !important;
    border-radius:10px !important;
    font-weight:700 !important;
}
.stButton > button:hover { opacity:0.88 !important; }
[data-testid="stDownloadButton"] > button {
    background:linear-gradient(90deg,#059669,#10b981) !important;
    color:white !important;
    border:none !important;
    border-radius:10px !important;
    font-weight:700 !important;
}
.stDataFrame { border:1px solid #e2e8f0; border-radius:12px; }

/* ======= موبايل ======= */
@media (max-width:640px) {
    .sys-header { flex-direction:column; gap:10px; text-align:center; padding:14px 16px; }
    .sys-header-user { text-align:center; }
}
</style>
""", unsafe_allow_html=True)

# ===================== Supabase =====================
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

PROGRAMS = {
    "reports": {
        "name": "سداد فوري & Opay",
        "icon": "💳",
        "desc": "عرض وتحليل بيانات السدادات — تقارير دقيقة ومتنوعة",
    },
    "installments": {
        "name": "الأقساط المستحقة",
        "icon": "📋",
        "desc": "متابعة الأقساط المستحقة مع بيانات الدفع من فوري و Opay",
    },
}

# ===================== دوال مساعدة =====================

def get_logo_b64():
    for p in ["logo.png","images/logo.png","static/logo.png","assets/logo.png"]:
        if os.path.exists(p):
            with open(p,"rb") as f:
                return base64.b64encode(f.read()).decode()
    return None

def show_header(user=None):
    logo_b64  = get_logo_b64()
    full_name = user.get("full_name", "") if user else ""
    role      = user.get("role", "")      if user else ""

    if logo_b64:
        logo_part = (
            "<img src='data:image/png;base64," + logo_b64 +
            "' alt='logo' style='height:52px;border-radius:10px;'>"
        )
    else:
        logo_part = "<span style='font-size:32px'>📊</span>"

    if user:
        right_part = (
            "<div style='text-align:left;color:#bfdbfe;font-size:13px;line-height:1.8'>"
            "<div>👤 <strong style='color:#fff'>" + full_name + "</strong></div>"
            "<div style='font-size:11px;color:#7dd3fc'>" + role + "</div>"
            "</div>"
        )
    else:
        right_part = ""

    header_html = (
        "<div style='display:flex;align-items:center;justify-content:space-between;"
        "background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 60%,#2563eb 100%);"
        "padding:14px 28px;border-radius:18px;margin-bottom:24px;"
        "box-shadow:0 8px 32px rgba(30,58,138,0.25);'>"
        "<div style='display:flex;align-items:center;gap:14px;'>"
        + logo_part +
        "<div>"
        "<div style='color:#fff;font-size:22px;font-weight:800;'>نظام كاريتاس</div>"
        "<div style='color:#93c5fd;font-size:12px;margin-top:2px;'>لوحة التقارير والمتابعة</div>"
        "</div>"
        "</div>"
        + right_part +
        "</div>"
    )
    st.markdown(header_html, unsafe_allow_html=True)

def check_login(u, p):
    res = supabase.table("app_users").select("*").eq("id",u).eq("password_hash",p).execute()
    return res.data[0] if res.data else None

def find_col(df, candidates):
    for c in candidates:
        if c in df.columns: return c
    return None

# ===================== جلب البيانات =====================

def fetch_reports_data():
    all_data, limit, offset = [], 1000, 0
    while True:
        res = supabase.table("all_payments_report").select("*").range(offset, offset+limit-1).execute()
        if not res.data: break
        all_data.extend(res.data)
        if len(res.data) < limit: break
        offset += limit
    df = pd.DataFrame(all_data)
    if not df.empty:
        df['تاريخ الدفع'] = pd.to_datetime(df['تاريخ الدفع'], dayfirst=True, errors='coerce')
    return df

def fetch_outstanding_data():
    all_data, limit, offset = [], 1000, 0
    while True:
        res = supabase.table("outstanding_with_payments").select("*").range(offset, offset+limit-1).execute()
        if not res.data: break
        all_data.extend(res.data)
        if len(res.data) < limit: break
        offset += limit
    return pd.DataFrame(all_data)

# ===================== Excel =====================

def thin_border():
    s = Side(border_style="thin", color="D1D5DB")
    return Border(left=s, right=s, top=s, bottom=s)

def write_total_row(ws, total_row, cols, last_data_row):
    for ci in range(1, len(cols)+1):
        c = ws.cell(row=total_row, column=ci)
        c.fill=PatternFill("solid",fgColor="BFDBFE"); c.border=thin_border()
        c.alignment=Alignment(horizontal='center',vertical='center')
        c.font=Font(bold=True,color="1E3A8A",name="Arial",size=11)
    ws.cell(row=total_row, column=1).value = "✦ الإجمالي"
    if 'المبلغ' in cols:
        ci=cols.index('المبلغ')+1; cl=get_column_letter(ci)
        ws.cell(row=total_row,column=ci).value=f"=SUM({cl}3:{cl}{last_data_row})"
        ws.cell(row=total_row,column=ci).number_format='#,##0.00'
    ws.row_dimensions[total_row].height=26

def generate_reports_excel_single(df_display, sheet_title="التقرير", report_title="تقرير السدادات"):
    wb=Workbook(); ws=wb.active; ws.title=sheet_title[:31]
    ws.sheet_view.rightToLeft=True
    cols=list(df_display.columns); last_col=get_column_letter(len(cols))
    ws.merge_cells(f'A1:{last_col}1')
    ws['A1'].value=report_title; ws['A1'].font=Font(bold=True,size=14,color="1E3A8A",name="Arial")
    ws['A1'].fill=PatternFill("solid",fgColor="EFF6FF")
    ws['A1'].alignment=Alignment(horizontal='center',vertical='center')
    ws.row_dimensions[1].height=32
    for ci,h in enumerate(cols,1):
        c=ws.cell(row=2,column=ci,value=h)
        c.font=Font(bold=True,color="FFFFFF",name="Arial",size=11)
        c.fill=PatternFill("solid",fgColor="1E3A8A")
        c.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
        c.border=thin_border()
    ws.row_dimensions[2].height=24
    for ri,row in enumerate(df_display.itertuples(index=False),3):
        bg="F0F4FF" if ri%2==0 else "FFFFFF"
        for ci,val in enumerate(row,1):
            c=ws.cell(row=ri,column=ci,value=val)
            c.fill=PatternFill("solid",fgColor=bg)
            c.alignment=Alignment(horizontal='center',vertical='center')
            c.font=Font(name="Arial",size=10); c.border=thin_border()
    ldr=2+len(df_display); write_total_row(ws,ldr+1,cols,ldr)
    cw={"اسم العميل":28,"الفرع":20}
    for ci,col in enumerate(cols,1):
        ws.column_dimensions[get_column_letter(ci)].width=cw.get(col,18)
    ws.freeze_panes="A3"
    buf=io.BytesIO(); wb.save(buf); return buf.getvalue()

def generate_reports_excel_daily(df_display, original_df):
    wb=Workbook(); wb.remove(wb.active)
    DARK="1E3A8A"; LIGHT="EFF6FF"; ALT="F0F4FF"; TBG="BFDBFE"; WHT="FFFFFF"

    def style_sheet(ws, df_part, title_text):
        ws.sheet_view.rightToLeft=True
        cols=list(df_part.columns)
        ws.merge_cells(f'A1:{get_column_letter(len(cols))}1')
        ws['A1'].value=title_text; ws['A1'].font=Font(bold=True,size=13,color=DARK,name="Arial")
        ws['A1'].fill=PatternFill("solid",fgColor=LIGHT)
        ws['A1'].alignment=Alignment(horizontal='center',vertical='center')
        ws.row_dimensions[1].height=30
        for ci,h in enumerate(cols,1):
            c=ws.cell(row=2,column=ci,value=h)
            c.font=Font(bold=True,color=WHT,name="Arial",size=10)
            c.fill=PatternFill("solid",fgColor=DARK)
            c.alignment=Alignment(horizontal='center',vertical='center'); c.border=thin_border()
        ws.row_dimensions[2].height=22
        for ri,row in enumerate(df_part.itertuples(index=False),3):
            bg=ALT if ri%2==0 else WHT
            for ci,val in enumerate(row,1):
                c=ws.cell(row=ri,column=ci,value=val)
                c.fill=PatternFill("solid",fgColor=bg)
                c.alignment=Alignment(horizontal='center',vertical='center')
                c.font=Font(name="Arial",size=10); c.border=thin_border()
        ldr=2+len(df_part); write_total_row(ws,ldr+1,cols,ldr)
        ws.freeze_panes="A3"
        cw={"اسم العميل":28,"الفرع":20}
        for ci,col in enumerate(cols,1):
            ws.column_dimensions[get_column_letter(ci)].width=cw.get(col,17)

    ws_sum=wb.create_sheet("ملخص يومي"); ws_sum.sheet_view.rightToLeft=True
    sc=["التاريخ","عدد العمليات","إجمالي المبلغ (ج.م)"]; nsc=len(sc)
    ws_sum.merge_cells(f'A1:{get_column_letter(nsc)}1')
    ws_sum['A1'].value="ملخص يومي - تقرير السدادات"
    ws_sum['A1'].font=Font(bold=True,size=14,color=DARK,name="Arial")
    ws_sum['A1'].fill=PatternFill("solid",fgColor=LIGHT)
    ws_sum['A1'].alignment=Alignment(horizontal='center',vertical='center')
    ws_sum.row_dimensions[1].height=32
    for ci,h in enumerate(sc,1):
        c=ws_sum.cell(row=2,column=ci,value=h)
        c.font=Font(bold=True,color=WHT,name="Arial"); c.fill=PatternFill("solid",fgColor=DARK)
        c.alignment=Alignment(horizontal='center',vertical='center'); c.border=thin_border()
    ws_sum.row_dimensions[2].height=22
    temp=original_df.copy(); temp['_date']=temp['تاريخ الدفع'].dt.date
    dates=sorted(temp['_date'].dropna().unique())
    for ri,d in enumerate(dates,3):
        ddf=temp[temp['_date']==d]; bg=ALT if ri%2==0 else WHT
        for ci in range(1,nsc+1):
            c=ws_sum.cell(row=ri,column=ci)
            c.fill=PatternFill("solid",fgColor=bg)
            c.alignment=Alignment(horizontal='center',vertical='center')
            c.font=Font(name="Arial",size=10); c.border=thin_border()
        ws_sum.cell(row=ri,column=1).value=str(d)
        ws_sum.cell(row=ri,column=2).value=len(ddf)
        ws_sum.cell(row=ri,column=3).value=float(ddf['المبلغ'].sum())
        ws_sum.cell(row=ri,column=3).number_format='#,##0.00'
    trs=2+len(dates)+1
    for ci in range(1,nsc+1):
        c=ws_sum.cell(row=trs,column=ci)
        c.fill=PatternFill("solid",fgColor=TBG); c.border=thin_border()
        c.alignment=Alignment(horizontal='center',vertical='center')
        c.font=Font(bold=True,color=DARK,name="Arial")
    ws_sum.cell(row=trs,column=1).value="✦ الإجمالي الكلي"
    ws_sum.cell(row=trs,column=3).value=f"=SUM(C3:C{trs-1})"
    ws_sum.cell(row=trs,column=3).number_format='#,##0.00'
    ws_sum.row_dimensions[trs].height=26
    for ci,w in enumerate([18,18,25],1):
        ws_sum.column_dimensions[get_column_letter(ci)].width=w
    ws_sum.freeze_panes="A3"
    for d in dates:
        ddf=temp[temp['_date']==d].copy()
        dd=ddf.rename(columns={'client_code':'كود العميل','client_name':'اسم العميل','branch_name':'الفرع'})
        if 'تاريخ الدفع' in dd.columns:
            dd['تاريخ الدفع']=dd['تاريخ الدفع'].dt.strftime('%Y-%m-%d')
        drop=[c for c in dd.columns if c.startswith('_') or c=='id']
        dd=dd.drop(columns=drop,errors='ignore')
        ws_day=wb.create_sheet(str(d)[:31]); style_sheet(ws_day,dd,f"تقرير سدادات يوم {d}")
    buf=io.BytesIO(); wb.save(buf); return buf.getvalue()

def generate_outstanding_excel(df, title="تقرير الأقساط المستحقة"):
    wb=Workbook(); ws=wb.active; ws.title="الأقساط المستحقة"
    ws.sheet_view.rightToLeft=True
    cols=list(df.columns); last_col=get_column_letter(len(cols))
    ws.merge_cells(f'A1:{last_col}1')
    ws['A1'].value=title; ws['A1'].font=Font(bold=True,size=16,color="1E3A8A",name="Arial")
    ws['A1'].fill=PatternFill("solid",fgColor="EFF6FF")
    ws['A1'].alignment=Alignment(horizontal='center',vertical='center')
    ws.row_dimensions[1].height=35
    headers=['اسم المسؤول','كود الفرع','اسم الفرع','تاريخ استحقاق القسط','تاريخ حالة القسط',
             'كود العميل','اسم العميل','الرقم القومي','رقم القرض','حالة القسط','قيمة القسط',
             'نوع الفاتورة','تاريخ التحويل','وقت التحويل','مبلغ فوري','رقم حساب الفوترة',
             'رقم تحويل فوري','الرقم المرجعي','مبلغ Opay','تاريخ الدفع Opay','وقت الدفع Opay']
    for ci,h in enumerate(headers[:len(cols)],1):
        c=ws.cell(row=2,column=ci,value=h)
        c.font=Font(bold=True,color="FFFFFF",name="Arial",size=11)
        c.fill=PatternFill("solid",fgColor="1E3A8A")
        c.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
        c.border=thin_border()
    ws.row_dimensions[2].height=30
    for ri,row in enumerate(df.itertuples(index=False),3):
        for ci,val in enumerate(row,1):
            c=ws.cell(row=ri,column=ci,value=val)
            c.alignment=Alignment(horizontal='center',vertical='center')
            c.font=Font(name="Arial",size=10); c.border=thin_border()
            st_=str(row[9]) if len(row)>9 else ""
            if "مسدد جزئي" in st_:
                c.fill=PatternFill("solid",fgColor="FFCCCC"); c.font=Font(color="9C0006",bold=True)
            elif "غير مدفوع" in st_ or st_=="":
                c.fill=PatternFill("solid",fgColor="FFE699"); c.font=Font(color="7F4A00")
            else:
                c.fill=PatternFill("solid",fgColor="E2EFDA"); c.font=Font(color="375623")
    cw={'اسم العميل':25,'اسم الفرع':20,'اسم المسؤول':18,'الرقم القومي':15}
    for ci,col in enumerate(headers[:len(cols)],1):
        ws.column_dimensions[get_column_letter(ci)].width=cw.get(col,15)
    ws.freeze_panes="A3"
    buf=io.BytesIO(); wb.save(buf); return buf.getvalue()

# ===================================================================
# ===================== صفحة فوري =====================
# ===================================================================

def reports_page():
    if 'user' not in st.session_state:
        st.warning("⚠️ يجب تسجيل الدخول أولاً"); st.stop()

    user=st.session_state['user']
    show_header(user)

    col_back, col_title = st.columns([1,6])
    with col_back:
        if st.button("🏠 الرئيسية"):
            st.query_params.clear(); st.rerun()
    with col_title:
        st.markdown('<div class="sec-title">💳 سداد فوري & Opay</div>', unsafe_allow_html=True)

    is_admin      = user.get('role') == 'admin'
    user_branches = user.get('branches', [])

    with st.spinner("جاري تحميل البيانات..."):
        df_raw = fetch_reports_data()
    if df_raw.empty:
        st.info("📭 لا توجد بيانات متاحة"); return

    df_acc  = df_raw if is_admin else df_raw[df_raw['branch_name'].isin(user_branches)]
    v_dates = df_acc['تاريخ الدفع'].dropna()
    if v_dates.empty:
        st.info("📭 لا توجد تواريخ متاحة"); return

    # ── فلاتر ──
    st.markdown('<div class="filter-bar"><div class="filter-bar-title">🔍 أدوات البحث والتصفية</div>', unsafe_allow_html=True)
    fc1,fc2,fc3,fc4 = st.columns(4)
    with fc1: start_d = st.date_input("📅 من تاريخ", v_dates.min().date(), key="r_from")
    with fc2: end_d   = st.date_input("📅 إلى تاريخ", v_dates.max().date(), key="r_to")
    with fc3:
        codes=["الكل"]+sorted(df_acc['كود الخدمة'].unique().tolist())
        sel_code=st.selectbox("🏷️ كود الخدمة", codes, key="r_code")
    with fc4: s_name=st.text_input("🔎 بحث بالاسم أو الكود", key="r_search")
    st.markdown('</div>', unsafe_allow_html=True)

    mask = (df_acc['تاريخ الدفع'].dt.date >= start_d) & (df_acc['تاريخ الدفع'].dt.date <= end_d)
    if sel_code != "الكل": mask &= (df_acc['كود الخدمة'] == sel_code)
    if s_name:
        mask &= (df_acc['client_name'].astype(str).str.contains(s_name,na=False,case=False) |
                 df_acc['client_code'].astype(str).str.contains(s_name,na=False,case=False))

    final_df = df_acc.loc[mask]
    if final_df.empty:
        st.warning("⚠️ لا توجد بيانات تطابق معايير البحث"); return

    counts=final_df['كود الخدمة'].value_counts()
    codes_html=" &nbsp;|&nbsp; ".join([f"<b>{k}</b>: {v}" for k,v in counts.items()])

    k1,k2,k3=st.columns(3)
    with k1: st.markdown(f'<div class="kpi-card"><div class="kpi-lbl">💰 إجمالي المبالغ</div><div class="kpi-val">{final_df["المبلغ"].sum():,.0f} ج.م</div></div>',unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="kpi-card"><div class="kpi-lbl">📊 عدد العمليات</div><div class="kpi-val">{len(final_df):,} حركة</div></div>',unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="kpi-card"><div class="kpi-lbl">📋 الأكواد</div><div style="font-size:13px;color:#1e3a8a;margin-top:6px">{codes_html}</div></div>',unsafe_allow_html=True)

    with st.expander("📅 الملخص اليومي", expanded=False):
        daily=final_df.groupby(final_df['تاريخ الدفع'].dt.date).agg(
            عدد_العمليات=('المبلغ','count'), إجمالي_المبلغ=('المبلغ','sum')).reset_index()
        daily.columns=['التاريخ','عدد العمليات','إجمالي المبلغ (ج.م)']
        st.dataframe(daily, use_container_width=True, hide_index=True)

    st.markdown('<div class="sec-title">📋 البيانات التفصيلية</div>', unsafe_allow_html=True)
    display_df=final_df.copy().rename(columns={'client_code':'كود العميل','client_name':'اسم العميل','branch_name':'الفرع'})
    drop_cols=[c for c in display_df.columns if c.startswith('_') or c=='id']
    display_df=display_df.drop(columns=drop_cols,errors='ignore')
    if 'تاريخ الدفع' in display_df.columns:
        display_df['تاريخ الدفع']=display_df['تاريخ الدفع'].dt.strftime('%Y-%m-%d')
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=420)

    # ── تحميل ──
    st.markdown('<div class="sec-title">📥 تحميل التقرير</div>', unsafe_allow_html=True)
    dl1,dl2,dl3=st.columns([2,2,2])
    with dl1:
        split_mode=st.radio("نوع التنزيل",
            ["كل البيانات في شيت واحد","تقسيم يوم يوم (شيت لكل يوم)"], key="r_split")
    with dl2:
        selected_day="كل الأيام"
        if split_mode=="تقسيم يوم يوم (شيت لكل يوم)":
            av=sorted(final_df['تاريخ الدفع'].dropna().dt.date.unique())
            selected_day=st.selectbox("اختر اليوم", ["كل الأيام"]+[str(d) for d in av], key="r_day")
    with dl3:
        if split_mode=="تقسيم يوم يوم (شيت لكل يوم)":
            if selected_day=="كل الأيام":
                xls=generate_reports_excel_daily(display_df,final_df)
                fname=f"تقرير_كل_الأيام_{datetime.now().date()}.xlsx"
            else:
                sd=pd.to_datetime(selected_day).date()
                ddf=display_df[pd.to_datetime(display_df['تاريخ الدفع'],errors='coerce').dt.date==sd]
                xls=generate_reports_excel_single(ddf,sheet_title=selected_day,report_title=f"تقرير سدادات يوم {selected_day}")
                fname=f"تقرير_{selected_day}.xlsx"
        else:
            xls=generate_reports_excel_single(display_df,report_title=f"تقرير السدادات - {start_d} إلى {end_d}")
            fname=f"تقرير_{datetime.now().date()}.xlsx"
        st.download_button("📊 تحميل Excel", data=xls, file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)

# ===================================================================
# ===================== صفحة الأقساط المستحقة =====================
# ===================================================================

def outstanding_page():
    if 'user' not in st.session_state:
        st.warning("⚠️ يجب تسجيل الدخول أولاً"); st.stop()

    user=st.session_state['user']
    show_header(user)

    col_back,col_title=st.columns([1,6])
    with col_back:
        if st.button("🏠 الرئيسية"):
            st.query_params.clear(); st.rerun()
    with col_title:
        st.markdown('<div class="sec-title">📋 الأقساط المستحقة — فوري & Opay</div>',unsafe_allow_html=True)

    is_admin      = user.get('role')=='admin'
    branches_list = user.get('branches',[])

    if isinstance(branches_list,str):
        import json
        try:    branches_list=json.loads(branches_list)
        except: branches_list=[branches_list]

    with st.spinner("جاري تحميل البيانات..."):
        df_raw=fetch_outstanding_data()
    if df_raw.empty:
        st.info("📭 لا توجد بيانات متاحة"); return

    branch_col  = find_col(df_raw,['branch_name','Branch_name','اسم الفرع','branch','Branch'])
    officer_col = find_col(df_raw,['officer_name','Officer_name','اسم المسؤول','officer','Officer','emp_name','employee_name'])
    inst_col    = find_col(df_raw,['inst_amount','قيمة القسط','amount','inst_amt'])
    fawry_col   = find_col(df_raw,['fawry_amount','fawry_amt','Amount'])
    opay_col    = find_col(df_raw,['opay_amount','opay_amt','opayAmount'])
    client_col  = find_col(df_raw,['client_name','اسم العميل','client','name'])
    nation_col  = find_col(df_raw,['nation_id','الرقم القومي','nation','national_id'])

    if not branch_col:
        st.error("❌ لم يتم العثور على عمود الفرع"); return

    # فلترة الصلاحيات
    if not is_admin and branches_list:
        df_acc=df_raw[df_raw[branch_col].astype(str).isin(branches_list)].copy()
    else:
        df_acc=df_raw.copy()

    # ── فلاتر ──
    st.markdown('<div class="filter-bar"><div class="filter-bar-title">🔍 أدوات البحث والتصفية</div>',unsafe_allow_html=True)
    fc1,fc2,fc3,fc4=st.columns(4)

    with fc1:
        if not is_admin and branches_list:
            avail=sorted(df_acc[branch_col].dropna().unique().tolist())
            if len(avail)>1:
                sel_br=st.selectbox("🏢 الفرع",["الكل"]+avail,key="o_branch")
                if sel_br!="الكل": df_acc=df_acc[df_acc[branch_col]==sel_br]
            else:
                st.markdown(f"🏢 **الفرع:** {avail[0] if avail else '—'}")
        else:
            all_br=sorted(df_acc[branch_col].dropna().unique().tolist())
            sel_br=st.selectbox("🏢 الفرع",["الكل"]+all_br,key="o_branch_admin")
            if sel_br!="الكل": df_acc=df_acc[df_acc[branch_col]==sel_br]

    with fc2:
        off_f=None
        for c in df_acc.columns:
            if any(k in c.lower() for k in ['officer','مسؤول','مسئول']): off_f=c; break
        if off_f:
            offs=sorted(df_acc[off_f].dropna().unique().tolist())
            sel_off=st.selectbox("👤 الاخصائي",["الكل"]+offs,key="o_officer")
            if sel_off!="الكل": df_acc=df_acc[df_acc[off_f]==sel_off]

    with fc3:
        search_name=st.text_input("🔎 بحث باسم العميل",key="o_name")
        if search_name and client_col:
            df_acc=df_acc[df_acc[client_col].astype(str).str.contains(search_name,na=False,case=False)]

    with fc4:
        search_nat=st.text_input("🆔 بحث بالرقم القومي",key="o_nat")
        if search_nat and nation_col:
            df_acc=df_acc[df_acc[nation_col].astype(str).str.contains(search_nat,na=False,case=False)]

    st.markdown('</div>',unsafe_allow_html=True)

    if df_acc.empty:
        st.warning("⚠️ لا توجد بيانات تطابق معايير البحث"); return

    # ── تحويل الأعمدة لـ numeric ──
    for c in [inst_col, fawry_col, opay_col]:
        if c: df_acc[c] = pd.to_numeric(df_acc[c], errors='coerce').fillna(0)

    # ── حساب المدفوع والمتبقي لكل صف بشكل صريح ──
    df_acc['_paid'] = (
        (df_acc[fawry_col] if fawry_col else 0) +
        (df_acc[opay_col]  if opay_col  else 0)
    )
    df_acc['_inst'] = df_acc[inst_col] if inst_col else 0
    # المتبقي لكل صف = القسط - المدفوع (لا يقل عن صفر)
    df_acc['_remaining'] = (df_acc['_inst'] - df_acc['_paid']).clip(lower=0)

    # ── تحديد الحالة بناءً على الأعمدة المحسوبة ──
    def get_status(row):
        paid = row['_paid']
        inst = row['_inst']
        if inst <= 0:            return "❌ غير مدفوع"
        if paid >= inst:         return "✅ مدفوع بالكامل"
        elif paid > 0:           return "⚠️ مسدد جزئي"
        else:                    return "❌ غير مدفوع"

    df_acc['حالة الدفع'] = df_acc.apply(get_status, axis=1)
    status_order = {"✅ مدفوع بالكامل": 0, "⚠️ مسدد جزئي": 1, "❌ غير مدفوع": 2}
    df_acc['_sk'] = df_acc['حالة الدفع'].map(status_order)
    df_acc = df_acc.sort_values('_sk').drop('_sk', axis=1)

    # ── الإحصائيات الكلية من الأعمدة المحسوبة ──
    ti = df_acc['_inst'].sum()
    tp = df_acc['_paid'].sum()
    tr = df_acc['_remaining'].sum()   # مجموع المتبقي الحقيقي لكل صف

    # إحصائيات المسدد جزئي
    df_partial   = df_acc[df_acc['حالة الدفع'] == "⚠️ مسدد جزئي"]
    partial_cnt  = len(df_partial)
    partial_paid = df_partial['_paid'].sum()
    partial_rem  = df_partial['_remaining'].sum()

    # إحصائيات غير المدفوع
    df_unpaid  = df_acc[df_acc['حالة الدفع'] == "❌ غير مدفوع"]
    unpaid_cnt = len(df_unpaid)

    # ── KPIs ──
    k1,k2,k3,k4 = st.columns(4)
    with k1:
        st.markdown(
            f'''<div class="kpi-card">
                <div class="kpi-lbl">💰 إجمالي المستحق</div>
                <div class="kpi-val">{ti:,.0f} ج.م</div>
                <div style="font-size:11px;color:#64748b;margin-top:4px">{len(df_acc):,} قسط</div>
            </div>''', unsafe_allow_html=True)
    with k2:
        st.markdown(
            f'''<div class="kpi-card" style="border-top-color:#059669">
                <div class="kpi-lbl">💳 إجمالي المدفوع</div>
                <div class="kpi-val" style="color:#059669">{tp:,.0f} ج.م</div>
                <div style="font-size:11px;color:#059669;margin-top:4px">
                    {len(df_acc[df_acc["حالة الدفع"]=="✅ مدفوع بالكامل"]):,} مكتمل
                </div>
            </div>''', unsafe_allow_html=True)
    with k3:
        st.markdown(
            f'''<div class="kpi-card" style="border-top-color:#dc2626">
                <div class="kpi-lbl">📊 إجمالي المتبقي</div>
                <div class="kpi-val" style="color:#dc2626">{tr:,.0f} ج.م</div>
                <div style="font-size:11px;color:#dc2626;margin-top:4px">
                    يشمل السداد الجزئي
                </div>
            </div>''', unsafe_allow_html=True)
    with k4:
        partial_color = "#f59e0b" if partial_cnt > 0 else "#7c3aed"
        st.markdown(
            f'''<div class="kpi-card" style="border-top-color:{partial_color}">
                <div class="kpi-lbl">⚠️ مسدد جزئي</div>
                <div class="kpi-val" style="color:{partial_color}">{partial_cnt:,} قسط</div>
                <div style="font-size:11px;color:{partial_color};margin-top:4px">
                    متبقي: {partial_rem:,.0f} ج.م
                </div>
            </div>''', unsafe_allow_html=True)

    # ── بانر تحذير لو في مسدد جزئي ──
    if partial_cnt > 0:
        st.markdown(
            f'''<div style="background:linear-gradient(90deg,#fffbeb,#fef3c7);
                        border:1.5px solid #f59e0b;border-right:5px solid #f59e0b;
                        border-radius:12px;padding:14px 20px;margin:14px 0;
                        display:flex;align-items:center;gap:12px;">
                <div style="font-size:24px">⚠️</div>
                <div>
                    <div style="font-weight:800;color:#92400e;font-size:14px">
                        يوجد {partial_cnt:,} قسط مسدد جزئياً — لم يكتمل السداد بعد
                    </div>
                    <div style="color:#b45309;font-size:12px;margin-top:3px">
                        إجمالي ما تم سداده جزئياً: <strong>{partial_paid:,.2f} ج.م</strong>
                        &nbsp;|&nbsp;
                        إجمالي المتبقي منهم: <strong>{partial_rem:,.2f} ج.م</strong>
                        &nbsp;|&nbsp;
                        غير المدفوع كلياً: <strong>{unpaid_cnt:,} قسط</strong>
                    </div>
                </div>
            </div>''', unsafe_allow_html=True)

    # ===== ملخص الفروع =====
    unique_branches = df_acc[branch_col].dropna().unique().tolist()

    if len(unique_branches) == 1:
        # ── كارت فرع واحد (الصورة 2) ──
        br_name = unique_branches[0]
        br_inst = df_acc[inst_col].sum()  if inst_col  else 0
        br_paid = (df_acc[fawry_col].sum() if fawry_col else 0) + (df_acc[opay_col].sum() if opay_col else 0)
        br_rem  = br_inst - br_paid
        br_cnt  = len(df_acc)

        st.markdown(
            "<div style='background:#fff;border-radius:16px;padding:24px 28px;"
            "box-shadow:0 4px 20px rgba(30,58,138,0.10);border:1px solid #e0e7ff;margin-bottom:20px;'>"
            "<div style='text-align:center;font-size:17px;font-weight:800;color:#1e3a8a;"
            "margin-bottom:20px;border-bottom:2px solid #e0e7ff;padding-bottom:12px;'>"
            "📍 ملخص فرع: " + br_name + "</div>"
            "<div style='display:grid;grid-template-columns:1fr 1fr;gap:14px;'>"
            "<div style='background:#1e3a8a;border-radius:12px;padding:16px;text-align:center;'>"
            "<div style='color:#93c5fd;font-size:12px;margin-bottom:6px;'>إجمالي المستحق</div>"
            "<div style='color:#fff;font-size:20px;font-weight:800;'>" + f"{br_inst:,.2f}" + " ج.م</div></div>"
            "<div style='background:#2d6a4f;border-radius:12px;padding:16px;text-align:center;'>"
            "<div style='color:#b7e4c7;font-size:12px;margin-bottom:6px;'>إجمالي المدفوع</div>"
            "<div style='color:#fff;font-size:20px;font-weight:800;'>" + f"{br_paid:,.2f}" + " ج.م</div></div>"
            "<div style='background:#c1440e;border-radius:12px;padding:16px;text-align:center;'>"
            "<div style='color:#ffd6c0;font-size:12px;margin-bottom:6px;'>إجمالي المتبقي</div>"
            "<div style='color:#fff;font-size:20px;font-weight:800;'>" + f"{br_rem:,.2f}" + " ج.م</div></div>"
            "<div style='background:#5b2d8e;border-radius:12px;padding:16px;text-align:center;'>"
            "<div style='color:#d8b4fe;font-size:12px;margin-bottom:6px;'>عدد الحالات</div>"
            "<div style='color:#fff;font-size:20px;font-weight:800;'>" + f"{br_cnt:,}" + "</div></div>"
            "</div></div>",
            unsafe_allow_html=True
        )

    else:
        # ── جدول ملخص الفروع (الصورة 1) ──
        st.markdown('<div class="sec-title">🏢 ملخص إجمالي الفروع</div>', unsafe_allow_html=True)

        grp_cols = {inst_col: 'sum'} if inst_col else {}
        if inst_col:
            br_sum = df_acc.groupby(branch_col).agg({inst_col: 'sum'}).reset_index()
            br_sum.columns = ['اسم الفرع', 'إجمالي المستحق']
        else:
            br_sum = df_acc.groupby(branch_col).size().reset_index()
            br_sum.columns = ['اسم الفرع', 'عدد الحالات']

        br_sum['عدد الحالات'] = df_acc.groupby(branch_col).size().values

        if fawry_col:
            fs = df_acc.groupby(branch_col)[fawry_col].sum().reset_index()
            fs.columns = ['اسم الفرع', '_fawry']
            br_sum = br_sum.merge(fs, on='اسم الفرع', how='left')
            br_sum['_fawry'] = br_sum['_fawry'].fillna(0)
        else:
            br_sum['_fawry'] = 0

        if opay_col:
            ops = df_acc.groupby(branch_col)[opay_col].sum().reset_index()
            ops.columns = ['اسم الفرع', '_opay']
            br_sum = br_sum.merge(ops, on='اسم الفرع', how='left')
            br_sum['_opay'] = br_sum['_opay'].fillna(0)
        else:
            br_sum['_opay'] = 0

        br_sum['إجمالي المدفوع'] = br_sum['_fawry'] + br_sum['_opay']
        br_sum = br_sum.drop(columns=['_fawry', '_opay'])
        # المتبقي الحقيقي = مجموع _remaining لكل فرع (يشمل المسدد جزئي)
        br_rem = df_acc.groupby(branch_col)['_remaining'].sum().reset_index()
        br_rem.columns = ['اسم الفرع', 'إجمالي المتبقي']
        br_sum = br_sum.merge(br_rem, on='اسم الفرع', how='left')
        br_sum['إجمالي المتبقي'] = br_sum['إجمالي المتبقي'].fillna(0)
        br_sum = br_sum.sort_values('إجمالي المستحق', ascending=False)

        # صف الإجمالي الكلي
        total_row = {
            'اسم الفرع':        'الإجمالي الكلي',
            'عدد الحالات':      br_sum['عدد الحالات'].sum(),
            'إجمالي المستحق':   br_sum['إجمالي المستحق'].sum(),
            'إجمالي المدفوع':   br_sum['إجمالي المدفوع'].sum(),
            'إجمالي المتبقي':   br_sum['إجمالي المتبقي'].sum(),
        }
        br_sum_display = br_sum.copy()
        for c in ['إجمالي المستحق', 'إجمالي المدفوع', 'إجمالي المتبقي']:
            br_sum_display[c] = br_sum_display[c].apply(lambda x: f"{x:,.2f}")

        # رسم الجدول بـ HTML
        rows_html = ""
        for _, row in br_sum_display.iterrows():
            rows_html += (
                "<tr>"
                "<td style='padding:10px 14px;text-align:right;border-bottom:1px solid #e2e8f0;'>" + str(row['اسم الفرع']) + "</td>"
                "<td style='padding:10px 14px;text-align:center;border-bottom:1px solid #e2e8f0;font-weight:700;color:#1e3a8a;'>" + str(int(row['عدد الحالات'])) + "</td>"
                "<td style='padding:10px 14px;text-align:center;border-bottom:1px solid #e2e8f0;color:#1e3a8a;font-weight:600;'>" + str(row['إجمالي المستحق']) + "</td>"
                "<td style='padding:10px 14px;text-align:center;border-bottom:1px solid #e2e8f0;color:#059669;font-weight:600;'>" + str(row['إجمالي المدفوع']) + "</td>"
                "<td style='padding:10px 14px;text-align:center;border-bottom:1px solid #e2e8f0;color:#dc2626;font-weight:600;'>" + str(row['إجمالي المتبقي']) + "</td>"
                "</tr>"
            )

        # صف الإجمالي
        rows_html += (
            "<tr style='background:#1e3a8a;'>"
            "<td style='padding:12px 14px;text-align:right;color:#fff;font-weight:800;border-radius:0 0 0 12px;'>الإجمالي الكلي</td>"
            "<td style='padding:12px 14px;text-align:center;color:#fff;font-weight:800;'>" + f"{int(total_row['عدد الحالات']):,}" + "</td>"
            "<td style='padding:12px 14px;text-align:center;color:#fbbf24;font-weight:800;'>" + f"{total_row['إجمالي المستحق']:,.2f}" + "</td>"
            "<td style='padding:12px 14px;text-align:center;color:#6ee7b7;font-weight:800;'>" + f"{total_row['إجمالي المدفوع']:,.2f}" + "</td>"
            "<td style='padding:12px 14px;text-align:center;color:#fca5a5;font-weight:800;border-radius:0 0 12px 0;'>" + f"{total_row['إجمالي المتبقي']:,.2f}" + "</td>"
            "</tr>"
        )

        table_html = (
            "<div style='overflow-x:auto;margin-bottom:20px;'>"
            "<table style='width:100%;border-collapse:collapse;background:#fff;"
            "border-radius:14px;overflow:hidden;box-shadow:0 4px 20px rgba(30,58,138,0.10);'>"
            "<thead>"
            "<tr style='background:#1e3a8a;'>"
            "<th style='padding:14px;text-align:right;color:#fff;font-size:14px;'>اسم الفرع</th>"
            "<th style='padding:14px;text-align:center;color:#fff;font-size:14px;'>عدد الحالات</th>"
            "<th style='padding:14px;text-align:center;color:#fff;font-size:14px;'>إجمالي المستحق</th>"
            "<th style='padding:14px;text-align:center;color:#fff;font-size:14px;'>إجمالي المدفوع</th>"
            "<th style='padding:14px;text-align:center;color:#fff;font-size:14px;'>إجمالي المتبقي</th>"
            "</tr>"
            "</thead>"
            "<tbody>" + rows_html + "</tbody>"
            "</table></div>"
        )
        st.markdown(table_html, unsafe_allow_html=True)

    st.markdown('<div class="sec-title">📋 جدول الأقساط المستحقة</div>',unsafe_allow_html=True)
    col_map=[
        ('حالة الدفع','📊 حالة الدفع'),(branch_col,'🏢 اسم الفرع'),
        (client_col,'👤 اسم العميل'),(nation_col,'🆔 الرقم القومي'),
        ('inst_mat_date','📅 تاريخ الاستحقاق'),(inst_col,'💰 قيمة القسط'),
        (fawry_col,'💳 مبلغ فوري'),(opay_col,'📱 مبلغ Opay'),
        (officer_col,'👨‍💼 المسؤول'),('loan_number','🔢 رقم القرض'),
        ('inst_status','📌 حالة القسط'),
    ]
    dcols=[]; dnames=[]
    for col,name in col_map:
        if col and col in df_acc.columns: dcols.append(col); dnames.append(name)

    if dcols:
        df_disp=df_acc[dcols].copy(); df_disp.columns=dnames
        if '📅 تاريخ الاستحقاق' in df_disp.columns:
            df_disp['📅 تاريخ الاستحقاق']=pd.to_datetime(df_disp['📅 تاريخ الاستحقاق'],errors='coerce').dt.strftime('%Y-%m-%d')
        for c in ['💰 قيمة القسط','💳 مبلغ فوري','📱 مبلغ Opay']:
            if c in df_disp.columns:
                df_disp[c]=df_disp[c].apply(lambda x:f"{x:,.2f}" if pd.notna(x) and x>0 else "0.00")
        def color_rows(row):
            s=row['📊 حالة الدفع']
            if 'مسدد جزئي' in s:  return ['background-color:#FFCCCC;color:#9C0006;font-weight:bold']*len(row)
            elif 'غير مدفوع' in s: return ['background-color:#FFE699;color:#7F4A00;font-weight:bold']*len(row)
            else:                   return ['background-color:#E2EFDA;color:#375623']*len(row)
        st.dataframe(df_disp.style.apply(color_rows,axis=1),use_container_width=True,height=450)

    if inst_col:
        with st.expander("📊 ملخص حسب حالة الدفع",expanded=False):
            sm=df_acc.groupby('حالة الدفع').agg({inst_col:'sum'}).reset_index()
            sm['عدد الأقساط']=df_acc.groupby('حالة الدفع').size().values
            sm['إجمالي فوري']=df_acc.groupby('حالة الدفع')[fawry_col].sum().values if fawry_col else 0
            sm['إجمالي Opay']=df_acc.groupby('حالة الدفع')[opay_col].sum().values  if opay_col  else 0
            sm['إجمالي المدفوع']=sm['إجمالي فوري']+sm['إجمالي Opay']
            # المتبقي من _remaining (يعكس المسدد جزئي بشكل صحيح)
            rem_by_status = df_acc.groupby('حالة الدفع')['_remaining'].sum().reset_index()
            rem_by_status.columns = ['حالة الدفع', 'المتبقي']
            sm = sm.merge(rem_by_status, on='حالة الدفع', how='left')
            sm['المتبقي'] = sm['المتبقي'].fillna(0)
            sm.columns=['حالة الدفع','إجمالي المستحق','عدد الأقساط','إجمالي فوري','إجمالي Opay','إجمالي المدفوع','المتبقي']
            for c in ['إجمالي المستحق','إجمالي فوري','إجمالي Opay','إجمالي المدفوع','المتبقي']:
                sm[c]=sm[c].apply(lambda x:f"{x:,.2f}")
            sm['_o']=sm['حالة الدفع'].map(status_order)
            sm=sm.sort_values('_o').drop('_o',axis=1)
            st.dataframe(sm,use_container_width=True,hide_index=True)

    ofc=None
    for c in df_acc.columns:
        if any(k in c.lower() for k in ['officer','مسؤول','مسئول']): ofc=c; break
    if ofc and len(df_acc[ofc].dropna().unique())>0:
        with st.expander("👥 ملخص حسب المسؤول",expanded=False):
            try:
                os_=df_acc.groupby(ofc).agg({inst_col:['sum','count']}).reset_index()
                os_.columns=['اسم المسؤول','إجمالي المستحق','عدد الأقساط']
                if fawry_col:
                    fs=df_acc.groupby(ofc)[fawry_col].sum().reset_index(); fs.columns=['اسم المسؤول','إجمالي فوري']
                    os_=os_.merge(fs,on='اسم المسؤول',how='left'); os_['إجمالي فوري']=os_['إجمالي فوري'].fillna(0)
                else: os_['إجمالي فوري']=0
                if opay_col:
                    ops=df_acc.groupby(ofc)[opay_col].sum().reset_index(); ops.columns=['اسم المسؤول','إجمالي Opay']
                    os_=os_.merge(ops,on='اسم المسؤول',how='left'); os_['إجمالي Opay']=os_['إجمالي Opay'].fillna(0)
                else: os_['إجمالي Opay']=0
                os_['إجمالي المدفوع']=os_['إجمالي فوري']+os_['إجمالي Opay']
                # المتبقي الحقيقي من _remaining
                rem_off = df_acc.groupby(ofc)['_remaining'].sum().reset_index()
                rem_off.columns = ['اسم المسؤول', 'المتبقي']
                os_ = os_.merge(rem_off, on='اسم المسؤول', how='left')
                os_['المتبقي'] = os_['المتبقي'].fillna(0)
                os_['متوسط القسط']=os_['إجمالي المستحق']/os_['عدد الأقساط']
                for c in ['إجمالي المستحق','إجمالي فوري','إجمالي Opay','إجمالي المدفوع','المتبقي','متوسط القسط']:
                    os_[c]=os_[c].apply(lambda x:f"{x:,.2f}")
                os_=os_.sort_values('إجمالي المستحق',ascending=False)
                st.dataframe(os_,use_container_width=True,hide_index=True)
            except Exception as e:
                st.warning(f"تعذر عرض ملخص المسؤولين: {e}")

    st.markdown('<div class="sec-title">📥 تحميل التقرير</div>',unsafe_allow_html=True)
    xls=generate_outstanding_excel(df_acc)
    st.download_button("📊 تحميل Excel ملون",data=xls,
        file_name=f"الاقساط_المستحقة_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ===================================================================
# ===================== الصفحة الرئيسية =====================
# ===================================================================

def main_app():
    if 'user' not in st.session_state:
        # شاشة الدخول
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 100%);
                    border-radius:20px;padding:50px 20px;text-align:center;margin-bottom:30px;">
            <div style="font-size:56px;margin-bottom:10px">📊</div>
            <div style="font-size:28px;font-weight:800;color:white;margin-bottom:6px">نظام كاريتاس</div>
            <div style="color:#93c5fd;font-size:14px">لوحة التقارير والمتابعة</div>
        </div>
        """,unsafe_allow_html=True)
        c1,c2,c3=st.columns([1,1.4,1])
        with c2:
            with st.form("login_form"):
                st.markdown("### 🔐 تسجيل الدخول")
                username=st.text_input("👤 اسم المستخدم",placeholder="أدخل اسم المستخدم")
                password=st.text_input("🔑 كلمة المرور",type="password",placeholder="أدخل كلمة المرور")
                if st.form_submit_button("دخول",use_container_width=True):
                    user=check_login(username,password)
                    if user:
                        st.session_state['user']=user; st.rerun()
                    else:
                        st.error("❌ خطأ في اسم المستخدم أو كلمة المرور")
        return

    user=st.session_state['user']
    show_header(user)

    _,col_out=st.columns([9,1])
    with col_out:
        if st.button("🚪 خروج",use_container_width=True):
            del st.session_state['user']; st.rerun()

    st.markdown(f"""
    <div style="text-align:center;margin:8px 0 28px;">
        <span style="font-size:15px;color:#64748b">
            مرحباً <strong style="color:#1e3a8a">{user['full_name']}</strong> — اختر الخدمة
        </span>
    </div>
    """,unsafe_allow_html=True)

    cols=st.columns(len(PROGRAMS))
    for i,(prog_id,prog) in enumerate(PROGRAMS.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="prog-card">
                <span class="prog-card-icon">{prog['icon']}</span>
                <div class="prog-card-name">{prog['name']}</div>
                <div class="prog-card-desc">{prog['desc']}</div>
                <span class="prog-card-badge">✅ متاح الآن</span>
            </div>
            <div style="height:12px"></div>
            """,unsafe_allow_html=True)
            if st.button(f"فتح — {prog['name']}",key=f"open_{prog_id}",use_container_width=True):
                st.query_params["page"]=prog_id; st.rerun()

    st.markdown("""
    <div style="text-align:center;margin-top:60px;padding:20px;
                color:#94a3b8;font-size:12px;border-top:1px solid #e2e8f0;">
        نظام كاريتاس للتقارير © 2025
    </div>
    """,unsafe_allow_html=True)

# ===================================================================
# ===================== تشغيل التطبيق =====================
# ===================================================================

query_params=st.query_params
page=query_params.get("page","home")

if page!="home" and 'user' not in st.session_state:
    st.warning("⚠️ يجب تسجيل الدخول أولاً")
    if st.button("🔐 تسجيل الدخول"):
        st.query_params.clear(); st.rerun()
    st.stop()

if   page=="home":         main_app()
elif page=="reports":      reports_page()
elif page=="installments": outstanding_page()
else:
    if 'user' in st.session_state: main_app()
    else: st.query_params.clear(); st.rerun()