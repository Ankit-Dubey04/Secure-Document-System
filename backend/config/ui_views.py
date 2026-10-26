from django.shortcuts import render


def application_shell(request):
    """Serve the UI shell; API JWT authentication remains client-to-API only."""
    return render(request, "ui/index.html")
