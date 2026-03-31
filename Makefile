.PHONY: help dev docs pit check-docs check-scoring check-calibration-runner calibrate calibrate-release extract-population promote-fixtures

help: ## Show available commands
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

dev: ## Start dev server with hot reload
	uv run uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

docs: ## List managed docs
	@echo "Docs:"
	@for f in docs/*.md; do \
		layer=$$(basename "$$f" | sed 's/-.*//' ); \
		title=$$(awk '/^title:/{print substr($$0, index($$0,":")+2)}' "$$f"); \
		stab=$$(awk '/^stability:/{print substr($$0, index($$0,":")+2)}' "$$f"); \
		desc=$$(awk '/^description:/{print substr($$0, index($$0,":")+2)}' "$$f"); \
		printf "  %-8s %-30s [%-9s] %s\n" "$$layer" "$$f ($$title)" "$$stab" "$$desc"; \
	done

pit: ## List point-in-time research docs
	@if [ -d docs/pit ]; then \
		echo "PIT docs:"; \
		for f in docs/pit/*.md; do \
			[ -f "$$f" ] || continue; \
			date=$$(awk '/^date:/{print substr($$0, index($$0,":")+2)}' "$$f"); \
			title=$$(awk '/^title:/{print substr($$0, index($$0,":")+2)}' "$$f"); \
			printf "  %-12s %s\n" "$$date" "$$title"; \
		done; \
	else echo "No PIT docs yet"; fi

check-docs: ## Validate frontmatter schema (title, description, stability, responsibility)
	@fail=0; for f in docs/*.md; do \
		for field in title description stability responsibility; do \
			if ! awk "/^$$field:/{found=1} END{exit !found}" "$$f"; then \
				echo "FAIL: $$f missing '$$field'"; fail=1; \
			fi; \
		done; \
	done; \
	if [ $$fail -eq 1 ]; then exit 1; fi; \
	echo "All docs OK"

check-scoring: ## Verify calibration scorer matches the app scorer
	uv run python tools/check_scoring_parity.py

check-calibration-runner: ## Verify Python calibration runner matches the JS scorer
	uv run python tools/check_calibration_runner_parity.py

calibrate: ## Run calibration search against exported JSON (usage: make calibrate FILE=path/to/export.json)
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make calibrate FILE=path/to/export.json"; \
		exit 1; \
	fi
	uv run python tools/run_calibration.py "$(FILE)"

calibrate-release: ## Run the production calibration gate (usage: make calibrate-release FILE=path/to/export.json)
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make calibrate-release FILE=path/to/export.json"; \
		exit 1; \
	fi
	tmp_fixtures="/private/tmp/calibration-release-fixtures.json"; \
	uv run python tools/promote_calibration_fixtures.py "$(FILE)" --score-window 0.5 --directional-shift 0.25 --append-to "tools/calibration-regression.json" --output "$$tmp_fixtures"; \
	uv run python tools/run_calibration.py "$(FILE)" --regression-fixtures "$$tmp_fixtures" --challenge-worsen-ceiling 0.05

extract-population: ## Extract a reusable population profile JSON (usage: make extract-population OUTPUT=path.json [DB=data/games.db] [PARAMS_FROM=export.json])
	@if [ -z "$(OUTPUT)" ]; then \
		echo "Usage: make extract-population OUTPUT=path.json [DB=data/games.db] [PARAMS_FROM=export.json]"; \
		exit 1; \
	fi
	uv run python tools/extract_population_profile.py --db "$(or $(DB),data/games.db)" $(if $(PARAMS_FROM),--params-from "$(PARAMS_FROM)",) --output "$(OUTPUT)"

promote-fixtures: ## Promote reviewed calibration rows into regression fixtures (usage: make promote-fixtures FILE=export.json OUTPUT=fixtures.json)
	@if [ -z "$(FILE)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "Usage: make promote-fixtures FILE=export.json OUTPUT=fixtures.json [APPEND_TO=tools/calibration-regression.json]"; \
		exit 1; \
	fi
	uv run python tools/promote_calibration_fixtures.py "$(FILE)" $(if $(APPEND_TO),--append-to "$(APPEND_TO)",) --output "$(OUTPUT)"
