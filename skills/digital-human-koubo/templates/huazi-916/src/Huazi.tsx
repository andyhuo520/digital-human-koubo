// 9:16 网红花字口播（数据驱动）：数字人口播 + 逐字弹跳字幕 + 关键词放大变色 + 动态表情 + 跳切推近 + 卡片/盖章/大字 + 作品画中画 + 号召。
// 内容全写在 edit.json，时间全部来自 tl.json（scripts/align.py 逐字对齐）。改稿只改这两个文件，不用碰代码。
// 时间写法（edit.json 里所有 at / until）："3:" = 第 3 段开头；"3:end" = 第 3 段结束；"3:关键词" = 第 3 段里这个词开始；"3:关键词#2" = 第 2 次出现；数字 = 绝对秒。
import React from "react";
import { AbsoluteFill, Audio, Easing, Img, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame } from "remotion";
import tl from "./tl.json";
import edit from "./edit.json";
import { NotoEmoji } from "./icons/NotoEmoji";
import { PackLayer, type PackItem } from "./kit/registry";

const FPS = 30;
const F = (s: number) => Math.round(s * FPS);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ZH = '"PingFang SC","Hiragino Sans GB",sans-serif';
const EN = '"Avenir Next","Helvetica Neue",Arial,sans-serif';
const COLORS: Record<string, string> = { yellow: "#FFE14D", pink: "#FF5A8A", cyan: "#3EE6FF", red: "#FF4D4F", green: "#38E08C", orange: "#FF7A1A", purple: "#A78BFA", white: "#FFFFFF" };
const col = (c?: string, d = "yellow") => COLORS[c ?? d] ?? c ?? COLORS[d];

type Seg = { i: number; start: number; end: number; text: string; chars: Record<string, number> };
type TRef = string | number;
type E = {
  title?: { left?: string; right?: string }; preset?: "克制" | "标准" | "热闹"; badge?: string; brand?: string; tail?: number;
  chapters?: Array<{ at: TRef; t: string }>; keys?: string[]; emojis?: Array<{ at: TRef; e: string; side?: "l" | "r"; y?: number }>; punch?: TRef[];
  cards?: Array<Record<string, any> & { type: string; at: TRef; until?: TRef }>;
  showcase?: Array<{ from: TRef; to: TRef; note?: string; items: Array<{ src: string; label?: string; ratio?: "16:9" | "9:16" | "1:1"; fit?: "cover" | "contain"; at?: TRef }> }>;
  cta?: { at: TRef; text: string; sub?: string; subAt?: TRef };
  music?: { src: string; vol?: number }; voice?: string; video?: string; videoCrop?: number; credits?: string;
  /** 包装组件（templates/packaging 组件库，字段见 references/packaging.md）：[{ use: "Counter", at: "3:积分", ... }] */
  pack?: PackItem[];
};
const SEGS = tl.segs as unknown as Seg[];
const ED = edit as unknown as E;
const TAIL = ED.tail ?? 1.2;
export const TOTAL_FRAMES = F(tl.total + TAIL);
const BRAND = col(ED.brand, "orange");

/* ---------- 预设：花字强度 ---------- */
const PRESETS = {
  克制: { cap: 66, key: 76, pop: 0.12, emoji: 0.75, emojiAll: false, punch: 0.06, alt: 1.0, flash: 0.0, sfx: 0.6, keyColors: ["yellow"] },
  标准: { cap: 76, key: 92, pop: 0.3, emoji: 1.0, emojiAll: true, punch: 0.14, alt: 1.09, flash: 0.28, sfx: 1.0, keyColors: ["yellow"] },
  热闹: { cap: 82, key: 106, pop: 0.45, emoji: 1.15, emojiAll: true, punch: 0.2, alt: 1.11, flash: 0.4, sfx: 1.2, keyColors: ["yellow", "pink", "cyan"] },
};
const P = PRESETS[ED.preset ?? "标准"];

