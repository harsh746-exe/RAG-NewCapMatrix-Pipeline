Run tests with:

```bash
cd /Volumes/HarshT9/RAG-NewCapMatrix-Pipeline
python -m unittest discover -s tests -p "test_*.py"
```

Notes:
- Tests are intentionally offline and do not call Azure/OpenAI.
- They validate document discovery/conversion (DOCX) and RAG metadata parsing/formatting.

