import streamlit as st
import random
import threading
import io
import base64
import qrcode
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="2027年生達年會 羊年大賽跑", page_icon="🐑", layout="wide")

SHEEP_COUNT = 6
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
        "base_url": "",
    }


state = get_shared_state()


def new_pin():
    return str(random.randint(1000, 9999))


def qr_image_base64(url: str) -> str:
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


st.markdown("""
<style>
.stApp{
    background:
      radial-gradient(circle at 20% 0%, rgba(143,31,31,0.5), transparent 55%),
      radial-gradient(circle at 85% 15%, rgba(200,138,58,0.22), transparent 50%),
      #1c1210;
    color:#f7ecd2;
}
h1,h2,h3{color:#ffd166 !important;}
.pen-box{
    background:linear-gradient(160deg,#331c14,#26170f);border:1px solid #c98a3a;
    border-radius:14px;padding:16px;text-align:center;margin-bottom:10px;
}
.pen-empty{color:#6b5a48;}
.lane-box{
    background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
    border-radius:14px;padding:10px 18px;margin-bottom:12px;
}
.lane-fill{
    background:linear-gradient(90deg,#e8b34d,#ffd166);height:26px;border-radius:13px;
}
.winner-box{
    text-align:center;background:radial-gradient(circle at center, rgba(143,31,31,0.96), rgba(20,10,8,0.98));
    border-radius:20px;padding:50px 20px;border:2px solid #ffd166;
}
.qr-card{
    background:#331c14;border:1px solid #c98a3a;border-radius:12px;padding:14px;text-align:center;
}
.qr-card img{background:#fff;padding:8px;border-radius:8px;}
</style>
""", unsafe_allow_html=True)


def go_home():
    st.query_params.clear()
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


role = st.query_params.get("role", None)
p_param = st.query_params.get("p", None)

# =================================================================
# HOME
# =================================================================
if role is None:
    st.markdown("<div class='eventname'>2027年生達年會</div>", unsafe_allow_html=True)
    st.title("🐑 羊年大賽跑")
    st.caption("喝完一瓶啤酒，狂點手機衝第一")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🖥️ 大螢幕主控")
        st.write("投影用，設定參賽者名單、產生 QR Code、顯示賽跑畫面與得獎公告")
        if st.button("進入大螢幕主控", use_container_width=True):
            st.query_params["role"] = "display"
            st.rerun()
    with c2:
        st.subheader("📱 參賽者掃碼進入")
        st.write("請用主控台產生的專屬 QR Code 掃碼進入，不要直接手動進這裡")
        if st.button("（測試用）手動進入認領畫面", use_container_width=True):
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

    with st.expander("⚙️ 主控台：設定參賽者名單", expanded=(state["phase"] == "claiming")):
        base_url = st.text_input(
            "這個網站的公開網址（貼一次即可，用來產生 QR Code）",
            value=state["base_url"],
            placeholder="例：https://sheep-race-xxxx.streamlit.app"
        )
        if base_url != state["base_url"]:
            with state["lock"]:
                state["base_url"] = base_url.strip()

        st.write("**輸入 6 位參賽者的單位與姓名：**")
        cols = st.columns(3)
        form_values = []
        for i in range(SHEEP_COUNT):
            with cols[i % 3]:
                existing = state["claims"][i]
                unit = st.text_input(f"{i+1} 號羊 - 單位", value=(existing["unit"] if existing else ""), key=f"u_{i}")
                name = st.text_input(f"{i+1} 號羊 - 姓名", value=(existing["name"] if existing else ""), key=f"n_{i}")
                form_values.append((unit.strip(), name.strip()))

        colA, colB, colC = st.columns(3)
        with colA:
            if st.button("✅ 設定名單並產生 QR Code", use_container_width=True):
                with state["lock"]:
                    if not state["pin"]:
                        state["pin"] = new_pin()
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
                    state["round"] += 1
                    state["claims"] = [None] * SHEEP_COUNT
                    state["progress"] = [0] * SHEEP_COUNT
                    state["phase"] = "claiming"
                    state["winner_idx"] = None

        if state["pin"] is None:
            with state["lock"]:
                state["pin"] = new_pin()
        st.success(f"通關密碼：**{state['pin']}**（口頭告知參賽者，不要投影出去）")

        if any(state["claims"]) and state["base_url"]:
            st.markdown("---")
            st.write("**參賽者專屬 QR Code：**")
            qcols = st.columns(3)
            for i in range(SHEEP_COUNT):
                c = state["claims"][i]
                if not c:
                    continue
                url = f"{state['base_url'].rstrip('/')}/?role=control&p={i}"
                img_b64 = qr_image_base64(url)
                with qcols[i % 3]:
                    st.markdown(f"""
                    <div class="qr-card">
                      <b>{c['name']}</b><br>
                      <span style="font-size:12px;color:#b39a72;">{c['unit']}</span><br>
                      <img src="data:image/png;base64,{img_b64}" width="150"><br>
                      <span style="font-size:10px;color:#8a7355;word-break:break-all;">{url}</span>
                    </div>
                    """, unsafe_allow_html=True)
        elif any(state["claims"]) and not state["base_url"]:
            st.warning("https://2027sheep-race-vxezm7iwzzxxsdcm2fjkgo.streamlit.app/?role=control")

    if state["phase"] == "finished" and state["winner_idx"] is not None:
        w = state["claims"][state["winner_idx"]]
        name = w["name"] if w else f"第{state['winner_idx']+1}隻羊"
        unit = w["unit"] if w else ""
        st.balloons()
        st.markdown(f"""
        <div class="winner-box">
          <div style="font-size:20px;color:#e8b34d;letter-spacing:6px;">丁未羊年 · 賽跑冠軍</div>
          <div style="font-size:80px;margin:10px 0;">🐑🏆</div>
          <div style="font-size:18px;color:#e0c69a;">{unit}</div>
          <div style="font-size:56px;font-weight:900;color:#ffd166;margin-bottom:16px;">{name}</div>
          <div style="font-size:30px;font-weight:800;">{state['blessing']}</div>
        </div>
        """, unsafe_allow_html=True)

    elif state["phase"] == "claiming":
        cols = st.columns(SHEEP_COUNT)
        for i in range(SHEEP_COUNT):
            c = state["claims"][i]
            with cols[i]:
                if c:
                    st.markdown(f"""<div class="pen-box">🐑<br><b>{c['name']}</b><br>
                                 <span style="font-size:12px;color:#b39a72;">{c['unit']}</span></div>""",
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
            st.markdown(f"**{name}** <span style='color:#b39a72;font-size:12px;'>{unit}</span>", unsafe_allow_html=True)
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

    my_i = None
    if p_param is not None:
        try:
            idx = int(p_param)
            if 0 <= idx < SHEEP_COUNT and state["claims"][idx]:
                my_i = idx
        except ValueError:
            pass

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

    if my_i is None:
        st.warning("這組連結沒有對應到有效的參賽者，請重新掃描主控台提供的 QR Code，或回首頁手動操作。")
        st.stop()

    my_c = state["claims"][my_i]

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
        st.caption("下一輪開始前，主控台會重新設定名單並產生新的 QR Code，請等候新的連結。")
