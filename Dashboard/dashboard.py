import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static


def load_data():
    dataframes = {
        "Customers": pd.read_csv("../data/customers_dataset.csv"),
        "Geolocation": pd.read_csv("../data/geolocation_dataset.csv"),
        "Order Items": pd.read_csv("../data/order_items_dataset.csv"),
        "Order Payments": pd.read_csv("../data/order_payments_dataset.csv"),
        "Order Reviews": pd.read_csv("../data/order_reviews_dataset.csv"),
        "Orders": pd.read_csv("../data/orders_dataset.csv"),
        "Product Category": pd.read_csv("../data/product_category_name_translation.csv"),
        "Products": pd.read_csv("../data/products_dataset.csv"),
        "Sellers": pd.read_csv("../data/sellers_dataset.csv"),
    }
    return dataframes


def clean_data(dataframes):
    cleaned_dataframes = {}
    
    for name, df in dataframes.items():
        df = df.copy()

        
        df.drop_duplicates(inplace=True)

        
        for col in df.columns:
            if df[col].isnull().sum() > 0:
                if df[col].dtype == "object":
                    df.dropna(subset=[col], inplace=True)  
                else:
                    df[col].fillna(df[col].mean(), inplace=True)  

        
        for col in df.select_dtypes(include=np.number).columns:
            data = df[col].dropna()  
            if len(data) > 0:
                q25, q75 = np.percentile(data, 25), np.percentile(data, 75)
                iqr = q75 - q25
                cut_off = iqr * 1.5  
                minimum, maximum = q25 - cut_off, q75 + cut_off
                df[col] = df[col].mask((df[col] < minimum) | (df[col] > maximum), maximum)  

        
        cleaned_dataframes[name] = df
        
    return cleaned_dataframes


def perform_eda(cleaned_dataframes):
    if not cleaned_dataframes:
        return "Dataset yang diperlukan untuk analisis ini belum tersedia."
    
    all_df = pd.merge(
        left=cleaned_dataframes["Customers"],
        right=cleaned_dataframes["Orders"],
        how="inner",
        left_on="customer_id",
        right_on="customer_id"
    )

    rating_state = pd.merge(
        left=all_df,
        right=cleaned_dataframes["Order Reviews"],
        how="inner",
        left_on="order_id",
        right_on="order_id"
    )

    
    state_review_analysis = rating_state.groupby("customer_state")["review_score"].mean().reset_index()
    state_review_analysis = state_review_analysis.sort_values(by="review_score", ascending=False)

    
    products_state = pd.merge(
        left=rating_state,
        right=cleaned_dataframes["Order Items"],
        how="inner",
        left_on="order_id",
        right_on="order_id"
    )

    products_state = pd.merge(
        left=products_state,
        right=cleaned_dataframes["Products"],
        how="inner",
        left_on="product_id",
        right_on="product_id"
    )

    state_products_analysis = products_state.groupby(["customer_state", "product_category_name"]).size().reset_index(name="total_purchases")
    top_product_per_state = state_products_analysis.loc[state_products_analysis.groupby("customer_state")["total_purchases"].idxmax()]

    return state_review_analysis, top_product_per_state



def display_dataframes(dataframes):
    for name, df in dataframes.items():
        st.subheader(f"{name} Dataset")
        st.dataframe(df.head())

def display_eda_results(state_review_analysis, top_product_per_state):
    tab1, tab2 = st.tabs(["Pertanyaan 1", "Pertanyaan 2"])

    
    with tab1:
        st.subheader("Rata-rata Rating per Negara")
        st.dataframe(state_review_analysis)
        st.write("""
        **Rata-rata Rating per Negara:**  
        Analisis menunjukkan variasi dalam tingkat kepuasan pelanggan di setiap negara. Beberapa negara memberikan rating yang lebih tinggi, yang dapat digunakan untuk meningkatkan strategi pemasaran.
        """)

    
    with tab2:
        st.subheader("Produk Terbanyak Dibeli per Negara")
        st.dataframe(top_product_per_state)
        st.write("""
        **Produk Terbanyak Dibeli per Negara:**  
        Analisis menunjukkan produk yang paling sering dibeli oleh pelanggan di setiap negara. Ini dapat digunakan sebagai acuan untuk menentukan strategi pemasaran yang efektif.
        """)

