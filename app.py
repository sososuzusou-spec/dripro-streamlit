import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

st.set_page_config(page_title="Sales App", page_icon="📈", layout="wide")

# --- Secretsから認証情報とシートURLを取得 ---
info = st.secrets["gcp_service_account"]
SHEET_URL = st.secrets["SHEET_URL"]

# --- Google Sheets 接続 ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(info, scopes=SCOPES)
gc = gspread.authorize(creds)

sh = gc.open_by_url(SHEET_URL)
ws_titles = [w.title for w in sh.worksheets()]
ws = sh.worksheet("sales") if "sales" in ws_titles else sh.add_worksheet("sales", rows=1000, cols=10)

headers = ["date","event","product","qty","unit_price","amount"]
try:
    if ws.acell("A1").value != "date":
        ws.update("A1", [headers])
except:
    ws.update("A1", [headers])

st.title("📈 Sales Entry & Dashboard")

with st.form("entry", clear_on_submit=True):
    c1, c2, c3, c4, c5 = st.columns([1,2,2,1,1])
    d = c1.date_input("日付", value=date.today())
    event = c2.text_input("イベント名", placeholder="フェアトレードフェス")
    product = c3.text_input("商品名", placeholder="ギフトセットA")
    qty = c4.number_input("数量", min_value=1, step=1, value=1)
    unit = c5.number_input("単価（円）", min_value=0, step=1, value=1000)
    submitted = st.form_submit_button("登録")
    if submitted:
        if not event.strip() or not product.strip():
            st.error("イベント名と商品名は必須です")
        else:
            amount = int(qty) * int(unit)
            ws.append_row([d.isoformat(), event.strip(), product.strip(), int(qty), int(unit), amount])
            st.success("登録しました！")

records = ws.get_all_records()
df = pd.DataFrame(records) if records else pd.DataFrame(columns=headers)
if not df.empty:
    df["date"] = pd.to_datetime(df["date"])

st.subheader("ダッシュボード")
k1, k2, k3 = st.columns(3)
total = int(df["amount"].sum()) if not df.empty else 0
events = df["event"].nunique() if not df.empty else 0
items = df["product"].nunique() if not df.empty else 0
k1.metric("合計売上", f"{total:,} 円")
k2.metric("イベント数", events)
k3.metric("商品数", items)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**イベント別 売上合計**")
    if not df.empty:
        st.bar_chart(df.groupby("event")["amount"].sum().sort_values(ascending=False))
    else:
        st.info("データがありません")

with c2:
    st.markdown("**日次 売上推移**")
    if not df.empty:
        day = df.groupby("date")["amount"].sum().sort_index()
        st.line_chart(day)
    else:
        st.info("データがありません")

st.divider()
st.markdown("**明細（ダウンロード可）**")
st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)
st.download_button(
    "CSVダウンロード",
    (df.sort_values("date", ascending=False)).to_csv(index=False).encode("utf-8-sig"),
    "sales_export.csv",
    "text/csv"
)
