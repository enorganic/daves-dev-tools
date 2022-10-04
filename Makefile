# python 3.6 is used, for the time being, in order to ensure compatibility
install:
	{ rm -R venv || echo ""; } && \
	{ python3.7 -m venv venv || py -3.7 -m venv venv ; } && \
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	pip install --upgrade pip wheel && \
	pip install pre-commit && \
	pip install -r requirements.txt -e . --config-settings editable_mode=compat && \
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
	 -e .\
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
	pip install --upgrade pre-commit && \
	pre-commit autoupdate && \
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
	 -aen all\
	 setup.cfg pyproject.toml tox.ini && \
	daves-dev-tools requirements freeze\
	 -e pip\
	 -e wheel\
	 . pyproject.toml tox.ini\
	 > requirements.txt

test:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && python3 -m tox -r
