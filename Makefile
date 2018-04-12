all: ./generate_code.py test document result | clean
	python3 $^

clean:
	-rm -r result/*
