"""NanoWall v2 — live, emoji-powered class feedback for a nanotechnology English lesson.

Deployment: Streamlit Community Cloud. Only the teacher's admin view requires
ADMIN_PASSWORD in Streamlit Cloud Secrets; never place it in a public repository.
"""

import csv
import hmac
import html
import sqlite3
from contextlib import contextmanager
from io import BytesIO, StringIO
from pathlib import Path

import qrcode
import streamlit as st

st.set_page_config(
    page_title="NanoWall ✨ · Nanotechnology",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_PATH = Path(__file__).with_name("feedback.db")
REACTIONS = {
    "💡": "I learned something",
    "🤯": "Mind-blowing!",
    "🚀": "I'm inspired",
    "🧬": "I want to know more",
}


@contextmanager
def database():
    connection = sqlite3.connect(DB_PATH, timeout=20)
    connection.execute("PRAGMA busy_timeout=20000")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def prepare_database():
    with database() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(feedback)")}
        if "reaction" not in columns:
            # Works with the previous NanoWall database as well.
            connection.execute("ALTER TABLE feedback ADD COLUMN reaction TEXT NOT NULL DEFAULT '💬'")
        if "student_name" not in columns:
            # Older anonymous feedback remains visible after upgrading.
            connection.execute(
                "ALTER TABLE feedback ADD COLUMN student_name TEXT NOT NULL DEFAULT 'Anonymous student'"
            )


def save_feedback(student_name, message, reaction):
    with database() as connection:
        connection.execute(
            "INSERT INTO feedback (student_name, message, reaction) VALUES (?, ?, ?)",
            (student_name, message, reaction if reaction in REACTIONS else "💡"),
        )


def load_feedback(limit=60):
    with database() as connection:
        if limit is None:
            return connection.execute(
                "SELECT id, student_name, message, reaction FROM feedback ORDER BY id DESC"
            ).fetchall()
        return connection.execute(
            "SELECT id, student_name, message, reaction FROM feedback ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def feedback_count():
    with database() as connection:
        return connection.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]


def delete_feedback(message_id):
    with database() as connection:
        connection.execute("DELETE FROM feedback WHERE id = ?", (message_id,))


def clear_feedback():
    with database() as connection:
        connection.execute("DELETE FROM feedback")


def csv_safe(value):
    # Prevent spreadsheet programs from treating student text as formulas.
    value = str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def export_feedback_csv(messages):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Student name", "Feedback (English)", "Reaction"])
    for message_id, student_name, message, reaction in messages:
        writer.writerow([message_id, csv_safe(student_name), csv_safe(message), reaction])
    return output.getvalue().encode("utf-8-sig")


def make_qr(url):
    code = qrcode.QRCode(box_size=8, border=2)
    code.add_data(url)
    code.make(fit=True)
    img = code.make_image(fill_color="#152343", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { color-scheme: dark; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp {
    color: #F4F7FF;
    background:
      radial-gradient(ellipse 53% 35% at 6% 2%, rgba(35,216,198,.17), transparent 72%),
      radial-gradient(ellipse 42% 32% at 100% 12%, rgba(163,103,255,.18), transparent 70%),
      radial-gradient(ellipse 50% 30% at 50% 100%, rgba(40,103,225,.12), transparent 75%),
      #090E21;
}
/* A faint molecular-dot pattern instead of heavy background images. */
.stApp::before {
    content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
    background-image:radial-gradient(circle,rgba(160,183,250,.24) 1px,transparent 1px);
    background-size:34px 34px; opacity:.22;
    -webkit-mask-image:linear-gradient(to bottom,black,transparent 95%);
    mask-image:linear-gradient(to bottom,black,transparent 95%);
}
.block-container { position:relative; z-index:1; max-width:1240px; padding-top:1.5rem; padding-bottom:4rem; }
[data-testid="stHeader"] { background:transparent; }
#MainMenu, footer { visibility:hidden; }
[data-testid="stMarkdownContainer"] p { line-height:1.6; }
h1, h2, h3 { font-family:'Space Grotesk',sans-serif; }
.nw-header { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:12px;
    padding:10px 0 30px; }
.nw-brand { display:flex; gap:10px; align-items:center; color:#F6F8FF; font-weight:800;
    font-family:'Space Grotesk',sans-serif; font-size:1.08rem; letter-spacing:-.03em; }
.nw-brand-icon { display:inline-flex; width:36px; height:36px; align-items:center; justify-content:center;
    border-radius:12px; border:1px solid rgba(114,245,223,.3); background:rgba(104,236,219,.10); font-size:1.3rem; }
.nw-pill { border-radius:999px; padding:7px 13px; color:#BDD4EF; background:rgba(151,165,217,.08);
    border:1px solid rgba(150,171,228,.19); font-size:.78rem; font-weight:750; letter-spacing:.03em; }
.nw-eyebrow { display:inline-flex; align-items:center; gap:7px; border-radius:999px;
    padding:9px 13px; background:rgba(85,230,209,.09); color:#75F5DD; border:1px solid rgba(117,245,221,.23);
    text-transform:uppercase; letter-spacing:.13em; font-weight:850; font-size:.72rem; }
.nw-title { font-family:'Space Grotesk',sans-serif; font-size:clamp(3rem,6.7vw,6.2rem);
    line-height:1.01; letter-spacing:-.065em; font-weight:700; color:#F7F8FF; margin:22px 0 21px; }
.nw-title .gradient { background:linear-gradient(98deg,#74F9DB 12%,#9ECAFF 57%,#D3A2FF);
    -webkit-background-clip:text; background-clip:text; color:transparent; }
.nw-desc { color:#B2C1DF; font-size:clamp(1.04rem,1.4vw,1.2rem); line-height:1.65;
    max-width:630px; margin-bottom:21px; }
.nw-sparks { display:flex; gap:10px; flex-wrap:wrap; margin-top:15px; }
.nw-spark { display:inline-flex; align-items:center; gap:7px; border-radius:999px; padding:7px 12px;
    font-weight:600; color:#C4D2EA; font-size:.83rem; border:1px solid rgba(130,157,228,.2);
    background:rgba(23,36,68,.62); }
/* Orbit illustration drawn entirely with CSS. */
.nano-scene { margin:12px auto 25px; max-width:280px; height:235px; position:relative; }
.nano-glow { position:absolute; inset:36px; border-radius:50%; background:radial-gradient(circle,rgba(111,248,216,.24),rgba(111,119,238,.05) 65%,transparent 70%);
    filter:blur(15px); }
.nano-ring { position:absolute; width:185px; height:185px; left:50%; top:50%; margin:-92.5px 0 0 -92.5px;
    border:2px solid rgba(123,231,228,.52); border-radius:50%; transform:rotate(30deg) scaleY(.55);
    box-shadow:0 0 18px rgba(88,207,216,.08); }
.nano-ring.r2 { transform:rotate(90deg) scaleY(.55); border-color:rgba(171,137,253,.52); }
.nano-ring.r3 { transform:rotate(150deg) scaleY(.55); border-color:rgba(126,190,251,.45); }
.nano-core { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
    width:92px; height:92px; display:flex; align-items:center; justify-content:center; font-size:2.95rem;
    border-radius:30px; background:linear-gradient(145deg,rgba(91,233,209,.23),rgba(141,110,255,.3));
    border:1px solid rgba(153,244,226,.45); box-shadow:0 0 45px rgba(87,237,206,.16);
    animation:floatCore 5s ease-in-out infinite; }
.nano-dot { position:absolute; width:14px; height:14px; border-radius:50%; z-index:3;
    background:#7DF9DA; box-shadow:0 0 16px rgba(125,249,218,.85); }
.nano-dot.d1 { top:35px; left:81px; animation:orbitFloat 4s ease-in-out infinite; }
.nano-dot.d2 { bottom:22px; right:67px; background:#B6A0FF; box-shadow:0 0 18px rgba(182,160,255,.8); animation:orbitFloat 5s ease-in-out infinite reverse; }
.nano-dot.d3 { top:91px; right:29px; width:10px; height:10px; background:#8BD2FF; box-shadow:0 0 14px rgba(139,210,255,.8); }
@keyframes floatCore { 0%,100%{transform:translate(-50%,-50%)} 50%{transform:translate(-50%,-58%)} }
@keyframes orbitFloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-9px)} }
.nw-orbit-caption { text-align:center; color:#A4B7D8; font-size:.84rem; margin-top:-8px; letter-spacing:.05em; }
.nw-qr-head { text-align:center; font-size:.85rem; font-weight:800; color:#75F4DA;
    margin-bottom:8px; text-transform:uppercase; letter-spacing:.12em; }
.nw-divider { margin:26px 0 24px; height:1px;
    background:linear-gradient(90deg,rgba(118,252,224,.45),rgba(189,154,255,.33),transparent); }
.nw-section-title { font-family:'Space Grotesk',sans-serif; color:#F4F8FF;
    font-size:clamp(1.45rem,2.7vw,2rem); line-height:1.2; letter-spacing:-.03em; font-weight:700; }
.nw-section-sub { color:#99AACD; font-size:.94rem; margin-top:5px; }
.nw-live { display:inline-flex; align-items:center; gap:8px; padding:8px 13px;
    border:1px solid rgba(104,240,198,.30); background:rgba(59,195,156,.11); color:#8CFADC;
    font-size:.74rem; font-weight:800; letter-spacing:.09em; border-radius:999px; }
.nw-live-dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:#79FFD5;
    box-shadow:0 0 10px #79FFD5; animation:blink 2s ease-in-out infinite; }
@keyframes blink {50%{opacity:.35} }
.nw-wall-meta {display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:20px;}
.nw-stats { display:flex; flex-wrap:wrap; gap:7px; align-items:center; margin:13px 0 22px; }
.nw-stat { background:rgba(22,34,61,.7); border:1px solid rgba(136,163,231,.16);
    border-radius:10px; padding:7px 11px; color:#C3CEE7; font-size:.88rem; }
.nw-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(255px,1fr)); gap:16px; }
.nw-card { padding:22px 21px; border-radius:19px; background:linear-gradient(145deg,rgba(31,45,77,.96),rgba(20,29,55,.92));
    border:1px solid rgba(139,171,230,.22); box-shadow:0 14px 38px rgba(3,6,17,.15);
    min-height:165px; transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease; }
.nw-card:hover { transform:translateY(-4px); border-color:rgba(127,244,217,.55); box-shadow:0 15px 45px rgba(46,195,182,.12); }
.nw-card:nth-child(4n+2) { border-top:2px solid #BB9EFF; }
.nw-card:nth-child(4n+3) { border-top:2px solid #76DDFF; }
.nw-card:nth-child(4n+4) { border-top:2px solid #FFC78D; }
.nw-card:nth-child(4n+1) { border-top:2px solid #77F5DA; }
.nw-card-top { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:18px; }
.nw-student { display:inline-flex; align-items:center; min-width:0; gap:9px; color:#F2F8FF;
    font-weight:800; font-size:.96rem; overflow-wrap:anywhere; }
.nw-student-avatar {flex:none; width:35px; height:35px; display:inline-flex; align-items:center;
    justify-content:center; border-radius:11px; background:linear-gradient(130deg,#70EFD4,#A997FF);
    color:#0E1732; font-size:1.02rem; font-weight:900; }
.nw-reaction { display:flex; align-items:center; justify-content:center; width:42px; height:42px;
    border-radius:14px; font-size:1.45rem; background:rgba(105,120,206,.13); border:1px solid rgba(138,154,229,.16); }
.nw-message { color:#F7F8FF; font-family:'Space Grotesk',sans-serif; font-size:1.12rem;
    line-height:1.56; font-weight:500; overflow-wrap:anywhere; white-space:pre-wrap; }
.nw-empty { border:1px dashed rgba(135,170,238,.33); background:rgba(30,45,80,.38);
    border-radius:22px; text-align:center; padding:50px 18px; color:#B4C2DF; }
.nw-empty-emoji {font-size:3.3rem; display:block; margin-bottom:12px; animation:floatCore 5s ease-in-out infinite;}
.nw-empty b { display:block; color:#F7F8FF; font-family:'Space Grotesk',sans-serif; font-size:1.5rem; margin-bottom:8px; }
.nw-student-title { font-family:'Space Grotesk',sans-serif; font-size:clamp(2.7rem,6vw,4.35rem);
    line-height:1.05; letter-spacing:-.055em; font-weight:700; color:#F8F9FF; margin:20px 0 14px; }
.nw-student-title span { background:linear-gradient(100deg,#79F7D9,#B7A0FE);
    -webkit-background-clip:text; background-clip:text; color:transparent; }
.nw-card-prompt { border-radius:18px; padding:18px 22px; margin:21px 0;
    border:1px solid rgba(116,247,215,.25); background:linear-gradient(140deg,rgba(36,103,112,.22),rgba(86,63,158,.13)); }
.nw-card-prompt small { color:#75F3DA; letter-spacing:.12em; text-transform:uppercase; font-size:.7rem; font-weight:900; }
.nw-card-prompt strong { display:block; font-size:1.14rem; color:#F4FBFF; margin:7px 0 9px; }
.nw-card-prompt p { color:#B6CCE0; margin:0; font-size:.92rem; }
.nw-input-caption { color:#A1B4D6; font-size:.88rem; margin-bottom:13px; }
.nw-footer { text-align:center; font-size:.8rem; color:#7F93B5; margin-top:40px; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { background:#141F3A; border:1px solid #3B5077;
    border-radius:16px; color:#F5FAFF; font-size:1.04rem; }
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color:#7EF7DE; box-shadow:0 0 0 1px rgba(126,247,222,.24); }
[data-testid="stRadio"] label { color:#E7EDFF; }
[data-testid="stRadio"] div[role="radiogroup"] { gap:9px; flex-wrap:wrap; }
[data-testid="stFormSubmitButton"] button[kind="primary"],
.stButton button[kind="primary"] { background:linear-gradient(103deg,#76F6D9,#A2C6FF); color:#10223E;
    border:0; border-radius:13px; font-weight:850; }
[data-testid="stLinkButton"] a { border-radius:13px; border-color:rgba(142,196,235,.3); }
[data-testid="stImage"] img { border-radius:15px; border:7px solid #fff; }
@media(max-width:768px) {
    .block-container {padding:1rem .95rem 3rem;}
    .nw-title {font-size:3.25rem;}
    .nw-header {padding-bottom:12px;}
    .nw-grid {grid-template-columns:1fr;}
    .nano-scene {height:165px;transform:scale(.77);margin:-4px auto 0;}
    .nw-orbit-caption {margin-top:0;}
}
@media(prefers-reduced-motion:reduce) { .nw-live-dot,.nano-core,.nano-dot,.nw-empty-emoji {animation:none!important;} .nw-card {transition:none;} }
</style>
""",
    unsafe_allow_html=True,
)


def header(right_label="🌟 ENGLISH • NANOTECHNOLOGY"):
    st.markdown(
        '<div class="nw-header"><div class="nw-brand"><span class="nw-brand-icon">🧬</span>'
        '<span>NanoWall <span style="color:#77F8DD">✦</span></span></div>'
        f'<span class="nw-pill">{html.escape(right_label)}</span></div>',
        unsafe_allow_html=True,
    )


def url_with_view(base_url, view):
    # st.context.url is the public app URL on Streamlit Cloud.
    return f"{base_url.rstrip('/')}/?view={view}"


prepare_database()
base_url = st.context.url
wall_url = url_with_view(base_url, "wall")
student_url = url_with_view(base_url, "student")
view = st.query_params.get("view", "wall")

if view == "student":
    header("📱 STUDENT SPACE")
    _, center, _ = st.columns([1, 2.7, 1])
    with center:
        st.markdown('<span class="nw-eyebrow">✨ Your name. Your ideas.</span>', unsafe_allow_html=True)
        st.markdown('<div class="nw-student-title">Your voice.<br><span>Our future. 🚀</span></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="nw-desc">Take 20 seconds to tell us what you discovered '
            'about the tiny world of nanotechnology. In English, of course! 🇬🇧</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="nw-card-prompt"><small>💭 Today\'s reflection</small>'
            '<strong>What surprised you or what did you learn today?</strong>'
            '<p>💡 “Today I learned that...”<br>🔬 “I was surprised that...”<br>'
            '🌍 “Nanotechnology could change...”</p></div>',
            unsafe_allow_html=True,
        )
        with st.form("send_feedback", clear_on_submit=True):
            student_name = st.text_input(
                "👩‍🎓 Your name / Имя студента",
                placeholder="e.g. Amina / Амина",
                max_chars=40,
            )
            reaction = st.radio(
                "Choose an emoji for your thoughts ✨",
                options=list(REACTIONS),
                format_func=lambda emoji: f"{emoji} {REACTIONS[emoji]}",
                horizontal=True,
            )
            message = st.text_area(
                "✍️ Write your feedback in English",
                placeholder="Today I learned that nanotechnology can help doctors...",
                height=145,
                max_chars=300,
            )
            submitted = st.form_submit_button("🚀 Send to the wall", type="primary", use_container_width=True)
        if submitted:
            if not student_name.strip():
                st.warning("👩‍🎓 Please write your name first!")
            elif not message.strip():
                st.warning("✍️ Write a short sentence first, please!")
            else:
                save_feedback(student_name.strip(), message.strip(), reaction)
                st.success("✨ Sent! Your name and feedback are now on the class wall.")
                st.balloons()
        st.markdown(
            '<p class="nw-input-caption">🧑‍🎓 Your name will appear with your message &nbsp; • &nbsp; '
            '💬 Visible on the classroom screen &nbsp; • &nbsp; 💙 Be kind</p>',
            unsafe_allow_html=True,
        )
        st.link_button("👀 See the feedback wall", wall_url, use_container_width=True)
        st.markdown('<p class="nw-footer">Made for curious minds 🔬✨</p>', unsafe_allow_html=True)

elif view == "admin":
    header("🔐 TEACHER ONLY")
    st.markdown('<div class="nw-section-title">🛠️ Панель преподавателя</div>', unsafe_allow_html=True)
    st.markdown('<p class="nw-section-sub">Управление отзывами студентов</p>', unsafe_allow_html=True)
    st.link_button("⬅️ На экран отзывов", wall_url)

    try:
        admin_password = st.secrets.get("ADMIN_PASSWORD")
    except Exception:
        admin_password = None

    if not admin_password:
        st.error("Установи ADMIN_PASSWORD в Streamlit Cloud → App settings → Secrets.")
        st.code('ADMIN_PASSWORD = "придумай_свой_пароль"', language="toml")
        st.stop()

    if not st.session_state.get("admin_authenticated", False):
        with st.form("admin_login"):
            password_input = st.text_input("Пароль преподавателя", type="password")
            login_clicked = st.form_submit_button("🔓 Войти", type="primary")
        if login_clicked:
            if hmac.compare_digest(password_input, str(admin_password)):
                st.session_state["admin_authenticated"] = True
                st.rerun()
            else:
                st.error("Неверный пароль")
        st.stop()

    if st.button("🔒 Выйти из панели"):
        st.session_state["admin_authenticated"] = False
        st.rerun()

    messages = load_feedback(limit=None)
    st.metric("💬 Всего отзывов", len(messages))

    if messages:
        st.download_button(
            "📥 Скачать отзывы (CSV)",
            data=export_feedback_csv(messages),
            file_name="nanowall_feedback.csv",
            mime="text/csv",
        )
        with st.expander("🗑️ Очистить все отзывы", expanded=False):
            st.warning("Все отзывы исчезнут без возможности восстановления. При необходимости сначала скачай CSV.")
            with st.form("confirm_clear_form"):
                confirmed = st.checkbox("Да, я хочу удалить все сообщения")
                clear_clicked = st.form_submit_button("🗑️ Удалить всё", type="primary")
                if clear_clicked:
                    if confirmed:
                        clear_feedback()
                        st.rerun()
                    else:
                        st.error("Сначала поставь галочку подтверждения")

        st.markdown("### 📝 Сообщения студентов")
        for message_id, student_name, message, reaction in messages:
            with st.container(border=True):
                content_col, button_col = st.columns([5, 1], vertical_alignment="center")
                with content_col:
                    st.caption(f"{reaction} {student_name} · отзыв #{message_id}")
                    st.write(message)
                with button_col:
                    if st.button("🗑️ Удалить", key=f"delete_{message_id}"):
                        delete_feedback(message_id)
                        st.rerun()
    else:
        st.info("✨ Пока нет отзывов. После нового занятия они появятся здесь.")

else:
    header("🔬 NANOTECHNOLOGY • ENGLISH CLASS")
    left, right = st.columns([3.4, 1.5], gap="large", vertical_alignment="center")
    with left:
        st.markdown('<span class="nw-eyebrow">✦ Welcome to the nano universe</span>', unsafe_allow_html=True)
        st.markdown('<div class="nw-title">Tiny things.<br><span class="gradient">Big ideas. ✨</span></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="nw-desc">Your thoughts are powerful, even when the science is tiny! '
            'Share what you learned about <strong style="color:#E6FCF9">nanotechnology</strong> '
            'and watch our classroom wall come alive. ⚛️</div>',
            unsafe_allow_html=True,
        )
        st.link_button("✍️ Write your reflection →", student_url, type="primary")
        st.markdown(
            '<div class="nw-sparks"><span class="nw-spark">🧬 Science</span>'
            '<span class="nw-spark">💡 Discovery</span>'
            '<span class="nw-spark">🚀 The future</span>'
            '<span class="nw-spark">🇬🇧 English</span></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            '<div class="nano-scene"><div class="nano-glow"></div><div class="nano-ring"></div>'
            '<div class="nano-ring r2"></div><div class="nano-ring r3"></div>'
            '<span class="nano-core">🧬</span><span class="nano-dot d1"></span>'
            '<span class="nano-dot d2"></span><span class="nano-dot d3"></span></div>'
            '<div class="nw-orbit-caption">⚛️ Small scale, endless possibilities</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="nw-qr-head">📱 Scan & share</div>', unsafe_allow_html=True)
        _, qr_col, _ = st.columns([1, 2.4, 1])
        with qr_col:
            st.image(make_qr(student_url), use_container_width=True)

    st.markdown('<div class="nw-divider"></div>', unsafe_allow_html=True)

    @st.fragment(run_every="2s")
    def show_live_wall():
        messages = load_feedback()
        total = feedback_count()
        st.markdown(
            '<div class="nw-wall-meta"><div>'
            '<div class="nw-section-title">💬 Our idea wall</div>'
            f'<div class="nw-section-sub">{total} thoughts shared by our class ✨</div>'
            '</div><span class="nw-live"><span class="nw-live-dot"></span> LIVE NOW</span></div>',
            unsafe_allow_html=True,
        )
        if messages:
            amounts = {reaction: 0 for reaction in REACTIONS}
            for _, _, _, reaction in messages:
                if reaction in amounts:
                    amounts[reaction] += 1
            stats = "".join(
                f'<span class="nw-stat">{emoji} {count}</span>'
                for emoji, count in amounts.items() if count
            )
            if stats:
                st.markdown(f'<div class="nw-stats">{stats}</div>', unsafe_allow_html=True)
            cards = []
            for message_id, student_name, message, reaction in messages:
                safe_name = html.escape(student_name, quote=True)
                safe_initial = html.escape(student_name[:1].upper() or "?", quote=True)
                safe_message = html.escape(message, quote=True)
                safe_reaction = html.escape(reaction if reaction in REACTIONS else "💬")
                cards.append(
                    '<article class="nw-card"><div class="nw-card-top">'
                    f'<span class="nw-student"><span class="nw-student-avatar">{safe_initial}</span>'
                    f'<span>{safe_name}</span></span>'
                    f'<span class="nw-reaction">{safe_reaction}</span></div>'
                    f'<div class="nw-message">{safe_message}</div></article>'
                )
            st.markdown(f'<div class="nw-grid">{"".join(cards)}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="nw-empty"><span class="nw-empty-emoji">💌</span>'
                '<b>Your ideas belong here!</b>Scan the QR code to leave the first message. 🚀</div>',
                unsafe_allow_html=True,
            )

    show_live_wall()
    st.markdown('<p class="nw-footer">🧬 NanoWall · Every big idea starts small ✨</p>', unsafe_allow_html=True)

