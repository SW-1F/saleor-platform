import os

from django.core import signing
from django.core.exceptions import ValidationError

from ...account.models import Group
from ...permission.enums import get_permissions
from ..error_codes import PluginErrorCode
from ..openid_connect.plugin import OpenIDConnectPlugin
from ..openid_connect.utils import OAUTH_TOKEN_REFRESH_FIELD, jwt_decode
from ..openid_connect.utils import get_saleor_permission_names
from . import PLUGIN_ID


def _env(name: str) -> str | None:
    value = os.environ.get(name)
    return value.strip() if value else None


class GoogleOIDCPlugin(OpenIDConnectPlugin):
    PLUGIN_ID = PLUGIN_ID
    PLUGIN_NAME = "Google"
    PLUGIN_DESCRIPTION = "Basic Google login for Saleor Dashboard."
    DEFAULT_CONFIGURATION = [
        {"name": "client_id", "value": _env("GOOGLE_OIDC_CLIENT_ID")},
        {"name": "client_secret", "value": _env("GOOGLE_OIDC_CLIENT_SECRET")},
        {"name": "enable_refresh_token", "value": True},
        {
            "name": "oauth_authorization_url",
            "value": "https://accounts.google.com/o/oauth2/v2/auth",
        },
        {
            "name": "oauth_token_url",
            "value": "https://oauth2.googleapis.com/token",
        },
        {
            "name": "json_web_key_set_url",
            "value": "https://www.googleapis.com/oauth2/v3/certs",
        },
        {"name": "oauth_logout_url", "value": "https://accounts.google.com/logout"},
        {
            "name": "user_info_url",
            "value": "https://openidconnect.googleapis.com/v1/userinfo",
        },
        {"name": "audience", "value": _env("GOOGLE_OIDC_CLIENT_ID")},
        {"name": "use_oauth_scope_permissions", "value": False},
        {"name": "staff_user_domains", "value": _env("GOOGLE_OIDC_STAFF_DOMAINS")},
        {
            "name": "default_group_name_for_new_staff_users",
            "value": "Google Login Staff",
        },
    ]

    @classmethod
    def get_default_active(cls):
        return bool(_env("GOOGLE_OIDC_CLIENT_ID") and _env("GOOGLE_OIDC_CLIENT_SECRET"))

    def _allowed_staff_emails(self) -> set[str]:
        raw_value = _env("GOOGLE_OIDC_STAFF_EMAILS")
        if not raw_value:
            return set()
        return {email.strip().lower() for email in raw_value.split(",") if email.strip()}

    def is_staff_user_email(self, user):
        user_email = (user.email or "").strip().lower()

        if user_email and user_email in self._allowed_staff_emails():
            return True

        return super().is_staff_user_email(user)

    def _grant_full_permissions_if_allowed(self, user):
        if not self.is_staff_user_email(user):
            return None

        permissions = get_permissions()
        user.effective_permissions = permissions

        return get_saleor_permission_names(permissions)

    def _use_scope_permissions(self, user, scope):
        full_permissions = self._grant_full_permissions_if_allowed(user)
        if full_permissions is not None:
            return full_permissions

        return super()._use_scope_permissions(user, scope)

    def _ensure_staff_access(self, user):
        if not self.is_staff_user_email(user):
            return []

        permissions = get_permissions()
        permission_names = get_saleor_permission_names(permissions)
        default_group_name = self.config.default_group_name or "Google Login Staff"
        group, _ = Group.objects.get_or_create(
            name=default_group_name,
            defaults={"restricted_access_to_channels": False},
        )
        group.permissions.set(permissions)
        user.groups.add(group)
        user.user_permissions.set(permissions)

        if not user.is_staff:
            user.is_staff = True
            user.save(update_fields=["is_staff"])

        user.effective_permissions = permissions
        if hasattr(user, "_perm_cache"):
            user._perm_cache = None
        if hasattr(user, "_user_perm_cache"):
            user._user_perm_cache = None
        if hasattr(user, "_group_perm_cache"):
            user._group_perm_cache = None

        return permission_names

    def get_and_update_user_permissions(self, user, use_scope_permissions, scope):
        full_permissions = self._grant_full_permissions_if_allowed(user)
        if full_permissions is not None:
            return full_permissions

        return super().get_and_update_user_permissions(user, use_scope_permissions, scope)

    # These pass-through overrides are required because Saleor lists external auth
    # plugins by checking methods present in the class __dict__.
    def external_obtain_access_tokens(self, data, request, previous_value):
        result = super().external_obtain_access_tokens(data, request, previous_value)

        if not result.user or not self.is_staff_user_email(result.user):
            return result

        self._ensure_staff_access(result.user)

        return result

    def external_authentication_url(self, data, request, previous_value):
        if not self.active:
            return previous_value

        if not self.use_authorization_flow:
            return previous_value

        redirect_uri = data.get("redirectUri")
        if not redirect_uri:
            msg = "Missing required field - redirectUri"
            raise ValidationError(
                {
                    "redirectUri": ValidationError(
                        msg, code=PluginErrorCode.NOT_FOUND.value
                    )
                }
            )

        kwargs = {
            "redirect_uri": redirect_uri,
            "state": signing.dumps({"redirectUri": redirect_uri}),
        }
        if self.config.audience:
            kwargs["audience"] = self.config.audience
        if self.config.enable_refresh_token:
            # Google only issues a refresh token reliably when offline access
            # is requested with an explicit consent prompt.
            kwargs["access_type"] = "offline"
            kwargs["prompt"] = "consent"

        uri, _state = self.oauth.create_authorization_url(
            self.config.authorization_url, **kwargs
        )
        return {"authorizationUrl": uri}

    def external_logout(self, data, request, previous_value):
        return {}

    def authenticate_user(self, request, previous_value):
        user = super().authenticate_user(request, previous_value)

        if user and self.is_staff_user_email(user):
            self._ensure_staff_access(user)

        return user

    def external_verify(self, data, request, previous_value):
        user, payload = super().external_verify(data, request, previous_value)

        if user and self.is_staff_user_email(user):
            permission_names = self._ensure_staff_access(user)
            payload["permissions"] = permission_names

        return user, payload

    def external_refresh(self, data, request, previous_value):
        refresh_token = data.get("refreshToken")
        if refresh_token:
            try:
                previous_refresh_payload = jwt_decode(refresh_token)
                previous_oauth_refresh_token = previous_refresh_payload.get(
                    OAUTH_TOKEN_REFRESH_FIELD
                )
            except Exception:
                previous_oauth_refresh_token = None
        else:
            previous_oauth_refresh_token = None

        result = super().external_refresh(data, request, previous_value)

        if previous_oauth_refresh_token and not result.refresh_token:
            result.refresh_token = refresh_token

        if result.user and self.is_staff_user_email(result.user):
            self._ensure_staff_access(result.user)

        return result
