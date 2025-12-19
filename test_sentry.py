"""
Script de test pour envoyer des erreurs à Sentry
"""

from sentry_logging import init_sentry, capture_message, capture_exception, log_user_creation
import sentry_sdk

print("=== Test Sentry pour Epic Events CRM ===\n")

result = init_sentry()
if not result:
    print("ERREUR: Sentry n'est pas configuré. Vérifiez SENTRY_DSN dans .env")
    exit(1)

print("Sentry initialisé avec succès\n")
print("Envoi d'un message de test...")
capture_message("Test Epic Events CRM - Message de vérification", level='info')
print("Message envoyé!\n")
print("Envoi d'une exception de test...")
try:
    # Erreur de div par 0
    result = 1 / 0
except Exception as e:
    capture_exception(e)
    print(f"Exception capturée et envoyée: {type(e).__name__}: {e}\n")

print("Simulation d'un log de création d'utilisateur...")
log_user_creation(
    user_info={'user_id': 1, 'email': 'admin@test.com', 'name': 'Admin Test'},
    created_user_info={'name': 'Nouveau User', 'email': 'new@test.com', 'department': 'Commercial'}
)
print("Log de création envoyé!\n")
sentry_sdk.flush(timeout=5)

print("TERMINÉ! Vérifiez votre dashboard Sentry")