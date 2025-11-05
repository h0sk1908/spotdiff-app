# app.py
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image
import streamlit as st

# -----------------------------
# 설정
# -----------------------------
BASE_DIR = Path("problems")
LEFT_NAMES = ["image_left.png", "image_left.jpg", "image_left.jpeg"]
RIGHT_NAMES = ["image_right.png", "image_right.jpg", "image_right.jpeg"]
TITLE_NAME = "제목.txt"
EXPLAIN_NAME = "해설.txt"

BOX_SIZE = 420
BG_COLOR = (0, 0, 0)
BUTTON_MAX = 16  # 1~16번

st.set_page_config(page_title="X-ray Quiz", layout="wide")

# -----------------------------
# 유틸
# -----------------------------
def _read_text(path: Path) -> str:
    # 윈도우 줄바꿈/UTF-8 BOM 제거 + 트림
    txt = path.read_text(encoding="utf-8")
    txt = txt.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff").rstrip()
    return txt

def _find_first_exist(folder: Path, candidates: List[str]) -> Optional[Path]:
    for name in candidates:
        p = folder / name
        if p.exists():
            return p
    return None

def fit_square(path: str, box_size: int = BOX_SIZE, bg_color=BG_COLOR) -> Image.Image:
    img = Image.open(path).convert("RGB")
    img.thumbnail((box_size, box_size), Image.LANCZOS)
    canvas = Image.new("RGB", (box_size, box_size), bg_color)
    x = (box_size - img.width) // 2
    y = (box_size - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas

@st.cache_data(show_spinner=False)
def scan_problems(base_dir: Path) -> List[Dict]:
    items: List[Dict] = []
    if not base_dir.exists():
        return items
    for sub in sorted([p for p in base_dir.iterdir() if p.is_dir()]):
        left_img = _find_first_exist(sub, LEFT_NAMES)
        right_img = _find_first_exist(sub, RIGHT_NAMES)
        title_txt = sub / TITLE_NAME
        expl_txt = sub / EXPLAIN_NAME
        if (left_img is None) or (right_img is None) or (not title_txt.exists()) or (not expl_txt.exists()):
            continue
        items.append({
            "folder": sub.name,
            "title": _read_text(title_txt),
            "image_left_path": str(left_img),
            "image_right_path": str(right_img),
            "explanation": _read_text(expl_txt),
        })
    return items

# -----------------------------
# 앱 UI
# -----------------------------
st.markdown(
    "<h1 style='text-align:center; margin-top:30px; margin-bottom:40px;'>X-ray Quiz</h1>",
    unsafe_allow_html=True
)

with st.sidebar:
    if st.button("문제 목록 다시 불러오기", use_container_width=True):
        scan_problems.clear()
        st.rerun()

problems = scan_problems(BASE_DIR)
if not problems:
    st.error("표시할 문제가 없습니다. 'problems/' 폴더를 확인하세요.")
    st.stop()

if "sel" not in st.session_state:
    st.session_state.sel = 0
if "answer" not in st.session_state:
    st.session_state.answer = None

def _reset_selection():
    st.session_state.answer = None

# -----------------------------
# 상단: 문제 선택 버튼(1~16)
# -----------------------------
st.markdown("<div style='text-align:center; font-size:20px; font-weight:600; margin-bottom:20px;'>문제 선택</div>", unsafe_allow_html=True)
cols = st.columns(BUTTON_MAX)
total = len(problems)
for i, col in enumerate(cols):
    label = f"{i+1}"
    enabled = i < total
    with col:
        if st.button(label, use_container_width=True, key=f"btn_{i}", disabled=not enabled):
            st.session_state.sel = i
            _reset_selection()
            st.rerun()

st.markdown("<div style='margin-top:25px;'></div>", unsafe_allow_html=True)

sel = min(st.session_state.sel, len(problems) - 1)
p = problems[sel]

# -----------------------------
# 문제 제목(작게) + 여백
# -----------------------------
st.markdown(
    f"<h4 style='text-align:center; margin-top:10px; margin-bottom:25px;'>{p['title']}</h4>",
    unsafe_allow_html=True
)

# -----------------------------
# 이미지(규칙적 간격 + 동일 크기)
# -----------------------------
left_sp, colA, gap, colB, right_sp = st.columns([1, 4, 0.8, 4, 1])
with colA:
    st.image(fit_square(p["image_left_path"]), width=BOX_SIZE)
with gap:
    st.write("")
with colB:
    st.image(fit_square(p["image_right_path"]), width=BOX_SIZE)

st.markdown("<div style='margin-top:35px;'></div>", unsafe_allow_html=True)

# -----------------------------
# O/X 버튼(초기 미선택, 누르면 해설 표시)
# -----------------------------
bcol1, bcol2, _ = st.columns([1, 1, 6])
with bcol1:
    if st.button("O", use_container_width=True, key=f"ans_o_{sel}"):
        st.session_state.answer = "O"
with bcol2:
    if st.button("X", use_container_width=True, key=f"ans_x_{sel}"):
        st.session_state.answer = "X"

# -----------------------------
# 해설: 줄바꿈 보존
# -----------------------------
if st.session_state.answer in ["O", "X"]:
    st.markdown("<div style='margin-top:25px;'></div>", unsafe_allow_html=True)
    st.markdown("**해설**")
    # 단락/줄바꿈 보존: \n → <br>
    expl_html = p["explanation"].replace("\n", "<br>")
    st.markdown(expl_html, unsafe_allow_html=True)
