import type { ComponentType } from "react";

import type { LearnVisualId } from "@/lib/learn/types";

import AssetClassExplorer from "./visuals/AssetClassExplorer";
import DataPipeline from "./visuals/DataPipeline";
import MetricsExplorer from "./visuals/MetricsExplorer";
import MicrostructureStack from "./visuals/MicrostructureStack";
import OrderTypeGuide from "./visuals/OrderTypeGuide";
import QuantJourney from "./visuals/QuantJourney";
import StrategyMap from "./visuals/StrategyMap";

const VISUALS: Record<LearnVisualId, ComponentType> = {
  "quant-journey": QuantJourney,
  "data-pipeline": DataPipeline,
  "asset-explorer": AssetClassExplorer,
  "microstructure-stack": MicrostructureStack,
  "order-types": OrderTypeGuide,
  "metrics-explorer": MetricsExplorer,
  "strategy-map": StrategyMap,
};

export default function LearnVisual({ id }: { id: LearnVisualId }) {
  const Comp = VISUALS[id];
  return Comp ? <Comp /> : null;
}
