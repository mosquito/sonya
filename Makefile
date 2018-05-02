build: sdist mac_wheel linux_wheel

sdist:
	python3 setup.py sdist

mac_wheel:
	export WHEEL_TOOL=/Library/Frameworks/Python.framework/Versions/3.6/bin/wheel
	python3.4 setup.py bdist_wheel
	python3.5 setup.py bdist_wheel
	python3.6 setup.py bdist_wheel

linux_wheel:
	docker run -it --rm \
		-v `pwd`:/app/src:ro \
		-v `pwd`/dist:/app/dst \
		--entrypoint /bin/bash \
		quay.io/pypa/manylinux1_x86_64 \
		/app/src/scripts/make-wheels.sh

test-env-py27:
	docker build -t sonya:test-py27 -f Dockerfile.py27 .

test-env-py36:
	docker build -t sonya:test-py36 -f Dockerfile.py36 .

test-py36: test-env-py36
	docker run --rm -t -w /mnt -v $(shell pwd)/tests:/mnt/tests:ro \
	    sonya:test-py36 pytest tests

test-py27: test-env-py27
	docker run --rm -t -w /mnt -v $(shell pwd)/tests:/mnt/tests:ro \
	    sonya:test-py27 pytest tests

test: test-py36 test-py27
