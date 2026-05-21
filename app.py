
import numpy as np
import pandas as pd
import re
import math
import streamlit as st

# 讀取 CSV 檔案
try:
    data = pd.read_csv("各國家資訊.csv", encoding="utf-8")
    print(" 成功載入資料！")
except Exception as e:
    print(f" 載入失敗: {e}")

# 定義清洗與物理修正函式
def clean_hours(hours_str):
    if pd.isna(hours_str): return 0
    numbers = re.findall(r'\d+', str(hours_str).replace(',', ''))
    if not numbers: return 0
    nums = [int(num) for num in numbers]
    return sum(nums) / len(nums)

def get_solar_correction(latitude, day_of_year):
    lat_rad = math.radians(latitude)
    # 赤緯角公式：23.45 * sin( (360/365) * (284 + n) )
    declination = 23.45 * math.sin(math.radians((360 / 365) * (284 + day_of_year)))
    decl_rad = math.radians(declination)
    # 餘弦修正 (Cosine Correction)
    correction_factor = math.cos(lat_rad - decl_rad)
    return max(0, correction_factor)

data['日照時數_數值'] = data['年均日照時長 (Hours)'].apply(clean_hours)

# 設定模擬參數：夏至、1平方米面板、18%效率、75%性能比
target_day = 172 # 夏至
panel_area = 1   # 1平方米
efficiency = 0.18
pr = 0.75

data['角度修正係數'] = data['緯度 (Latitude)'].apply(lambda x: get_solar_correction(x, target_day))

# 公式：(年總時數/365) * 面積 * 效率 * PR * 角度修正
data['修正後日發電預估_kWh'] = (data['日照時數_數值'] / 365) * panel_area * efficiency * pr * data['角度修正係數']

df_result = data.sort_values(by='修正後日發電預估_kWh', ascending=False)

print("\n--- 各國家太陽能發電潛力排名 (前10名) ---")
# 選擇要顯示的欄位，確保這些欄位都在 data 中
output_cols = ['國家名稱', '緯度 (Latitude)', '角度修正係數', '修正後日發電預估_kWh']
print(df_result[output_cols].head(10))


import matplotlib.pyplot as plt
import seaborn as sns
import os  # 內建模處處理路徑

#定義 top_10 (取排序後的前十名)
top_10 = df_result.head(10)

# 設定字體防止中文亂碼 (Windows 常用字體)
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False 

plt.figure(figsize=(12, 7))

# 修正：x 軸名稱必須對應你上面定義的 '修正後日發電預估_kWh'
sns.barplot(
    x='修正後日發電預估_kWh', 
    y='國家名稱', 
    data=top_10, 
    palette='YlOrRd_r', 
    hue='國家名稱', 
    legend=False
)

plt.title('全球前 10 名太陽能發電潛力國家 (考慮幾何修正)', fontsize=15)
plt.xlabel('每日預計發電量 (kWh/m²)', fontsize=12)
plt.ylabel('國家名稱', fontsize=12)

# 在長條末端顯示數值
for i, v in enumerate(top_10['修正後日發電預估_kWh']):
    plt.text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=10)

plt.tight_layout()

# 儲存與顯示
plt.savefig('太陽能排行.png', dpi=300)
print("✅ 圖片已成功儲存為 '太陽能排行.png'")

# 取得桌面路徑
def get_desktop_path():
    home = os.path.expanduser("~")
    
    # 候選路徑列表
    candidates = [
        os.path.join(home, "Desktop"),                   # 標準路徑
        os.path.join(home, "OneDrive", "Desktop"),       # OneDrive 英文路徑
        os.path.join(home, "OneDrive", "桌面"),          # OneDrive 中文路徑
    ]
    
    for path in candidates:
        if os.path.exists(path):
            return path
    return home # 如果都找不到，最後保險存到使用者根目錄

# 取得正確的儲存完整路徑
target_desktop = get_desktop_path()
full_save_path = os.path.join(target_desktop, "太陽能排行.png")

# 執行儲存
plt.savefig(full_save_path, dpi=300)
print(f"圖片已成功儲存至桌面！")
print(f"檔案位置：{full_save_path}")

