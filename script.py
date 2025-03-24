from embeddings import generate_embedding
import json

query = "Is React fast?"
vector = generate_embedding(query)  # Should return a 768-dim list
print(json.dumps(vector))  # Copy-paste this into SQL query
