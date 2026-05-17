import numpy as np
import pandas as pd
import re
import math
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ==========================================
# 0. 網頁基本設定 (必須放在最上方)
# ==========================================
st.set_page_config(
    page_title="全球太陽能發電潛力動態分析系統",
    page_icon="☀️",
    layout="wide"  # 寬螢幕佈局，方便左邊對照表格、右邊看圖表
)

st.title("☀️ 全球太陽能發電潛力動態分析儀表板")
st.markdown("本系統採用**赤緯角公轉模型**與**餘弦幾何修正 (Cosine Correction)**，即時動態評估全球各國的太陽能發電潛能。")

# ==========================================
# 1. 定義清洗與物理修正函式 (加入快取機制優化反應速度)
# ==========================================
def clean_hours(hours_str):
    if pd.isna(hours_str): return 0
    numbers = re.findall(r'\d+', str(hours_str).replace(',', ''))
    if not numbers: return 0
    nums = [int(num) for num in numbers]
    return sum(nums) / len(nums)

def get_solar_correction(latitude, day_of_year):
    lat_rad = math.radians(latitude)
    declination = 23.45 * math.sin(math.radians((360 / 365) * (284 + day_of_year)))
    dec_rad = math.radians(declination)
    correction_factor = math.cos(lat_rad - dec_rad)
    return max(0, correction_factor)

@st.cache_data
def load_and_preprocess():
    """讀取並預處理資料，使用快取避免每次滑動元件都重新讀取 CSV"""
    try:
        df = pd.read_csv("各國家資訊.csv", encoding="utf-8")
        df['日照時數_數值'] = df['年均日照時長 (Hours)'].apply(clean_hours)
        return df
    except Exception as e:
        st.error(f"❌ 數據載入失敗，請確認 '各國家資訊.csv' 是否在同一資料夾下。錯誤資訊: {e}")
        return None

# 載入資料
data = load_and_preprocess()

