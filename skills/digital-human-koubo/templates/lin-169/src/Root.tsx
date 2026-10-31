import React from "react";
import { Composition } from "remotion";
import { Lin } from "./Lin";
import plan from "./scenes.json";

export const Root: React.FC = () => (
  <Composition id="Lin" component={Lin} durationInFrames={Math.round((plan as any).total * 30)} fps={30} width={1920} height={1080} />
);