/* ---------- 时间解析 ---------- */
const T = (r: TRef | undefined, fallback = 0): number => {
  if (r === undefined) return fallback;
  if (typeof r === "number") return r;
  const m = /^(\d+):(.*)$/.exec(r);
  if (!m) throw new Error(`时间写法不对：${r}`);
  const s = SEGS[Number(m[1]) - 1];
  if (!s) throw new Error(`没有第 ${m[1]} 段：${r}`);
  const w = m[2];
  if (!w) return s.start;
  if (w === "end") return s.end;
  const [word, nthS] = w.split("#");
  let idx = -1;
  for (let k = 0; k < Number(nthS ?? 1); k++) idx = s.text.indexOf(word, idx + 1);
  if (idx < 0) throw new Error(`第 ${m[1]} 段找不到「${word}」`);
  while (s.chars[String(idx)] === undefined && idx < s.text.length) idx++;
  return s.chars[String(idx)] ?? s.start;
};
const segAt = (t: number) => Math.max(0, SEGS.findIndex((s) => t >= s.start && t < s.end));
const sp = (f: number, at: number, damping = 12, stiffness = 180, mass = 0.7) => spring({ frame: f - F(at), fps: FPS, config: { damping, stiffness, mass } });
const win = (f: number, a: number, b: number, d = 5) => interpolate(f, [F(a), F(a) + d, F(b) - d, F(b)], [0, 1, 1, 0], clamp);
const stroke = (px: number, c = "#111") => Array.from({ length: 16 }, (_, a) => `${(Math.cos((a / 16) * Math.PI * 2) * px).toFixed(1)}px ${(Math.sin((a / 16) * Math.PI * 2) * px).toFixed(1)}px 0 ${c}`).join(",");
const isLatin = (c: string) => /[A-Za-z0-9.]/.test(c);

const SHOWS = (ED.showcase ?? []).map((s) => ({ ...s, a: T(s.from), b: T(s.to) }));
const inShow = (t: number) => SHOWS.some((s) => t >= s.a && t < s.b);
const shrinkAt = (f: number) => Math.max(0, ...SHOWS.map((s) => interpolate(f, [F(s.a) - 2, F(s.a) + 10, F(s.b) - 10, F(s.b)], [0, 1, 1, 0], { ...clamp, easing: Easing.inOut(Easing.cubic) })));
const KEYS = (ED.keys ?? []).slice().sort((a, b) => b.length - a.length);
/** 没写 punch 时：每段第一个关键词推一下 */
const PUNCH = (ED.punch ?? SEGS.map((s) => { const k = KEYS.find((k) => s.text.includes(k)); return k ? `${s.i}:${k}` : null; }).filter(Boolean) as string[]).map((r) => T(r));

/* ================= 主播 ================= */
const Host: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const base = segAt(t) % 2 ? P.alt : 1.0;
  let punch = 0;
  for (const at of PUNCH) { const d = f - F(at); if (d >= 0 && d < 26) punch = Math.max(punch, interpolate(d, [0, 4, 26], [0, 1, 0], { ...clamp, easing: Easing.out(Easing.quad) })); }
  const shrink = shrinkAt(f);
  const sc = base * (1 + P.punch * punch);
  const full = { x: 0, y: 0, w: 1080, h: 1920, r: 0 }, pip = { x: 700, y: 1010, w: 330, h: 586, r: 34 };
  const m = (a: number, b: number) => a + (b - a) * shrink;
  const box = { x: m(full.x, pip.x), y: m(full.y, pip.y), w: m(full.w, pip.w), h: m(full.h, pip.h), r: m(full.r, pip.r) };
  const crop = ED.videoCrop ?? 0;
  return (
    <div style={{ position: "absolute", left: box.x, top: box.y, width: box.w, height: box.h, borderRadius: box.r, overflow: "hidden",
      boxShadow: shrink > 0.05 ? `0 0 0 ${6 * shrink}px #fff, 0 20px 60px rgba(0,0,0,.5)` : "none", zIndex: shrink > 0.05 ? 30 : 0 }}>
      <div style={{ position: "absolute", left: 0, top: -crop * (box.w / 1080), width: box.w, height: (box.w * 1920 + crop * 2 * box.w) / 1080, transform: `scale(${sc})`, transformOrigin: "50% 26%", filter: "contrast(1.05) saturate(1.07) brightness(1.02)" }}>
        <OffthreadVideo src={staticFile(ED.video ?? "main.mp4")} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>
      {P.flash > 0 && SEGS.slice(1).map((s, k) => { const d = f - F(s.start); return d >= 0 && d < 3 ? <div key={k} style={{ position: "absolute", inset: 0, background: "#fff", opacity: (1 - d / 3) * P.flash }} /> : null; })}
    </div>
  );
};

