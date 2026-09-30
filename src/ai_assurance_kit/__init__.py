"""ai-assurance-kit: proportionate AI assurance as structured records, checks and cards.

Unofficial. Not government guidance. Informed by public UK guidance and the NIST AI RMF;
it does not implement, certify or satisfy any of them.
"""

__version__ = "0.1.0"

from ai_assurance_kit.schema import SCHEMA_VERSION, AIUseRecord

__all__ = ["SCHEMA_VERSION", "AIUseRecord", "__version__"]
