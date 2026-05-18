import pandas as pd
import re
import math
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Load and clean data
df = pd.read_csv("各國家資訊.csv")

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

df['日照時數_平均'] = df['年均日照時長 (Hours)'].apply(clean_hours)
target_day = 172
df['角度修正係數'] = df['緯度 (Latitude)'].apply(lambda x: get_solar_correction(x, target_day))
df['修正後日發電預估_kWh'] = (df['日照時數_平均'] / 365) * 1 * 0.18 * 0.75 * df['角度修正係數']

top_10 = df.sort_values(by='修正後日發電預估_kWh', ascending=False).head(10)

# Set plotting style
sns.set_theme(style="whitegrid")

# Set font for matplotlib
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

# Establish figure and ax object, set DPI for high quality
fig, ax = plt.subplots(figsize=(12, 8), dpi=150)

# Corrected seaborn call to avoid FutureWarning
plot = sns.barplot(
    x='修正後日發電預估_kWh', 
    y='國家名稱', 
    data=top_10, 
    palette='YlOrRd_r',
    hue='國家名稱',
    legend=False,
    ax=ax
)

ax.set_title('Top 10 Countries for Solar Potential (Summer Solstice Simulation)', fontsize=16)
ax.set_xlabel('Estimated Daily Energy Production (kWh/m²)', fontsize=14)
ax.set_ylabel('Country Name', fontsize=14)

# Set fontsize of y-axis and x-axis labels
ax.tick_params(axis='y', labelsize=12)
ax.tick_params(axis='x', labelsize=12)

# Add text labels on bars
for i, v in enumerate(top_10['修正後日發電預估_kWh']):
    ax.text(v + 0.005, i, f'{v:.3f}', va='center', fontsize=12)

plt.tight_layout()

# Streamlit to render image
st.pyplot(fig)