import json
import numpy as np
import requests
from sklearn.metrics.pairwise import cosine_similarity
import os

class VectorDB:
    def __init__(self):
        self.mistral_api_key = os.getenv('MISTRAL_API_KEY')
        self.documents = []
        self.embeddings = []
        self.doc_metadata = []
    
    async def create_database(self, programs_data):
        """Создание векторной базы данных"""
        documents = []
        metadata = []
        
        for program_key, program_data in programs_data.items():
            docs, meta = self._create_documents_from_program(program_key, program_data)
            documents.extend(docs)
            metadata.extend(meta)

        embeddings = []
        batch_size = 10
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            batch_embeddings = await self._get_embeddings(batch)
            embeddings.extend(batch_embeddings)
        
        self.documents = documents
        self.embeddings = np.array(embeddings)
        self.doc_metadata = metadata

        await self._save_database()
    
    def _create_documents_from_program(self, program_key, program_data):
        """Создание документов из данных программы"""
        documents = []
        metadata = []
        if program_data.get('description'):
            documents.append(f"Программа {program_data['title']}: {program_data['description']}")
            metadata.append({
                'program': program_key,
                'type': 'description',
                'title': program_data['title']
            })
        if program_data.get('career_prospects'):
            documents.append(f"Карьерные перспективы программы {program_data['title']}: {program_data['career_prospects']}")
            metadata.append({
                'program': program_key,
                'type': 'career',
                'title': program_data['title']
            })
        for faq_item in program_data.get('faq', []):
            if faq_item.get('question') and faq_item.get('answer'):
                documents.append(f"Вопрос: {faq_item['question']} Ответ: {faq_item['answer']}")
                metadata.append({
                    'program': program_key,
                    'type': 'faq',
                    'title': program_data['title']
                })
        for req in program_data.get('admission_requirements', []):
            if req.get('description'):
                documents.append(f"Поступление через {req['method']}: {req['description']}")
                metadata.append({
                    'program': program_key,
                    'type': 'admission',
                    'title': program_data['title']
                })

        if program_data.get('partners'):
            partners_text = f"Партнеры программы {program_data['title']}: {', '.join(program_data['partners'])}"
            documents.append(partners_text)
            metadata.append({
                'program': program_key,
                'type': 'partners',
                'title': program_data['title']
            })
        
        return documents, metadata
    
    async def _get_embeddings(self, texts):
        """Получение эмбеддингов от Mistral API"""
        headers = {
            'Authorization': f'Bearer {self.mistral_api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'mistral-embed',
            'input': texts
        }
        
        response = requests.post(
            'https://api.mistral.ai/v1/embeddings',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            return [item['embedding'] for item in result['data']]
        else:
            raise Exception(f"Ошибка получения эмбеддингов: {response.status_code}")
    
    async def search(self, query, top_k=5):
        """Векторный поиск релевантных документов"""
        if not self.embeddings.size:
            return []
        query_embedding = await self._get_embeddings([query])
        query_vector = np.array(query_embedding[0]).reshape(1, -1)
   
        similarities = cosine_similarity(query_vector, self.embeddings)[0]
 
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.3:
                results.append({
                    'document': self.documents[idx],
                    'metadata': self.doc_metadata[idx],
                    'score': float(similarities[idx])
                })
        
        return results
    
    async def _save_database(self):
        """Сохранение базы данных"""
        os.makedirs('data', exist_ok=True)
        with open('data/documents.json', 'w', encoding='utf-8') as f:
            json.dump({
                'documents': self.documents,
                'metadata': self.doc_metadata
            }, f, ensure_ascii=False, indent=2)
        np.save('data/embeddings.npy', self.embeddings)
    
    async def load_database(self):
        """Загрузка базы данных"""
        try:
            with open('data/documents.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.documents = data['documents']
                self.doc_metadata = data['metadata']
            
            self.embeddings = np.load('data/embeddings.npy')
            return True
        except FileNotFoundError:
            return False