def visual_data(state_review_analysis, top_product_per_state):
    tab1, tab2, tab3 = st.tabs(["Pertanyaan 1", "Pertanyaan 2", "Analisis Lanjutan"])

    geolocation_df = dataframes["Geolocation"]
    
    with tab1:
        st.subheader("Rata-rata Rating per Negara")
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.bar(
            state_review_analysis["customer_state"], 
            state_review_analysis["review_score"], 
            color='skyblue'
        )

        ax.set_xlabel("Negara")
        ax.set_ylabel("Rata-rata Review Score")
        ax.set_title("Rata-rata Review Score di Setiap Negara")
        ax.set_xticklabels(state_review_analysis["customer_state"], rotation=45)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        st.pyplot(fig)

        st.write("""
        **Rata-rata Rating per Negara:**  
        kita dapat melihat visual rata rata rating untuk setiap negara.
        """)

    
    with tab2:
        st.subheader("Produk Terbanyak Dibeli per Negara")
        fig, ax = plt.subplots(figsize=(12, 6))

        sns.lineplot(
            data=top_product_per_state,
            x="customer_state",
            y="total_purchases",
            hue="product_category_name",
            marker="o",
            linewidth=2,
            ax=ax
        )

        ax.set_xticklabels(top_product_per_state["customer_state"], rotation=45)
        ax.set_xlabel("Customer State")
        ax.set_ylabel("Total Purchases")
        ax.set_title("Produk Paling Banyak Dibeli di Tiap Negara (Line Chart)")
        ax.legend(title="Product Category", bbox_to_anchor=(1, 1))
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        st.pyplot(fig)

        st.write("""
        **Produk Terbanyak Dibeli per Negara:**  
        kita dapat melihat visual barang yang banyak di beli pada setiap negara
        """)
    with tab3:
        st.subheader("Analisis Lanjutan")

        if len(geolocation_df) > 10000:
            geolocation_df = geolocation_df.sample(n=10000, random_state=42)

        map_center = [geolocation_df["geolocation_lat"].mean(), geolocation_df["geolocation_lng"].mean()]
        m = folium.Map(location=map_center, zoom_start=5)

        for _, row in geolocation_df.iterrows():
            folium.CircleMarker(
                location=[row["geolocation_lat"], row["geolocation_lng"]],
                radius=2,
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.5
            ).add_to(m)

        heat_data = geolocation_df[["geolocation_lat", "geolocation_lng"]].values.tolist()
        HeatMap(heat_data, radius=10, blur=15).add_to(m)

        folium_static(m)

        st.write("""
        **Analisis Penggunaan E-Commerce di Berbagai Negara:**  
        Melalui analisis ini, kita dapat melihat negara mana saja yang menggunakan toko e-commerce dari perusahaan kami. Berdasarkan distribusi data, penggunaan e-commerce ini terlihat tidak merata, dengan konsentrasi pengguna yang lebih tinggi di beberapa negara tertentu. Hal ini menunjukkan bahwa meskipun platform kami sudah digunakan di banyak negara, namun penyebarannya belum begitu luas di seluruh benua dan negara.

        Distribusi geografis ini memberikan wawasan yang berguna mengenai potensi pasar yang belum tergarap dan area-area yang dapat difokuskan lebih lanjut untuk memperluas jangkauan platform e-commerce kami. Kami berharap dengan melihat data ini, perusahaan dapat merencanakan strategi ekspansi yang lebih tepat sasaran dan efisien di masa depan.
        """)



with st.sidebar:
    menu = st.selectbox(
        "Pilih halaman",
        ("Home", "Data Wrangling", "Exploratory Data Analysis (EDA)", "Visualization & Explanatory Analysis", "Conclusion")
    )


dataframes = load_data()