def search_country_data(df):
    print("\n" + "="*30)
    target = input("🔍 請輸入想查詢的國家名稱（支援關鍵字搜尋，輸入 'q' 退出）: ").strip()
    
    if target.lower() == 'q':
        return

    # 使用 str.contains 進行模糊搜尋，na=False 避免空值報錯
    results = df[df['國家名稱'].str.contains(target, na=False, case=False)]

    if results.empty:
        print(f"❌ 找不到包含 '{target}' 的國家資訊，請檢查拼字或嘗試其他關鍵字。")
    else:
        print(f"\n✅ 找到 {len(results)} 筆相關結果：")
        # 整理輸出資訊
        for _, row in results.iterrows():
            print("-" * 20)
            print(f"國家名稱：{row['國家名稱']}")
            print(f"地理座標：緯度 {row['緯度 (Latitude)']}°")
            print(f"角度修正係數：{row['角度修正係數']:.4f}")
            print(f"預估日發電量：{row['修正後日發電預估_kWh']:.3f} kWh/m²")
            
            # 計算相對於平均值的強弱
            avg_val = df['修正後日發電預估_kWh'].mean()
            if row['修正後日發電預估_kWh'] > avg_val:
                print(" 評估結果：該地區發電潛力高於全球平均。")
            else:
                print(" 評估結果：該地區發電潛力低於全球平均。")


#search_term = st.text_input("輸入國家名稱進行查詢")
#if search_term:
#   search_res = df_result[df_result['國家名稱'].str.contains(search_term)]
#    st.write(search_res[['國家名稱', '緯度 (Latitude)', '修正後日發電預估_kWh']])

def start_interactive_search(df):
    print("\n" + "-" * 40)
    print(" 歡迎使用全球太陽能數據查詢系統")
    print(" 輸入『國家名稱關鍵字』進行查詢")
    print(" 輸入 'all' 顯示目前排行榜前 n 名")
    print(" 輸入 'q' 或 'exit' 結束程式")
    print("-" * 40)

    while True:
        user_input = input("\n 請輸入查詢指令: ").strip()

        # 退出機制
        if user_input.lower() in ['q', 'exit']:
            print(" 感謝使用，程式已結束。")
            break
        
        # 顯示前 n 名，預設為 10 名
        elif user_input.lower() == 'all':
            try :
                top_n = int(input(" 您想顯示/繪製前幾名的國家排名？ (例如輸入 5 或 15) "))
                if top_n <= 0: top_n = 10
            except ValueError:
                print("輸入格式錯誤，已預設顯示前 10 名")
                top_n = 10
            print(df[['國家名稱', '緯度 (Latitude)', '修正後日發電預估_kWh']].head(top_n).to_string(index=False))
            continue

        # 關鍵字搜尋邏輯
        else:
            # 使用 contains 進行模糊搜尋，na=False 防止空值報錯
            results = df[df['國家名稱'].str.contains(user_input, na=False, case=False)]

            if not results.empty:
                print(f"\n 找到 {len(results)} 筆相關結果：")
                for i, row in results.iterrows():
                    print(f"----------------------------------------")
                    print(f"【 {row['國家名稱']} 】")
                    print(f"  ▸ 緯度位置: {row['緯度 (Latitude)']}°")
                    print(f"  ▸ 角度修正: {row['角度修正係數']:.4f} (基於夏至模擬)")
                    print(f"  ▸ 日發電量: {row['修正後日發電預估_kWh']:.3f} kWh/m²")
                    
                    # 分析
                    if row['角度修正係數'] > 0.9:
                        print(" 注意 : 該國地理位置極佳，受入射角損失極小。")
                    elif row['角度修正係數'] < 0.6:
                        print(" 注意 : 緯度較高，入射角導致能量大幅損失。")
            else:
                print(f" 找不到與 '{user_input}' 相關的國家，請嘗試其他關鍵字（例如：台灣、Egypt）。")
start_interactive_search(df_result)



import numpy as np
import pandas as pd
import re
import math
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import os  # 內建模組處理路徑

# 讀取 CSV 檔案
try:
    data = pd.read_csv("各國家資訊.csv", encoding="utf-8")
    print(" 成功載入資料！")
except Exception as e:
    print(f" 載入失敗: {e}")

