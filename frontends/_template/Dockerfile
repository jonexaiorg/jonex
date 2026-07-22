FROM nginx:1.20.1-alpine

WORKDIR /usr/share/nginx/html

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

COPY dist ./{{STANDALONE_BASE_DIR}}/
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -sf http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
