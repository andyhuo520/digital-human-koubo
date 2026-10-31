// 小林式解说（16:9）：主播全屏 / 景深字 / 紫色题板 + 主播小窗 / B-roll + 数据卡 / 图表 / 公式逐项长出 / 算例填数。
// 数据驱动：src/scenes.json（scripts/lin_scenes.py 生成，时间都是整片绝对秒）+ src/cues.json（字幕，scripts/lin_subs.py 生成）。
// 所有动画由帧号推导；主播小窗 = 同一条 public/main.mp4 按全局时间同步裁脸。
import React from "react";
import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import plan from "./scenes.json";
import cues from "./cues.json";

const FPS = 30;
const CFG: any = (plan as any).config || {};
const FONT = '"PingFang SC", "Hiragino Sans GB", sans-serif';
const NUM = '"DIN Alternate", "DIN Condensed", "Helvetica Neue", sans-serif';
const C = { bg1: "#1E1233", bg2: "#35205A", line: "rgba(255,226,160,0.35)", gold: "#F6E3A1", gold2: "#E9C46A", lime: "#DDF27C", ink: "#FFFFFF", dim: "rgba(255,255,255,0.62)", teal: "#4FB3A9", red: "#E25B4B", ...(CFG.colors || {}) };
const goldText: React.CSSProperties = { background: "linear-gradient(180deg,#FFF6D2 0%,#F3D98B 45%,#C99A3E 100%)", WebkitBackgroundClip: "text", color: "transparent" };
// 主播脸在 main.mp4（按 1920×1080 计）里的中心点：小窗按它裁。换形象/机位后用 scripts/lin_scenes.py --face 量一次
const FACE = { x: CFG.face?.[0] ?? 1215, y: CFG.face?.[1] ?? 390 };
const AUDIO = CFG.audio ?? "mix.wav";             // 混好的整片音轨；没有就写 "main.mp4"
const DISCLOSURE = CFG.disclosure ?? "内容由 AI 数字人演绎";
const BROLL_TAG = CFG.brollTag ?? "AI 生成画面";
type Sc = any;

const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
const useK = (at: number, cfg = { damping: 16, stiffness: 150 }) => {
  const f = useCurrentFrame(); return spring({ frame: f - Math.round(at * FPS), fps: FPS, config: cfg });
};
const Pop: React.FC<{ at: number; children: React.ReactNode; dy?: number; style?: React.CSSProperties }> = ({ at, children, dy = 24, style }) => {
  const k = useK(at);
  return <div style={{ opacity: Math.min(1, k * 1.3), transform: `translateY(${(1 - k) * dy}px) scale(${0.94 + 0.06 * k})`, ...style }}>{children}</div>;
};

/* ── 主播小窗：circle-tl / circle-bl / rect-l / rect-r ── */
export const PIP_BOX: Record<string, [number, number, number, number]> = { "circle-tl": [70, 60, 300, 300], "circle-bl": [70, 630, 300, 300], "rect-l": [70, 220, 400, 520], "rect-r": [1450, 220, 400, 520] };
const Pip: React.FC<{ kind: string; a: number }> = ({ kind, a }) => {
  const k = useK(0.05);
  if (!kind || kind === "none") return null;
  const circle = kind.startsWith("circle");
  const [x, y, W, H] = PIP_BOX[kind];
  const s = circle ? 0.62 : 0.82, cy = circle ? W / 2 : 190;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: W, height: H, borderRadius: circle ? "50%" : 22, overflow: "hidden", border: `4px solid ${C.gold2}`,
      boxShadow: "0 18px 50px rgba(0,0,0,.45)", opacity: k, transform: `scale(${0.85 + 0.15 * k})` }}>
      <OffthreadVideo src={staticFile("main.mp4")} muted startFrom={Math.round(a * FPS)}
        style={{ position: "absolute", width: 1920 * s, height: 1080 * s, left: W / 2 - FACE.x * s, top: cy - FACE.y * s, maxWidth: "none" }} />
    </div>
  );
};
// 题板面板避开小窗：右侧方形小窗时面板靠左，否则靠右
const panelX = (pip: string, w: number) => (pip === "rect-r" ? 110 : pip === "rect-l" || pip?.startsWith("circle") ? 1920 - 110 - w : 110);

