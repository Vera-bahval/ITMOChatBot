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
    
    async def create_database(self, programs_data, curriculum):
        """Создание векторной базы данных"""
        documents = []
        metadata = []
        
        print("Создание документов...")
        
        for program_key, program_data in programs_data.items():
            docs, meta = self._create_documents_from_program(program_key, program_data, curriculum)
            documents.extend(docs)
            metadata.extend(meta)

        print("Получение эмбеддингов...")
        
        embeddings = []
        batch_size = 10
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            try:
                batch_embeddings = await self._get_embeddings(batch)
                embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"Ошибка получения эмбеддингов для батча {i//batch_size + 1}: {e}")
                for _ in batch:
                    embeddings.append([0] * 1024)  
        self.documents = documents
        self.embeddings = np.array(embeddings)
        self.doc_metadata = metadata

        await self._save_database()
        print("Векторная база данных создана и сохранена")
    
    def _create_documents_from_program(self, program_key, program_data, curriculum):
        """Создание документов из данных программы"""

        documents = []
        metadata = []
        
        program_title = program_data.get('title', f'Программа {program_key}')

        for courses_types, courses in curriculum.items():
            titles = [course.get('title', "") for course in courses]
            semesters = [course.get('semester', "") for course in courses]
            if courses_types == 'obligatory_courses':
                name = 'Обязательные курсы: '
            elif courses_types == 'practices':
                name = 'Практические курсы: '
            elif courses_types == 'elective_courses':
                name = 'Выборные диспицлины: '
            elif courses_types == 'soft_skills':
                name = 'Курсы по софт-скилам: '
            elif courses_types == 'universal_preparation':
                name = 'Универсальные дисциплины: '
            elif courses_types == 'gia':
                name = 'Государственная аттестация: '
            
            line = name
            for title, semester in zip(titles, semesters):
                line += f'{title} ({semester}), '
            
            documents.append(line)
            metadata.append({
                    'program': program_key,
                    'type': 'curriculum',
                    'title': program_title
                })
   
        description_data = program_data.get('description', {})
        if isinstance(description_data, dict):
            if description_data.get('lead'):
                documents.append(f"Программа {program_title}: {description_data['lead']}")
                metadata.append({
                    'program': program_key,
                    'type': 'description_lead',
                    'title': program_title
                })
            
            if description_data.get('full_description'):
                documents.append(f"Подробное описание программы {program_title}: {description_data['full_description']}")
                metadata.append({
                    'program': program_key,
                    'type': 'description_full',
                    'title': program_title
                })
        elif isinstance(description_data, str) and description_data:
            documents.append(f"Программа {program_title}: {description_data}")
            metadata.append({
                'program': program_key,
                'type': 'description',
                'title': program_title
            })

        if program_data.get('career_prospects'):
            documents.append(f"Карьерные возможности после программы {program_title}: {program_data['career_prospects']}")
            metadata.append({
                'program': program_key,
                'type': 'career',
                'title': program_title
            })

        study_info = program_data.get('study_info', {})
        if study_info:
            study_text = f"Обучение на программе {program_title}: "
            study_details = []
            
            if study_info.get('period'):
                study_details.append(f"длительность {study_info['period']}")
            if study_info.get('mode'):
                study_details.append(f"форма обучения {study_info['mode']}")
            if study_info.get('language'):
                study_details.append(f"язык обучения {study_info['language']}")
            if study_info.get('military'):
                study_details.append("есть военный учебный центр")
            
            if study_details:
                study_text += ", ".join(study_details)
                documents.append(study_text)
                metadata.append({
                    'program': program_key,
                    'type': 'study_info',
                    'title': program_title
                })
  
        cost_info = program_data.get('cost_info', {})
        admission_info = program_data.get('admission_info', {})
 
        cost_data = cost_info or admission_info.get('cost', {})
        if cost_data:
            cost_text = f"Стоимость обучения на программе {program_title}: "
            if cost_data.get('russian'):
                cost_text += f"для граждан РФ {cost_data['russian']} рублей в год"
            if cost_data.get('foreigner'):
                cost_text += f", для иностранных граждан {cost_data['foreigner']} рублей в год"
            
            documents.append(cost_text)
            metadata.append({
                'program': program_key,
                'type': 'cost',
                'title': program_title
            })
  
        if admission_info and admission_info.get('directions'):
            for direction in admission_info['directions']:
                if direction.get('title') and direction.get('code'):
                    direction_text = f"Направление подготовки {direction['code']} {direction['title']} в программе {program_title}"

                    quotas = direction.get('quotas', {})
                    if quotas:
                        quota_details = []
                        if quotas.get('budget'):
                            quota_details.append(f"{quotas['budget']} бюджетных мест")
                        if quotas.get('contract'):
                            quota_details.append(f"{quotas['contract']} контрактных мест")
                        if quotas.get('target_reception'):
                            quota_details.append(f"{quotas['target_reception']} целевых мест")
                        
                        if quota_details:
                            direction_text += f": {', '.join(quota_details)}"
                    
                    documents.append(direction_text)
                    metadata.append({
                        'program': program_key,
                        'type': 'direction',
                        'title': program_title,
                        'direction_code': direction.get('code')
                    })
        
        admission_requirements = program_data.get('admission_requirements', [])
        if admission_requirements:
            for req in admission_requirements:
                if req.get('method') and req.get('description'):
                    documents.append(f"Поступление на {program_title} через {req['method']}: {req['description']}")
                    metadata.append({
                        'program': program_key,
                        'type': 'admission_method',
                        'title': program_title,
                        'method': req['method']
                    })
        
        for faq_item in program_data.get('faq', []):
            if faq_item.get('question') and faq_item.get('answer'):
                documents.append(f"Вопрос по программе {program_title}: {faq_item['question']} Ответ: {faq_item['answer']}")
                metadata.append({
                    'program': program_key,
                    'type': 'faq',
                    'title': program_title,
                    'question': faq_item['question']
                })

        partners = program_data.get('partners', [])
        if partners:
            partners_text = f"Партнеры программы {program_title}: {', '.join(partners)}"
            documents.append(partners_text)
            metadata.append({
                'program': program_key,
                'type': 'partners',
                'title': program_title
            })
 
        achievements = program_data.get('achievements', [])
        if achievements:
            for achievement in achievements:
                if achievement.get('text'):
                    documents.append(f"Достижения студентов программы {program_title}: {achievement['text']}")
                    metadata.append({
                        'program': program_key,
                        'type': 'achievements',
                        'title': program_title
                    })

        social_links = program_data.get('social_links', {})
        if social_links:
            social_text = f"Программа {program_title} в социальных сетях: "
            social_info = []
            if social_links.get('vk'):
                social_info.append("ВКонтакте")
            if social_links.get('tg'):
                social_info.append("Telegram")
            if social_links.get('site'):
                social_info.append("официальный сайт")
            
            if social_info:
                social_text += ", ".join(social_info)
                documents.append(social_text)
                metadata.append({
                    'program': program_key,
                    'type': 'contacts',
                    'title': program_title
                })

        curriculum_info = program_data.get('curriculum_info', {})
        if curriculum_info and curriculum_info.get('link'):
            documents.append(f"Учебный план программы {program_title} доступен для скачивания")
            metadata.append({
                'program': program_key,
                'type': 'curriculum',
                'title': program_title,
                'link': curriculum_info.get('link')
            })
        
        return documents, metadata
    
    async def _get_embeddings(self, texts):
        """Получение эмбеддингов по Mistral API"""

        if not self.mistral_api_key:
            print("MISTRAL_API_KEY не найден, используем заглушки")
            return [[np.random.random(1024).tolist() for _ in texts]]
        
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
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return [item['embedding'] for item in result['data']]
        else:
            raise Exception(f"Ошибка получения эмбеддингов: {response.status_code}, {response.text}")
    
    async def search(self, query, top_k=5, min_score=0.2):
        """Векторный поиск"""

        if not self.embeddings.size:
            print("База данных пуста")
            return []
        
        try:
            query_embedding = await self._get_embeddings([query])
            query_vector = np.array(query_embedding[0]).reshape(1, -1)
        except Exception as e:
            print(f"Ошибка получения эмбеддинга для запроса: {e}")
            return []
   
        similarities = cosine_similarity(query_vector, self.embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > min_score:
                results.append({
                    'document': self.documents[idx],
                    'metadata': self.doc_metadata[idx],
                    'score': float(similarities[idx])
                })
        
        return results
    
    def get_programs_summary(self):
        """Получение сводки по программам в базе"""

        programs = {}
        for meta in self.doc_metadata:
            program_key = meta.get('program')
            if program_key not in programs:
                programs[program_key] = {
                    'title': meta.get('title'),
                    'document_types': {},
                    'total_docs': 0
                }
            
            doc_type = meta.get('type', 'unknown')
            programs[program_key]['document_types'][doc_type] = \
                programs[program_key]['document_types'].get(doc_type, 0) + 1
            programs[program_key]['total_docs'] += 1
        
        return programs
    
    async def _save_database(self):
        """Сохранение базы данных"""
        os.makedirs('data', exist_ok=True)

        with open('data/documents.json', 'w', encoding='utf-8') as f:
            json.dump({
                'documents': self.documents,
                'metadata': self.doc_metadata
            }, f, ensure_ascii=False, indent=2)

        np.save('data/embeddings.npy', self.embeddings)

        summary = self.get_programs_summary()
        with open('data/database_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"Сохранено: {len(self.documents)} документов, {len(self.embeddings)} эмбеддингов")
    
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
            print("База данных не найдена")
            return False
        except Exception as e:
            print(f"Ошибка загрузки базы данных: {e}")
            return False