/* ================= 顶部：标题 + 章节 + AI 标识 ================= */
const CH = (ED.chapters ?? []).map((c, k) => ({ at: T(c.at), t: c.t, n: "①②③④⑤⑥⑦⑧⑨"[k] }));
const TopBar: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const p = sp(f, 0.2, 14, 140);
  const cur = [...CH].reverse().find((c) => t >= c.at) ?? CH[0];
  return (
    <>
      {ED.title && (
        <div style={{ position: "absolute", left: 0, right: 0, top: 96, display: "flex", justifyContent: "center", opacity: p, transform: `translateY(${(1 - p) * -40}px)` }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 30px", borderRadius: 999, background: "rgba(15,15,20,.72)", border: "2px solid rgba(255,255,255,.18)" }}>
            {ED.title.left && <><span style={{ fontFamily: ZH, fontWeight: 600, fontSize: 36, color: "#fff" }}>{ED.title.left}</span><span style={{ width: 2, height: 30, background: "rgba(255,255,255,.35)" }} /></>}
            <span style={{ fontFamily: ZH, fontWeight: 600, fontSize: 36, color: COLORS.yellow }}>{ED.title.right}</span>
          </div>
        </div>
      )}
      {cur && (
        <div style={{ position: "absolute", left: 0, right: 0, top: 178, display: "flex", justifyContent: "center", opacity: p }}>
          <div style={{ transform: `scale(${0.6 + 0.4 * sp(f, cur.at, 11, 200)})`, padding: "6px 22px", borderRadius: 12, background: BRAND, fontFamily: ZH, fontWeight: 600, fontSize: 30, color: "#fff", boxShadow: `0 6px 20px ${BRAND}77` }}>{cur.n} {cur.t}</div>
        </div>
      )}
      <div style={{ position: "absolute", left: 30, top: 40, fontFamily: ZH, fontSize: 22, color: "rgba(255,255,255,.8)", padding: "4px 12px", borderRadius: 8, background: "rgba(0,0,0,.35)" }}>{ED.badge ?? "内容由 AI 数字人演绎"}</div>
    </>
  );
};

