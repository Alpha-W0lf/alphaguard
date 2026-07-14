.PHONY: smoke preflight sync test bundle

sync:
	uv sync --all-extras

preflight:
	ALPHAGUARD_MODE=replay uv run alphaguard preflight

# Kafka must remain stopped for this target.
smoke:
	ALPHAGUARD_MODE=replay ALPHAGUARD_RAG_MODE=fixture \
		KMP_DUPLICATE_LIB_OK=TRUE OMP_NUM_THREADS=1 \
		uv run alphaguard smoke --event-id evt-aapl-001

test:
	uv run pytest -q

bundle:
	uv run python scripts/build_fixture_bundle.py