/* ── 紫色题板背景 ── */
const BoardBg: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: `radial-gradient(120% 90% at 30% 20%, ${C.bg2} 0%, ${C.bg1} 70%)` }}>
      <AbsoluteFill style={{ backgroundImage: "linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px)", backgroundSize: "64px 64px" }} />
      <div style={{ position: "absolute", left: -120, bottom: -160, width: 520, height: 520, borderRadius: 80, background: "#5B8F3A", opacity: 0.35, transform: `rotate(${18 + f * 0.02}deg)` }} />
      <div style={{ position: "absolute", right: -90, top: -140, width: 420, height: 420, borderRadius: 70, background: C.teal, opacity: 0.22, transform: `rotate(${-14 - f * 0.015}deg)` }} />
      {[0, 1].map((i) => <div key={i} style={{ position: "absolute", left: 0, right: 0, [i ? "bottom" : "top"]: 0, height: 26, backgroundImage: `repeating-linear-gradient(90deg, ${C.gold2} 0 22px, transparent 22px 44px)`, opacity: 0.25 }} />)}
    </AbsoluteFill>
  );
};
const Panel: React.FC<{ x: number; y: number; w: number; h: number; children: React.ReactNode }> = ({ x, y, w, h, children }) => {
  const k = useK(0);
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h, borderRadius: 28, background: "linear-gradient(180deg, rgba(70,48,112,.92), rgba(44,28,74,.94))",
      border: `2px solid ${C.line}`, boxShadow: "0 30px 80px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.08)", opacity: k, transform: `translateY(${(1 - k) * 30}px)`,
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", fontFamily: FONT, color: C.ink }}>{children}</div>
  );
};
const Tag: React.FC<{ t: string }> = ({ t }) => <div style={{ background: C.gold2, color: "#2A1A40", fontSize: 30, fontWeight: 800, padding: "6px 22px", borderRadius: 10, marginBottom: 18 }}>{t}</div>;
const Title: React.FC<{ t: string }> = ({ t }) => <div style={{ fontSize: 46, fontWeight: 700, letterSpacing: "0.06em", color: C.gold, marginBottom: 26 }}>{t}</div>;

/* ── host：主播全屏，可叠景深字 depth / 侧卡 lower / lower2 ── */
const Host: React.FC<{ s: Sc }> = ({ s }) => (
  <AbsoluteFill>
    {s.depth && <DepthText d={s.depth} a={s.a} />}
    {s.lower && <Lower t={s.lower} at={0.4} until={(s.lowerTo ?? s.b) - s.a} />}
    {s.lower2 && <Lower t={s.lower2.t} at={s.lower2.at - s.a} until={s.b - s.a} />}
  </AbsoluteFill>
);
// 景深字：大字 → 抠出来的主播（scripts/cutout_video.py 抠 cut/<段>.mp4，cutout 从场景开头起播）；count=1 时数字从 0 滚到目标
const DepthText: React.FC<{ d: any; a: number }> = ({ d, a }) => {
  const f = useCurrentFrame();
  const at = (d.at ?? a) - a;
  const k = spring({ frame: f - Math.round(at * FPS), fps: FPS, config: { damping: 14, stiffness: 120 } });
  let txt = d.lines[0];
  if (d.count) txt = String(Math.round(interpolate(f, [at * FPS, at * FPS + 24], [0, Number(txt)], clamp)));
  const len = d.lines[0].length;
  const size = d.size ?? (len <= 3 ? 520 : len === 4 ? 330 : 270);
  return (
    <>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start", paddingTop: d.top ?? (len <= 3 ? 40 : 90) }}>
        <div style={{ fontFamily: len <= 3 ? NUM : FONT, fontWeight: 900, fontSize: size, lineHeight: 1, letterSpacing: "0.04em", ...goldText,
          opacity: Math.min(1, k * 1.4), transform: `translateY(${(1 - k) * 120}px) scale(${0.9 + 0.1 * k})`, filter: "drop-shadow(0 10px 30px rgba(0,0,0,.35))", whiteSpace: "nowrap" }}>{txt}</div>
      </AbsoluteFill>
      <OffthreadVideo src={staticFile(d.src)} transparent muted style={{ position: "absolute", width: 1920, height: 1080 }} />
    </>
  );
};
const Lower: React.FC<{ t: string[]; at: number; until: number }> = ({ t, at, until }) => {
  const f = useCurrentFrame();
  const k = useK(at); const out = interpolate(f, [until * FPS - 10, until * FPS], [1, 0], clamp);
  return (
    <div style={{ position: "absolute", left: 90, top: 300, opacity: k * out, transform: `translateX(${(1 - k) * -50}px)` }}>
      <div style={{ background: "rgba(30,18,51,.86)", border: `2px solid ${C.gold2}`, borderRadius: 20, padding: "22px 30px", fontFamily: FONT, boxShadow: "0 20px 50px rgba(0,0,0,.35)" }}>
        <div style={{ fontSize: 34, color: C.gold, fontWeight: 600 }}>{t[0]}</div>
        <div style={{ fontSize: 46, color: "#fff", fontWeight: 800, marginTop: 6 }}>{t[1]}</div>
      </div>
    </div>
  );
};

