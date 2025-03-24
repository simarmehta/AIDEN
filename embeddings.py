
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-base-en-v1.5")

def generate_embedding(text: str, is_query: bool = False):
    """
    Generate vector embedding.
    """
    if is_query:
        text = "Represent this question for retrieval: " + text
    else:
        text = "Represent this passage for retrieval: " + text

    return model.encode(text).tolist()
