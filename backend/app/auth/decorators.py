rom functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def roles_required(*allowed_roles):
    """Restrict a route to one or more of: admin, vendor, analyst.

    Usage:
        @roles_required("admin", "analyst")
        def some_view():
            ...
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role")
            if role not in allowed_roles:
                return jsonify(error="Forbidden: insufficient role"), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def vendor_scoped(fn):
    """Ensures a vendor-role user can only access their own vendor_id resources."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") == "vendor":
            requested_vendor_id = kwargs.get("vendor_id")
            if requested_vendor_id and str(requested_vendor_id) != str(claims.get("vendor_id")):
                return jsonify(error="Forbidden: cross-vendor access denied"), 403
        return fn(*args, **kwargs)

    return wrapper
