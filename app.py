"""NanoWall — live feedback for an English lesson about nanotechnology."""

import csv
import hmac
import html
import sqlite3
from io import BytesIO, StringIO
from pathlib import Path

import qrcode
import streamlit as st


st.set_page_config(
    page_title="NanoWall · English Lesson",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_PATH = Path(__file__).with_name("feedback.db")


def database():
    # Separate connection per operation so multiple students can submit at once.
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.execute("PRAGMA busy_timeout=15000")
    return connection


def prepare_database():
    with database() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def save_feedback(message):
    with database() as connection:
        connection.execute(
            "INSERT INTO feedback (message) VALUES (?)", (message,)
        )


def load_feedback(limit=60):
    with database() as connection:
        if limit is None:
            return connection.execute(
                "SELECT id, message FROM feedback ORDER BY id DESC"
            ).fetchall()
        return connection.execute(
            "SELECT id, message FROM feedback ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()


def delete_feedback(message_id):
    with database() as connection:
        connection.execute("DELETE FROM feedback WHERE id = ?", (message_id,))


def clear_feedback():
    with database() as connection:
        connection.execute("DELETE FROM feedback")


def export_feedback_csv(messages):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Feedback (English)"])
    for message_id, message in messages:
        writer.writerow([message_id, message])
    return output.getvalue().encode("utf-8-sig")


def make_qr(url):
    code = qrcode.QRCode(box_size=8, border=2)
    code.add_data(url)
    code.make(fit=True)
    img = code.make_image(fill_color="#101932", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { color-scheme: dark; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp {
    background:
        radial-gradient(ellipse 650px 460px at 2% 2%, rgba(64, 209, 205, .12), transparent 72%),
        radial-gradient(ellipse 680px 500px at 100% 9%, rgba(147, 107, 255, .16), transparent 70%),
        radial-gradient(ellipse 520px 380px at 52% 96%, rgba(54, 109, 241, .10), transparent 76%),
        #0A1022;
}
.block-container { max-width: 1260px; padding-top: 2rem; padding-bottom: 4rem; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMarkdownContainer"] p { line-height: 1.5; }
.hero-tag { display: inline-block; padding: 7px 13px; border: 1px solid rgba(96, 239, 219, .35);
    border-radius: 999px; color: #70EDD7; background: rgba(35, 206, 190, .07);
    letter-spacing: .14em; font-size: .72rem; font-weight: 800; text-transform: uppercase; }
.hero-title { font-family: 'Space Grotesk', sans-serif; font-size: clamp(2.7rem, 6vw, 5.3rem);
    font-weight: 700; line-height: 1.06; letter-spacing: -.055em; margin: 16px 0 12px;
    color: #F6F8FF; }
.hero-title span { background: linear-gradient(110deg,#77FBE0 15%,#A78BFA 88%);
    -webkit-background-clip: text; background-clip: text; color: transparent; }
.hero-sub { color: #ABB6D4; font-size: 1.15rem; max-width: 660px; margin: 0 0 18px; }
.dividerline { height: 1px; background: linear-gradient(90deg,rgba(115,249,222,.5),rgba(150,118,255,.25),transparent);
    margin: 26px 0 24px; }
.wall-top { display: flex; flex-wrap: wrap; align-items: center; gap: 12px;
    justify-content: space-between; margin-bottom: 20px; }
.wall-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.45rem; font-weight: 700;
    color: #F6F8FF; }
.live-label { display: inline-flex; align-items: center; gap: 8px; color: #78F5D9;
    background: rgba(112,245,217,.08); padding: 7px 12px; border-radius: 999px;
    border: 1px solid rgba(112,245,217,.20); font-size: .80rem; }
.live-dot { height: 7px; width: 7px; display: inline-block; background: #78F5D9;
    border-radius: 50%; box-shadow: 0 0 11px #78F5D9; }
.feedback-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(265px,1fr)); gap: 17px; }
.feedback-card { min-height: 150px; padding: 22px 22px 18px; border-radius: 19px;
    border: 1px solid rgba(154,178,236,.19);
    background: linear-gradient(145deg,rgba(35,46,85,.88),rgba(20,31,57,.87));
    box-shadow: 0 12px 35px rgba(1,4,16,.16); }
.feedback-card:nth-child(3n+2) { border-top-color: rgba(172,137,255,.60); }
.feedback-card:nth-child(3n+3) { border-top-color: rgba(106,235,224,.60); }
.feedback-card-head { display: flex; justify-content: space-between; align-items: center;
    color: #9FACCB; text-transform: uppercase; letter-spacing: .1em;
    font-size: .69rem; font-weight: 800; margin-bottom: 20px; }
.feedback-card-head b { font-size: 1.15rem; color: #86F7DD; }
.feedback-text { font-family: 'Space Grotesk', sans-serif; color: #F6F7FF;
    font-size: 1.10rem; font-weight: 500; line-height: 1.55; overflow-wrap: anywhere;
    white-space: pre-wrap; }
.empty-wall { border: 1px dashed rgba(150,173,225,.27); border-radius: 24px;
    padding: 60px 24px; text-align: center; color: #B6C2DF;
    background: rgba(27,38,72,.30); }
.empty-wall strong { font-family: 'Space Grotesk', sans-serif; color: #F6F8FF;
    font-size: 1.45rem; display: block; margin-bottom: 8px; }
.form-heading { font-family: 'Space Grotesk', sans-serif; font-size: clamp(2rem, 5vw, 3.6rem);
    font-weight: 700; letter-spacing: -.04em; line-height: 1.15; color: #F7F9FF; margin: 20px 0 10px; }
.student-sub { color: #B5C1DF; font-size: 1.08rem; margin-bottom: 28px; }
.prompt-box { padding: 18px 20px; background: rgba(108,234,213,.08); color: #C6F4EB;
    border: 1px solid rgba(108,234,213,.23); border-radius: 15px; margin-bottom: 18px; }
.prompt-box span { font-size: .82rem; letter-spacing: .08em; text-transform: uppercase; color: #72EFD9; }
.prompt-box strong { color: #F5F9FF; display: block; font-size: 1.18rem; margin: 7px 0; }
.small-note { font-size: .90rem; color: #A4B3D0; }
[data-testid="stTextArea"] textarea { background: #182441; border: 1px solid #3A4C71;
    color: #F4F7FF; border-radius: 14px; font-size: 1.05rem; }
.stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(110deg,#79F9DE,#92B8FF); border: none; color: #0B1830;
    font-weight: 800; border-radius: 13px; padding: 10px 24px;
}
[data-testid="stImage"] img { border: 7px solid white; border-radius: 13px; }
@media (max-width: 650px) { .block-container { padding: 1.2rem .9rem 3rem; }
.hero-title { font-size: 2.9rem; } .feedback-grid { grid-template-columns: 1fr; } }
</style>
""",
    unsafe_allow_html=True,
)

prepare_database()
base_url = st.context.url.rstrip("/")
student_url = f"{base_url}/?view=student" if base_url.endswith(".app") else f"{base_url}?view=student"
wall_url = f"{base_url}/?view=wall" if base_url.endswith(".app") else f"{base_url}?view=wall"
admin_url = f"{base_url}/?view=admin" if base_url.endswith(".app") else f"{base_url}?view=admin"
view = st.query_params.get("view", "wall")

if view == "student":
    _, center, _ = st.columns([1, 2.4, 1])
    with center:
        st.markdown('<span class="hero-tag">🧬 ENGLISH · NANOTECHNOLOGY</span>', unsafe_allow_html=True)
        st.markdown('<div class="form-heading">Your voice.<br>Our <span style="color:#7CF3DA">future.</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="student-sub">Share one thought about today’s nanotechnology lesson.</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="prompt-box"><span>💬 Your reflection</span>'
            '<strong>What did you find interesting or learn today?</strong>'
            'Start with: “Today I learned...” or “I was surprised that...”</div>',
            unsafe_allow_html=True,
        )
        with st.form("send_feedback", clear_on_submit=True):
            message = st.text_area(
                "Write your feedback in English",
                placeholder="Today I learned that nanotechnology can...",
                height=155,
                max_chars=300,
            )
            submitted = st.form_submit_button("🚀 Send feedback", use_container_width=True)
        if submitted:
            if message.strip():
                save_feedback(message.strip())
                st.success("Your feedback is on the screen! Thank you. ✨")
                st.balloons()
            else:
                st.warning("Please write a short message first.")
        st.markdown('<p class="small-note">No name needed · English practice · Your message is shown on the class screen.</p>', unsafe_allow_html=True)
        st.link_button("↗ View the feedback wall", wall_url, use_container_width=True)
elif view == "admin":
    st.markdown('<span class="hero-tag">🧬 NANOWALL · TEACHER</span>', unsafe_allow_html=True)
    st.title("Панель преподавателя")
    st.link_button("← Вернуться к экрану отзывов", wall_url)

    # A password must be set in Streamlit Cloud → App settings → Secrets.
    # Never store this password in the public GitHub repository.
    try:
        admin_password = st.secrets.get("ADMIN_PASSWORD")
    except Exception:
        admin_password = None

    if not admin_password:
        st.error("Сначала задай ADMIN_PASSWORD в настройках Secrets на Streamlit Cloud.")
        st.code('ADMIN_PASSWORD = "сюда_свой_надёжный_пароль"', language="toml")
        st.stop()

    if not st.session_state.get("admin_authenticated", False):
        with st.form("admin_login"):
            password_input = st.text_input("Пароль преподавателя", type="password")
            login_clicked = st.form_submit_button("Войти", type="primary")
        if login_clicked:
            if hmac.compare_digest(password_input, str(admin_password)):
                st.session_state["admin_authenticated"] = True
                st.rerun()
            else:
                st.error("Неверный пароль")
        st.stop()

    if st.button("🔒 Выйти"):
        st.session_state["admin_authenticated"] = False
        st.rerun()

    messages = load_feedback(limit=None)
    st.metric("Всего отзывов", len(messages))

    if messages:
        st.download_button(
            "⬇️ Скачать все отзывы (CSV)",
            data=export_feedback_csv(messages),
            file_name="nanowall_feedback.csv",
            mime="text/csv",
        )

        with st.expander("🗑️ Очистить все отзывы", expanded=False):
            st.warning("Это удалит все отзывы без возможности восстановления. При необходимости сначала скачай CSV.")
            with st.form("confirm_clear_form"):
                confirmed = st.checkbox("Подтверждаю удаление всех отзывов")
                clear_clicked = st.form_submit_button("Удалить все отзывы", type="primary")
                if clear_clicked:
                    if confirmed:
                        clear_feedback()
                        st.rerun()
                    else:
                        st.error("Сначала отметь подтверждение")

        st.subheader("Отзывы студентов")
        for message_id, message in messages:
            with st.container(border=True):
                content_col, button_col = st.columns([5, 1], vertical_alignment="center")
                with content_col:
                    st.caption(f"Отзыв #{message_id}")
                    st.write(message)
                with button_col:
                    if st.button("Удалить", key=f"delete_{message_id}"):
                        delete_feedback(message_id)
                        st.rerun()
    else:
        st.info("Пока нет отзывов. Новые сообщения появятся здесь.")
else:
    left, right = st.columns([4.7, 1.2], gap="large", vertical_alignment="center")
    with left:
        st.markdown('<span class="hero-tag">🧬 ENGLISH CLASS · NANOTECHNOLOGY</span>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">Small ideas.<br><span>Big future.</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub">What did you learn about nanotechnology today? Share your thoughts in English.</div>', unsafe_allow_html=True)
        st.link_button("✍️ Write your feedback", student_url)
    with right:
        st.image(make_qr(student_url), width=158)
        st.caption("📱 Scan to leave feedback")

    st.markdown('<div class="dividerline"></div>', unsafe_allow_html=True)

    @st.fragment(run_every="2s")
    def show_live_wall():
        messages = load_feedback()
        st.markdown(
            f'<div class="wall-top"><span class="wall-title">Class feedback · {len(messages)} messages</span>'
            '<span class="live-label"><i class="live-dot"></i> LIVE · Updates automatically</span></div>',
            unsafe_allow_html=True,
        )
        if not messages:
            st.markdown(
                '<div class="empty-wall"><strong>💭 Your thoughts go here.</strong>'
                'Scan the QR code and be the first to share!</div>',
                unsafe_allow_html=True,
            )
        else:
            cards = []
            for message_id, message in messages:
                safe_text = html.escape(message, quote=True)
                cards.append(
                    f'<article class="feedback-card">'
                    f'<div class="feedback-card-head"><span>Anonymous student</span><b>✦</b></div>'
                    f'<div class="feedback-text">{safe_text}</div>'
                    f'</article>'
                )
            st.markdown(f'<div class="feedback-grid">{"".join(cards)}</div>', unsafe_allow_html=True)

    show_live_wall()

