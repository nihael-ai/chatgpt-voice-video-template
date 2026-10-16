import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import spec from '../../spec.json';
const ease=(n:number)=>{const x=Math.max(0,Math.min(1,n));return x*x*(3-2*x);};
const typographic:React.CSSProperties={fontFamily:'"Noto Sans CJK JP",sans-serif',fontWeight:700};
const Shape:React.FC<{s:(typeof spec.shapes)[number];t:number}>=({s,t})=>{
  const p=ease((t-s.appears)/0.6);
  if(p<=0)return null;
  const prominence=(t>=7&&s.kind!=='circle')?1-ease((t-7)/0.7):1;
  if(prominence<=0)return null;
  let x=s.x,y=s.y+Math.trunc(22*(1-p)),size=Math.trunc(s.size*(0.7+0.3*p));
  if(t>=7&&s.kind==='circle'){
    const q=ease((t-7)/1);x=Math.trunc(x+(spec.video.width/2-x)*q);
    y=Math.trunc(y+(185-y)*q);size=Math.trunc(size*(1+0.35*q));
  }
  const half=size/2;
  return <g opacity={p*prominence}>
    {s.kind==='circle'?<circle cx={x} cy={y} r={half} fill={s.color}/>:
    s.kind==='triangle'?<polygon points={x+','+(y-half)+' '+(x-half)+','+(y+half)+' '+(x+half)+','+(y+half)} fill={s.color}/>:
    <rect x={x-half} y={y-half} width={size} height={size} rx={14} fill={s.color}/>}
    <text x={x} y={y} fill="#0f1f35" fontSize={18} fontWeight={700} fontFamily="Noto Sans CJK JP" textAnchor="middle" dominantBaseline="middle">{s.label}</text>
  </g>;
};
export const Video:React.FC=()=>{
  const t=useCurrentFrame()/spec.video.fps;
  const cap=spec.captions.find(c=>c.start<=t&&t<c.end)??spec.captions[spec.captions.length-1];
  const intro=ease((t-0.35)/0.7);const end=ease((t-10)/0.4);
  return <AbsoluteFill style={{backgroundColor:spec.colors.background,color:spec.colors.foreground,...typographic}}>
    <div style={{position:'absolute',top:23,left:0,width:'100%',textAlign:'center',fontSize:27,...typographic}}>{spec.title}</div>
    <div style={{position:'absolute',top:79,left:64,right:64,height:2,backgroundColor:'#41536f'}}/>
    {t<3&&<div style={{position:'absolute',top:149,left:0,width:'100%',fontSize:37+8*intro,opacity:intro,textAlign:'center',...typographic}}>情報が伝わる3つの形</div>}
    <svg width={spec.video.width} height={spec.video.height} style={{position:'absolute',left:0,top:0}}>
      {t>=3&&spec.shapes.map(s=><Shape s={s} t={t} key={s.kind}/>)}
    </svg>
    {t>=10&&<div style={{position:'absolute',left:160,top:120,width:320,height:140,borderRadius:22,backgroundColor:'#17304a',opacity:end,display:'flex',alignItems:'center',justifyContent:'center',fontSize:34,...typographic}}>情報は一つずつ</div>}
    <div style={{position:'absolute',left:0,top:294,width:'100%',textAlign:'center',fontSize:19,...typographic}}>{cap.text}</div>
  </AbsoluteFill>;
};