if data is not None:
    # ==========================================
    # 2. 側邊欄控制面板 (取代原本終端機的 input)
    # ==========================================
    st.sidebar.header("⚙️ 模擬參數調整")
    
    # 動態模擬天數滑桿
    target_day = st.sidebar.slider(
        "📅 選擇一年中的第幾天 (Day of Year)", 
        min_value=1, 
        max_value=365, 
        value=172,
        help="提示：春分(80)、夏至(172)、秋分(264)、冬至(355)"
    )
    
    # 動態排名數量輸入框
    top_n = st.sidebar.number_input(
        "📊 欲顯示與繪製的排行榜名次數量", 
        min_value=1, 
        max_value=len(data), 
        value=10
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("💡 **固定物理參數設定：**\n- 面板面積：1 $m^2$\n- 光電轉換效率：18%\n- 系統性能比 (PR)：75%")

    # ==========================================
    # 3. 核心物理運算與排序
    # ==========================================
    panel_area = 1   
    efficiency = 0.18
    pr = 0.75

    # 帶入動態設定的 target_day 進行幾何修正與計算
    processed_data = data.copy()
    processed_data['角度修正係數'] = processed_data['緯度 (Latitude)'].apply(lambda x: get_solar_correction(x, target_day))
    processed_data['修正後日發電預估_kWh'] = (processed_data['日照時數_數值'] / 365) * panel_area * efficiency * pr * processed_data['角度修正係數']
    
    # 排序並取出前 N 名
    df_result = processed_data.sort_values(by='修正後日發電預估_kWh', ascending=False)
    top_data = df_result.head(top_n)

    # ==========================================
    # 4. 主畫面佈局設計：左側表格，右側圖表
    # ==========================================
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader(f"🏆 發電潛力排行榜 (Top {top_n})")
        display_cols = ['國家名稱', '緯度 (Latitude)', '角度修正係數', '修正後日發電預估_kWh']
        # 使用 st.dataframe 呈現精美的網頁資料表
        st.dataframe(
            top_data[display_cols].style.format({
                '角度修正係數': '{:.4f}',
                '修正後日發電預估_kWh': '{:.3f} kWh'
            }),
            use_container_width=True
        )
        
    with col2:
        st.subheader("📊 數據視覺化長條圖")
        
        # 設定字體防止中文亂碼
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
        plt.rcParams['axes.unicode_minus'] = False 
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            x='修正後日發電預估_kWh', 
            y='國家名稱', 
            data=top_data, 
            palette='YlOrRd_r', 
            hue='國家名稱', 
            legend=False,
            ax=ax
        )
        ax.set_title(f'全球前 {top_n} 名太陽能發電潛力國家 (第 {target_day} 天模擬)', fontsize=14, fontweight='bold')
        ax.set_xlabel('每日預計發電量 (kWh/m²)', fontsize=11)
        ax.set_ylabel('國家名稱', fontsize=11)
        
        # 在長條末端顯示數值
        for i, v in enumerate(top_data['修正後日發電預估_kWh']):
            ax.text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=9)
            
        plt.tight_layout()
        # 關鍵：將圖表渲染至 Streamlit 網頁畫面上
        st.pyplot(fig)

    # ==========================================
    # 5. 網頁版互動式搜尋模組 (取代原本的 while 迴圈)
    # ==========================================
    st.markdown("---")
    st.subheader("🔍 國家數據即時搜尋系統")
    
    # 網頁輸入框，當字串有變更時會即時啟動下方搜尋
    search_input = st.text_input("請輸入想查詢的國家名稱關鍵字（例如：台灣、Egypt，留空則不顯示）：").strip()
    
    if search_input:
        search_results = df_result[df_result['國家名稱'].str.contains(search_input, na=False, case=False)]
        
        if not search_results.empty:
            st.success(f"✅ 找到 {len(search_results)} 筆相符的國家資料：")
            
            for _, row in search_results.iterrows():
                # 使用展開摺疊面板呈顯各國詳細報告
                with st.expander(f"🌍 詳細數據報告：{row['國家名稱']}"):
                    # 建立三欄式網頁指標卡片
                    m1, m2, m3 = st.columns(3)
                    m1.metric("地理座標", f"緯度 {row['緯度 (Latitude)']}°")
                    m2.metric("角度修正係數", f"{row['角度修正係數']:.4f}")
                    m3.metric("預估日發電量", f"{row['修正後日發電預估_kWh']:.3f} kWh/m²")
                    
                    # 結合計算平均值進行動態分析
                    avg_val = df_result['修正後日發電預估_kWh'].mean()
                    if row['修正後日發電預估_kWh'] > avg_val:
                        st.markdown("**💡 綜合評估狀態：** 🟢 高於全球當前模擬平均值")
                    else:
                        st.markdown("**💡 綜合評估狀態：** 🔴 低於全球當前模擬平均值")
                    
                    # 基於目前模擬溫和呈現物理評語
                    if row['角度修正係數'] > 0.9:
                        st.caption(f"物理分析：該國在第 {target_day} 天的地理幾何夾角極佳，幾何能量損耗極小。")
                    elif row['角度修正係數'] < 0.5:
                        st.caption(f"物理分析：該國在第 {target_day} 天的太陽入射夾角偏低，大氣路徑與幾何損失嚴重。")
        else:
            st.error(f"❌ 找不到與 '{search_input}' 相關的國家，請重新輸入。")
            
    # ==========================================
    # 6. 背景同步儲存至桌面 (保留本地執行時的存圖功能)
    # ==========================================
    def get_desktop_path():
        home = os.path.expanduser("~")
        candidates = [os.path.join(home, "Desktop"), os.path.join(home, "OneDrive", "Desktop"), os.path.join(home, "OneDrive", "桌面")]
        for path in candidates:
            if os.path.exists(path): return path
        return home

    try:
        full_save_path = os.path.join(get_desktop_path(), f"太陽能排行_第{target_day}天.png")
        fig.savefig(full_save_path, dpi=150)
    except:
        pass