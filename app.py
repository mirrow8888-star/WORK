import io

import pandas as pd
import requests
import streamlit as st
import urllib3

# verify=False 會產生警告,這裡關閉警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_URL = "https://data.tainan.gov.tw/File/ResourceCsvDownload/24b8d897-7971-45f9-8489-b4918ee41ed7"  # 換連結

st.set_page_config(page_title="臺南市政府資料開放平臺", layout="wide")
st.title("📊 臺南市政府開放資料檢視器")


@st.cache_data(ttl=3600, show_spinner="資料下載中...")
def load_data(url: str) -> pd.DataFrame:
    response = requests.get(url, verify=False, timeout=30)
    response.raise_for_status()
    # 先用 utf-8-sig(繁體中文),失敗時依序嘗試 big5 / cp950
    for enc in ("utf-8-sig", "big5", "cp950"):
        try:
            df = pd.read_csv(io.BytesIO(response.content), encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("無法判斷 CSV 編碼")
    return df.dropna()


# ---------- 側邊欄 ----------
with st.sidebar:
    st.header("設定")
    url = st.text_input("CSV 連結", value=DEFAULT_URL)
    if st.button("🔄 重新載入資料"):
        st.cache_data.clear()
        st.rerun()

# ---------- 載入資料 ----------
try:
    df = load_data(url.strip())
except Exception as e:
    st.error(f"資料載入失敗:{e}")
    st.stop()

if df.empty:
    st.warning("資料在移除空值(dropna)後為空,請確認連結或資料內容。")
    st.stop()

# ---------- 關鍵字搜尋 ----------
keyword = st.text_input("🔍 關鍵字搜尋(搜尋所有欄位)")
if keyword:
    mask = (
        df.astype(str)
        .apply(lambda col: col.str.contains(keyword, case=False, regex=False))
        .any(axis=1)
    )
    view = df[mask]
else:
    view = df

# ---------- 顯示 ----------
c1, c2 = st.columns(2)
c1.metric("符合筆數", f"{len(view):,}")
c2.metric("欄位數", len(view.columns))

st.dataframe(view, use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ 下載 CSV",
    data=view.to_csv(index=False).encode("utf-8-sig"),
    file_name="data01.csv",
    mime="text/csv",
)
