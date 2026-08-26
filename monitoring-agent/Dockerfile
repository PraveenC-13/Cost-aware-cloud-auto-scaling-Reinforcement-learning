# --- Build stage ---
FROM golang:1.22-alpine AS build
WORKDIR /app
COPY go.mod ./
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /agent ./cmd/agent

# --- Run stage ---
FROM alpine:3.19
# docker CLI is needed inside the container so `docker stats` works against
# the host's Docker socket (mount /var/run/docker.sock when running this image).
RUN apk add --no-cache docker-cli
COPY --from=build /agent /agent
EXPOSE 9100
ENTRYPOINT ["/agent"]
