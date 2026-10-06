.PHONY: test scenarios bench lab demo

test:
	pytest tests/

scenarios:
	pytest tests/test_a2_harness.py

bench:
	python hive_bench/benchmark.py

lab:
	python scripts/make_lab.py

demo:
	python scenarios/runner.py
