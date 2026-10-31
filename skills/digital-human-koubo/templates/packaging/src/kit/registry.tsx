// 包装组件注册表：按名字调用组件（edit.json / brief.json 里的 "pack" 列表直接用）。
// 每条：{ "use": "Counter", "at": "3:积分", "until": "3:end", ...组件参数 }
// 时间：任何叫 at / until 的字段（包括数组里嵌套的，如 words[].at、pins[].at、camera[].at）都可以写 "段:词"，由调用方传入的 T() 换成秒。
// 竖屏 9:16 时，没写位置参数的组件自动换成竖屏默认位置（VERT）。
import React from "react";
import { AbsoluteFill } from "remotion";
import { useT } from "./core";
import { FreezeFrame, HandDraw, Highlight, ZoomFocus } from "./Annotate";
import { ChapterCard, Countdown, Counter, LowerThird, RetentionCaption, SourceTag, SpecCard } from "./Text";
import { CompareWipe, Danmaku, PaperCollage, ProgressChapters, ReactionPop, TeaserColdOpen } from "./Overlay";
import { MapRoute } from "./Map";
import { ArchiveCards, BarCompare, CalloutPill, DocFocus, GhostWord, LeaderLabel, LineDraw, PunchInHost, RecapBoard, SearchTyping, SlamText, TornStrip, TypedNameTag } from "./Explain";
import { NumberSpike, ProgressTracker, ReviewCards, WordStack } from "./Beast";
import { GlassPanel, KeywordStack, Odometer, SourceDoc } from "./Polish";
import { TextBehind } from "./Depth";
import { Aside, ColdOpenFreeze, EvidenceCard, GlitchInterstitial, HostFloaters, MemeWindow, NamePlate, PollPop, TiltLine } from "./Wangan";

export const PACK: Record<string, React.FC<any>> = {
  RetentionCaption, ZoomFocus, HandDraw, FreezeFrame, Highlight, LowerThird, SourceTag, Counter, Countdown, ChapterCard, SpecCard,
  Danmaku, ReactionPop, ProgressChapters, TeaserColdOpen, CompareWipe, PaperCollage, MapRoute,
  MemeWindow, ColdOpenFreeze, EvidenceCard, PollPop, GlitchInterstitial, NamePlate, HostFloaters, Aside, TiltLine,
  DocFocus, TypedNameTag, PunchInHost, RecapBoard, SearchTyping, CalloutPill, LeaderLabel, LineDraw, BarCompare, GhostWord, SlamText, TornStrip, ArchiveCards,
  NumberSpike, ProgressTracker, ReviewCards, WordStack,
  KeywordStack, GlassPanel, Odometer, SourceDoc, TextBehind,
};
/** 竖屏默认位置（1080×1920） */
const VERT: Record<string, Record<string, any>> = {
  RetentionCaption: { y: 1180, size: 92 },
  ZoomFocus: { box: { x: 40, y: 420, w: 1000, h: 1000 } },
  LowerThird: { x: 60, y: 1300 },
  SourceTag: { y: 1780 },
  Counter: { y: 720, size: 190 },
  Countdown: { x: 640, y: 270 },
  SpecCard: { x: 90, y: 880 },
  Danmaku: { top: 320, width: 1080, lanes: 6 },
  ReactionPop: { x: 640, y: 640, size: 280 },
  CompareWipe: { box: { x: 40, y: 420, w: 1000, h: 1100 } },
  NamePlate: { x: 60, y: 1250, qx: 80, qy: 420 },
  PollPop: { qy: 330 },
  KeywordStack: { x: 90, y: 1000 },
  GlassPanel: { x: 76, y: 980 },
  Odometer: { y: 760 },
  TextBehind: { crop: 60, y: 0.28 },
};
export type PackItem = { use: string; [k: string]: any };
const walk = (v: any, T: (r: any) => number, key = ""): any => {
  if (key === "stepAt" && Array.isArray(v)) return v.map((x) => (typeof x === "string" || typeof x === "number" ? T(x) : x));   // 步骤时刻也能写 "段:词"
  if (Array.isArray(v)) return v.map((x) => walk(x, T));
  if (v && typeof v === "object") return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, walk(x, T, k)]));
  if ((key === "at" || key === "until") && (typeof v === "string" || typeof v === "number")) return T(v);
  return v;
};
/** 一层包装：items 里每条按 use 找组件渲染。T 把 "段:词" 换成秒（不传就只认数字秒）。 */
export const PackLayer: React.FC<{ items: PackItem[]; T?: (r: any) => number }> = ({ items, T = (r) => Number(r) }) => {
  const { W, H, t } = useT();
  const vertical = H > W;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {items.map((it, k) => {
        const Comp = PACK[it.use];
        if (!Comp) throw new Error(`没有包装组件「${it.use}」，可用：${Object.keys(PACK).join("、")}`);
        const { use, ...props } = it;
        const p = walk({ ...(vertical ? VERT[use] ?? {} : {}), ...props }, T);
        if (use === "Highlight") return null; // 荧光笔要包在文字外面用，不能单独叠层
        // 可见窗口：有顶层 at 的条目只在 [at, until] 里渲染；没写 until 就用 at + (dur ?? 0) + hold（默认 3.5 秒）
        if (typeof p.at === "number") {
          const end = typeof p.until === "number" ? p.until : p.at + (typeof p.dur === "number" ? p.dur : 0) + (p.hold ?? 3.5);
          if (t < p.at - 0.1 || t > end) return null;
        }
        return <Comp key={k} {...p} />;
      })}
    </AbsoluteFill>
  );
};
export { Highlight };