# 定義清洗與物理修正函式
def clean_hours(hours_str):
    if pd.isna(hours_str): return 0
    numbers = re.findall(r'\d+', str(hours_str).replace(',', ''))
    if not numbers: return 0
    nums = [int(num) for num in numbers]
    return sum(nums) / len(nums)

def get_solar_correction(latitude, day_of_year):
    lat_rad = math.radians(latitude)
    # 赤緯角公式：23.45 * sin( (360/365) * (284 + n) )
    declination = 23.45 * math.sin(math.radians((360 / 365) * (284 + day_of_year)))
    dec_rad = math.radians(declination)
    # 餘弦修正 (Cosine Correction)
    correction_factor = math.cos(lat_rad - dec_rad)
    return max(0, correction_factor)

# 資料清洗
data['日照時數_數值'] = data['年均日照時長 (Hours)'].apply(clean_hours)

# ==========================================
# 新增：互動式參數設定（動態天數與自訂排名）
# ==========================================
print("\n" + "="*40)
print(" 請設定太陽能模擬參數")
print(" 提示：常規節氣天數參考 —— 春分(80)、夏至(172)、秋分(264)、冬至(355)")
print("="*40)

# 動態模擬天數輸入與防呆
try:
    target_day = int(input(" 請輸入模擬的一年中第幾天 (1 ~ 365): "))
    if not (1 <= target_day <= 365):
        print(" 日期超出範圍（必須在 1~365 之間），已自動預設為夏至 (172)")
        target_day = 172
except ValueError:
    print("輸入格式錯誤，已自動預設為夏至 (172)")
    target_day = 172

# 動態排名數量輸入與防呆
try:
    top_n = int(input("您想顯示/繪製前幾名的國家排名？ (例如輸入 5 或 15): "))
    if top_n <= 0:
        print("數量必須大於 0，已預設顯示前 10 名")
        top_n = 10
except ValueError:
    print("輸入格式錯誤，已預設顯示前 10 名")
    top_n = 10

# 設定固定物理參數：1平方米面板、18%效率、75%性能比
panel_area = 1   # 1平方米
efficiency = 0.18
pr = 0.75

# 帶入動態設定的 target_day 進行幾何修正
data['角度修正係數'] = data['緯度 (Latitude)'].apply(lambda x: get_solar_correction(x, target_day))

# 核心公式計算
data['修正後日發電預估_kWh'] = (data['日照時數_數值'] / 365) * panel_area * efficiency * pr * data['角度修正係數']

# 重新排序數據
df_result = data.sort_values(by='修正後日發電預估_kWh', ascending=False)

# 根據使用者設定的 top_n 擷取資料區段
top_data = df_result.head(top_n)

print(f"\n--- 各國家太陽能發電潛力排名 (前 {top_n} 名 / 第 {target_day} 天模擬) ---")
output_cols = ['國家名稱', '緯度 (Latitude)', '角度修正係數', '修正後日發電預估_kWh']
print(top_data[output_cols].to_string(index=False))


# ==========================================
#  視覺化圖表調整 (同步連動 top_n 與 target_day)
# ==========================================
#  設定字體防止中文亂碼 (Windows 常用字體)
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False 

plt.figure(figsize=(12, 7))

#  使用動態擷取的 top_data 進行繪圖
sns.barplot(
    x='修正後日發電預估_kWh', 
    y='國家名稱', 
    data=top_data, 
    palette='YlOrRd_r', 
    hue='國家名稱', 
    legend=False
)

# 讓圖表標題動態反映模擬天數與名次
plt.title(f'全球前 {top_n} 名太陽能發電潛力國家 (一年中第 {target_day} 天模擬)', fontsize=15, fontweight='bold')
plt.xlabel('每日預計發電量 (kWh/m²)', fontsize=12)
plt.ylabel('國家名稱', fontsize=12)

# 在長條末端顯示數值
for i, v in enumerate(top_data['修正後日發電預估_kWh']):
    plt.text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=10)

plt.tight_layout()

# 儲存與顯示
plt.savefig('太陽能排行.png', dpi=300)
print("\n 圖片已成功儲存為 '太陽能排行.png'")

