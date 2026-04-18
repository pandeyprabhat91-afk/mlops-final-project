#!/usr/bin/env bash
# gen_certs.sh -- Generate self-signed TLS certificates for local/on-prem deployment.
# Replace with CA-signed certs for production.
set -euo pipefail

CERT_DIR="nginx/certs"
mkdir -p "$CERT_DIR"

SUBJ="//C=US\ST=Local\L=Local\O=DeepScan\CN=localhost"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$CERT_DIR/server.key" \
  -out "$CERT_DIR/server.crt" \
  -subj "$SUBJ"

echo "Certificates written to $CERT_DIR/"
