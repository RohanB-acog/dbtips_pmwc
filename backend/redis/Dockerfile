FROM redis/redis-stack:7.2.0-v10
ARG REDIS_PASSWORD
COPY redis-stack.conf /redis-stack.conf
RUN sed -i "s/PLACEHOLDER_PASSWORD/${REDIS_PASSWORD}/g" /redis-stack.conf