"""3-Model AI Synthesis, Pluggable Fallbacks, and Ambiguity Abstention Engine Package."""

from prototype.engine.synthesis.providers import (
    BaseSynthesisProvider,
    DeterministicFallbackProvider,
    GeminiSynthesisProvider,
    OllamaSynthesisProvider,
    OpenAISynthesisProvider,
    PluggableLLMProvider,
)
from prototype.engine.synthesis.model1_diagnostic import Model1Diagnostic
from prototype.engine.synthesis.model2_macro import Model2MacroSentinel
from prototype.engine.synthesis.model3_prescriptive import Model3Prescriptive
from prototype.engine.synthesis.abstention import AbstentionEngine

__all__ = [
    "BaseSynthesisProvider",
    "DeterministicFallbackProvider",
    "GeminiSynthesisProvider",
    "OllamaSynthesisProvider",
    "OpenAISynthesisProvider",
    "PluggableLLMProvider",
    "Model1Diagnostic",
    "Model2MacroSentinel",
    "Model3Prescriptive",
    "AbstentionEngine",
]
