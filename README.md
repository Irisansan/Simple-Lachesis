# Simple-Lachesis

A simplified implementation of Lachesis in Go and in Python in order to simulate/mechanize runs of the protocol and examine its properties of Liveness, Safety, etc.

## PyLachesis:

- this is an implementation of the Lachesis consensus protocol in Python
- the relevant class and lachesis consensus methods are implemented in `/PyLachesis/lachesis.py`

## GoLachesis:

- this is an implementation of the Lachesis consensus protocol in Go
- the relevant code is in `/GoLachesis`
- run `main.go`
- reading files and setting the validators is currently done through `main.go`

## Inputs & Test Case Generation:

- the Python script to generate test cases as pdfs and as text inputs for the Python and Go implementations are in `/inputs`
- some sample DAGs are available in the directory
- the script allows to generate custom DAGs

### Why Both?

- Go is (far) more performant, but Python is easier to add changes to ad-hoc and to test with 
- the idea is to leverage the benefits of both languages and to arrive at a performant, stable port
- Python has more libraries for graphing and data science
