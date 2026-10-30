# Official non-root NGINX image, pinned to a multi-platform release digest.
FROM ghcr.io/nginx/nginx-unprivileged:1.30.6-alpine-slim@sha256:984a21e29bb10d4c0e122374b97b89a2101823a9331e0f3c6c04bc285ccf447f

# .dockerignore admits only static code/artwork and these server files.
# No collection JSON, snapshots, captures, credentials or native files enter the image.
COPY index.html /usr/share/nginx/html/index.html
COPY pokemon-sleep/*.html pokemon-sleep/*.js pokemon-sleep/*.css pokemon-sleep/*.svg /usr/share/nginx/html/pokemon-sleep/
COPY pokemon-sleep/assets/ /usr/share/nginx/html/pokemon-sleep/assets/
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --chmod=755 deploy/entrypoint.sh /field-notes-entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["/field-notes-entrypoint.sh"]
