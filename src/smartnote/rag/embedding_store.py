from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer


class EmbeddingStore:
    def __init__(self):
        # 프로젝트 루트 기준 .chroma_db/ 에 저장
        db_path = Path(__file__).parent.parent.parent.parent / ".chroma_db"
        self.client = chromadb.PersistentClient(path=str(db_path))

        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

        # 컬렉션: RDB의 테이블 개념
        self.collection = self.client.get_or_create_collection(
            name="smartnote",
            metadata={"hnsw:space": "cosine"},  # 코사인 유사도 사용 명시
        )

        # ChromaDB 클라이언트 초기화 (로컬 파일 저장 경로 설정)
        # sentence-transformers 모델 로드
        # ChromaDB collection 가져오기 or 생성

    def add_note(self, note_id: str, content: str, metadata: dict) -> None:
        embedding = self.model.encode(content).tolist()

        self.collection.upsert(  # add 대신 upsert: 같은 id면 덮어씀
            ids=[note_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
        )

        # content를 임베딩 → ChromaDB에 저장
        # metadata: title, category, subcategory, tags, file_path

    def search_related(
        self, content: str, top_k: int = 3, cur_title: str = ""
    ) -> list[dict]:
        embedding = self.model.encode(content).tolist()

        # 만약 3개보다 적을경우
        all_note_cnt = self.collection.count()
        if all_note_cnt < 3:
            top_k = all_note_cnt

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
        )
        # print(results)
        # results 구조 정리해서 반환
        output = []
        for i, metadata in enumerate(results["metadatas"][0]):
            # TODO: 유사도가 너무 낮을시는 제외. 노트별 유사도 확인해보고 수치설정
            if results["distances"][0][i] < 0.5:
                continue

            # 자기 자신과 이름이 같으면 pass
            if metadata.get("title") == cur_title:
                continue

            output.append(
                {
                    "title": metadata.get("title", ""),
                    # cosine distance → similarity
                    "similarity": 1 - results["distances"][0][i],
                    "file_path": metadata.get("file_path", ""),
                }
            )
        return output


if __name__ == "__main__":
    store = EmbeddingStore()
    store.add_note("test-1", "돌고래는 바다에 사는 포유류입니다", {"title": "돌고래"})
    results = store.search_related("바다에 사는 동물")
    print(results)

    print("ok")
