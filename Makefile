.PHONY: test compile controller lab demo reset
test:
	python -m unittest discover -s tests -v
compile:
	python -m compileall -q controller topology tests
controller:
	bash scripts/start_controller.sh
lab:
	bash scripts/start_lab.sh
demo:
	bash scripts/run_demo.sh
reset:
	bash scripts/reset_lab.sh