if menu == "Home":
    st.title("Home")
    st.write("""
    Selamat datang di halaman utama analisis data E-Commerce publik. Pada halaman ini, saya akan melakukan analisis terkait beberapa aspek penting dalam data E-Commerce, antara lain:
    
    1. **Rata-rata rating yang diberikan oleh setiap pelanggan di setiap negara** - Saya akan menggali pola pemberian rating oleh pelanggan di berbagai negara dan mencari tahu bagaimana rata-rata rating ini bervariasi.
    
    2. **Barang yang paling laku terjual di setiap negara** - Dengan menganalisis produk-produk yang terjual, kita akan menemukan barang-barang terpopuler di setiap wilayah geografis.
    
    3. **Lokasi pengguna dari setiap negara** - Saya akan mengidentifikasi sebaran lokasi pengguna berdasarkan data yang tersedia.

    Analisis ini dilakukan menggunakan beberapa library Python, di antaranya:
    - **NumPy** untuk perhitungan numerik,
    - **Pandas** untuk manipulasi dan analisis data,
    - **Matplotlib** dan **Seaborn** untuk visualisasi data.
    """)

elif menu == "Data Wrangling":
    st.title("Data Wrangling")
    st.write("""
    Dalam tahap ini, kita akan melakukan persiapan data sebelum dianalisis lebih lanjut.
    Proses ini mencakup tiga langkah utama: **Gathering Data**, **Assessing Data**, dan **Cleaning Data**.
    """)

    tab1, tab2, tab3 = st.tabs(["Gathering Data", "Assessing Data", "Cleaning Data"])

    
    with tab1:
        st.header("Gathering Data")
        st.write("""
        **Gathering Data** adalah proses mengumpulkan data dari berbagai sumber. 
        Berikut adalah beberapa dataset yang digunakan dalam analisis ini:
        """)

        display_dataframes(dataframes)
        st.write("""
        - Dalam dataset **E-Commerce Public**, terdapat **9 file CSV** yang digunakan untuk analisis.
        - Dataset yang tersedia mencakup informasi pelanggan, lokasi, transaksi, produk, dan penjual.
        """)

    
    with tab2:
        st.header("Assessing Data")
        st.write("""
        **Assessing Data** adalah tahap evaluasi untuk memahami kualitas data sebelum melanjutkan ke analisis lebih lanjut.
        Kami menemukan beberapa masalah yang perlu ditangani: **duplikasi data, nilai kosong (missing values), dan outlier**.
        """)
        
        for name, df in dataframes.items():
            duplicate_count = df.duplicated().sum()
            missing_values = df.isnull().sum()
            outlier_count = 0
            
            for col in df.select_dtypes(include=np.number):
                data = df[col].dropna()
                if len(data) > 0:
                    q25, q75 = np.percentile(data, 25), np.percentile(data, 75)
                    iqr = q75 - q25
                    cut_off = iqr * 1.5
                    minimum, maximum = q25 - cut_off, q75 + cut_off
                    outliers = [x for x in data if x < minimum or x > maximum]
                    outlier_count += len(outliers)

            
            st.subheader(f"{name} Dataset")
            st.write(f"- **Jumlah Data Duplikat:** {duplicate_count}")
            st.write(f"- **Jumlah Data Kosong:**")
            st.write(missing_values[missing_values > 0])
            st.write(f"- **Jumlah Outlier:** {outlier_count}")
            st.write("---")

        st.write("""
        **Data Duplikat**
         **Dataset yang memiliki duplikasi:**
         **Geolocation Dataset** → Terdapat beberapa baris yang memiliki nilai yang sama.
        
        **Data Kosong (Missing Values)**
         **Kolom yang memiliki nilai kosong dalam beberapa dataset:**
         **Order Reviews Dataset**  
                 `review_comment_title`, `review_comment_message`  
         **Orders Dataset**  
                 `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`  
         **Products Dataset**  
                 `product_category_name`, `product_name_length`, `product_description_length`,  
                 `product_photos_qty`, `product_weight_g`, `product_length_cm`,  
                 `product_height_cm`, `product_width_cm`
        
        **Data Outlier**
         **Dataset yang mengandung outlier:**
         **Geolocation Dataset**
         **Products Dataset**
         **Order Reviews Dataset**
         **Order Items Dataset**
         **Order Payments Dataset**
        """)

    
    with tab3:
        st.header("Cleaning Data")
        st.write("""
        Cleaning Data adalah proses memperbaiki data agar siap untuk dianalisis. Beberapa teknik yang umum digunakan meliputi:
        
        - **Menghapus atau Mengisi Data yang Hilang**: Menggunakan metode seperti imputasi (mengganti nilai yang hilang dengan rata-rata atau median).
        - **Menghapus Duplikasi**: Menghapus entri yang berulang agar tidak terjadi bias dalam analisis.
        - **Menangani Outlier**: Menghapus atau mentransformasi nilai ekstrem yang tidak sesuai.
        """)
        
        cleaned_dataframes = clean_data(dataframes)
        
        st.write("Dataset yang sudah dibersihkan:")
        display_dataframes(cleaned_dataframes)
        st.write("""
        **Data duplikat** telah dihapus.
        **Data kosong** telah ditangani: jika tipe data *object*, maka baris tersebut dihapus; jika numerik, nilai kosong diganti dengan rata-rata.
        **Outlier** telah ditangani dengan menggantinya menggunakan nilai maksimum dalam rentang IQR.
        """)

