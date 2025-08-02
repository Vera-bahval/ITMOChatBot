import requests
import json
import os

class AIAssistant:
    def __init__(self):
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "deepseek/deepseek-chat-v3-0324:free"
    
    async def generate_response(self, user_message, relevant_docs, user_context):
        """Генерация ответа с использованием DeepSeek"""
        context_text = self._format_context(relevant_docs)
        background_info = self._format_user_background(user_context.get('background', {}))
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(user_message, context_text, background_info)
        response = await self._call_openrouter_api(system_prompt, user_prompt)
        
        return response
    
    def _format_context(self, relevant_docs):
        """Форматирование контекста"""
        if not relevant_docs:
            return "Контекст не найден."
        
        context_parts = []
        for doc in relevant_docs:
            context_parts.append(f"[{doc['metadata']['type']}] {doc['document']}")
        
        return "\n\n".join(context_parts)
    
    #Обработка информации о пользователе сгеннерирована ИИ
    def _format_user_background(self, background):
        """Форматирование информации о пользователе"""
        background_parts = []
        
        if background.get('programming'):
            background_parts.append("Пользователь имеет опыт программирования")
        if background.get('analytics'):
            background_parts.append("Пользователь имеет опыт работы с данными/аналитикой")
        if background.get('management'):
            background_parts.append("Пользователь имеет опыт управления/менеджмента")
        
        return " | ".join(background_parts) if background_parts else "Информация о бэкграунде пользователя отсутствует"
    
    #Системный промпт сгеннерирован ИИ
    def _create_system_prompt(self):
        """Создание системного промпта"""
        return """Ты - помощник абитуриента магистерских программ ИТМО в области искусственного интеллекта. 

Твоя задача:
1. Отвечать ТОЛЬКО на вопросы, связанные с магистерскими программами ИТМО:
   - "Искусственный интеллект" 
   - "Управление ИИ-продуктами/AI Product"

2. Помогать выбрать подходящую программу на основе бэкграунда пользователя

3. Давать рекомендации по выборным дисциплинам

4. Предоставлять информацию о поступлении, обучении, карьерных перспективах

ВАЖНО:
- Если вопрос НЕ связан с этими программами, вежливо откажись и предложи задать вопрос по теме
- Используй только информацию из предоставленного контекста
- Давай персональные рекомендации на основе бэкграунда пользователя
- Отвечай на русском языке
- Форматируй ответ с использованием Markdown для лучшей читаемости"""
    
    def _create_user_prompt(self, user_message, context_text, background_info):
        """Создание пользовательского промпта"""
        return f"""
Вопрос пользователя: {user_message}

Информация о пользователе: {background_info}

Релевантная информация из базы данных:
{context_text}

Пожалуйста, дай полный и полезный ответ на основе предоставленной информации. Если нужно дать рекомендации по выбору программы или дисциплин, учитывай бэкграунд пользователя.
"""
    
    async def _call_openrouter_api(self, system_prompt, user_prompt):
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Ошибка API: {response.status_code} - {response.text}")