/* ── broll：public/broll/<clip>.mp4 全屏慢推 + 主播圆窗；可叠 float / card / slam / banner / chips / stat / doc ── */
const Broll: React.FC<{ s: Sc }> = ({ s }) => {
  const f = useCurrentFrame(); const d = s.b - s.a;
  const rate = Math.max(0.55, Math.min(1, (s.clipLen ?? 5) / d));
  const zoom = interpolate(f, [0, d * FPS], [1.02, 1.12], clamp);
  const r = (t: number) => t - s.a;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
        <OffthreadVideo src={staticFile(`broll/${s.clip}.mp4`)} muted playbackRate={rate} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(20,10,35,.55) 0%, rgba(20,10,35,.05) 55%)" }} />
      {BROLL_TAG && <div style={{ position: "absolute", right: 36, bottom: 30, fontFamily: FONT, fontSize: 20, color: "rgba(255,255,255,.8)", background: "rgba(0,0,0,.35)", padding: "4px 10px", borderRadius: 6 }}>{BROLL_TAG}</div>}
      {s.float && s.float.map((t: string, i: number) => {
        const k = spring({ frame: f - 6 - i * 9, fps: FPS, config: { damping: 12, stiffness: 120 } });
        const xs = [560, 1180, 860], ys = [300, 260, 560];
        return <div key={i} style={{ position: "absolute", left: xs[i % 3], top: ys[i % 3] - f * 0.6, fontFamily: FONT, fontWeight: 900, fontSize: i === 2 ? 150 : 110, ...goldText, opacity: k, transform: `scale(${0.6 + 0.4 * k})`, filter: "drop-shadow(0 8px 24px rgba(0,0,0,.6))" }}>{t}</div>;
      })}
      {s.card && <Pop at={r(s.cardAt)} style={{ position: "absolute", left: 420, top: 300 }}>
        <div style={{ background: "rgba(30,18,51,.86)", border: `2px solid ${C.gold2}`, borderRadius: 24, padding: "28px 38px", fontFamily: FONT, boxShadow: "0 24px 60px rgba(0,0,0,.4)" }}>
          <div style={{ fontSize: 34, color: C.gold, fontWeight: 600 }}>{s.card[0]}</div>
          <div style={{ fontSize: 72, color: "#fff", fontWeight: 900, fontFamily: NUM, marginTop: 8 }}>{s.card[1]}</div>
          {s.card[2] && <div style={{ fontSize: 34, color: "#fff", fontWeight: 600, marginTop: 6, opacity: .9 }}>{s.card[2]}</div>}
        </div></Pop>}
      {s.slam && <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        {(() => { const k = spring({ frame: f - Math.round(r(s.slamAt) * FPS), fps: FPS, config: { damping: 9, stiffness: 160 } });
          return <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 230, color: "#fff", textShadow: `0 0 40px ${C.red}, 0 10px 30px rgba(0,0,0,.6)`, opacity: Math.min(1, k * 1.5), transform: `scale(${2 - k})` }}>{s.slam}</div>; })()}
      </AbsoluteFill>}
      {s.banner && <Pop at={r(s.bannerAt)} style={{ position: "absolute", left: 0, right: 0, top: 640, display: "flex", justifyContent: "center" }}>
        <div style={{ display: "flex", gap: 18, alignItems: "center", background: "rgba(20,12,36,.88)", border: `2px solid ${C.gold2}`, borderRadius: 18, padding: "20px 40px", fontFamily: FONT, fontSize: 62, fontWeight: 900 }}>
          {s.banner.map((t: string, i: number) => <span key={i} style={{ color: "#fff", ...(i % 2 ? { background: i === s.banner.length - 1 ? C.red : "#3E5BA9", padding: "0 14px", borderRadius: 10 } : {}) }}>{t}</span>)}
        </div></Pop>}
      {s.chips && <div style={{ position: "absolute", left: 420, top: 330, display: "flex", flexDirection: "column", gap: 22 }}>
        {s.chips.map((c: string, i: number) => <Pop key={i} at={r(s.chipsAt) + i * (s.stagger ? 1.3 : 0.35)}>
          <div style={{ display: "inline-block", background: "rgba(30,18,51,.86)", border: `2px solid ${C.gold2}`, borderRadius: 999, padding: "14px 34px", fontFamily: FONT, fontSize: 48, fontWeight: 800, color: "#fff" }}>{c}</div></Pop>)}
      </div>}
      {s.stat && <div style={{ position: "absolute", left: 420, top: 240, display: "flex", flexDirection: "column", gap: 30 }}>
        {s.stat.map((x: string[], i: number) => <Pop key={i} at={r(s.statAt[i])}>
          <div style={{ fontFamily: FONT, fontSize: 34, color: C.gold, fontWeight: 600 }}>{x[0]}</div>
          <div style={{ fontFamily: NUM, fontSize: i === 0 ? 190 : 120, fontWeight: 900, lineHeight: 1, ...goldText, filter: "drop-shadow(0 8px 24px rgba(0,0,0,.5))" }}>{x[1]}</div></Pop>)}
      </div>}
      {s.doc && <Pop at={r(s.docAt)} style={{ position: "absolute", left: 420, top: 250 }}>
        <div style={{ width: 640, background: "#FBF8F0", borderRadius: 10, padding: "36px 44px", fontFamily: FONT, color: "#222", boxShadow: "0 30px 70px rgba(0,0,0,.5)", transform: "rotate(-2deg)" }}>
          <div style={{ fontSize: 44, fontWeight: 900 }}>{s.doc[0]}</div>
          <div style={{ height: 2, background: "#ddd", margin: "18px 0" }} />
          <div style={{ fontSize: 38, lineHeight: 1.6 }}>{s.doc[1]}<br /><span style={{ background: "#FFE76A", padding: "0 6px" }}>{s.doc[2]}</span></div>
        </div></Pop>}
      <Pip kind={s.pip ?? "circle-bl"} a={s.a} />
    </AbsoluteFill>
  );
};

