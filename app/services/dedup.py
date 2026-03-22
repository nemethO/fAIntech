# Deduplication Service
#
# Responsibilities:
# - Generate SHA-256 hash from transaction key fields:
#   (date, amount, partner, description, account_id)
# - Check existing hashes before import
# - Report duplicate count back to import wizard