elif menu == "Exploratory Data Analysis (EDA)":
    st.title("Exploratory Data Analysis (EDA)")
    st.write("""
    **Exploratory Data Analysis (EDA)** adalah tahap awal dalam analisis data yang bertujuan untuk mengeksplorasi dan memahami pola, tren, serta hubungan dalam data.
    Pada bagian ini, kita akan melihat statistik dasar dan wawasan penting dari data yang telah dibersihkan, serta menjawab pertanyaan-pertanyaan yang akan membantu dalam pengambilan keputusan bisnis.
    """)

    cleaned_dataframes = clean_data(dataframes)
    state_review_analysis, top_product_per_state = perform_eda(cleaned_dataframes)
    
    display_eda_results(state_review_analysis, top_product_per_state)


elif menu == "Visualization & Explanatory Analysis":
    st.title("Visualization & Explanatory Analysis")
    st.write("""
    Pada bagian ini, kita akan menjelajahi visualisasi dan analisis yang mendalam terkait dengan pembelian yang dilakukan di toko e-commerce kami.

    1. **Rata-rata Review Score di Setiap Negara:**  
    Kami akan menampilkan visualisasi dari rata-rata skor review yang diberikan oleh pelanggan di setiap negara. Ini memberikan gambaran tentang bagaimana pelanggan di berbagai negara memberikan penilaian terhadap produk yang dibeli.

    2. **Barang yang Banyak Dibeli pada Setiap Negara:**  
    Di sini, kita akan melihat produk-produk yang paling sering dibeli di setiap negara. Visualisasi ini membantu untuk mengidentifikasi produk yang paling diminati oleh pelanggan di masing-masing wilayah.

    3. **Analisis Negara yang Menggunakan Toko E-commerce Kami:**  
    Kami juga akan menganalisis negara-negara mana saja yang menggunakan toko e-commerce kami. Ini membantu kami untuk memahami distribusi pengguna berdasarkan negara dan mengenali tren pasar di berbagai wilayah.
    """)

    cleaned_dataframes = clean_data(dataframes)
    state_review_analysis, top_product_per_state = perform_eda(cleaned_dataframes)
    
    visual_data(state_review_analysis, top_product_per_state)

elif menu == "Conclusion":
    st.title("Conclusion")
    st.write("""
    **Conclution pertanyaan 1** : saya dapat menyimpulkan untuk negara AP memiliki rating rata rata tertinggi untuk menilai suatu produk, dan negara AM memiliki rating rata rata terendah, mungkin saya dapat menganalisis seller pada negara AM melakukan penjualan yang kurang baik diantara semua negara, yang membuat nya mendapatkan rata rata rating terendah.

    **Conclution pertanyaan 2** : saya dapat menyimpulkan ,category product: cama mesa banho di negara SP sangat laku pesat, toko e-commerse kami mungkin akan merekomendasikan untuk seller baru untuk menjual product tersebut di negara SP.

    **Conclution analis lanjutan** : pendistribusian pengguna terhadap layanan e-commerse ini cukup luas, terlihat dari grafik visualisasi yang telah saya buat.
    """)
