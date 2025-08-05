docker compose down -v && docker volume prune -f && docker compose up -d --wait && docker logs tg_test_postgres
