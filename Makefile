.PHONY:
	install
	clean
.DEFAULT_GOAL := install

install:
	python3.6 -m venv venv &&\
	venv/bin/pip3 install -r requirements.txt -e '.[test,dev]'

clean:
	venv/bin/daves-dev-tools clean

distribute:
	venv/bin/daves-dev-tools . --skip-existing

requirements:
	venv/bin/python3 scripts/update_setup_requirements.py
