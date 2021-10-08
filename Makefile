install:
	(python3.6 -m venv venv || python3 -m venv venv) && \
	venv/bin/pip3 install\
	 -r test_requirements.txt\
	 -r dev_requirements.txt\
	 -e '.[all]'

clean:
	venv/bin/daves-dev-tools clean

distribute:
	venv/bin/daves-dev-tools . --skip-existing

requirements:
	venv/bin/python3 scripts/update_setup_requirements.py
