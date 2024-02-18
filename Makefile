SHELL := bash
PYTHON_VERSION := 3.8

install:
	{ rm -R venv || echo "" ; } && \
	{ python$(PYTHON_VERSION) -m venv venv || py -$(PYTHON_VERSION) -m venv venv ; } && \
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	pip install --upgrade pip wheel && \
	pip install -c requirements.txt flake8 mypy black tox pytest -e . && \
	{ mypy --install-types --non-interactive || echo "" ; } && \
	echo "Installation complete"

ci-install:
	{ python3 -m venv venv || py -3 -m venv venv ; } && \
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	python3 -m pip install --upgrade pip wheel && \
	pip install -c requirements.txt tox -e . && \
	echo "Installation complete"

reinstall:
	{ rm -R venv || echo "" ; } && \
	{ python$(PYTHON_VERSION) -m venv venv || py -$(PYTHON_VERSION) -m venv venv ; } && \
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	pip install --upgrade pip wheel && \
	pip install flake8 mypy black tox pytest isort -e . && \
	{ mypy --install-types --non-interactive || echo "" ; } && \
	make requirements && \
	echo "Installation complete"

editable:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools install-editable --upgrade-strategy eager -ed . && \
	make upgrade

clean:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools uninstall-all\
	 -e .\
     -e pyproject.toml\
     -e tox.ini\
     -e requirements.txt && \
	daves-dev-tools clean

distribute:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools distribute --skip-existing

upgrade:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools requirements freeze\
	 -nv '*' . pyproject.toml tox.ini \
	 > .requirements.txt && \
	pip install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	rm .requirements.txt && \
	make requirements

requirements:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools requirements update\
	 -i more-itertools -aen all\
	 setup.cfg pyproject.toml tox.ini && \
	daves-dev-tools requirements freeze\
	 -e pip\
	 -e wheel\
	 . pyproject.toml tox.ini\
	 > requirements.txt

# Run all tests
test:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	if [[ "$$(python -V)" = "Python $(PYTHON_VERSION)."* ]] ;\
	then tox -r -p -o ;\
	else tox -r -e pytest ;\
	fi

format:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	isort . && black . && flake8 && mypy
