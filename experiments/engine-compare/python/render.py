"""Standalone 12 s Pillow/FFmpeg animation comparison. No TTS, no APIs."""
from __future__ import annotations
import argparse, json, math, subprocess, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT = next((p for p in (
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
) if Path(p).is_file()), None)
if FONT is None:
    raise RuntimeError("Noto Sans CJK must be installed")
def ease(t):
    x=max(0,min(1,t))
    return x*x*(3-2*x)
def font(size):
    return ImageFont.truetype(FONT,size)
def frame(spec,t):
    w,h,fps=(spec["video"][k] for k in ("width","height","fps"))
    canvas=Image.new("RGB",(w,h),spec["colors"]["background"])
    d=ImageDraw.Draw(canvas)
    d.text((w//2,46),spec["title"],font=font(27),fill="white",anchor="mm")
    d.line((64,79,w-64,79),fill="#41536f",width=2)
    caption=next((z["text"] for z in spec["captions"] if z["start"]<=t<z["end"]),spec["captions"][-1]["text"])
    d.text((w//2,319),caption,font=font(19),fill="white",anchor="mm")
    if t<3:
        a=ease((t-0.35)/0.7)
        if a>0:
            overlay=Image.new("RGBA",(w,h))
            draw=ImageDraw.Draw(overlay)
            draw.text((w//2,179),"情報が伝わる3つの形",anchor="mm",font=font(round(37+8*a)),fill=(255,255,255,round(255*a)))
            canvas=Image.alpha_composite(canvas.convert("RGBA"),overlay).convert("RGB")
        return canvas
    for s in spec["shapes"]:
        progress=ease((t-s["appears"])/0.6)
        if progress<=0: continue
        importance=(1-ease((t-7)/0.7)) if t>=7 and s["kind"]!="circle" else 1
        if importance<=0: continue
        alpha=round(255*progress*importance)
        x,y=s["x"],s["y"]+int(22*(1-progress))
        size=int(s["size"]*(0.7+0.3*progress))
        if t>=7 and s["kind"]=="circle":
            q=ease((t-7)/1.0)
            x=int(x+(w//2-x)*q)
            y=int(y+(185-y)*q)
            size=int(size*(1+0.35*q))
        half=size//2
        rgba=tuple(bytes.fromhex(s["color"].lstrip("#")))+(alpha,)
        ov=Image.new("RGBA",(w,h))
        od=ImageDraw.Draw(ov)
        if s["kind"]=="circle":od.ellipse((x-half,y-half,x+half,y+half),fill=rgba)
        elif s["kind"]=="triangle":od.polygon([(x,y-half),(x-half,y+half),(x+half,y+half)],fill=rgba)
        else:od.rounded_rectangle((x-half,y-half,x+half,y+half),radius=14,fill=rgba)
        od.text((x,y),s["label"],anchor="mm",font=font(18),fill=(15,31,53,alpha))
        canvas=Image.alpha_composite(canvas.convert("RGBA"),ov).convert("RGB")
    if t>=10:
        a=ease((t-10)/0.4)
        ov=Image.new("RGBA",(w,h))
        od=ImageDraw.Draw(ov)
        od.rounded_rectangle((160,120,480,260),radius=22,fill=(23,48,74,round(220*a)))
        od.text((w//2,185),"情報は一つずつ",anchor="mm",font=font(34),fill=(255,255,255,round(255*a)))
        canvas=Image.alpha_composite(canvas.convert("RGBA"),ov).convert("RGB")
    return canvas
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--spec",default="experiments/engine-compare/spec.json")
    p.add_argument("--output",default="build/engine-compare/python.mp4")
    p.add_argument("--frames",default="",help="Comma separated frame numbers; write PNG only")
    a=p.parse_args()
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
    w,h,fps=(spec["video"][k] for k in ("width","height","fps"))
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    n=round(fps*spec["video"]["duration_seconds"])
    if a.frames:
        for no in map(int,a.frames.split(",")):
            if no<0 or no>=n:raise ValueError("frame out of range")
            frame(spec,no/fps).save(out.parent/f"python-{no:03d}.png")
        return
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{w}x{h}","-r",str(fps),"-i","-","-an","-c:v","libx264","-crf","23","-pix_fmt","yuv420p","-movflags","+faststart",str(out)]
    start=time.monotonic()
    with subprocess.Popen(cmd,stdin=subprocess.PIPE) as proc:
        try:
            for i in range(n):proc.stdin.write(frame(spec,i/fps).tobytes())
        finally:proc.stdin.close()
        code=proc.wait()
        if code:raise RuntimeError(f"ffmpeg failed: {code}")
    print(json.dumps({"renderer":"python","frames":n,"seconds":round(time.monotonic()-start,3),"output":str(out)}))
if __name__=="__main__": main()