/* ================= 花字字幕 ================= */
type Line = { text: string; i0: number; seg: number; start: number; end: number };
const LINES: Line[] = (() => {
  const out: Line[] = [];
  SEGS.forEach((s, si) => {
    const tAt = (i: number) => { let k = i; while (s.chars[String(k)] === undefined && k < s.text.length) k++; return s.chars[String(k)] ?? s.end; };
    const parts: Array<[string, number]> = []; let buf = "", b0 = 0;
    for (let i = 0; i < s.text.length; i++) {
      const c = s.text[i];
      if ("，。、：；！？".includes(c)) { if (buf.trim()) parts.push([buf, b0]); buf = ""; b0 = i + 1; continue; }
      if (!buf) b0 = i; buf += c;
    }
    if (buf.trim()) parts.push([buf, b0]);
    const fin: Array<[string, number]> = [];
    for (const [p, o] of parts) {
      if (Array.from(p.replace(/\s/g, "")).length <= 12) { fin.push([p, o]); continue; }
      let cut = Math.floor(p.length / 2); while (cut < p.length && isLatin(p[cut])) cut++;
      fin.push([p.slice(0, cut), o], [p.slice(cut), o + cut]);
    }
    fin.forEach(([p, o], k) => { const nx = fin[k + 1]; out.push({ text: p.trim(), i0: o + (p.length - p.trimStart().length), seg: si, start: tAt(o), end: nx ? tAt(nx[1]) - 0.02 : s.end }); });
  });
  return out;
})();
const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const ln = LINES.find((l) => t >= l.start - 0.04 && t < l.end);
  if (!ln) return null;
  const s = SEGS[ln.seg];
  const hl: number[] = new Array(ln.text.length).fill(-1);
  KEYS.forEach((k, ki) => { let i = ln.text.indexOf(k); while (i >= 0) { for (let j = i; j < i + k.length; j++) if (hl[j] < 0) hl[j] = ki; i = ln.text.indexOf(k, i + 1); } });
  const show = inShow(t);
  const enter = sp(f, ln.start - 0.04, 13, 220);
  let pos = 0;
  return (
    <div style={{ position: "absolute", left: 40, right: show ? 380 : 40, top: show ? 1640 : 1560, display: "flex", justifyContent: "center", flexWrap: "wrap", transform: `scale(${(0.86 + 0.14 * enter) * (show ? 0.82 : 1)})`, zIndex: 40 }}>
      {Array.from(ln.text).map((c, k) => {
        const idx = ln.i0 + pos; pos += c.length;
        let wi = idx; if (isLatin(c)) while (wi > 0 && isLatin(s.text[wi - 1])) wi--;
        const ta = s.chars[String(wi)] ?? s.chars[String(idx)] ?? ln.start;
        const on = f - F(ta) + 2;
        const isK = hl[k] >= 0;
        const kc = col(P.keyColors[(hl[k] < 0 ? 0 : hl[k]) % P.keyColors.length]);
        const pk = spring({ frame: on, fps: FPS, config: { damping: 9, stiffness: 260, mass: 0.5 } });
        const shown = on >= 0;
        if (c === " ") return <span key={k} style={{ width: 18 }} />;
        return (
          <span key={k} style={{
            display: "inline-block", fontFamily: isLatin(c) ? EN : ZH, fontWeight: isK ? 800 : 600, fontSize: isK ? P.key : P.cap, lineHeight: 1.18, color: isK ? kc : "#fff",
            opacity: shown ? 1 : 0, transform: `translateY(${shown ? (1 - pk) * 26 : 26}px) scale(${shown ? (isK ? 0.6 + 0.4 * pk + P.pop * 0.4 * Math.max(0, 1 - on / 10) : 1 - P.pop + P.pop * pk) : 0.7})`,
            textShadow: `${stroke(isK ? 6 : 5, isK ? "#3B1D00" : "#111")}, 0 8px 16px rgba(0,0,0,.45)`,
          }}>{c}</span>
        );
      })}
    </div>
  );
};

/* ================= 表情 ================= */
const EMO = (ED.emojis ?? []).map((m) => ({ ...m, at: T(m.at), side: m.side ?? "r" })).filter((_, k) => P.emojiAll || k % 2 === 0);
const Emojis: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <>
      {EMO.map((m, k) => {
        const nx = EMO.slice(k + 1).find((n) => n.side === m.side);
        const end = Math.min(m.at + 2.2, nx ? nx.at : 999);
        if (f < F(m.at) - 1 || f > F(end) + 6) return null;
        const p = sp(f, m.at, 8, 240, 0.6), out = interpolate(f, [F(end) - 2, F(end) + 6], [1, 0], clamp);
        const wob = Math.sin((f - F(m.at)) / 4) * 6 * Math.max(0, 1 - (f - F(m.at)) / 30);
        return (
          <div key={k} style={{ position: "absolute", left: m.side === "l" ? 40 : 800, top: m.y ?? 520, transform: `scale(${p * out * P.emoji}) rotate(${(m.side === "l" ? -10 : 10) + wob}deg)`, zIndex: 20, filter: "drop-shadow(0 10px 18px rgba(0,0,0,.4))" }}>
            <NotoEmoji char={m.e} at={F(m.at)} size={230} cycles={2} />
          </div>
        );
      })}
    </>
  );
};

