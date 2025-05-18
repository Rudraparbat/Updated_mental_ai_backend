from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec 
import os


class BrainForAI:
    def __init__(self , namespace):
        self.pc = Pinecone(api_key=os.getenv("PINE_API_KEY"))
        self.index_name = "mindforai"
        self.index = self.pc.Index(self.index_name)
        self.namespace = namespace
    
    def EmbeddingForData(self , query) :
        inputs = [f"Q: {d['question']} A: {d['answer']}" for d in query]
        embeddings = self.pc.inference.embed(
        model="multilingual-e5-large",
        inputs=inputs,
        parameters={
            "input_type": "passage", 
            "truncate": "END"
        }
        )
        return embeddings

    def UpsertData(self , data) :
        embed_data = self.EmbeddingForData(data)
        vectors = [
        {
            "id": item["id"],
            "values": embedding['values'],
            "metadata": {"q": item["question"] , "a" : item['answer']}
        }
        for item, embedding in zip(data, embed_data)
        ]
        self.index.upsert(vectors=vectors, namespace=self.namespace)

    def InsertData(self , data) :
        self.UpsertData(data)
    

    def EmbeddingForQuery(self , query) :
        query_embedding = self.pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[query],
        parameters={
            "input_type": "query"
        }
        )
        return query_embedding[0].values


    def Search(self , query) :
        main_q = self.EmbeddingForQuery(query)
        results = self.index.query(
        namespace=self.namespace,
        vector=main_q,
        top_k=1,
        include_values=False,
        include_metadata=True
        )

        trimmed = [result['metadata'] for result in results.matches]
        if trimmed == [] :
            return None
        question = trimmed[0]['q']
        answer = trimmed[0]['a']

        return [question , answer]

    def Delete(self) :
        self.index.delete(delete_all=True , namespace=self.namespace)
        print("sorry you r disconnected we have no data on you")


