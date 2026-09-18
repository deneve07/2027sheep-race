import streamlit as st
import random
import threading
import io
import base64
import qrcode
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="2027年生達年會 羊年大賽跑", page_icon="🐑", layout="wide")

# ⚠️ 部署到 Streamlit Cloud 拿到網址後，把它填在這裡並重新部署一次，
#    現場就不用再手動貼網址了。例如：
#    BASE_URL = "https://sheep-race-xxxx.streamlit.app"
BASE_URL = "https://2027sheep-race-vxezm7iwzzxxsdcm2fjkgo.streamlit.app/"

SHEEP_COUNT = 6
ROUND_COUNT = 4          # 預先產生幾輪的 QR Code
TAPS_TO_FINISH = 60
BLESSINGS = [
    "三陽開泰迎新歲，福祿雙全樂逍遙",
    "羊年旺旺來，事業步步高升",
    "金羊送福到，好運連連一整年",
    "喜氣洋洋迎丁未，闔家平安福滿盈",
    "羊年行大運，鴻圖大展創新猷",
    "羊羊得意展宏圖，年年有餘萬事興",
]


@st.cache_resource
def get_shared_state():
    return {
        "lock": threading.Lock(),
        "pin": None,
        "claims": [None] * SHEEP_COUNT,   # {"unit":.., "name":..}
        "phase": "claiming",              # claiming | racing | finished
        "progress": [0] * SHEEP_COUNT,
        "round": 1,
        "winner_idx": None,
        "blessing": "",
        "base_url": BASE_URL,
    }


state = get_shared_state()


def new_pin():
    return str(random.randint(1000, 9999))


def qr_image_base64(url: str) -> str:
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# =================================================================
# CSS — 尾牙夜店喜氣風：更亮、更有霓虹感
# =================================================================
st.markdown("""
<style>
@keyframes glow {
  0%,100% { text-shadow: 0 0 18px rgba(255,209,102,0.55), 0 0 40px rgba(255,80,160,0.25); }
  50%     { text-shadow: 0 0 30px rgba(255,209,102,0.9), 0 0 60px rgba(255,80,160,0.5); }
}
.stApp{
    background:
      radial-gradient(circle at 15% -5%, rgba(255,80,160,0.35), transparent 45%),
      radial-gradient(circle at 90% 0%, rgba(255,196,0,0.30), transparent 45%),
      radial-gradient(circle at 50% 100%, rgba(180,20,60,0.35), transparent 55%),
      linear-gradient(160deg, #2b0f1c 0%, #1a0f14 60%, #120a0e 100%);
    color:#fdf3df;
}
h1{
    color:#ffd166 !important;
    animation: glow 2.4s ease-in-out infinite;
    font-weight:900 !important;
}
h2,h3{color:#ffb3d9 !important; font-weight:800 !important;}

.pen-box{
    background:linear-gradient(160deg,#4a1f33,#331226);
    border:2px solid #ff8fc7;
    box-shadow:0 0 18px rgba(255,143,199,0.25);
    border-radius:16px;padding:18px;text-align:center;margin-bottom:10px;
}
.pen-empty{color:#c9a3b8; border-color:#7a4a5f;}
.lane-box{
    background:rgba(255,255,255,0.08);border:1px solid rgba(255,209,102,0.35);
    border-radius:14px;padding:10px 18px;margin-bottom:12px;
}
.lane-fill{
    background:linear-gradient(90deg,#ff8fc7,#ffd166);height:26px;border-radius:13px;
    box-shadow:0 0 14px rgba(255,209,102,0.6);
}
.winner-box{
    text-align:center;
    background:radial-gradient(circle at center, rgba(255,80,160,0.35), rgba(30,10,20,0.97));
    border-radius:24px;padding:50px 20px;border:3px solid #ffd166;
    box-shadow:0 0 60px rgba(255,209,102,0.4);
}
.qr-card{
    background:linear-gradient(160deg,#4a1f33,#331226);
    border:2px solid #ffd166;border-radius:14px;padding:14px;text-align:center;
    box-shadow:0 0 14px rgba(255,209,102,0.2);
}
.qr-card img{background:#fff;padding:8px;border-radius:8px;}

.sheep-card{
    background:linear-gradient(160deg,#3a1a2c,#2a1220);
    border:1px solid #ff8fc7;border-radius:14px;padding:14px 16px;margin-bottom:14px;
}
.sheep-card-title{font-weight:800;color:#ffd166;font-size:15px;margin-bottom:8px;}

/* ---- contrast / readability ---- */
div[data-testid="stWidgetLabel"] p, div[data-testid="stWidgetLabel"] label{
    color:#fdf3df !important; font-weight:700;
}
div[data-testid="stCaptionContainer"] p, .stCaption, small{
    color:#ffcfe6 !important;
}
.stTextInput input, .stNumberInput input{
    color:#fdf3df !important;
    background:#1f0f18 !important;
    border:1px solid #ff8fc7 !important;
}
.stTextInput input::placeholder{
    color:#a97b93 !important;
    opacity:1 !important;
}
.stMarkdown p, .stMarkdown li, .stApp p{
    color:#fdf3df;
}
div[data-testid="stExpander"]{
    border:1px solid #ff8fc7 !important; border-radius:14px !important;
    background:rgba(74,31,51,0.35) !important;
}
div[data-testid="stExpander"] summary p{
    color:#ffd166 !important; font-weight:800 !important; font-size:16px !important;
}
.stAlert p{ color:#1c1210 !important; }
.stButton button{
    border-radius:10px !important; font-weight:800 !important;
    border:1px solid #ffd166 !important;
}
</style>
""", unsafe_allow_html=True)


