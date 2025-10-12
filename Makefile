# DrChat - Makefile para gestionar diferentes configuraciones de Docker Compose
# Descripción: Comandos para levantar el proyecto con diferentes configuraciones de bases de datos

.PHONY: help up up-external-neo4j up-external-postgres up-external down logs build status evaluation

# Comando por defecto - mostrar ayuda
help:
	@echo "DrChat - Comandos disponibles:"
	@echo ""
	@echo "=== Comandos principales ==="
	@echo "  up                  - Levantar proyecto completo (con todas las bases de datos locales)"
	@echo "  up-external-neo4j   - Levantar proyecto con Neo4j externo (configurar NEO4J_URI en .env)"
	@echo "  up-external-postgres - Levantar proyecto con PostgreSQL externo (configurar POSTGRES_* en .env)"
	@echo "  up-external         - Levantar proyecto con todas las bases de datos externas"
	@echo ""
	@echo "=== Comandos de gestión ==="
	@echo "  down                - Detener proyecto completo"
	@echo "  status              - Ver estado de contenedores"
	@echo "  logs                - Ver logs de file-service y document-processor-worker"
	@echo "  build               - Construir todas las imágenes"
	@echo "  evaluation          - Evaluar el pipeline completo"
	@echo ""

# Comandos para levantar servicios
up:
	@echo "Levantando DrChat con todas las bases de datos locales..."
	docker compose up -d

up-external-neo4j:
	@echo "Levantando DrChat con Neo4j externo..."
	@echo "Asegúrate de tener configurado NEO4J_URI en tu archivo .env"
	docker compose up -d --scale neo4j=0

up-external-postgres:
	@echo "Levantando DrChat con PostgreSQL externo..."
	@echo "Asegúrate de tener configuradas las variables POSTGRES_* en tu archivo .env"
	docker compose up -d --scale postgres=0

up-external:
	@echo "Levantando DrChat con bases de datos externas..."
	@echo "Asegúrate de tener configurados NEO4J_URI y POSTGRES_* en tu archivo .env"
	docker compose up -d --scale neo4j=0 --scale postgres=0

# Comandos para detener servicios
down:
	@echo "Deteniendo DrChat completo..."
	docker compose down

# Comandos adicionales de utilidad
logs:
	@echo "Mostrando logs de file-service y document-processor-worker..."
	docker compose logs -f file-service document-processor-worker

build:
	@echo "Construyendo todas las imágenes de DrChat..."
	docker compose build

# Comandos para ver estado
status:
	@echo "Estado de los contenedores de DrChat..."
	docker compose ps

# Evaluación
evaluation:
	@echo "Evaluando el desempeño de DrChat..."
	python backend/evaluation/main.py