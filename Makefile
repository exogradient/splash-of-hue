.PHONY: help dev docs pit check-docs

help: ## Show available commands
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

dev: ## Start dev server with hot reload
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

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
