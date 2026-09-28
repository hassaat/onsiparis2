import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# --- 1. SAYFA AYARLARI VE CSS ---
st.set_page_config(
    page_title="Ön Sipariş Paneli", 
    layout="centered", 
    page_icon="📝"
)

# Session State Tanımlamaları
if "siparis_gonderildi" not in st.session_state:
    st.session_state.siparis_gonderildi = False

# Arayüz Özelleştirmeleri
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    .price-text { color: #2ecc71; font-weight: bold; font-size: 1.15rem; }
    .model-header { font-size: 1.1rem; font-weight: bold; color: #222; margin-bottom: 2px; }
    [data-testid="stImage"] img { border-radius: 12px; }
    .stTextInput input { border-radius: 8px; }
    .stNumberInput div { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO VE BAŞLIK ---
LOGO_URL = "https://b2bc.ams3.cdn.digitaloceanspaces.com/haselektron/ckeditor/pictures/66/hassaat-logo2.png"

st.markdown(f"""
    <div style="display: block; margin-left: auto; margin-right: auto; width: 300px; text-align: center;">
        <img src="{LOGO_URL}" style="width: 380px; height: auto;">
        <h2 style='
            color: #0096D6; 
            font-size: 1.8rem; 
            font-weight: bold; 
            letter-spacing: 1.5px; 
            margin-top: 20px;
            margin-bottom: 40px;
            text-transform: uppercase;
        '>
        ÖN SİPARİŞ TALEBİ
        </h2>
    </div>
    """, unsafe_allow_html=True)

# --- 3. VERİ BAĞLANTISI (KESİNTİSİZ TEKRAR DENEMELİ) ---
URL = "https://script.google.com/macros/s/AKfycbxI5Xez-zVT2R1ajG-trRk_49y-byTmHLnSpos0mco10OWDZ69UNgecXFIDv9jp8MfZ9g/exec"

@st.cache_data(ttl=30, show_spinner=False)
def verileri_yukle():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    # Anlık Google kopmalarına karşı 5 kez tekrar dener
    for _ in range(5):
        try:
            res = requests.get(URL, headers=headers, timeout=20, allow_redirects=True)
            if res.status_code == 200:
                json_data = res.json()
                if isinstance(json_data, list) and len(json_data) > 0:
                    return pd.DataFrame(json_data)
        except Exception:
            time.sleep(1)
    return pd.DataFrame()

# --- 4. ANA FORM VE AKIŞ ---
df = verileri_yukle()

if df.empty:
    st.error("⚠️ Stok listesi şu an yüklenemiyor. Lütfen birkaç saniye sonra yeniden deneyin.")
    if st.button("🔄 Yeniden Dene", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
else:
    # Sipariş başarıyla gönderildiyse gösterilecek ekran
    if st.session_state.siparis_gonderildi:
        st.balloons()
        st.success("✅ Siparişiniz başarıyla iletilmiştir!")
        if st.button("➕ Yeni Sipariş Oluştur", type="primary", use_container_width=True):
            st.session_state.siparis_gonderildi = False
            st.rerun()

    # Müşteri Bilgileri
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        musteri = st.text_input("👤 Adınız Soyadınız", placeholder="Adınız Soyadınız", key="input_musteri")
    with col_b2:
        firma = st.text_input("🏢 Firma Adı", placeholder="Şirket Adı", key="input_firma")

    st.write("---")
    st.subheader("Mevcut Modeller")
    
    siparisler = {}

    # Ürünleri Listeleme Döngüsü
    for i, row in df.iterrows():
        model_kodu = str(row.get('Kodu', '')).strip()
        stok_miktari = row.get('Miktar', 0)
        gorsel_linki = row.get('URL', '')
        fiyat = row.get('P.S.F.', '0')

        try:
            stok = int(float(stok_miktari))
        except:
            stok = 0

        # Sadece stoğu olan ürünleri göster
        if stok > 0 and model_kodu:
            input_key = f"sel_{model_kodu}"

            with st.container():
                c_img, c_info, c_input = st.columns([1, 2, 1])
                with c_img:
                    if gorsel_linki:
                        st.image(gorsel_linki, use_container_width=True)
                with c_info:
                    st.markdown(f"<p class='model-header'>{model_kodu}</p>", unsafe_allow_html=True)
                    st.markdown(f"Fiyat: <span class='price-text'>{fiyat} TL</span>", unsafe_allow_html=True)
                    st.caption(f"Stok: {stok}")
                with c_input:
                    adet = st.number_input("Adet", min_value=0, max_value=stok, key=input_key, step=1)
                    if adet > 0:
                        siparisler[model_kodu] = adet
            st.divider()

    # --- SİPARİŞİ ONAYLA VE GÖNDER ---
    if st.button("🚀 Siparişi Onayla ve Gönder", use_container_width=True, type="primary"):
        if musteri and firma and siparisler:
            veri_paketi = [
                {
                    "Tarih": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Müşteri": musteri,
                    "Firma": firma,
                    "Model": m,
                    "Adet": a
                } for m, a in siparisler.items()
            ]
            
            with st.spinner("Siparişiniz iletiliyor..."):
                basarili = False
                for _ in range(3):
                    try:
                        res = requests.post(URL, json=veri_paketi, timeout=25)
                        if res.status_code == 200 and "Başarılı" in res.text:
                            basarili = True
                            break
                    except:
                        time.sleep(1)

                if basarili:
                    # GÜVENLİ SIFIRLAMA: Session state üzerindeki adet seçimlerini temizliyoruz
                    for key in list(st.session_state.keys()):
                        if key.startswith("sel_"):
                            del st.session_state[key]

                    # Başarı bayrağını set et, önbelleği temizle ve sayfayı yenile
                    st.session_state.siparis_gonderildi = True
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("⚠️ Sunucu yoğunluğu nedeniyle iletilemedi. Lütfen tekrar deneyin.")
        else:
            st.warning("⚠️ Lütfen adınızı, firmanızı doldurduğunuzdan ve en az bir üründen adet seçtiğinizden emin olun.")

st.caption("© 2026 Has Saat")