def go_home():
    st.query_params.clear()
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


role = st.query_params.get("role", None)
p_param = st.query_params.get("p", None)
r_param = st.query_params.get("r", None)

# =================================================================
# HOME
# =================================================================
if role is None:
    st.markdown("<div style='color:#ffb3d9;letter-spacing:6px;'>2027年生達年會</div>", unsafe_allow_html=True)
    st.title("🐑 羊年大賽跑")
    st.caption("喝完一瓶啤酒，狂點手機衝第一")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🖥️ 大螢幕主控")
        st.write("投影用，設定當輪參賽者姓名、顯示賽跑畫面與得獎公告")
        if st.button("進入大螢幕主控", use_container_width=True):
            st.query_params["role"] = "display"
            st.rerun()
    with c2:
        st.subheader("📱 參賽者掃碼進入")
        st.write("請用現場發放的 QR Code 掃碼進入，不要直接手動進這裡")
        if st.button("（測試用）手動進入", use_container_width=True):
            st.query_params["role"] = "control"
            st.rerun()
    st.stop()


# =================================================================
# DISPLAY (main screen)
# =================================================================
if role == "display":
    st_autorefresh(interval=500, key="display_refresh")

    top_l, top_r = st.columns([5, 1])
    with top_l:
        st.title("🐑 羊年大賽跑 · 大螢幕")
        st.caption(f"第 {state['round']} 輪　|　目前階段：" +
                   {"claiming": "設定/認領中", "racing": "比賽中", "finished": "本輪結束"}[state["phase"]])
    with top_r:
        if st.button("← 回首頁"):
            go_home()

    if state["pin"] is None:
        with state["lock"]:
            state["pin"] = new_pin()

    # ---------------- 事前列印用 QR Code（跟名單無關，可以提早印好） ----------------
    with st.expander("🖨️ 事前列印用 QR Code（共 %d 輪 × 6 張，活動前先印好）" % ROUND_COUNT, expanded=False):
        st.caption("每張 QR Code 已經固定對應「第幾輪、第幾號羊」，跟參賽者姓名無關，可以提早印出來，現場照輪次發給對應的人即可。")
        st.success(f"通關密碼：**{state['pin']}**（口頭告知參賽者，不要投影出去）")
        for r in range(1, ROUND_COUNT + 1):
            st.markdown(f"**第 {r} 輪**")
            qcols = st.columns(6)
            for i in range(SHEEP_COUNT):
                url = f"{state['base_url'].rstrip('/')}/?role=control&r={r}&p={i}"
                img_b64 = qr_image_base64(url)
                with qcols[i]:
                    st.markdown(f"""
                    <div class="qr-card">
                      <b>{i+1} 號羊</b><br>
                      <img src="data:image/png;base64,{img_b64}" width="110">
                    </div>
                    """, unsafe_allow_html=True)

    # ---------------- 當輪：輸入參賽者姓名 ----------------
    with st.expander("⚙️ 當輪參賽者：輸入單位與姓名", expanded=(state["phase"] == "claiming")):
        form_values = []
        cols = st.columns(3)
        for i in range(SHEEP_COUNT):
            existing = state["claims"][i]
            with cols[i % 3]:
                st.markdown(f'<div class="sheep-card"><div class="sheep-card-title">🐑 {i+1} 號羊</div>', unsafe_allow_html=True)
                unit = st.text_input("單位", value=(existing["unit"] if existing else ""), key=f"u_{i}", placeholder="例：業務部")
                name = st.text_input("姓名", value=(existing["name"] if existing else ""), key=f"n_{i}", placeholder="姓名")
                st.markdown('</div>', unsafe_allow_html=True)
                form_values.append((unit.strip(), name.strip()))

        colA, colB, colC = st.columns(3)
        with colA:
            if st.button("✅ 套用本輪名單", use_container_width=True):
                with state["lock"]:
                    new_claims = []
                    for unit, name in form_values:
                        new_claims.append({"unit": unit, "name": name} if name else None)
                    state["claims"] = new_claims
                st.rerun()
        with colB:
            can_start = state["phase"] == "claiming" and any(state["claims"])
            if st.button("▶️ 開始比賽", disabled=not can_start, use_container_width=True):
                with state["lock"]:
                    state["progress"] = [0] * SHEEP_COUNT
                    state["phase"] = "racing"
                    state["winner_idx"] = None
        with colC:
            if st.button("🔁 開始下一輪", use_container_width=True):
                with state["lock"]:
                    state["round"] = state["round"] + 1 if state["round"] < ROUND_COUNT else 1
                    state["claims"] = [None] * SHEEP_COUNT
                    state["progress"] = [0] * SHEEP_COUNT
                    state["phase"] = "claiming"
                    state["winner_idx"] = None
                st.rerun()

    if state["phase"] == "finished" and state["winner_idx"] is not None:
        w = state["claims"][state["winner_idx"]]
        name = w["name"] if w else f"第{state['winner_idx']+1}隻羊"
        unit = w["unit"] if w else ""
        st.balloons()
        st.markdown(f"""
        <div class="winner-box">
          <div style="font-size:20px;color:#ffb3d9;letter-spacing:6px;">丁未羊年 · 賽跑冠軍</div>
          <div style="font-size:80px;margin:10px 0;">🐑🏆</div>
          <div style="font-size:18px;color:#ffe0f0;">{unit}</div>
          <div style="font-size:56px;font-weight:900;color:#ffd166;margin-bottom:16px;">{name}</div>
          <div style="font-size:30px;font-weight:800;color:#fdf3df;">{state['blessing']}</div>
        </div>
        """, unsafe_allow_html=True)

    elif state["phase"] == "claiming":
        cols = st.columns(SHEEP_COUNT)
        for i in range(SHEEP_COUNT):
            c = state["claims"][i]
            with cols[i]:
                if c:
                    st.markdown(f"""<div class="pen-box">🐑<br><b>{c['name']}</b><br>
                                 <span style="font-size:12px;color:#ffcfe6;">{c['unit']}</span></div>""",
                                unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="pen-box pen-empty">🐑<br>{i+1} 號羊<br>尚未設定</div>""",
                                unsafe_allow_html=True)

    else:  # racing
        for i in range(SHEEP_COUNT):
            c = state["claims"][i]
            if not c:
                continue
            name = c["name"]
            unit = c["unit"]
            pct = min(100, int(state["progress"][i] / TAPS_TO_FINISH * 100))
            st.markdown(f"**{name}** <span style='color:#ffcfe6;font-size:12px;'>{unit}</span>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="lane-box">
              <div class="lane-fill" style="width:{pct}%;"></div>
            </div>
            """, unsafe_allow_html=True)

        for i in range(SHEEP_COUNT):
            if state["claims"][i] and state["progress"][i] >= TAPS_TO_FINISH and state["phase"] == "racing":
                with state["lock"]:
                    if state["phase"] == "racing":
                        state["phase"] = "finished"
                        state["winner_idx"] = i
                        state["blessing"] = random.choice(BLESSINGS)
                st.rerun()


