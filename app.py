import time
from io import BytesIO
from typing import List, Tuple
from PIL import Image, ImageDraw
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="Spot-the-Difference MVP", layout="wide")

IMG_NORMAL_PATH = "images/normal.png"
IMG_LESION_PATH = "images/lesion.png"

# 정답 영역과 판정 반경(px)
GT_RECTS: List[Tuple[int,int,int,int]] = [(300, 140, 360, 200)]
RADIUS = 20

@st.cache_data
def load_image(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")

def point_in_expanded_rect(x, y, rect, r):
    x1, y1, x2, y2 = rect
    return (x1 - r) <= x <= (x2 + r) and (y1 - r) <= y <= (y2 + r)

def score_clicks(clicks, rects, r):
    used = set(); tp = 0
    for (cx, cy) in clicks:
        hit_idx = None
        for i, rect in enumerate(rects):
            if i in used:
                continue
            if point_in_expanded_rect(cx, cy, rect, r):
                hit_idx = i; break
        if hit_idx is not None:
            tp += 1; used.add(hit_idx)
    fp = max(0, len(clicks) - tp)
    fn = len(rects) - len(used)
    prec = tp/(tp+fp) if (tp+fp)>0 else 0.0
    rec  = tp/(tp+fn) if (tp+fn)>0 else 0.0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec, "f1": f1}

def draw_feedback(base_img: Image.Image, rects, clicks):
    vis = base_img.copy()
    d = ImageDraw.Draw(vis, "RGBA")
    # 정답 박스
    for (x1,y1,x2,y2) in rects:
        d.rectangle((x1,y1,x2,y2), outline=(0,200,0,255), fill=(0,255,0,60), width=2)
    # 클릭 포인트
    for (cx, cy) in clicks:
        d.ellipse((cx-6, cy-6, cx+6, cy+6), outline=(0,0,0,255), width=2)
    return vis

# 데이터 로드
img_normal = load_image(IMG_NORMAL_PATH)
img_lesion = load_image(IMG_LESION_PATH)
W, H = img_lesion.size

# 상태 초기화
if "clicks" not in st.session_state:
    st.session_state.clicks = []
if "t0" not in st.session_state:
    st.session_state.t0 = time.time()

st.title("틀린그림찾기 — 최소 실행 버전(MVP)")
st.caption("우측 이미지를 클릭해 포인트를 추가하십시오. [제출]로 채점합니다.")

colL, colR = st.columns(2, gap="large")

with colL:
    st.subheader("Normal")
    st.image(img_normal, caption="참고용", use_container_width=False)

with colR:
    st.subheader("Lesion (클릭 대상)")
    # 현재까지의 클릭을 시각화한 오버레이 이미지 생성
    overlay = draw_feedback(img_lesion, [], st.session_state.clicks)
    # 이미지를 클릭하여 좌표 1개를 반환
    coord = streamlit_image_coordinates(overlay, key="lesion_click")
    # 클릭이 발생하면 저장
    if coord and ("x" in coord and "y" in coord):
        st.session_state.clicks.append((int(coord["x"]), int(coord["y"])))
        st.rerun()

# 조작 버튼
b1, b2, b3 = st.columns(3)
with b1:
    if st.button("되돌리기(Undo)"):
        if st.session_state.clicks:
            st.session_state.clicks.pop()
        st.rerun()
with b2:
    if st.button("초기화(Reset)"):
        st.session_state.clicks = []
        st.session_state.t0 = time.time()
        st.rerun()
with b3:
    submitted = st.button("제출", type="primary")

# 결과
st.write(f"현재 클릭 수: {len(st.session_state.clicks)}")
if submitted:
    time_ms = int((time.time() - st.session_state.t0) * 1000)
    result = score_clicks(st.session_state.clicks, GT_RECTS, RADIUS)
    st.write(f"**TP {result['tp']} / FP {result['fp']} / FN {result['fn']}**")
    st.write(
        f"Precision {result['precision']:.2f} | Recall {result['recall']:.2f} "
        f"| F1 {result['f1']:.2f} | Time {time_ms} ms"
    )
    st.image(draw_feedback(img_lesion, GT_RECTS, st.session_state.clicks),
             caption="정답(녹색)과 클릭(검정) 오버레이")
