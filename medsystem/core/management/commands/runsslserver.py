from pathlib import Path
import ssl

from django.core.management.commands.runserver import Command as RunserverCommand


class Command(RunserverCommand):
    help = "Run the development server with a local SSL certificate."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--ssl-certfile",
            default=None,
            help="Path to the SSL certificate file (.crt/.pem).",
        )
        parser.add_argument(
            "--ssl-keyfile",
            default=None,
            help="Path to the SSL private key file (.key/.pem).",
        )

    def get_handler(self, *args, **options):
        handler = super().get_handler(*args, **options)

        certfile = options.get("ssl_certfile") or Path("certs/localhost.crt")
        keyfile = options.get("ssl_keyfile") or Path("certs/localhost.key")

        certfile = Path(certfile)
        keyfile = Path(keyfile)

        if not certfile.exists():
            raise FileNotFoundError(f"SSL certificate not found: {certfile}")
        if not keyfile.exists():
            raise FileNotFoundError(f"SSL key not found: {keyfile}")

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=str(certfile), keyfile=str(keyfile))
        return context.wrap_socket(handler, server_side=True)
