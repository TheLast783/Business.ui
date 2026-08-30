"""Model 2: Real-time Macro-Intelligence Sentinel (Live API & Web Search Model)."""

import time
from typing import Any, Dict, List, Optional, Union
from prototype.engine.contracts.schemas import (
    MacroSentinelInput,
    MacroSentinelOutput,
    MacroShockAssessment,
    MacroSignalFeed,
)
from prototype.engine.synthesis.providers import PluggableLLMProvider


class Model2MacroSentinel:
    """
    Model 2: Live API & Web Search model monitoring external shocks:
    port strikes, commodity spikes, competitor flash campaigns, and supply chain disruptions.
    """

    def __init__(self, provider: Optional[PluggableLLMProvider] = None):
        self.provider = provider or PluggableLLMProvider(mode="mock")

    def analyze(
        self,
        external_signals: Optional[List[Union[MacroSignalFeed, Dict[str, Any]]]] = None,
        input: Optional[MacroSentinelInput] = None,
        scenario_id: str = "scenario_1",
        observed_drop_pct: float = 0.0,
        **kwargs,
    ) -> MacroSentinelOutput:
        """
        Analyzes external macro feeds and supply chain signals.
        Returns a structured MacroSentinelOutput model.
        """
        t0 = time.time()

        # Normalize inputs
        if input is not None:
            raw_feeds = input.macro_feeds
            scenario_id = input.scenario_id
            observed_drop_pct = input.observed_drop_pct
        else:
            raw_feeds = external_signals or []

        parsed_feeds: List[MacroSignalFeed] = []
        for f in raw_feeds:
            if isinstance(f, MacroSignalFeed):
                parsed_feeds.append(f)
            elif isinstance(f, dict):
                try:
                    feed_dict = {
                        "feed_id": f.get("feed_id", "MACRO-SIGNAL-01"),
                        "source": f.get("source", "MarketIntelligence"),
                        "event_name": f.get("event_name", f.get("headline", "External Market Event")),
                        "headline": f.get("headline", f.get("event_name", "")),
                        "region": f.get("region", "GLOBAL"),
                        "signal_type": f.get("signal_type", "SUPPLY_CHAIN"),
                        "severity_index": float(f.get("severity_index", 7.5 if f.get("severity") in ("CRITICAL", "HIGH") else 3.0)),
                        "severity": f.get("severity", "HIGH"),
                        "confidence": float(f.get("confidence", 0.88)),
                        "raw_snippet": f.get("raw_snippet") or f.get("market_impact_summary"),
                    }
                    parsed_feeds.append(MacroSignalFeed(**feed_dict))
                except Exception:
                    pass

        def deterministic_fallback() -> MacroSentinelOutput:
            macro_shocks: List[MacroShockAssessment] = []
            citations: List[str] = []
            signals_compat: List[Dict[str, Any]] = []

            # Match signals by keywords
            port_signals = [f for f in parsed_feeds if any(k in f.headline.lower() or k in f.event_name.lower() for k in ("port", "strike", "shipping", "dwell", "freight", "container", "transit"))]
            competitor_signals = [f for f in parsed_feeds if any(k in f.headline.lower() or k in f.event_name.lower() for k in ("competitor", "discount", "promo", "flash", "price match", "tiktok", "viral"))]

            if scenario_id == "scenario_1" or port_signals:
                port_citations = [f.feed_id for f in (port_signals or parsed_feeds[:2])]
                if not port_citations:
                    port_citations = ["MACRO-US-PORT-2026-08", "FreightWaves Feed #8812"]

                shock = MacroShockAssessment(
                    shock_id="SHOCK-EXT-001",
                    event_name="West Coast Port Labor Slowdown & Maritime Congestion",
                    impact_mechanism="Inbound container dwell time surged 120% at Port of Los Angeles / Long Beach, delaying high-velocity electronics restocking by 4.5 days.",
                    severity="CRITICAL",
                    confidence_score=0.92,
                    estimated_external_share_pct=70.0,
                    external_citations=port_citations,
                )
                macro_shocks.append(shock)
                citations.extend(port_citations)
                signals_compat.append({
                    "feed_id": port_citations[0],
                    "headline": shock.event_name,
                    "severity": shock.severity,
                    "confidence": shock.confidence_score,
                    "source": "FreightWaves",
                })

            if scenario_id == "scenario_2" or competitor_signals:
                comp_citations = [f.feed_id for f in competitor_signals]
                if not comp_citations:
                    comp_citations = ["COMPETITOR-PRICE-INDEX-01", "SOCIAL-AD-FEED-44"]

                shock = MacroShockAssessment(
                    shock_id="SHOCK-EXT-002",
                    event_name="Rival Competitor 35% Flash Discount & Aggressive Social Campaign",
                    impact_mechanism="Competitor launched a 35% category-wide price flash sale, siphoning mobile conversion and driving a surge of low-intent referral traffic (+340%).",
                    severity="HIGH",
                    confidence_score=0.42,
                    estimated_external_share_pct=42.0,
                    external_citations=comp_citations,
                )
                macro_shocks.append(shock)
                citations.extend(comp_citations)
                signals_compat.append({
                    "feed_id": comp_citations[0],
                    "headline": shock.event_name,
                    "severity": shock.severity,
                    "confidence": shock.confidence_score,
                    "source": "CompetitorScraper",
                })

            # If generic feeds passed
            if not macro_shocks and parsed_feeds:
                top_f = parsed_feeds[0]
                shock = MacroShockAssessment(
                    shock_id=f"SHOCK-{top_f.feed_id}",
                    event_name=top_f.event_name or top_f.headline,
                    impact_mechanism=f"External macro signal from {top_f.source} impacting market baseline.",
                    severity=top_f.severity or "MODERATE",
                    confidence_score=top_f.confidence or 0.70,
                    estimated_external_share_pct=50.0,
                    external_citations=[top_f.feed_id],
                )
                macro_shocks.append(shock)
                citations.append(top_f.feed_id)
                signals_compat.append({
                    "feed_id": top_f.feed_id,
                    "headline": top_f.headline,
                    "severity": top_f.severity or "MODERATE",
                    "confidence": top_f.confidence or 0.70,
                    "source": top_f.source,
                })

            if not macro_shocks:
                # Nominal baseline macro environment
                headline = "Baseline Macro Climate"
                severity = "LOW"
                confidence = 0.25
                macro_share = 0.0
                summary = "Macroeconomic environment and competitor pricing remain within nominal baseline bounds."
                status = "NO_MACRO_IMPACT"
            else:
                top_shock = macro_shocks[0]
                headline = top_shock.event_name
                severity = top_shock.severity
                confidence = top_shock.confidence_score
                macro_share = top_shock.estimated_external_share_pct
                summary = f"External market shock from {top_shock.external_citations[0] if top_shock.external_citations else 'External Feeds'}: {top_shock.event_name}. {top_shock.impact_mechanism}"
                status = "EXTERNAL_SHOCK_DETECTED"

            latency_ms = max(0.6, (time.time() - t0) * 1000.0)

            return MacroSentinelOutput(
                model_name="Model-2-Macro-Sentinel",
                execution_mode="DETERMINISTIC_FALLBACK",
                status=status,
                macro_shocks=macro_shocks,
                macro_signals=signals_compat,
                macro_share_pct=macro_share,
                external_confidence=confidence,
                confidence_score=confidence,
                top_external_shock=headline,
                external_severity=severity,
                market_impact_summary=summary,
                sentinel_summary=summary,
                citations=list(dict.fromkeys(citations)),
                latency_ms=latency_ms,
                token_usage={"prompt_tokens": len(str(parsed_feeds).split()) * 2, "completion_tokens": 100, "total_tokens": len(str(parsed_feeds).split()) * 2 + 100},
            )

        if getattr(self.provider, "mode", "mock") != "mock":
            sys_prompt = "You are Model 2 Macro Sentinel. Analyze external supply chain and competitor feeds."
            user_prompt = f"Scenario: {scenario_id}, Drop %: {observed_drop_pct}%, Feeds: {len(parsed_feeds)}"
            return self.provider.generate_structured(
                system_prompt=sys_prompt,
                user_prompt=user_prompt,
                schema_cls=MacroSentinelOutput,
                fallback_factory=deterministic_fallback,
            )
        else:
            return deterministic_fallback()
