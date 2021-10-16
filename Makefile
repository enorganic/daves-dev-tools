install:
	python3 -m venv venv && \
	venv/bin/pip3 install --upgrade pip && \
	venv/bin/pip3 install\
	 -r test_requirements.txt\
	 -e '.[all]' && \
	venv/bin/mypy --install-types --non-interactive

clean:
	venv/bin/daves-dev-tools clean

distribute:
	venv/bin/daves-dev-tools . --skip-existing

requirements:
	venv/bin/daves-dev-tools requirements update\
	 -v\
	 -aen all\
	 setup.cfg test_requirements.txt pyproject.toml tox.ini && \
	venv/bin/daves-dev-tools requirements freeze\
	 -r test_requirements.txt\
	 '.[all]'\
	 > requirements.txt