/* ── board：题板。tag / title / big[] / sub / choices[[字母,小字,大字]] + reveal / items[] + itemsAt[] / chips[] + chipsAt ── */
const Board: React.FC<{ s: Sc }> = ({ s }) => {
  const r = (t: number) => t - s.a; const w = 1300;
  return (
    <AbsoluteFill>
      <BoardBg />
      <Panel x={panelX(s.pip, w)} y={150} w={w} h={720}>
        {s.tag && <Tag t={s.tag} />}
        {s.title && <Title t={s.title} />}
        {s.big && s.big.map((b: string, i: number) => <Pop key={i} at={0.25 + i * 0.5}><div style={{ fontSize: s.big.length > 1 ? 92 : 120, fontWeight: 900, ...goldText, lineHeight: 1.2, textAlign: "center" }}>{b}</div></Pop>)}
        {s.sub && <Pop at={0.8}><div style={{ fontSize: 40, color: C.dim, marginTop: 26 }}>{s.sub}</div></Pop>}
        {s.choices && <div style={{ display: "flex", gap: 50, marginTop: 10 }}>
          {s.choices.map((c: string[], i: number) => <Pop key={i} at={i === 0 ? 0.4 : r(s.reveal)}>
            <div style={{ width: 460, padding: "36px 30px", borderRadius: 24, background: i ? "rgba(221,242,124,.14)" : "rgba(255,255,255,.07)", border: `2px solid ${i ? C.lime : C.line}`, textAlign: "center" }}>
              <div style={{ fontFamily: NUM, fontSize: 80, fontWeight: 900, color: i ? C.lime : C.gold }}>{c[0]}</div>
              <div style={{ fontSize: 38, color: C.dim, marginTop: 8 }}>{c[1]}</div>
              <div style={{ fontSize: 52, fontWeight: 800, marginTop: 10 }}>{c[2]}</div></div></Pop>)}
        </div>}
        {s.items && <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 30 }}>
          {s.items.map((t: string, i: number) => <Pop key={i} at={r(s.itemsAt[i])}>
            <div style={{ width: 440, padding: "30px 0", borderRadius: 20, background: "rgba(255,255,255,.07)", border: `2px solid ${C.line}`, textAlign: "center", fontSize: 54, fontWeight: 800 }}>
              <span style={{ color: C.lime, marginRight: 14 }}>✓</span>{t}</div></Pop>)}
        </div>}
        {s.chips && <div style={{ display: "flex", gap: 30, marginTop: 40 }}>
          {s.chips.map((c: string, i: number) => <Pop key={i} at={r(s.chipsAt) + i * 0.45}><div style={{ fontFamily: NUM, fontSize: 64, fontWeight: 900, color: "#2A1A40", background: C.lime, padding: "10px 34px", borderRadius: 16 }}>{c}</div></Pop>)}
        </div>}
      </Panel>
      <Pip kind={s.pip} a={s.a} />
    </AbsoluteFill>
  );
};

