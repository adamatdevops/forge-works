import hashlib
import hmac


def validate_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validate GitHub webhook HMAC-SHA256 signature."""
    if not signature.startswith("sha256="):
        return False
    expected = signature[7:]
    computed = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, computed)


def validate_argocd_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validate ArgoCD webhook HMAC-SHA1 signature."""
    if not signature.startswith("sha1="):
        return False
    expected = signature[5:]
    computed = hmac.new(secret.encode(), payload, hashlib.sha1).hexdigest()
    return hmac.compare_digest(expected, computed)


def validate_kubernetes_token(token: str, expected_token: str) -> bool:
    """Validate Kubernetes Bearer token."""
    if token.startswith("Bearer "):
        token = token[7:]
    return hmac.compare_digest(token, expected_token)