/* ================= 卡片库 ================= */
const Panel: React.FC<{ p: number; style?: React.CSSProperties; children: React.ReactNode }> = ({ p, style, children }) => (
  <div style={{ position: "absolute", left: 70, top: 900, width: 940, padding: "30px 34px", borderRadius: 32, background: "rgba(18,18,26,.86)", border: "2px solid rgba(255,255,255,.16)", boxShadow: "0 24px 70px rgba(0,0,0,.5)",
    opacity: Math.min(1, p * 1.5), transform: `translateY(${(1 - p) * 70}px) scale(${0.82 + 0.18 * p})`, ...style }}>{children}</div>
);
const Tag: React.FC<{ text: string; color?: string; bg?: string; size?: number }> = ({ text, color = "#fff", bg = "rgba(255,255,255,.1)", size = 30 }) => (
  <span style={{ display: "inline-block", fontFamily: ZH, fontWeight: 600, fontSize: size, color, background: bg, padding: "6px 16px", borderRadius: 12 }}>{text}</span>
);
type Card = Record<string, any> & { type: string; at: TRef; until?: TRef; a: number; b: number };
const CARDS: Card[] = (ED.cards ?? []).map((c, k, all) => {
  const a = T(c.at);
  const seg = SEGS[segAt(a)];
  const nextA = all.slice(k + 1).map((n) => T(n.at)).find((x) => x > a);
  return { ...c, a, b: c.until !== undefined ? T(c.until) : Math.min(seg.end + 0.15, nextA ?? 1e9, a + 4.5) };
});
const CardView: React.FC<{ c: Card }> = ({ c }) => {
  const f = useCurrentFrame();
  const p = sp(f, c.a, 12, 190);
  const items: any[] = c.items ?? [];
  switch (c.type) {
    case "stamp": {
      const q = sp(f, c.a, 10, 260, 0.6);
      return <div style={{ position: "absolute", left: c.x ?? 250, top: c.y ?? 1060, transform: `rotate(${c.rot ?? -7}deg) scale(${2 - q})`, opacity: Math.min(1, q * 2), fontFamily: ZH, fontWeight: 800, fontSize: c.size ?? 120, color: col(c.color, "green"), padding: "0 26px", border: `8px solid ${col(c.color, "green")}`, borderRadius: 24, background: "rgba(20,10,10,.55)" }}>{c.text}</div>;
    }
    case "big": return (
      <div style={{ position: "absolute", left: 0, right: 0, top: c.y ?? 1080, display: "flex", justifyContent: "center", transform: `rotate(${c.rot ?? -5}deg) scale(${sp(f, c.a, 9, 220)})` }}>
        <div style={{ padding: "18px 50px", borderRadius: 30, background: `linear-gradient(135deg, ${col(c.color)}, #FFB03A)`, fontFamily: ZH, fontWeight: 900, fontSize: c.size ?? 104, color: "#2A1600", boxShadow: "0 16px 40px rgba(255,176,58,.5)" }}>{c.text}</div>
      </div>
    );
    case "slam": return (
      <div style={{ position: "absolute", left: 0, right: 0, top: c.y ?? 1000, textAlign: "center", transform: `rotate(${c.rot ?? -4}deg) scale(${1.8 - 0.8 * sp(f, c.a, 9, 260)})`, opacity: Math.min(1, sp(f, c.a, 9, 260) * 2), fontFamily: ZH, fontWeight: 900, fontSize: c.size ?? 130, color: "#fff", textShadow: stroke(8, col(c.color, "orange")) }}>{c.text}</div>
    );
    case "tags": return (
      <Panel p={p}>
        {c.title && <div style={{ fontFamily: ZH, fontWeight: 600, fontSize: 36, color: "rgba(255,255,255,.75)", marginBottom: 20 }}>{c.title}</div>}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {items.map((it, k) => { const at = T(it.at ?? c.at) ; const on = f >= F(at); const q = sp(f, at, 11, 220);
            return <div key={k} style={{ padding: "22px 0", borderRadius: 18, textAlign: "center", background: on ? col(it.color, ["orange", "green", "cyan", "purple"][k % 4]) : "rgba(255,255,255,.06)", fontFamily: /[A-Za-z]/.test(it.t) ? EN : ZH, fontWeight: 800, fontSize: 44, color: on ? "#111" : "#fff", transform: `scale(${on ? 0.85 + 0.15 * q : 0.9})`, opacity: on ? 1 : 0.35 }}>{it.t}</div>; })}
        </div>
      </Panel>
    );
    case "bars": return (
      <Panel p={p}>
        {c.title && <div style={{ fontFamily: ZH, fontWeight: 600, fontSize: 36, color: "rgba(255,255,255,.75)", marginBottom: 18 }}>{c.title}</div>}
        {items.map((it, k) => { const g = interpolate(f, [F(c.a) + k * 3, F(c.a) + k * 3 + 18], [0, it.v], { ...clamp, easing: Easing.out(Easing.cubic) });
          return (
            <div key={k} style={{ display: "flex", alignItems: "center", gap: 18, margin: "12px 0" }}>
              <span style={{ width: 230, fontFamily: /[A-Za-z]/.test(it.t) ? EN : ZH, fontWeight: 700, fontSize: 34, color: "#fff" }}>{it.t}</span>
              <div style={{ flex: 1, height: 34, borderRadius: 17, background: "rgba(255,255,255,.08)" }}><div style={{ width: `${g * 100}%`, height: "100%", borderRadius: 17, background: col(it.color, "orange") }} /></div>
              {it.label && <span style={{ width: 130, fontFamily: ZH, fontWeight: 700, fontSize: 30, color: "#fff" }}>{it.label}</span>}
            </div>
          ); })}
        {c.note && <div style={{ fontFamily: ZH, fontSize: 24, color: "rgba(255,255,255,.55)", marginTop: 10 }}>{c.note}</div>}
      </Panel>
    );
    case "list": return (
      <Panel p={p}>
        {c.title && <div style={{ fontFamily: ZH, fontWeight: 700, fontSize: 40, color: "#fff", marginBottom: 16 }}>{c.title}</div>}
        {items.map((it, k) => { const at = T(it.at ?? c.at) + (it.at ? 0 : k * 0.25); const q = sp(f, at, 12, 200);
          return <div key={k} style={{ display: "flex", alignItems: "center", gap: 16, margin: "14px 0", opacity: Math.min(1, q * 1.5), transform: `translateX(${(1 - q) * 60}px)` }}><span style={{ fontSize: 40 }}>{it.tone === "bad" ? "❌" : "✅"}</span><span style={{ fontFamily: ZH, fontWeight: 600, fontSize: 40, color: it.tone === "bad" ? "#FFB3B3" : "#fff" }}>{it.t}</span></div>; })}
      </Panel>
    );
    case "number": {
      const v = interpolate(f, [F(c.a), F(c.a) + 24], [0, c.value], { ...clamp, easing: Easing.out(Easing.cubic) });
      return (
        <div style={{ position: "absolute", left: 0, right: 0, top: c.y ?? 1000, textAlign: "center", transform: `scale(${sp(f, c.a, 10, 220)})` }}>
          {c.label && <div style={{ fontFamily: ZH, fontWeight: 600, fontSize: 40, color: "#fff", textShadow: stroke(4) }}>{c.label}</div>}
          <div style={{ fontFamily: EN, fontWeight: 900, fontSize: c.size ?? 170, color: col(c.color), textShadow: stroke(8, "#3B1D00") }}>{(c.prefix ?? "") + Math.round(v).toLocaleString("en-US")}<span style={{ fontFamily: ZH, fontSize: 70 }}>{c.unit ?? ""}</span></div>
        </div>
      );
    }
    case "image": return (
      <div style={{ position: "absolute", left: c.x ?? 140, top: c.y ?? 880, width: c.w ?? 800, borderRadius: 26, overflow: "hidden", border: "5px solid #fff", boxShadow: "0 24px 60px rgba(0,0,0,.5)", opacity: Math.min(1, p * 1.5), transform: `translateY(${(1 - p) * 80}px) rotate(${c.rot ?? 0}deg)` }}>
        <Img src={staticFile(c.src)} style={{ width: "100%", display: "block" }} />
        {c.label && <div style={{ position: "absolute", left: 16, top: 14 }}><Tag text={c.label} bg="rgba(0,0,0,.6)" size={30} /></div>}
      </div>
    );
    case "vs": {
      const pr = sp(f, T(c.left?.at ?? c.at), 12, 170), pv = sp(f, T(c.right?.at ?? c.at), 12, 170);
      return (
        <div style={{ position: "absolute", left: 0, right: 0, top: c.y ?? 960, display: "flex", justifyContent: "center", alignItems: "center", gap: 30 }}>
          <div style={{ transform: `scale(${pr})` }}><Tag text={c.left?.t ?? ""} size={56} bg={BRAND} /></div>
          <div style={{ fontFamily: EN, fontWeight: 900, fontSize: 70, color: "#fff", textShadow: stroke(5), opacity: pv }}>VS</div>
          <div style={{ transform: `scale(${pv})` }}><Tag text={c.right?.t ?? ""} size={56} bg="rgba(40,40,52,.95)" /></div>
        </div>
      );
    }
    default: return null;
  }
};

