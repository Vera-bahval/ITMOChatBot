import asyncio
import logging
import os
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

class ITMOChatBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения! "
                           "Убедитесь, что создан .env файл с токеном.")
        
        self.vector_db = VectorDB()
        self.ai_assistant = AIAssistant()
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

    #Обработка команд бота сгенерирована с помощью ИИ
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        try:
            if not self.initialized:
                await update.message.reply_text("Инициализация бота, подождите немного...")
                await self.initialize_data()
            
            user_id = update.effective_user.id
            self.user_contexts[user_id] = {'stage': 'start', 'background': {}}
            
            welcome_message = """
🎓 Привет! Я помогу выбрать магистерскую программу ИТМО в области ИИ.

📚 Доступные программы:
• Искусственный интеллект
• Управление ИИ-продуктами/AI Product

Расскажите о своем образовании и опыте, чтобы я мог дать персональные рекомендации!
            """
            await update.message.reply_text(welcome_message)
            
        except Exception as e:
            logger.error(f"Ошибка в start_command: {e}")
            await update.message.reply_text("Произошла ошибка при запуске. Попробуйте еще раз.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        try:
            help_text = """
🤖 Доступные команды:
/start - Начать диалог
/help - Показать справку
/reset - Сбросить контекст беседы

❓ Примеры вопросов:
• "Какие предметы изучают на программе ИИ?"
• "Чем отличаются программы?"
• "Как поступить без экзаменов?"
• "Какие выборные дисциплины лучше взять?"
            """
            await update.message.reply_text(help_text)
            
        except Exception as e:
            logger.error(f"Ошибка в help_command: {e}")
    
    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сброс контекста пользователя"""
        try:
            user_id = update.effective_user.id
            self.user_contexts[user_id] = {'stage': 'start', 'background': {}}
            await update.message.reply_text("Контекст сброшен. Можете начать заново!")
            
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
                self.user_contexts[user_id] = {'stage': 'start', 'background': {}}
            relevant_docs = await self.vector_db.search(message)
            response = await self.ai_assistant.generate_response(
                message, 
                relevant_docs, 
                self.user_contexts[user_id]
            )
            await self._update_user_context(user_id, message)
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "Извините, произошла ошибка. Попробуйте переформулировать вопрос."
            )
    
    async def _update_user_context(self, user_id: int, message: str):
        """Обновление контекста пользователя"""
        try:
            message_lower = message.lower()
            
            if 'программист' in message_lower or 'разработчик' in message_lower:
                self.user_contexts[user_id]['background']['programming'] = True
            
            if 'аналитик' in message_lower or 'данные' in message_lower:
                self.user_contexts[user_id]['background']['analytics'] = True
            
            if 'менеджер' in message_lower or 'управление' in message_lower:
                self.user_contexts[user_id]['background']['management'] = True
                
        except Exception as e:
            logger.error(f"Ошибка обновления контекста: {e}")
    
    def run(self):
        """Запуск бота"""
        try:
            logger.info("Создание Telegram Application...")
            application = Application.builder().token(self.bot_token).build()
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
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