# =================================================================
# CONTROL (phone)
# =================================================================
elif role == "control":
    top_l, top_r = st.columns([5, 1])
    with top_l:
        st.title("🐑 羊年大賽跑")
    with top_r:
        if st.button("← 回首頁"):
            go_home()

    if "pin_ok" not in st.session_state:
        st.session_state.pin_ok = False
    if "my_taps" not in st.session_state:
        st.session_state.my_taps = 0

    if not st.session_state.pin_ok:
        st.write("請輸入通關密碼：")
        pin_try = st.text_input("通關密碼", max_chars=4, label_visibility="collapsed")
        if st.button("確認密碼", use_container_width=True):
            if state["pin"] and pin_try.strip() == state["pin"]:
                st.session_state.pin_ok = True
                st.rerun()
            else:
                st.error("密碼錯誤，請向主控台人員確認")
        st.stop()

    st_autorefresh(interval=700, key="control_refresh")

    my_i = None
    if p_param is not None:
        try:
            idx = int(p_param)
            if 0 <= idx < SHEEP_COUNT:
                my_i = idx
        except ValueError:
            pass

    my_round = None
    if r_param is not None:
        try:
            my_round = int(r_param)
        except ValueError:
            pass

    if my_i is None:
        st.warning("這組連結沒有對應到有效的號碼牌，請確認掃到正確的 QR Code，或回首頁手動操作。")
        st.stop()

    if my_round is not None and my_round != state["round"]:
        st.info(f"你的號碼牌是第 {my_round} 輪，目前是第 {state['round']} 輪，請稍候輪到你時再操作 🙏")
        st.stop()

    my_c = state["claims"][my_i]
    if not my_c:
        st.info(f"你是 🐑 {my_i+1} 號羊，主控台尚未輸入你的姓名，請稍候…")
        st.stop()

    if state["phase"] == "claiming":
        st.info(f"你是 🐑 {my_i+1} 號羊 · {my_c['name']}（{my_c['unit']}），等待主控台開始比賽…")

    elif state["phase"] == "racing":
        st.subheader(f"🐑 {my_i+1} 號羊 · {my_c['name']}")
        if st.button("狂點衝刺！", use_container_width=True, key="tapbtn"):
            with state["lock"]:
                state["progress"][my_i] += 1
                st.session_state.my_taps += 1
        st.write(f"已點擊 **{st.session_state.my_taps}** 下")
        pct = min(100, int(state["progress"][my_i] / TAPS_TO_FINISH * 100))
        st.progress(pct / 100)

    elif state["phase"] == "finished":
        if state["winner_idx"] == my_i:
            st.success("🏆 恭喜你第一名！請看大螢幕公布結果！")
        else:
            st.info("比賽結束，請看大螢幕公布結果！")
        st.caption("下一輪開始前，請等候工作人員發下一輪的號碼牌 QR Code。")