/* ================= 作品展示（主播缩成小窗） ================= */
const Showcase: React.FC<{ s: (typeof SHOWS)[number] }> = ({ s }) => {
  const f = useCurrentFrame();
  const per = (s.b - s.a) / s.items.length;
  const starts = s.items.map((r, k) => (r.at !== undefined ? T(r.at) : s.a + k * per));
  return (
    <AbsoluteFill style={{ opacity: win(f, s.a - 0.1, s.b, 6) }}>
      <AbsoluteFill style={{ background: "#0B0B10" }} />
      {s.items.map((r, k) => {
        const a = starts[k], e = starts[k + 1] ?? s.b;
        if (f < F(a) || f >= F(e)) return null;
        const z = interpolate(f, [F(a), F(e)], [1.0, 1.06]);
        const isImg = /\.(jpe?g|png|webp)$/i.test(r.src);
        const h = r.ratio === "9:16" ? 1200 : r.ratio === "1:1" ? 900 : 608, w = r.ratio === "9:16" ? 675 : r.ratio === "1:1" ? 900 : 1080;
        const media = (st: React.CSSProperties) => isImg ? <Img src={staticFile(r.src)} style={st} /> : <OffthreadVideo src={staticFile(r.src)} muted style={st} />;
        return (
          <AbsoluteFill key={k}>
            <Sequence from={F(a)} durationInFrames={F(e - a) + 2} layout="none">
              <AbsoluteFill style={{ filter: "blur(38px) brightness(.45) saturate(1.2)", transform: "scale(1.25)" }}>{media({ width: "100%", height: "100%", objectFit: "cover" })}</AbsoluteFill>
              <div style={{ position: "absolute", left: (1080 - w) / 2, top: 380, width: w, height: h, overflow: "hidden", borderRadius: r.ratio === "16:9" || !r.ratio ? 0 : 24, boxShadow: "0 30px 80px rgba(0,0,0,.6)" }}>
                <div style={{ width: "100%", height: "100%", transform: `scale(${z})`, background: r.fit === "contain" ? "#fff" : undefined }}>{media({ width: "100%", height: "100%", objectFit: r.fit ?? "cover" })}</div>
              </div>
            </Sequence>
            {r.label && <div style={{ position: "absolute", left: 40, top: 300, transform: `scale(${sp(f, a, 11, 220)})`, transformOrigin: "0 50%" }}><Tag text={r.label} size={40} bg={`${BRAND}EE`} /></div>}
            <div style={{ position: "absolute", inset: 0, background: "#fff", opacity: interpolate(f - F(a), [0, 3], [k ? 0.5 : 0, 0], clamp) }} />
          </AbsoluteFill>
        );
      })}
      {s.note && <div style={{ position: "absolute", left: 40, top: 398 + (({ "9:16": 1200, "1:1": 900 } as Record<string, number>)[s.items[0]?.ratio ?? ""] ?? 608), fontFamily: ZH, fontSize: 24, color: "rgba(255,255,255,.6)" }}>{s.note}</div>}
    </AbsoluteFill>
  );
};

