# python 3.6 is used, for the time being, in order to ensure compatibility
install:
	(python3.6 -m venv venv || python3 -m venv venv || \
	py -3.6 -m venv venv || py -3 -m venv venv) && \
	(. venv/bin/activate || venv/Scripts/activate.bat) && \
	pip install --upgrade pip pre-commit && \
	pip install -r requirements.txt -e '.[all]' && \
	pre-commit install\
	 --hook-type pre-push --hook-type pre-commit && \
	mypy --install-types --non-interactive ;

clean:
	(. venv/bin/activate || venv/Scripts/activate.bat) && \
	daves-dev-tools uninstall-all\
	 -e '.[all]'\
     -e pyproject.toml\
     -e tox.ini\
     -e requirements.txt && \
	daves-dev-tools clean

distribute:
	(. venv/bin/activate || venv/Scripts/activate.bat) && \
	daves-dev-tools distribute --skip-existing

upgrade:
	(. venv/bin/activate || venv/Scripts/activate.bat) && \
	pre-commit autoupdate && \
	daves-dev-tools requirements freeze\
	 -nv '*' . pyproject.toml tox.ini \
	 > .unversioned_requirements.txt && \
	pip3 install --upgrade --upgrade-strategy eager\
	 -r .unversioned_requirements.txt -e '.[all]' && \
	rm .unversioned_requirements.txt && \
	make requirements

requirements:
	(. venv/bin/activate || venv/Scripts/activate.bat) && \
	daves-dev-tools requirements update\
	 -v\
	 -aen all\
	 setup.cfg pyproject.toml tox.ini && \
	daves-dev-tools requirements freeze\
	 -nv setuptools -nv filelock -nv platformdirs\
	 '.[all]' pyproject.toml tox.ini\
	 > requirements.txt

test:
	(. venv/bin/activate || venv/Scripts/activate.bat) && tox -r
