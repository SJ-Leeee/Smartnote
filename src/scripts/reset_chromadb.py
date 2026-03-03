import shutil
from pathlib import Path
from smartnote.rag.embedding_store import EmbeddingStore

store = EmbeddingStore()
count = store.collection.count()

# 컬렉션 삭제
store.client.delete_collection("smartnote")

# 고아 폴더 정리
db_path = Path(__file__).parent.parent.parent / ".chroma_db"
for folder in db_path.iterdir():
    if folder.is_dir():  # UUID 폴더만
        shutil.rmtree(folder)
