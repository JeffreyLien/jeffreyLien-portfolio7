.PHONY: data validate test app all

data:
	python src/generate_synthetic_data.py

validate:
	python src/validate_transactions.py
	python src/build_issue_queue.py

test:
	pytest -q

app:
	streamlit run app/dashboard.py

all: data validate test
