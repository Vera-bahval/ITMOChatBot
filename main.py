import asyncio
import logging
import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from data_parser import DataParser
from vector_db import VectorDB
from ai_assistant import AIAssistant

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

#Анализатор контекста сгенерирован ИИ
class ContextAnalyzer:
    """Анализатор контекста пользователя"""
    
    def __init__(self):
        self.background_patterns = {
            'programming': [
                r'\b(программист|разработчик|developer|python|java|javascript|c\+\+|c#)\b',
                r'\b(frontend|backend|fullstack|веб-разработка|мобильная разработка)\b',
                r'\b(git|github|алгоритм|структуры данных|код|программирование)\b',
                r'\b(react|vue|angular|django|flask|spring|node\.js)\b'
            ],
            'analytics': [
                r'\b(аналитик|analyst|данные|data|статистика|excel|sql|tableau)\b',
                r'\b(бизнес-аналитик|data scientist|исследования|метрики|bi)\b',
                r'\b(pandas|numpy|r|статистический анализ|отчеты|dashboard)\b',
                r'\b(power bi|qlik|looker|matplotlib|seaborn)\b'
            ],
            'management': [
                r'\b(менеджер|manager|руководитель|управление|проект|команда)\b',
                r'\b(product manager|project manager|scrum|agile|планирование)\b',
                r'\b(лидерство|координация|бюджет|стратегия|roadmap)\b',
                r'\b(jira|confluence|trello|asana|управляю|руковожу)\b'
            ],
            'ml_experience': [
                r'\b(машинное обучение|ml|deep learning|нейронные сети|ai)\b',
                r'\b(tensorflow|pytorch|scikit-learn|keras|pandas)\b',
                r'\b(kaggle|модели|алгоритмы ml|feature engineering)\b',
                r'\b(computer vision|nlp|обработка изображений|текста)\b'
            ],
            'education': [
                r'\b(студент|учусь|университет|институт|бакалавр|специалист)\b',
                r'\b(диплом|курсовая|экзамен|сессия|преподаватель|вуз)\b',
                r'\b(итмо|спбгу|мгу|вшэ|политех|мфти|мифи)\b'
            ]
        }
        
        self.experience_patterns = {
            'junior': r'\b(новичок|junior|начинающий|без опыта|первый раз|изучаю)\b',
            'middle': r'\b(middle|опытный|несколько лет|работаю|год|лет опыта)\b',
            'senior': r'\b(senior|эксперт|много лет|руководил|ведущий|главный)\b'
        }
        
        self.interest_patterns = {
            'computer_vision': r'\b(компьютерное зрение|cv|изображения|картинки|opencv|yolo)\b',
            'nlp': r'\b(nlp|обработка текста|чат-бот|языковые модели|gpt|bert)\b',
            'product_development': r'\b(продукт|product|пользователи|метрики|growth|mvp)\b',
            'research': r'\b(исследования|наука|научная|статьи|публикации|конференции)\b'
        }
    
    def analyze_message(self, message: str) -> dict:
        """Анализ сообщения для извлечения информации о пользователе"""
        message_lower = message.lower()
        
        analysis = {
            'background': {},
            'experience_level': None,
            'interests': [],
            'education_mentioned': False
        }

        for category, patterns in self.background_patterns.items():
            detected = any(re.search(pattern, message_lower, re.IGNORECASE) for pattern in patterns)
            if category == 'education':
                analysis['education_mentioned'] = detected
            else:
                analysis['background'][category] = detected

        for level, pattern in self.experience_patterns.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                analysis['experience_level'] = level
                break

        for interest, pattern in self.interest_patterns.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                analysis['interests'].append(interest)
        
        return analysis

class ITMOChatBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения! "
                           "Убедитесь, что создан .env файл с токеном.")
        
        self.vector_db = VectorDB()
        self.ai_assistant = AIAssistant()
        self.context_analyzer = ContextAnalyzer()
        self.user_contexts = {} 
        self.initialized = False
        
    async def initialize_data(self):
        """Инициализация"""
        if self.initialized:
            return
            
        logger.info("Инициализация данных бота...")
        
        try:
            parser = DataParser()
            programs_data = await parser.parse_programs()
            await self.vector_db.create_database(programs_data)
            
            self.initialized = True
            logger.info("Данные готовы!")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации данных: {e}")
            raise

    #Логика обработчика команд сгенерирована ИИ
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not self.initialized:
                await update.message.reply_text("Инициализация бота, подождите немного...")
                await self.initialize_data()
            
            user_id = update.effective_user.id
            self.user_contexts[user_id] = {
                'stage': 'start', 
                'background': {},
                'experience_level': None,
                'interests': [],
                'message_history': []
            }
            
            welcome_message = """
🎓 *Добро пожаловать!*

Я помогу выбрать магистерскую программу ИТМО в области ИИ и составить план обучения.

📚 *Доступные программы:*
• Искусственный интеллект
• Управление ИИ-продуктами/AI Product

💬 *Расскажите о себе для персональных рекомендаций:*
• Какой у вас опыт работы?
• Какие технологии знаете?
• Какие цели преследуете?

Например: "Я программист на Python, работаю 3 года, интересует ML"
            """
            await update.message.reply_text(welcome_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка в start_command: {e}")
            await update.message.reply_text("Произошла ошибка при запуске. Попробуйте еще раз.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        try:
            help_text = """
🤖 *Команды:*
/start - Начать диалог
/help - Справка
/reset - Сбросить контекст
/profile - Показать ваш профиль

❓ *Примеры вопросов:*
• "Чем отличаются программы?"
• "Как поступить без экзаменов?"
• "Какую программу выбрать программисту?"
• "Какие выборные дисциплины взять?"
• "Сколько стоит обучение?"

💡 *Совет:* Расскажите о своем опыте для лучших рекомендаций!
            """
            await update.message.reply_text(help_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка в help_command: {e}")
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать профиль пользователя"""
        try:
            user_id = update.effective_user.id
            
            if user_id not in self.user_contexts:
                await update.message.reply_text("Сначала напишите /start")
                return
            
            user_context = self.user_contexts[user_id]
            background = user_context.get('background', {})
            
            if not any(background.values()):
                profile_text = "📋 *Ваш профиль пуст*\n\nРасскажите о своем опыте для персональных рекомендаций!"
            else:
                profile_parts = ["📋 *Ваш профиль:*\n"]
                
                if background.get('programming'):
                    profile_parts.append("💻 Опыт программирования")
                if background.get('analytics'):
                    profile_parts.append("📊 Опыт аналитики/работы с данными")
                if background.get('management'):
                    profile_parts.append("👥 Опыт управления/менеджмента")
                if background.get('ml_experience'):
                    profile_parts.append("🤖 Опыт машинного обучения")
                
                if user_context.get('experience_level'):
                    level_emoji = {'junior': '🌱', 'middle': '📈', 'senior': '🚀'}
                    level = user_context['experience_level']
                    profile_parts.append(f"{level_emoji.get(level, '📊')} Уровень: {level}")
                
                if user_context.get('interests'):
                    interests = ', '.join(user_context['interests'])
                    profile_parts.append(f"🎯 Интересы: {interests}")
                
                profile_text = "\n".join(profile_parts)
            
            await update.message.reply_text(profile_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка в profile_command: {e}")
    
    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сброс контекста пользователя"""
        try:
            user_id = update.effective_user.id
            self.user_contexts[user_id] = {
                'stage': 'start', 
                'background': {},
                'experience_level': None,
                'interests': [],
                'message_history': []
            }
            await update.message.reply_text("🔄 Контекст сброшен. Можете начать заново!")
            
        except Exception as e:
            logger.error(f"Ошибка в reset_command: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        try:
            if not self.initialized:
                await update.message.reply_text("Инициализация бота, подождите немного...")
                await self.initialize_data()
            
            user_id = update.effective_user.id
            message = update.message.text

            if user_id not in self.user_contexts:
                self.user_contexts[user_id] = {
                    'stage': 'start', 
                    'background': {},
                    'experience_level': None,
                    'interests': [],
                    'message_history': []
                }
            
            self.user_contexts[user_id]['message_history'].append(message)
 
            analysis = self.context_analyzer.analyze_message(message)
            self._update_user_context(user_id, analysis)
   
            relevant_docs = await self.vector_db.search(message)

            response = await self.ai_assistant.generate_response(
                message, 
                relevant_docs, 
                self.user_contexts[user_id]
            )
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "Извините, произошла ошибка. Попробуйте переформулировать вопрос."
            )
    
    def _update_user_context(self, user_id: int, analysis: dict):
        """Обновление контекста пользователя на основе анализа"""
        try:
            user_context = self.user_contexts[user_id]

            for category, detected in analysis['background'].items():
                if detected:
                    user_context['background'][category] = True
            if analysis.get('experience_level'):
                user_context['experience_level'] = analysis['experience_level']
            if analysis.get('interests'):
                current_interests = set(user_context.get('interests', []))
                new_interests = set(analysis['interests'])
                user_context['interests'] = list(current_interests | new_interests)
            if any(analysis['background'].values()) or analysis.get('experience_level') or analysis.get('interests'):
                logger.info(f"Обновлен контекст пользователя {user_id}: {user_context}")
                
        except Exception as e:
            logger.error(f"Ошибка обновления контекста: {e}")
    
    def run(self):
        """Запуск бота"""
        try:
            logger.info("Создание Telegram Application...")
            application = Application.builder().token(self.bot_token).build()
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("profile", self.profile_command))
            application.add_handler(CommandHandler("reset", self.reset_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            logger.info("Запуск бота...")
            application.run_polling(drop_pending_updates=True)
            
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise

def main():
    try:
        bot = ITMOChatBot()
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Программа завершена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
