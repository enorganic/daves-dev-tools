install:
	python3 -m venv venv && \
	venv/bin/pip3 install --upgrade pip && \
	venv/bin/pip3 install\
	 -r requirements.txt\
	 -e '.[all]' && \
	venv/bin/mypy --install-types --non-interactive

clean:
	venv/bin/daves-dev-tools clean

distribute:
	venv/bin/daves-dev-tools . --skip-existing

# Note: We don't freeze importlib-metadata because the version
# will vary by python version
requirements:
	venv/bin/daves-dev-tools requirements update\
	 -v\
	 -aen all\
	 setup.cfg pyproject.toml tox.ini && \
	echo 'importlib-metadata' > requirements.txt && \
	venv/bin/daves-dev-tools requirements freeze\
	 '.[all]' pyproject.toml tox.ini\
	 -e importlib-metadata\
	 >> requirements.txt
