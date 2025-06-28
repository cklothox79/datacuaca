import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import json
import os
from matplotlib.backends.backend_pdf import PdfPages

# 🛠️ Setup halaman
st.set_page_config(layout="wide")
st.title("📊 Visualisasi Curah Hujan Jawa Timur (2020–2024)")
st.markdown("### 👨‍💻 Editor: Ferri Kusuma (M8TB_14.22.0003)")

# 🔗 URL CSV
CSV_URL = "https://raw.githubusercontent.com/cklothox79/datacuaca/refs/heads/main/CH_SdaMjkSby_20202024.csv"

# 📁 Buat folder grafik jika belum ada
if not os.path.exists("grafik"):
    os.makedirs("grafik")

# 📥 Fungsi muat data
@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    df.rename(columns={
        'date': 'date',
        'mean': 'rainfall_mm',
        'name': 'location',
        '.geo': 'geo'
    }, inplace=True)

    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['month_name'] = df['date'].dt.strftime('%B')

    df['lat'] = df['geo'].apply(lambda x: json.loads(x)['coordinates'][1])
    df['lon'] = df['geo'].apply(lambda x: json.loads(x)['coordinates'][0])

    df = df.sort_values(by='date')
    return df

# 🔄 Load data
df = load_data(CSV_URL)
st.success("✅ Data berhasil dimuat!")

# 🔍 Sidebar filter
st.sidebar.header("🎚️ Filter Data")
locations = df['location'].unique()
years = sorted(df['year'].unique())

selected_locations = st.sidebar.multiselect("📍 Pilih Lokasi:", locations, default=list(locations))
selected_years = st.sidebar.multiselect("📅 Pilih Tahun:", years, default=years)

# Opsional: filter mingguan
st.sidebar.markdown("🗓️ Filter Mingguan (opsional)")
week_start = st.sidebar.date_input("Dari", pd.to_datetime("2020-01-01"))
week_end = st.sidebar.date_input("Sampai", pd.to_datetime("2024-12-31"))

df_filtered = df[
    (df['location'].isin(selected_locations)) &
    (df['year'].isin(selected_years)) &
    (df['date'] >= pd.to_datetime(week_start)) &
    (df['date'] <= pd.to_datetime(week_end))
]

# 📋 Tabel data
st.subheader("📋 Tabel Curah Hujan")
st.dataframe(df_filtered[['date', 'location', 'rainfall_mm']], use_container_width=True)

# 📈 Grafik Harian
st.subheader("📈 Grafik Harian")
fig1, ax1 = plt.subplots(figsize=(12, 4))
for loc in selected_locations:
    df_loc = df_filtered[df_filtered['location'] == loc]
    ax1.plot(df_loc['date'], df_loc['rainfall_mm'], label=loc)
ax1.set_ylabel("Curah Hujan (mm)")
ax1.set_title("Curah Hujan Harian")
ax1.grid(True)
ax1.legend()
st.pyplot(fig1)

# 📊 Grafik Bulanan
st.subheader("📊 Rata-rata Bulanan per Lokasi")
monthly_avg = df_filtered.groupby(['location', 'month'])['rainfall_mm'].mean().reset_index()
monthly_avg['month_name'] = monthly_avg['month'].apply(lambda x: pd.to_datetime(f"2024-{x:02d}-01").strftime('%B'))

month_order = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
monthly_avg['month_name'] = pd.Categorical(monthly_avg['month_name'], categories=month_order, ordered=True)
monthly_avg = monthly_avg.sort_values('month_name')

pivot_month = monthly_avg.pivot(index='month_name', columns='location', values='rainfall_mm')
fig2, ax2 = plt.subplots(figsize=(12, 4))
pivot_month.plot(kind='bar', ax=ax2)
ax2.set_ylabel("Curah Hujan (mm)")
ax2.set_title("Rata-rata Bulanan")
plt.xticks(rotation=45)
st.pyplot(fig2)

# 📅 Grafik Tahunan
st.subheader("📆 Rata-rata Tahunan per Lokasi")
yearly_avg = df_filtered.groupby(['location', 'year'])['rainfall_mm'].mean().reset_index()
pivot_year = yearly_avg.pivot(index='year', columns='location', values='rainfall_mm')
fig3, ax3 = plt.subplots(figsize=(10, 4))
pivot_year.plot(marker='o', ax=ax3)
ax3.set_ylabel("Curah Hujan (mm)")
ax3.set_title("Rata-rata Tahunan")
st.pyplot(fig3)

# ⚠️ Deteksi Hari Ekstrem
st.subheader("🌧️ Hari-Hari dengan Curah Hujan Ekstrem (> 50 mm)")
extreme_rain = df_filtered[df_filtered['rainfall_mm'] > 50]
st.dataframe(extreme_rain[['date', 'location', 'rainfall_mm']])
if not extreme_rain.empty:
    st.warning("🚨 Terdapat hari dengan hujan ekstrem!")
    st.markdown("- Periksa drainase dan sistem peringatan dini.")
    st.markdown("- Siapkan evakuasi bila rawan banjir.")
else:
    st.success("✅ Tidak ada hari dengan hujan ekstrem.")

# 🗺️ Peta Lokasi
st.subheader("🗺️ Lokasi Stasiun")
m = folium.Map(location=[-7.35, 112.6], zoom_start=9)
for loc in selected_locations:
    sample = df_filtered[df_filtered['location'] == loc].iloc[0]
    folium.Marker(
        location=[sample['lat'], sample['lon']],
        popup=loc,
        tooltip=loc,
        icon=folium.Icon(color="blue", icon="cloud")
    ).add_to(m)
st_folium(m, width=700)

# 📤 Ekspor PDF Otomatis
st.subheader("🧾 Ekspor Grafik ke PDF")
pdf_path = "grafik/laporan_curah_hujan.pdf"
with PdfPages(pdf_path) as pdf:
    pdf.savefig(fig1)
    pdf.savefig(fig2)
    pdf.savefig(fig3)
st.download_button("📄 Unduh PDF Grafik", open(pdf_path, "rb"), file_name="laporan_curah_hujan.pdf")

# 📥 Unduh Data CSV
st.subheader("⬇️ Unduh Data")
csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button("📥 Unduh CSV", data=csv, file_name='curah_hujan_terfilter.csv', mime='text/csv')