/* ── rates：2–3 张大数字卡 cards[[标签,数字,单位]] + cardsAt[]（最后一张标红） ── */
const Rates: React.FC<{ s: Sc }> = ({ s }) => (
  <AbsoluteFill>
    <BoardBg />
    <div style={{ position: "absolute", left: s.pip === "rect-r" ? 110 : 560, top: 240, display: "flex", gap: 40 }}>
      {s.cards.map((c: string[], i: number) => <Pop key={i} at={s.cardsAt[i] - s.a}>
        <div style={{ width: 380, height: 500, borderRadius: 26, background: i === s.cards.length - 1 ? "linear-gradient(180deg,#7A2232,#4A1424)" : "linear-gradient(180deg,#2B3F7A,#1C2950)", border: `3px solid ${C.gold2}`,
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", fontFamily: FONT, boxShadow: "0 30px 70px rgba(0,0,0,.5)" }}>
          <div style={{ fontSize: 34, color: C.gold, fontWeight: 600 }}>{c[0]}</div>
          <div style={{ display: "flex", alignItems: "baseline", marginTop: 30 }}>
            <span style={{ fontFamily: NUM, fontSize: 170, fontWeight: 900, ...goldText }}>{c[1]}</span><span style={{ fontSize: 56, color: C.gold, marginLeft: 8 }}>{c[2]}</span></div>
        </div></Pop>)}
    </div>
    <Pip kind={s.pip} a={s.a} />
  </AbsoluteFill>
);

/* ── curve：长期上涨曲线（示意）title / label + labelAt ── */
const Curve: React.FC<{ s: Sc }> = ({ s }) => {
  const f = useCurrentFrame();
  const pts: [number, number][] = [];
  for (let i = 0; i <= 120; i++) { const x = i / 120; pts.push([x, Math.exp(3.2 * x) - 1 + 0.6 * Math.sin(i * 1.7) * x + 0.4 * Math.sin(i * 0.53) * x]); }
  const maxY = Math.max(...pts.map((p) => p[1])); const W = 1040, H = 520;
  const d = pts.map((p, i) => `${i ? "L" : "M"}${(p[0] * W).toFixed(1)},${(H - (p[1] / maxY) * H).toFixed(1)}`).join(" ");
  const prog = interpolate(f, [8, 6.5 * FPS], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <BoardBg />
      <Panel x={panelX(s.pip, 1240)} y={140} w={1240} h={760}>
        <div style={{ fontSize: 40, color: C.gold, fontWeight: 700, alignSelf: "flex-start", marginLeft: 70 }}>{s.title}</div>
        <svg width={W + 40} height={H + 40} style={{ marginTop: 20 }}><g transform="translate(20,20)">
          {[0, 1, 2, 3, 4].map((i) => <line key={i} x1={0} x2={W} y1={(H / 4) * i} y2={(H / 4) * i} stroke="rgba(255,255,255,.08)" />)}
          <path d={d} fill="none" stroke={C.lime} strokeWidth={5} strokeDasharray={4000} strokeDashoffset={4000 * (1 - prog)} />
        </g></svg>
        <Pop at={s.labelAt - s.a} style={{ position: "absolute", left: 140, top: 200 }}>
          <div style={{ fontFamily: FONT, fontSize: 64, fontWeight: 900, color: "#2A1A40", background: C.lime, padding: "10px 30px", borderRadius: 16 }}>{s.label}</div></Pop>
      </Panel>
      <Pip kind={s.pip} a={s.a} />
    </AbsoluteFill>
  );
};

/* ── fall：瀑布柱（起点 / 扣除 / 结果）steps[[标签,数值]] + stepsAt[] ── */
const FallBar: React.FC<{ st: string[]; at: number; i: number }> = ({ st, at, i }) => {
  const k = useK(at); const hs = [420, 170, 250], tops = [0, 0, 170], cols = [C.teal, C.red, C.lime];
  return (
    <div style={{ width: 280, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ height: 420, width: 200, position: "relative" }}>
        <div style={{ position: "absolute", left: 0, right: 0, top: tops[i], height: hs[i] * k, background: cols[i], borderRadius: 14, opacity: 0.92 }} />
        <div style={{ position: "absolute", left: -40, right: -40, top: tops[i] - 80, textAlign: "center", fontFamily: NUM, fontSize: 70, fontWeight: 900, color: "#fff", opacity: k }}>{st[1]}</div>
      </div>
      <div style={{ fontSize: 36, color: C.gold, marginTop: 30, textAlign: "center", opacity: k }}>{st[0]}</div>
    </div>
  );
};
const Fall: React.FC<{ s: Sc }> = ({ s }) => (
  <AbsoluteFill>
    <BoardBg />
    <Panel x={panelX(s.pip, 1300)} y={150} w={1300} h={720}>
      <div style={{ display: "flex", gap: 90, alignItems: "flex-start", height: 520, marginTop: 20 }}>
        {s.steps.map((st: string[], i: number) => <FallBar key={i} st={st} at={s.stepsAt[i] - s.a} i={i} />)}
      </div>
    </Panel>
    <Pip kind={s.pip} a={s.a} />
  </AbsoluteFill>
);

/* ── assume：先 ?% 再揭晓。boxes[{label,v,hot?}]（两个，中间减号）+ reveal（第二个晚 1.6 秒）+ result{label,v} + resultAt ── */
const Box: React.FC<{ label: string; v: string; at: number; hot?: boolean }> = ({ label, v, at, hot }) => {
  const k = useK(at, { damping: 12, stiffness: 140 });
  return (
    <div style={{ width: 420, height: 300, borderRadius: 24, background: hot ? "linear-gradient(180deg,#7A2232,#4A1424)" : "linear-gradient(180deg,#2B3F7A,#1C2950)", border: `3px solid ${C.gold2}`,
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
      <div style={{ fontSize: 36, color: C.gold }}>{label}</div>
      <div style={{ fontFamily: NUM, fontSize: 120, fontWeight: 900, marginTop: 10, ...goldText, transform: `scale(${0.7 + 0.3 * k})` }}>{k > 0.05 ? v : "?%"}</div>
    </div>
  );
};
const Assume: React.FC<{ s: Sc }> = ({ s }) => {
  const kr = useK(s.resultAt - s.a);
  return (
    <AbsoluteFill>
      <BoardBg />
      <Panel x={panelX(s.pip, 1420)} y={130} w={1420} h={780}>
        <Tag t={s.tag ?? "重要假设"} />
        <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
          <Box label={s.boxes[0].label} v={s.boxes[0].v} at={s.reveal - s.a} hot={s.boxes[0].hot} />
          <div style={{ fontSize: 120, color: C.gold }}>{s.op ?? "−"}</div>
          <Box label={s.boxes[1].label} v={s.boxes[1].v} at={s.reveal - s.a + 1.6} hot={s.boxes[1].hot ?? true} />
        </div>
        <div style={{ marginTop: 40, opacity: kr, transform: `translateY(${(1 - kr) * 30}px)`, display: "flex", alignItems: "baseline", gap: 24 }}>
          <span style={{ fontSize: 50, color: "#fff", fontWeight: 700 }}>{s.result.label}</span>
          <span style={{ fontFamily: NUM, fontSize: 120, fontWeight: 900, color: "#2A1A40", background: C.lime, padding: "0 30px", borderRadius: 18 }}>{s.result.v}</span>
        </div>
      </Panel>
      <Pip kind={s.pip} a={s.a} />
    </AbsoluteFill>
  );
};

/* ── formula：推导行逐行出现 title / lines[] + linesAt[]（最后一行高亮） ── */
const Formula: React.FC<{ s: Sc }> = ({ s }) => (
  <AbsoluteFill>
    <BoardBg />
    <Panel x={panelX(s.pip, 1300)} y={150} w={1300} h={720}>
      <Title t={s.title} />
      <div style={{ alignSelf: "flex-start", marginLeft: 120, display: "flex", flexDirection: "column", gap: 34 }}>
        {s.lines.map((t: string, i: number) => <Pop key={i} at={s.linesAt[i] - s.a}><div style={{ fontSize: 76, fontWeight: 800, color: i === s.lines.length - 1 ? C.lime : "#fff" }}>{t}</div></Pop>)}
      </div>
    </Panel>
    <Pip kind={s.pip} a={s.a} />
  </AbsoluteFill>
);

/* ── big：上一行算式 top + 下一行结果 bottom（bottomAt 砸下） ── */
const Big: React.FC<{ s: Sc }> = ({ s }) => {
  const k = useK(s.bottomAt - s.a, { damping: 10, stiffness: 140 });
  return (
    <AbsoluteFill>
      <BoardBg />
      <Panel x={panelX(s.pip, 1300)} y={130} w={1300} h={800}>
        <Pop at={0.2}><div style={{ fontFamily: NUM, fontSize: 190, fontWeight: 900, ...goldText }}>{s.top}</div></Pop>
        <div style={{ fontFamily: NUM, fontSize: 260, fontWeight: 900, ...goldText, opacity: k, transform: `scale(${1.6 - 0.6 * k})`, lineHeight: 1.1 }}>{s.bottom}</div>
      </Panel>
      <Pip kind={s.pip} a={s.a} />
    </AbsoluteFill>
  );
};

/* ── stickers：四宫格 items[{t,img,at?,dim?}]（img 在 public/stickers/，无 at 的开场就出） ── */
const Stickers: React.FC<{ s: Sc }> = ({ s }) => (
  <AbsoluteFill>
    <BoardBg />
    <div style={{ position: "absolute", left: 200, top: 120, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 40 }}>
      {s.items.map((it: any, i: number) => <Pop key={i} at={it.at != null ? it.at - s.a : 0.2}>
        <div style={{ width: 720, height: 390, borderRadius: 28, background: "linear-gradient(180deg, rgba(70,48,112,.95), rgba(44,28,74,.95))", border: `3px solid ${it.dim ? C.line : C.gold2}`,
          display: "flex", alignItems: "center", justifyContent: "space-around", opacity: it.dim ? 0.45 : 1 }}>
          <div style={{ fontFamily: FONT, fontSize: 130, fontWeight: 900, ...goldText }}>{it.t}</div>
          {it.img && <Img src={staticFile(`stickers/${it.img}`)} style={{ width: 280, height: 280, objectFit: "contain" }} />}
        </div></Pop>)}
    </div>
  </AbsoluteFill>
);

/* ── bars：横向条形图 title / bars[[名,值]] + barsAt[] / unit / max / highlight（下标） ── */
const BarRow: React.FC<{ b: [string, number]; at: number; max: number; unit: string; hi: boolean }> = ({ b, at, max, unit, hi }) => {
  const k = useK(at);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 26 }}>
      <div style={{ width: 210, textAlign: "right", fontSize: 44, color: hi ? C.lime : "#fff", fontWeight: 700 }}>{b[0]}</div>
      <div style={{ height: 70, width: (b[1] / max) * 760 * k, borderRadius: 12, background: hi ? C.lime : C.gold2 }} />
      <div style={{ fontFamily: NUM, fontSize: 60, fontWeight: 900, color: "#fff", opacity: k }}>{b[1]} {unit}</div>
    </div>
  );
};
const Bars: React.FC<{ s: Sc }> = ({ s }) => {
  const max = s.max ?? Math.max(...s.bars.map((b: any) => b[1])) * 1.02;
  return (
    <AbsoluteFill>
      <BoardBg />
      <Panel x={panelX(s.pip, 1300)} y={150} w={1300} h={720}>
        <Title t={s.title} />
        <div style={{ display: "flex", flexDirection: "column", gap: 34, alignSelf: "flex-start", marginLeft: 90 }}>
          {s.bars.map((b: [string, number], i: number) => <BarRow key={i} b={b} at={s.barsAt[i] - s.a} max={max} unit={s.unit ?? ""} hi={i === s.highlight} />)}
        </div>
      </Panel>
      <Pip kind={s.pip} a={s.a} />
    </AbsoluteFill>
  );
};

/* ── formula2：公式逐项长出 title / terms[{t,label,img?,at}]，最新一项高亮；final=1 全部同时亮 ── */
const Term: React.FC<{ tm: any; at: number; hot: boolean; first: boolean }> = ({ tm, at, hot, first }) => {
  const k = useK(at);
  return (
    <>
      {!first && <div style={{ fontSize: 90, color: C.gold, opacity: k, marginTop: 20 }}>+</div>}
      <div style={{ opacity: k, transform: `translateY(${(1 - k) * 30}px)`, display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
        <div style={{ fontFamily: NUM, fontSize: 120, fontWeight: 900, padding: "0 26px", borderRadius: 18, background: hot ? C.lime : "transparent", ...(hot ? { color: "#2A1A40" } : goldText) }}>{tm.t}</div>
        {tm.img && <Img src={staticFile(`stickers/${tm.img}`)} style={{ width: 130, height: 130, objectFit: "contain" }} />}
        <div style={{ fontSize: 30, color: C.dim }}>{tm.label}</div>
      </div>
    </>
  );
};
const Formula2: React.FC<{ s: Sc }> = ({ s }) => {
  const f = useCurrentFrame();
  const lastI = s.terms.reduce((acc: number, tm: any, i: number) => (f >= (tm.at - s.a) * FPS ? i : acc), 0);
  const w = s.pip === "rect-r" ? 1300 : 1440;
  return (
    <AbsoluteFill>
      <BoardBg />
      <Panel x={panelX(s.pip, w)} y={170} w={w} h={680}>
        <Title t={s.title} />
        <div style={{ display: "flex", alignItems: "flex-start", gap: 20 }}>
          {s.terms.map((tm: any, i: number) => <Term key={i} tm={tm} at={tm.at - s.a} hot={!s.final && i === lastI} first={i === 0} />)}
        </div>
      </Panel>
      <Pip kind={s.pip} a={s.a} />
    </AbsoluteFill>
  );
};

/* ── calc：算例填数 tag / row[]（第 0 项开场就出，其余按 rowAt[i-1]）/ res + resAt / extra + extraAt ── */
const Calc: React.FC<{ s: Sc }> = ({ s }) => {
  const kr = useK(s.resAt - s.a, { damping: 12, stiffness: 140 });
  const ke = useK((s.extraAt ?? s.b + 9) - s.a);
  const parts = s.row.filter((x: string) => x);
  return (
    <AbsoluteFill>
      <BoardBg />
      <Panel x={panelX(s.pip, 1300)} y={150} w={1300} h={720}>
        {s.tag && <Tag t={s.tag} />}
        <div style={{ display: "flex", alignItems: "baseline", gap: 18, flexWrap: "wrap", justifyContent: "center", maxWidth: 1180 }}>
          {parts.map((p: string, i: number) => <Pop key={i} at={s.rowAt ? (i === 0 ? s.rowAt[0] - s.a - 0.3 : s.rowAt[i - 1] - s.a) : 0.3 + i * 0.4}>
            <span style={{ fontFamily: NUM, fontSize: 84, fontWeight: 900, color: i === 0 ? C.gold : "#fff" }}>{p}</span></Pop>)}
        </div>
        <div style={{ height: 3, width: 900, background: C.line, margin: "34px 0" }} />
        <div style={{ fontFamily: NUM, fontSize: 130, fontWeight: 900, color: "#2A1A40", background: C.lime, padding: "0 40px", borderRadius: 20, opacity: kr, transform: `scale(${1.3 - 0.3 * kr})` }}>{s.res}</div>
        {s.extra && <div style={{ fontSize: 48, color: "#fff", marginTop: 28, opacity: ke }}>{s.extra}</div>}
      </Panel>
      <Pip kind={s.pip} a={s.a} />
    </AbsoluteFill>
  );
};

export const MAP: Record<string, React.FC<{ s: Sc }>> = { host: Host, broll: Broll, board: Board, rates: Rates, curve: Curve, fall: Fall, assume: Assume, formula: Formula, big: Big, stickers: Stickers, bars: Bars, formula2: Formula2, calc: Calc };

const Sub: React.FC<{ t: number }> = ({ t }) => {
  const s = (cues as any).subs.find((x: any) => t >= x.a && t < x.b);
  if (!s) return null;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 56, display: "flex", justifyContent: "center" }}>
      <div style={{ fontFamily: FONT, fontSize: 52, fontWeight: 600, color: "#fff", padding: "4px 20px", textShadow: "0 0 3px rgba(0,0,0,.9), 0 2px 6px rgba(0,0,0,.75), 0 0 18px rgba(0,0,0,.4)" }}>{s.t}</div>
    </div>
  );
};

export const Lin: React.FC = () => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <OffthreadVideo src={staticFile("main.mp4")} muted style={{ width: "100%", height: "100%" }} />
      <Audio src={staticFile(AUDIO)} />
      {((plan as any).scenes as Sc[]).map((s, i) => {
        const Comp = MAP[s.type];
        const from = Math.round(s.a * FPS), dur = Math.max(1, Math.round(s.b * FPS) - from);
        return <Sequence key={i} from={from} durationInFrames={dur} layout="none"><AbsoluteFill><Comp s={s} /></AbsoluteFill></Sequence>;
      })}
      {DISCLOSURE && <div style={{ position: "absolute", right: 36, top: 30, fontFamily: FONT, fontSize: 20, color: "rgba(255,255,255,0.85)", background: "rgba(0,0,0,0.3)", padding: "5px 12px", borderRadius: 8 }}>{DISCLOSURE}</div>}
      <Sub t={f / fps} />
    </AbsoluteFill>
  );
};
