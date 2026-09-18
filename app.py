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
        "claims": [None] * SHEEP_COUNT,   # {"unit":.., "name":..}
        "phase": "claiming",              # claiming | racing | finished
        "progress": [0] * SHEEP_COUNT,
        "round": 1,
        "winner_idx": None,
        "blessing": "",
        "base_url": BASE_URL,
    }


state = get_shared_state()


@st.cache_data(show_spinner=False)
def qr_image_base64(url: str) -> str:
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def clear_roster_inputs():
    """真正清空表單輸入框（不只是清 state，連 widget 記住的舊值也一起刪掉）"""
    for i in range(SHEEP_COUNT):
        for prefix in ("u_", "n_"):
            key = f"{prefix}{i}"
            if key in st.session_state:
                del st.session_state[key]


# =================================================================
# CSS — 可愛喜氣派對風
# =================================================================
st.markdown("""
<style>
html, body, [class*="css"]{ font-size:18px !important; }

.stApp{
    background:
      radial-gradient(circle at 10% 0%, rgba(255,183,197,0.55), transparent 45%),
      radial-gradient(circle at 95% 10%, rgba(255,214,120,0.55), transparent 45%),
      linear-gradient(160deg, #fff8ec 0%, #ffeef2 55%, #fff3e0 100%);
    color:#3a1f0d;
}
h1{
    color:#e0293f !important;
    -webkit-text-stroke: 1px #ffe08a;
    font-weight:900 !important;
    font-size:2.6rem !important;
}
h2,h3{color:#c2185b !important; font-weight:800 !important;}

.pen-box{
    background:#ffffff;border:3px solid #ff8fa3;
    box-shadow:0 6px 14px rgba(224,41,63,0.12);
    border-radius:20px;padding:18px;text-align:center;margin-bottom:10px;
    font-size:1.05rem;
}
.pen-empty{color:#c79a86; border-color:#ffd9a8; background:#fffaf2;}

.qr-card{
    background:#ffffff;border:2px solid #ffb74d;border-radius:16px;padding:14px;text-align:center;
    box-shadow:0 4px 10px rgba(0,0,0,0.06);
}
.qr-card img{border-radius:8px;}

.sheep-card{
    background:#fffaf2;border:2px solid #ffb3c6;border-radius:18px;padding:16px 18px;margin-bottom:16px;
}
.sheep-card-title{font-weight:900;color:#d81b60;font-size:1.2rem;margin-bottom:8px;}

/* ---- widget contrast / size ---- */
div[data-testid="stWidgetLabel"] p, div[data-testid="stWidgetLabel"] label{
    color:#7a3b1f !important; font-weight:700 !important; font-size:1rem !important;
}
div[data-testid="stCaptionContainer"] p, .stCaption, small{ color:#a15a3a !important; }
.stTextInput input, .stNumberInput input{
    color:#3a1f0d !important; background:#ffffff !important;
    border:2px solid #ffb3c6 !important; font-size:1.1rem !important; border-radius:10px !important;
}
.stTextInput input::placeholder{ color:#c79a86 !important; opacity:1 !important; }
.stMarkdown p, .stMarkdown li, .stApp p{ color:#3a1f0d; }
div[data-testid="stExpander"]{
    border:2px solid #ffb3c6 !important; border-radius:18px !important;
    background:rgba(255,255,255,0.6) !important;
}
div[data-testid="stExpander"] summary p{
    color:#c2185b !important; font-weight:800 !important; font-size:1.15rem !important;
}
.stAlert p{ color:#3a1f0d !important; font-size:1.05rem !important; }
.stButton button{
    border-radius:12px !important; font-weight:800 !important;
    border:2px solid #e0293f !important; font-size:1.05rem !important;
    padding:0.6rem 1rem !important;
}

/* ---- 狂點按鈕：特別放大 ---- */
.st-key-tapbtn button{
    font-size:2rem !important;
    padding:2rem 1rem !important;
    border-radius:26px !important;
    background:linear-gradient(160deg,#ffd166,#ff8fa3) !important;
    color:#7a0e1f !important;
    border:4px solid #e0293f !important;
    box-shadow:0 8px 0 #b3223a, 0 12px 24px rgba(0,0,0,0.25) !important;
}
.st-key-tapbtn button:active{
    box-shadow:0 2px 0 #b3223a, 0 4px 10px rgba(0,0,0,0.2) !important;
}

/* ---- big text helpers for phone screens ---- */
.big-msg{
    font-size:1.7rem; font-weight:800; color:#c2185b; text-align:center;
    background:#fff; border:3px solid #ffb3c6; border-radius:18px; padding:24px 16px; line-height:1.5;
}
.huge-name{
    font-size:2.3rem; font-weight:900; color:#e0293f; text-align:center; margin:10px 0;
}
.tap-count-big{
    font-size:1.8rem; font-weight:900; color:#c2185b; text-align:center; margin-top:16px;
}
.tap-count-big b{ font-size:2.8rem; color:#e0293f; }

/* ---- race track: 草原 + 真的羊在跑 ---- */
.race-lane{ margin-bottom:14px; }
.race-lane .lane-name{ font-weight:800; font-size:1.05rem; color:#3a1f0d; margin-bottom:4px; }
.race-lane .lane-unit{ font-weight:400; font-size:0.85rem; color:#a15a3a; margin-left:6px; }
.grass-track{
    position:relative; height:64px; border-radius:32px; overflow:hidden;
    background:repeating-linear-gradient(90deg,#8bc34a 0 40px,#7cb342 40px 80px);
    border:3px solid #558b2f;
    box-shadow:inset 0 0 12px rgba(0,0,0,0.15);
}
.grass-track::before{
    content:""; position:absolute; top:50%; left:0; right:0; height:3px;
    background:repeating-linear-gradient(90deg, rgba(255,255,255,0.6) 0 14px, transparent 14px 30px);
    transform:translateY(-50%);
}
.finish-flag{ position:absolute; right:6px; top:50%; transform:translateY(-50%); font-size:28px; z-index:2; }
.running-sheep{
    position:absolute; top:50%; transform:translateY(-50%); font-size:36px;
    transition:left 0.4s ease-out;
    animation: hop 0.5s ease-in-out infinite;
    z-index:1;
}
@keyframes hop{
  0%,100%{ transform:translateY(-50%) rotate(0deg); }
  50%{ transform:translateY(-62%) rotate(-10deg); }
}

/* ---- winner celebration ---- */
.winner-box{
    text-align:center; position:relative; overflow:hidden;
    background:linear-gradient(160deg,#fff0f5,#ffe9c2);
    border-radius:26px; padding:50px 20px; border:4px solid #ff6f91;
    box-shadow:0 12px 30px rgba(224,41,63,0.2);
}
.fireworks-row{ font-size:2.4rem; letter-spacing:14px; margin-bottom:6px; }
.fireworks-row span{ display:inline-block; animation: pop 1s ease-in-out infinite; }
.fireworks-row span:nth-child(2){ animation-delay:0.15s; }
.fireworks-row span:nth-child(3){ animation-delay:0.3s; }
.fireworks-row span:nth-child(4){ animation-delay:0.45s; }
.fireworks-row span:nth-child(5){ animation-delay:0.6s; }
@keyframes pop{
  0%,100%{ transform:scale(1) rotate(0deg); opacity:0.85; }
  50%{ transform:scale(1.3) rotate(8deg); opacity:1; }
}
.winner-blessing{
    font-size:2.4rem !important; font-weight:900 !important; color:#3a1f0d !important; line-height:1.6;
}
.winner-name-huge{
    font-size:4rem !important; font-weight:900; color:#e0293f; margin-bottom:16px;
    -webkit-text-stroke: 1.5px #ffd166;
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
    st.markdown("<div style='color:#c2185b;letter-spacing:6px;font-weight:700;'>2027年生達年會</div>", unsafe_allow_html=True)
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
                   {"claiming": "設定中", "racing": "比賽中", "finished": "本輪結束"}[state["phase"]])
    with top_r:
        if st.button("← 回首頁"):
            go_home()

    # ---------------- 事前列印用 QR Code（已加快取，不會拖慢畫面） ----------------
    with st.expander("🖨️ 事前列印用 QR Code（共 %d 輪 × 6 張，活動前先印好）" % ROUND_COUNT, expanded=False):
        st.caption("每張 QR Code 固定對應「第幾輪、第幾號羊」，跟參賽者姓名無關，可以提早印出來，現場照輪次發給對應的人即可。掃碼進去不需要再輸入密碼。")
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
        with st.form("roster_form", clear_on_submit=False):
            unit_inputs = []
            name_inputs = []
            cols = st.columns(3)
            for i in range(SHEEP_COUNT):
                existing = state["claims"][i]
                with cols[i % 3]:
                    st.markdown(f'<div class="sheep-card"><div class="sheep-card-title">🐑 {i+1} 號羊</div>', unsafe_allow_html=True)
                    u = st.text_input("單位", value=(existing["unit"] if existing else ""), key=f"u_{i}", placeholder="例：業務部")
                    n = st.text_input("姓名", value=(existing["name"] if existing else ""), key=f"n_{i}", placeholder="姓名")
                    st.markdown('</div>', unsafe_allow_html=True)
                    unit_inputs.append(u)
                    name_inputs.append(n)
            submitted = st.form_submit_button("✅ 套用本輪名單", use_container_width=True)
            if submitted:
                with state["lock"]:
                    new_claims = []
                    for u, n in zip(unit_inputs, name_inputs):
                        u2, n2 = u.strip(), n.strip()
                        new_claims.append({"unit": u2, "name": n2} if n2 else None)
                    state["claims"] = new_claims
                st.success("已套用本輪名單 ✅")

        colA, colB, colC = st.columns(3)
        with colA:
            if st.button("🧹 清空本輪名單重填", use_container_width=True):
                with state["lock"]:
                    state["claims"] = [None] * SHEEP_COUNT
                    state["progress"] = [0] * SHEEP_COUNT
                    state["phase"] = "claiming"
                    state["winner_idx"] = None
                clear_roster_inputs()
                st.rerun()
        with colB:
            can_start = state["phase"] == "claiming" and any(state["claims"])
            if st.button("▶️ 開始比賽", disabled=not can_start, use_container_width=True):
                with state["lock"]:
                    state["progress"] = [0] * SHEEP_COUNT
                    state["phase"] = "racing"
                    state["winner_idx"] = None
                st.rerun()
        with colC:
            if st.button("🔁 開始下一輪（換下一組 QR）", use_container_width=True):
                with state["lock"]:
                    state["round"] = state["round"] + 1 if state["round"] < ROUND_COUNT else 1
                    state["claims"] = [None] * SHEEP_COUNT
                    state["progress"] = [0] * SHEEP_COUNT
                    state["phase"] = "claiming"
                    state["winner_idx"] = None
                clear_roster_inputs()
                st.rerun()

    if state["phase"] == "finished" and state["winner_idx"] is not None:
        w = state["claims"][state["winner_idx"]]
        name = w["name"] if w else f"第{state['winner_idx']+1}隻羊"
        unit = w["unit"] if w else ""
        st.markdown(f"""
        <div class="winner-box">
          <div class="fireworks-row">
            <span>🎉</span><span>🧨</span><span>✨</span><span>🧨</span><span>🎉</span>
          </div>
          <div style="font-size:1.4rem;color:#c2185b;letter-spacing:6px;font-weight:800;">丁未羊年 · 賽跑冠軍</div>
          <div style="font-size:5rem;margin:10px 0;">🐑🏆</div>
          <div style="font-size:1.3rem;color:#a15a3a;">{unit}</div>
          <div class="winner-name-huge">{name}</div>
          <div class="winner-blessing">{state['blessing']}</div>
          <div class="fireworks-row" style="margin-top:14px;">
            <span>🎊</span><span>🧨</span><span>🎆</span><span>🧨</span><span>🎊</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    elif state["phase"] == "claiming":
        cols = st.columns(SHEEP_COUNT)
        for i in range(SHEEP_COUNT):
            c = state["claims"][i]
            with cols[i]:
                if c:
                    st.markdown(f"""<div class="pen-box">🐑<br><b>{c['name']}</b><br>
                                 <span style="font-size:0.85rem;color:#a15a3a;">{c['unit']}</span></div>""",
                                unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="pen-box pen-empty">🐑<br>{i+1} 號羊<br>尚未設定</div>""",
                                unsafe_allow_html=True)

    else:  # racing — 草原賽道，每隻羊各自一條路往前跑
        for i in range(SHEEP_COUNT):
            c = state["claims"][i]
            if not c:
                continue
            name = c["name"]
            unit = c["unit"]
            real_pct = min(100, state["progress"][i] / TAPS_TO_FINISH * 100)
            show_pct = min(90, real_pct)  # 留空間讓羊在抵達終點旗前都看得到
            st.markdown(f"""
            <div class="race-lane">
              <div class="lane-name">{name}<span class="lane-unit">{unit}</span></div>
              <div class="grass-track">
                <div class="finish-flag">🏁</div>
                <div class="running-sheep" style="left:{show_pct}%;">🐑</div>
              </div>
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
# CONTROL (phone) — 不需要密碼，掃到哪張 QR 就直接對應哪隻羊
# =================================================================
elif role == "control":
    top_l, top_r = st.columns([5, 1])
    with top_l:
        st.title("🐑 羊年大賽跑")
    with top_r:
        if st.button("← 回首頁"):
            go_home()

    if "my_taps" not in st.session_state:
        st.session_state.my_taps = 0

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
        st.markdown('<div class="big-msg">⚠️ 這組連結沒有對應到有效的號碼牌<br>請確認掃到正確的 QR Code</div>', unsafe_allow_html=True)
        st.stop()

    if my_round is not None and my_round != state["round"]:
        st.markdown(f'<div class="big-msg">你的號碼牌是第 {my_round} 輪<br>目前是第 {state["round"]} 輪<br>請稍候輪到你時再操作 🙏</div>', unsafe_allow_html=True)
        st.stop()

    my_c = state["claims"][my_i]
    if not my_c:
        st.markdown(f'<div class="big-msg">你是 🐑 {my_i+1} 號羊<br>主控台尚未輸入你的姓名<br>請稍候…</div>', unsafe_allow_html=True)
        st.stop()

    if state["phase"] == "claiming":
        st.markdown(f"""
        <div class="big-msg">
          你是 🐑 {my_i+1} 號羊<br>
          <span class="huge-name">{my_c['name']}</span><br>
          {my_c['unit']}<br><br>
          等待主控台開始比賽…
        </div>
        """, unsafe_allow_html=True)

    elif state["phase"] == "racing":
        st.markdown(f'<div class="huge-name">🐑 {my_i+1} 號羊 · {my_c["name"]}</div>', unsafe_allow_html=True)
        if st.button("🏃 狂點衝刺！", use_container_width=True, key="tapbtn"):
            with state["lock"]:
                state["progress"][my_i] += 1
                st.session_state.my_taps += 1
        st.markdown(f'<div class="tap-count-big">已點擊 <b>{st.session_state.my_taps}</b> 下</div>', unsafe_allow_html=True)
        pct = min(100, int(state["progress"][my_i] / TAPS_TO_FINISH * 100))
        st.progress(pct / 100)

    elif state["phase"] == "finished":
        if state["winner_idx"] == my_i:
            st.markdown('<div class="big-msg">🏆 恭喜你第一名！<br>請看大螢幕公布結果！</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="big-msg">比賽結束！<br>請看大螢幕公布結果！</div>', unsafe_allow_html=True)
        st.caption("下一輪開始前，請等候工作人員發下一輪的號碼牌 QR Code。")
