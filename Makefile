.PHONY: build-image
build-image:
	docker compose build

.PHONY: up
up: build-image
	docker compose up -d

.PHONY: down
down:
	docker compose down
