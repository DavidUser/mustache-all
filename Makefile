all: ./generate_code.py clean
	python3 $<

clean:
	-rm -r result/*
