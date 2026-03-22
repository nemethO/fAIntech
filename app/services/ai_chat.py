# AI Chat Service (RAG Pipeline)
#
# Responsibilities:
# 1. Receive user question in Hungarian
# 2. Analyze intent (spending query, savings, tips, etc.)
# 3. Query relevant transactions from DB (retrieval step)
# 4. Build prompt with transaction context (augmentation step)
# 5. Send to LLM and return response (generation step)
# 6. Apply PII filter before sending data to LLM
#
# Quick-action buttons:
# - Havi osszefoglalo
# - Elelmiszer kiadasok
# - Ettermistatisztika
# - Megtakaritas
# - Keretallapot
# - Penzugyi tippek