/* ================= 号召 ================= */
const Cta: React.FC = () => {
  const f = useCurrentFrame();
  const c = ED.cta!; const a = T(c.at), b = T(c.subAt, a + 0.6);
  if (f < F(a)) return null;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 960, display: "flex", flexDirection: "column", alignItems: "center", gap: 26, zIndex: 35 }}>
      <div style={{ transform: `rotate(-4deg) scale(${sp(f, a, 9, 220)})`, fontFamily: ZH, fontWeight: 900, fontSize: 120, color: "#fff", textShadow: stroke(8, BRAND) }}>{c.text}</div>
      {c.sub && f >= F(b) && <div style={{ transform: `rotate(3deg) scale(${sp(f, b, 9, 220)})`, padding: "16px 46px", borderRadius: 999, background: `linear-gradient(135deg, #FFB03A, ${BRAND})`, fontFamily: ZH, fontWeight: 900, fontSize: 80, color: "#fff" }}>{c.sub}</div>}
    </div>
  );
};

/* ================= 声音：卡片/表情/章节自动配音效 ================= */
const SFX: Array<[number, string, number]> = (() => {
  const s: Array<[number, string, number]> = [];
  const snd: Record<string, string> = { stamp: "slam-2", big: "impact", slam: "slam-1", tags: "whoosh", bars: "swish-2", list: "page-1", number: "ding", image: "swish-1", vs: "pop" };
  CARDS.forEach((c) => { s.push([c.a - 0.05, snd[c.type] ?? "pop", 0.5]); (c.items ?? []).forEach((it: any) => it.at && s.push([T(it.at), "pop", 0.4])); });
  EMO.forEach((m) => s.push([m.at, "tap", 0.22]));
  CH.slice(1).forEach((c) => s.push([c.at, "whoosh", 0.4]));
  SHOWS.forEach((x) => { s.push([x.a - 0.1, "whoosh", 0.55]); s.push([x.b - 0.2, "whoosh", 0.45]); });
  if (ED.cta) s.push([T(ED.cta.at), "impact", 0.55], [T(ED.cta.subAt, T(ED.cta.at) + 0.6), "done", 0.5]);
  if (P.sfx > 1) PUNCH.forEach((a) => s.push([a, "pop", 0.3]));
  return s.map(([a, n, v]) => [a, n, Math.min(1, v * P.sfx)]);
})();

