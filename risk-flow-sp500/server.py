import http.server
import socketserver
import subprocess
import json
import logging
import sys

PORT = 8000
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class RiskFlowAPIHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/update_data':
            logger.info("Recibida peticion para actualizar datos...")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            scripts_to_run = [
                ("src.fetch_data", ["python", "-m", "src.fetch_data"]),
                ("src.clean_data", ["python", "-m", "src.clean_data"]),
                ("src.features", ["python", "-m", "src.features"]),
                ("src.simulation", ["python", "-m", "src.simulation"]),
                ("src.risk_metrics", ["python", "-m", "src.risk_metrics"]),
                ("scripts.generate_frontend_data", ["python", "scripts/generate_frontend_data.py"])
            ]
            
            success = True
            for name, cmd in scripts_to_run:
                logger.info(f"Ejecutando {name}...")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Error en {name}:\n{result.stderr}")
                    success = False
                    break
                else:
                    logger.info(f"{name} finalizado exitosamente.")
            
            response = {"status": "success" if success else "error"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404, "Endpoint no encontrado")

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), RiskFlowAPIHandler) as httpd:
        logger.info(f"Servidor Risk-Flow corriendo en http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Servidor detenido.")
            sys.exit(0)
