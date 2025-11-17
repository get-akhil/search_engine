pip install -r requirements.txt
gcc -o search_engine main.c bst_index.c query_processor.c tokenizer_utils.c
./search_engine
python app.py
