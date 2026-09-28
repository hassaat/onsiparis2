import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Ön Sipariş Paneli", layout="centered", page_icon="📝")

# Session State Tanımlamaları
if "siparis_gonderildi" not in st.session_state:
    st.session_state.siparis_gonderildi = False

# Arayüz Makyajı (CSS)
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

# --- 3. VERİ BAĞLANTISI ---
URL = "https://script.google.com/macros/s/AKfycbyDSOx6wrH871JYJ03IDxfRskcJj4qKImgj8hmyHmdzWfHyLmPPsi-J6nsREPo5cjuoVg/exec"

@st.cache_data(ttl=60, show_spinner=False)
def verileri_yukle():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    for _ in range(3):
        try:
            # Google Apps Script yönlendirmelerini allow_redirects=True ile takip ediyoruz
            res = requests.get(URL, headers=headers, timeout=15, allow_redirects=True)
            if res.status_code == 200:
                data = res.json()
                if data:
                    return pd.DataFrame(data)
        except Exception as e:
            time.sleep(1)
    return pd.DataFrame()

# --- 4. ANA FORM ---
df = verileri_yukle()

if df.empty:
    st.error("⚠️ Stok listesi şu an yüklenemiyor. Lütfen birkaç saniye sonra sayfayı yenileyin.")
    if st.button("🔄 Yeniden Dene"):
        st.cache_data.clear()  # Önbelleği temizleyip tekrar dener
        st.rerun()
else:
    # Sipariş gönderim sonrası ekranı
    if st.session_state.siparis_gonderildi:
        st.balloons()
        st.success("✅ Siparişiniz başarıyla iletilmiştir!")
        if st.button("➕ Yeni Sipariş Oluştur"):
            st.session_state.siparis_gonderildi = False
            st.rerun()

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        musteri = st.text_input("👤 Adınız Soyadınız", placeholder="Adınız Soyadınız", key="input_musteri")
    with col_b2:
        firma = st.text_input("🏢 Firma Adı", placeholder="Şirket Adı", key="input_firma")

    st.write("---")
    st.subheader("Mevcut Modeller")
    
    siparisler = {}

    for i, row in df.iterrows():
        model_kodu = str(row.get('Kodu', ''))
        stok_miktari = row.get('Miktar', 0)
        gorsel_linki = row.get('URL', '')
        fiyat = row.get('P.S.F.', '0')

        try:
            stok = int(float(stok_miktari))
        except:
            stok = 0

        if stok > 0:
            # Benzersiz Key: Model Kodu kullanarak key çakışmalarını ve hatayı engelliyoruz
            input_key = f"sel_{model_kodu}"
            
            # Key'i önceden güvenli şekilde başlatıyoruz
            if input_key not in st.session_state:
                st.session_state[input_key] = 0

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

    # --- SİPARİŞ GÖNDERME ---
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
                        res = requests.post(URL, json=veri_paketi, timeout=20)
                        if res.status_code == 200:
                            basarili = True
                            break
                    except:
                        time.sleep(1)

                if basarili:
                    # Seçili ürün adetlerini güvenli sıfırlama
                    for k in list(st.session_state.keys()):
                        if k.startswith("sel_"):
                            st.session_state[k] = 0

                    st.session_state.siparis_gonderildi = True
                    st.rerun()
                else:
                    st.error("⚠️ Sunucu yoğunluğu nedeniyle iletilemedi. Lütfen butona tekrar basarak deneyin.")
        else:
            st.warning("⚠️ Lütfen isim, firma ve en az bir ürün seçtiğinizden emin olun.")

st.caption("© 2026 Has Saat")