export const Huazi: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const vol = ED.music?.vol ?? 0.075;
  const showing = inShow(t);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Host />
      <div style={{ position: "absolute", left: 0, right: 0, top: 820, bottom: 0, background: "linear-gradient(180deg, transparent, rgba(0,0,0,.35) 30%, rgba(0,0,0,.5))", opacity: showing ? 0 : 1 }} />
      {CARDS.map((c, k) => (t >= c.a - 0.1 && t < c.b + 0.2 && !showing ? <AbsoluteFill key={k} style={{ opacity: win(f, c.a - 0.05, c.b + 0.15, 4) }}><CardView c={c} /></AbsoluteFill> : null))}
      {SHOWS.map((s, k) => (t >= s.a - 0.2 && t < s.b + 0.2 ? <React.Fragment key={k}><Showcase s={s} /><Host /></React.Fragment> : null))}
      {ED.pack && <PackLayer items={ED.pack} T={(r) => T(r)} />}
      {ED.cta && <Cta />}
      <Emojis />
      <TopBar />
      <Captions />
      {ED.credits && <div style={{ position: "absolute", left: 0, right: 0, bottom: 40, textAlign: "center", fontFamily: ZH, fontSize: 20, color: "rgba(255,255,255,.5)", opacity: interpolate(f, [TOTAL_FRAMES - F(TAIL) - 10, TOTAL_FRAMES - F(TAIL)], [0, 1], clamp) }}>{ED.credits}</div>}
      <Audio src={staticFile(ED.voice ?? "voice.wav")} />
      {ED.music && <Audio src={staticFile(ED.music.src)} loop volume={(fr) => interpolate(fr, [0, 10, TOTAL_FRAMES - 40, TOTAL_FRAMES - 1], [0, vol, vol, 0], clamp)} />}
      {SFX.map(([at, name, v], i) => <Sequence key={i} from={Math.max(0, F(at))} durationInFrames={F(2.5)} layout="none"><Audio src={staticFile(`sfx/${name}.wav`)} volume={v} /></Sequence>)}
    </AbsoluteFill>
  );
};
