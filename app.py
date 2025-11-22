import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_option_menu import option_menu
import os
import time
from bkt_engine import hitung_skor_baru

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS KEREN
# ==========================================
st.set_page_config(
    page_title="Smart Finance Tutor",
    page_icon="🎓",
    layout="wide" # Pakai layout lebar biar kayak Web App profesional
)

# CSS Custom untuk meniru gaya "Card" Android tapi di Web
st.markdown("""
<style>
    /* Hilangkan padding bawaan biar lebih luas */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Card Style (Kotak Putih dengan Bayangan) */
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #f0f0f0;
    }
    
    /* Header Text */
    .big-greeting {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0;
    }
    .sub-greeting {
        font-size: 1.1rem;
        color: #7f8c8d;
        margin-bottom: 20px;
    }

    /* Metric Box (Kotak Nilai) */
    .metric-box {
        text-align: center;
        background: linear-gradient(135deg, #6C63FF 0%, #4834d4 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
    }
    .metric-val { font-size: 1.5rem; font-weight: bold; }
    .metric-label { font-size: 0.8rem; opacity: 0.9; }

    /* Tombol Menu Ikon */
    .icon-btn {
        text-align: center;
        padding: 15px;
        border-radius: 10px;
        transition: transform 0.2s;
        cursor: pointer;
        background-color: #f8f9fa;
    }
    .icon-btn:hover {
        background-color: #eef0ff;
        transform: translateY(-3px);
    }
    .icon-img { width: 50px; margin-bottom: 10px; }
    .icon-text { font-weight: 600; color: #444; }

</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONEKSI GOOGLE SHEETS (DATABASE)
# ==========================================
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def init_connection():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
        elif os.path.exists("secrets.json"):
            creds = ServiceAccountCredentials.from_json_keyfile_name("secrets.json", SCOPES)
        else:
            return None
        
        client = gspread.authorize(creds)
        return client.open("ITS_Database")
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

sh = init_connection()

# --- FUNGSI DATABASE ---
def get_users():
    if sh is None: return pd.DataFrame()
    try: return pd.DataFrame(sh.worksheet("users").get_all_records())
    except: return pd.DataFrame()

def register_user_gsheet(email, password, nama, nim):
    if sh is None: return False
    try:
        wks = sh.worksheet("users")
        if email in wks.col_values(1): return False
        wks.append_row([email, password, nama, nim])
        sh.worksheet("scores").append_row([email, 0.1, 0.1, 0.1])
        return True
    except: return False

def get_user_score(email):
    if sh is None: return {'Analisis Likuiditas': 0.1, 'Analisis Profitabilitas': 0.1, 'Analisis Leverage': 0.1}
    try:
        wks = sh.worksheet("scores")
        cell = wks.find(email)
        vals = wks.row_values(cell.row)
        return {'Analisis Likuiditas': float(vals[1]), 'Analisis Profitabilitas': float(vals[2]), 'Analisis Leverage': float(vals[3])}
    except: return {'Analisis Likuiditas': 0.1, 'Analisis Profitabilitas': 0.1, 'Analisis Leverage': 0.1}

def update_user_score(email, skill, new_score):
    if sh is None: return
    try:
        wks = sh.worksheet("scores")
        cell = wks.find(email)
        col_map = {'Analisis Likuiditas': 2, 'Analisis Profitabilitas': 3, 'Analisis Leverage': 4}
        if skill in col_map: wks.update_cell(cell.row, col_map[skill], new_score)
    except: pass

# --- LOAD SOAL ---
@st.cache_data
def load_soal():
    if not os.path.exists("bank_soal.csv"): return pd.DataFrame()
    try:
        df = pd.read_csv("bank_soal.csv")
        if 'level' not in df.columns: df['level'] = 'Sedang'
        return df
    except: return pd.DataFrame()

df_soal = load_soal()

# ==========================================
# 3. STATE MANAGEMENT
# ==========================================
if 'user_info' not in st.session_state: st.session_state['user_info'] = None
if 'student_scores' not in st.session_state: st.session_state['student_scores'] = {}

# ==========================================
# 4. HALAMAN LOGIN (FULL SCREEN)
# ==========================================
if st.session_state['user_info'] is None:
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align: center;'>
            <img src='https://cdn-icons-png.flaticon.com/512/2921/2921222.png' width='80'>
            <h1 style='color: #4B0082;'>Smart Finance</h1>
            <p>Aplikasi Belajar Analisis Keuangan Berbasis AI</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔑 Masuk", "📝 Daftar"])
        
        with tab1:
            email = st.text_input("Email", key="log_email")
            pwd = st.text_input("Password", type="password", key="log_pwd")
            if st.button("Masuk Sekarang", type="primary", use_container_width=True):
                df_u = get_users()
                if not df_u.empty:
                    user = df_u[(df_u['email'] == email) & (df_u['password'] == str(pwd))]
                    if not user.empty:
                        u_data = user.iloc[0]
                        st.session_state['user_info'] = {'nama': u_data['nama'], 'nim': u_data['nim'], 'email': u_data['email']}
                        st.session_state['student_scores'] = get_user_score(u_data['email'])
                        st.rerun()
                    else: st.error("Akun tidak ditemukan!")
        
        with tab2:
            n_nama = st.text_input("Nama")
            n_nim = st.text_input("NIM")
            n_email = st.text_input("Email")
            n_pwd = st.text_input("Password", type="password")
            if st.button("Buat Akun", use_container_width=True):
                if register_user_gsheet(n_email, n_pwd, n_nama, n_nim):
                    st.success("Berhasil! Silakan Login.")
                else: st.error("Gagal daftar.")
        
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 5. DASHBOARD UTAMA (WEB APP STYLE)
# ==========================================
else:
    user = st.session_state['user_info']
    
    # --- HEADER NAVIGATION ---
    with st.container():
        col_nav1, col_nav2 = st.columns([1, 3])
        with col_nav1:
            st.markdown(f"### 👋 Hi, {user['nama'].split(' ')[0]}")
        with col_nav2:
            selected = option_menu(
                None, ["Beranda", "Materi", "Latihan", "Rapor"], 
                icons=['house', 'book', 'pencil', 'bar-chart'], 
                menu_icon="cast", default_index=0, orientation="horizontal",
                styles={"nav-link-selected": {"background-color": "#6C63FF"}}
            )

    st.markdown("---")

    # --- HALAMAN: BERANDA ---
    if selected == "Beranda":
        # Banner
        st.image("https://img.freepik.com/free-vector/flat-design-online-learning-banner_23-2150402664.jpg?w=1380", use_column_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Menu Grid (Pengganti Ikon Kotak Android)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("""<div class='card icon-btn' style='text-align:center'>
                <img src='