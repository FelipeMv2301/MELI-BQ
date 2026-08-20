from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def index(request):
    """
    Placeholder de arranque — HU-FM4.4 (panel de estado) todavía no está implementada.
    Ver backlog_proyecto/backlog-facturacion-ml.md.
    """
    return render(request, "facturacion_ml/index.html")