# 取得桌面路徑
def get_desktop_path():
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, "Desktop"),                   # 標準路徑
        os.path.join(home, "OneDrive", "Desktop"),       # OneDrive 英文路徑
        os.path.join(home, "OneDrive", "桌面"),          # OneDrive 中文路徑
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return home 

# 取得正確的儲存完整路徑 (檔名同步加上天數區隔，避免多次實驗被覆蓋)
target_desktop = get_desktop_path()
full_save_path = os.path.join(target_desktop, f"太陽能排行_第{target_day}天.png")

# 執行儲存到桌面
plt.savefig(full_save_path, dpi=300)
print(f"圖片已成功儲存至桌面！")
print(f"檔案位置：{full_save_path}")


# ==========================================
#  搜尋模組 (同步更新全域變數對應)
# ==========================================
def search_country_data(df):
    print("\n" + "="*30)
    target = input("🔍 請輸入想查詢的國家名稱（支援關鍵字搜尋，輸入 'q' 退出）: ").strip()
    
    if target.lower() == 'q':
        return

    results = df[df['國家名稱'].str.contains(target, na=False, case=False)]

    if results.empty:
        print(f"❌ 找不到包含 '{target}' 的國家資訊，請檢查拼字或嘗試其他關鍵字。")
    else:
        print(f"\n 找到 {len(results)} 筆相關結果：")
        for _, row in results.iterrows():
            print("-" * 20)
            print(f"國家名稱：{row['國家名稱']}")
            print(f"地理座標：緯度 {row['緯度 (Latitude)']}°")
            print(f"角度修正係數：{row['角度修正係數']:.4f}")
            print(f"預估日發電量：{row['修正後日發電預估_kWh']:.3f} kWh/m²")
            
            avg_val = df['修正後日發電預估_kWh'].mean()
            if row['修正後日發電預估_kWh'] > avg_val:
                print(" 評估結果：該地區發電潛力高於全球平均。")
            else:
                print(" 評估結果：該地區發電潛力低於全球平均。")

def start_interactive_search(df):
    print("\n" + "-" * 40)
    print(f" 歡迎使用全球太陽能數據查詢系統 (當前模擬：第 {target_day} 天)")
    print(" 輸入『國家名稱關鍵字』進行查詢")
    print(f" 輸入 'all' 顯示目前排行榜前 {top_n} 名")
    print(" 輸入 'q' 或 'exit' 結束程式")
    print("-" * 40)

    while True:
        user_input = input("\n 請輸入查詢指令: ").strip()

        # 退出機制
        if user_input.lower() in ['q', 'exit']:
            print(" 感謝使用，程式已結束。")
            break
        
        # 顯示前 N 名 (與使用者設定的 top_n 連動)
        elif user_input.lower() == 'all':
            print(f"\n 目前太陽能發電潛力前 {top_n} 名：")
            print(df[['國家名稱', '緯度 (Latitude)', '修正後日發電預估_kWh']].head(top_n).to_string(index=False))
            continue

        # 關鍵字搜尋邏輯
        else:
            results = df[df['國家名稱'].str.contains(user_input, na=False, case=False)]

            if not results.empty:
                print(f"\n 找到 {len(results)} 筆相關結果：")
                for i, row in results.iterrows():
                    print(f"----------------------------------------")
                    print(f"【 {row['國家名稱']} 】")
                    print(f"  ▸ 緯度位置: {row['緯度 (Latitude)']}°")
                    print(f"  ▸ 角度修正: {row['角度修正係數']:.4f} (基於第 {target_day} 天模擬)")
                    print(f"  ▸ 日發電量: {row['修正後日發電預估_kWh']:.3f} kWh/m²")
                    
                    # 基於動態修正係數的物理評語
                    if row['角度修正係數'] > 0.9:
                        print(" 注意 : 該國此時地理幾何夾角極佳，受入射角損失極小。")
                    elif row['角度修正係數'] < 0.5:
                        print(" 注意 : 此季節該國太陽入射夾角偏低，大氣與幾何損失嚴重。")
            else:
                print(f" 找不到與 '{user_input}' 相關的國家，請嘗試其他關鍵字（例如：台灣、Egypt）。")

# 啟動互動搜尋
start_interactive_search(df_result)


