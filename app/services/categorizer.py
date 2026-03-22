# AI Categorizer Service
#
# Responsibilities:
# - Take a list of transactions (partner + description)
# - Send to LLM (Gemini/GPT) for semantic categorization
# - Return category assignments with confidence scores
# - Respect human-in-the-loop overrides for future learning
#
# Default categories (from design):
# Elelmiszer, Etterem, Kozlekedes, Szorakozas,
# Vasarlas, Kozuzemi dijak, Lakhatas, Egeszseg, Egyeb
