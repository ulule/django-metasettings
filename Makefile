pep8:
	flake8 metasettings --ignore=E501,E127,E128,E124

test:
	coverage run --branch --source=metasettings manage.py test metasettings
	coverage report --omit=metasettings/test*

release:
	python setup.py sdist register upload -s
