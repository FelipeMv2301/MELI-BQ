"""
Adaptador de login social — portado casi verbatim de gestorBQ/cuentas/adapters.py. Restringe el
login de Google a cuentas @bioquimica.cl (server-side, además del filtro `hd` que ya hace Google
del lado del selector de cuenta — cinturón y tirantes, igual criterio que el original).
"""

import logging

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden

logger = logging.getLogger("allauth")


class BioquimicaSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get("email", "")
        if not email.endswith(settings.DOMINIO_PERMITIDO):
            raise ImmediateHttpResponse(
                HttpResponseForbidden("Acceso disponible solo a cuentas @bioquimica.cl")
            )

        # Reconciliación por email: si este login Google todavía no está enlazado a un
        # SocialAccount pero ya existe un User con el mismo correo, conectarlos aquí para
        # evitar el formulario de signup (que pediría username). Complementa a
        # SOCIALACCOUNT_EMAIL_AUTHENTICATION como cinturón y tirantes — mismo criterio que gestorBQ.
        if sociallogin.is_existing:
            return
        existing_user = get_user_model().objects.filter(email__iexact=email).first()
        if existing_user:
            sociallogin.connect(request, existing_user)

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        logger.error(
            "Fallo autenticación social: error=%s exception=%r extra_context=%s",
            error, exception, extra_context, exc_info=exception,
        )
        super().on_authentication_error(request, provider, error=error, exception=exception, extra_context=extra_context)
