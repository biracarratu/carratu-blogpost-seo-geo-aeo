#!/bin/sh
# Gera dois ZIPs: interno (com os perfis dos clientes Carratu) e público (só o template de perfil).
set -e
cd "$(dirname "$0")/.."
N=carratu-blogpost-seo-geo-aeo
OUT=${1:-dist}
mkdir -p "$OUT"
rm -f "$OUT/$N-interno.zip" "$OUT/$N.zip"
zip -qr "$OUT/$N-interno.zip" "$N" -x "$N/.git/*" "$N/build.sh" "*/__pycache__/*"
zip -qr "$OUT/$N.zip" "$N" -x "$N/.git/*" "$N/.gitignore" "$N/build.sh" "*/__pycache__/*" "$N/profiles/carratu-blog.json" "$N/profiles/pontua.json" "$N/profiles/aeogeo.json"
echo "ok: $OUT/$N-interno.zip e $OUT/$N.zip"
