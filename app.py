import os, time
from PIL import Image, ImageDraw
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="틀린그림찾기 - Capstone", page_icon="🧩", layout="wide")

RADIUS = 20
GT_RECTS = [(300, 140, 360, 200)]

def ensure_images():
    os.makedirs("images", exist_ok=True)
    n, l = "images/normal.png", "images/lesion.png"
    if not (os.path.exists(n) and os.path.exists(l)):
        W, H = 512, 512
        def base():
            img = Image.new("RGB", (W, H), "white")
            d = ImageDraw.Draw(img)
            for x in range(0, W, 64): d.line((x,0,x,H), fill=(230,230,230))
            for y in range(0, H, 64): d.line((0,y,W,y), fill=(230,230,230))
            d.rectangle((60,60,200,160), outline="black", width=3)
            d.ellipse((280,80,360,160), outline="black", width=3)
            d.rectangle((120,300,240,420), outline="black", width=3)
            return img
        base().save(n)
        img = base(); ImageDraw.Draw(img).rectangle((300,140,360,200), outline="red", width=3); img.save(l)
    return n, l

@st.cache_data
def load_image(path): return Image.open(path).convert("RGB")

def point_in_expanded_rect(x, y, rect, r):
    x1, y1, x2, y2 = rect
    return (x1-r) <= x <= (x2+r) and (y1-r) <= y <= (y2+r)

def score(clicks, rects, r):
    used=set(); tp=0
    for cx,cy in clicks:
        for i,rect in enumerate(rects):
            if i in used: continue
            if point_in_expanded_rect(cx,cy,rect,r): tp+=1; used.add(i); break
    fp=max(0,len(clicks)-tp); fn=len(rects)-len(used)
    prec=tp/(tp+fp) if tp+fp>0 else 0.0
    rec=tp/(tp+fn) if tp+fn>0 else 0.0
    f1=2*prec*rec/(prec+rec) if prec+rec>0 else 0.0
    return {"tp":tp,"fp":fp,"fn":fn,"precision":prec,"recall":rec,"f1":f1}

def draw_feedback(base_img, rects, clicks):
    vis=base_img.copy(); d=ImageDraw.Draw(vis,"RGBA")
    for x1,y1,x2,y2 in rects: d.rectangle((x1,y1,x2,y2), outline=(0,200,0,255), fill=(0,255,0,60), width=2)
    for cx,cy in clicks: d.ellipse((cx-6,cy-6,cx+6,cy+6), outline=(0,0,0,255), width=2)
    return vis

st.title("🧩 틀린그림찾기 — Capstone MVP")
st.caption("우측 이미지를 클릭한 뒤 [제출]을 누르세요. 정답은 녹색 사각형 기준입니다.")

n_path, l_path = ensure_images()
img_normal = load_image(n_path)
img_lesion = load_image(l_path)
W, H = img_lesion.size
if "t0" not in st.session_state: st.session_state.t0 = time.time()

colL, colR = st.columns(2, gap="large")
with colL:
    st.subheader("Normal")
    _ = st_canvas(fill_color="rgba(0,0,0,0)", stroke_width=1,
                  background_image=img_normal, height=H, width=W,
                  drawing_mode="transform", key="normal_canvas")
with colR:
    st.subheader("Lesion (클릭 대상)")
    c = st_canvas(fill_color="rgba(255,255,255,0.0)", stroke_width=2, stroke_color="#000000",
                  background_image=img_lesion, height=H, width=W,
                  drawing_mode="point", point_display_radius=6, key="lesion_canvas")

if st.button("✅ 제출", type="primary"):
    clicks=[]
    if c and c.json_data:
        for obj in c.json_data.get("objects", []):
            if obj.get("type")=="circle":
                cx = obj["left"] + obj.get("radius",6)*obj.get("scaleX",1.0)
                cy = obj["top"]  + obj.get("radius",6)*obj.get("scaleY",1.0)
                clicks.append((round(cx),round(cy)))
    ms=int((time.time()-st.session_state.t0)*1000)
    r=score(clicks, GT_RECTS, RADIUS)
    st.success(f"정답 {r['tp']} | 오답 {r['fp']} | 놓침 {r['fn']}")
    st.info(f"Precision {r['precision']:.2f} | Recall {r['recall']:.2f} | F1 {r['f1']:.2f} | Time {ms} ms")
    st.image(draw_feedback(img_lesion, GT_RECTS, clicks), caption="정답(녹색)·클릭(검정) 오버레이")

if st.button("🔄 리셋"):
    st.session_state.t0 = time.time()
    st.rerun()
