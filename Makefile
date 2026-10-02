.PHONY: help install list test converge verify destroy login \
        test-debian-12 test-ubuntu-2204 test-ubuntu-2404 test-rockylinux-9 test-amazonlinux-2023 \
        functional-test functional-test-debian-12

KITCHEN := bundle exec kitchen
SUITE   := default

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Setup:"
	@echo "  install              Install gem dependencies"
	@echo ""
	@echo "Kitchen:"
	@echo "  list                 List all instances"
	@echo "  test                 Run full test cycle for all instances"
	@echo "  converge             Converge all instances"
	@echo "  verify               Verify all instances"
	@echo "  destroy              Destroy all instances"
	@echo ""
	@echo "Per platform (SUITE=default):"
	@echo "  test-debian-12"
	@echo "  test-ubuntu-2204"
	@echo "  test-ubuntu-2404"
	@echo "  test-rockylinux-9"
	@echo "  test-amazonlinux-2023"
	@echo ""
	@echo "  login PLATFORM=debian-12   Open shell in running instance"
	@echo ""
	@echo "Functional tests (Kitchen):"
	@echo "  functional-test                Run functional tests on all platforms"
	@echo "  functional-test-debian-12      Run functional tests on Debian 12"

install:
	bundle config set --local path vendor/bundle
	bundle install

list:
	$(KITCHEN) list

test:
	$(KITCHEN) test

converge:
	$(KITCHEN) converge

verify:
	$(KITCHEN) verify

destroy:
	$(KITCHEN) destroy

login:
	$(KITCHEN) login $(SUITE)-$(PLATFORM)

test-debian-12:
	$(KITCHEN) test $(SUITE)-debian-12

test-ubuntu-2204:
	$(KITCHEN) test $(SUITE)-ubuntu-2204

test-ubuntu-2404:
	$(KITCHEN) test $(SUITE)-ubuntu-2404

test-rockylinux-9:
	$(KITCHEN) test $(SUITE)-rockylinux-9

test-amazonlinux-2023:
	$(KITCHEN) test $(SUITE)-amazonlinux-2023

# ── Functional tests (Kitchen) ──────────────────────────────
functional-test:
	$(KITCHEN) test functional

functional-test-debian-12:
	$(KITCHEN) test functional-debian-12