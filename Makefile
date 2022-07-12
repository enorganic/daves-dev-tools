# python 3.6 is used, for the time being, in order to ensure compatibility
install:
	{ python3.6 -m venv venv || python3 -m venv venv || \
	py -3.6 -m venv venv || py -3 -m venv venv ; } && \
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	{ python3 -m pip install --upgrade pip || echo "" ; } && \
	python3 -m pip install pre-commit && \
	python3 -m pip install -r requirements.txt -e '.[all]' && \
	pre-commit install\
	 --hook-type pre-push --hook-type pre-commit && \
	{ mypy --install-types --non-interactive || echo "" ; } && \
	echo "Installation complete"

editable:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools install-editable --upgrade-strategy eager -ed . && \
	make upgrade

clean:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools uninstall-all\
	 -e '.[all]'\
     -e pyproject.toml\
     -e tox.ini\
	 -e pre-commit\
     -e requirements.txt && \
	daves-dev-tools clean

distribute:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools distribute --skip-existing

upgrade:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	pre-commit autoupdate && \
	daves-dev-tools requirements freeze\
	 -nv '*' . pyproject.toml tox.ini \
	 > .requirements.txt && \
	python3 -m pip install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	rm .requirements.txt && \
	make requirements

requirements:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools requirements update\
	 -aen all\
	 setup.cfg pyproject.toml tox.ini && \
	daves-dev-tools requirements freeze\
	 -e pip\
	 -e wheel\
	 -nv '*'\
	 '.[all]' pyproject.toml tox.ini\
	 > requirements.txt

test:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && python3 -m tox -r
