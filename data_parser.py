import requests
from bs4 import BeautifulSoup
import json
import os

class DataParser:
    def __init__(self):
        self.programs = {
            'ai': 'https://abit.itmo.ru/program/master/ai',
            'ai_product': 'https://abit.itmo.ru/program/master/ai_product'
        }
    
    async def parse_programs(self):
        """Парсинг данных с сайтов программ"""
        programs_data = {}
        
        for program_key, url in self.programs.items():
            try:
                data = await self._parse_program_page(url, program_key)
                programs_data[program_key] = data
            except Exception as e:
                print(f"Ошибка парсинга {program_key}: {e}")

        os.makedirs('data', exist_ok=True)
        with open('data/programs_data.json', 'w', encoding='utf-8') as f:
            json.dump(programs_data, f, ensure_ascii=False, indent=2)
        
        return programs_data
    
    async def _parse_program_page(self, url, program_key):
        """Парсинг одной страницы программы"""
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        program_data = {
            'url': url,
            'title': self._extract_title(soup),
            'description': self._extract_description(soup),
            'admission_info': self._extract_admission_info(soup),
            'career_prospects': self._extract_career_info(soup),
            'partners': self._extract_partners(soup),
            'faq': self._extract_faq(soup),
            'admission_requirements': self._extract_admission_requirements(soup),
            'curriculum_info': self._extract_curriculum_info(soup)
        }
        
        return program_data
    
    def _extract_title(self, soup):
        """Извлечение названия программы"""
        title_element = soup.find('h1') or soup.find('title')
        return title_element.get_text(strip=True) if title_element else ""
    
    def _extract_description(self, soup):
        """Извлечение описания программы"""
        about_section = soup.find(text=lambda text: text and 'о программе' in text.lower())
        if about_section:
            parent = about_section.parent
            while parent and not parent.find_next_sibling():
                parent = parent.parent
            if parent:
                description_text = parent.find_next_sibling()
                if description_text:
                    return description_text.get_text(strip=True)
        description_elements = soup.find_all('p')
        for elem in description_elements:
            text = elem.get_text(strip=True)
            if len(text) > 100 and any(keyword in text.lower() for keyword in ['программа', 'обучение', 'магистр']):
                return text
        
        return ""
    
    def _extract_admission_info(self, soup):
        """Извлечение информации о поступлении"""
        admission_info = {}
        directions_text = soup.find_all(text=lambda text: text and 'направления подготовки' in text.lower())
        if directions_text:
            admission_info['directions'] = self._extract_directions_info(soup)
        cost_elements = soup.find_all(text=lambda text: text and 'стоимость' in text.lower())
        for elem in cost_elements:
            if elem.parent:
                cost_text = elem.parent.get_text(strip=True)
                admission_info['cost'] = cost_text
                break
        
        return admission_info
    
    def _extract_directions_info(self, soup):
        """Извлечение информации о направлениях подготовки"""
        directions = []
        direction_codes = soup.find_all(text=lambda text: text and text.strip().count('.') == 2 and text.strip().replace('.', '').isdigit())
        
        for code in direction_codes:
            direction_info = {'code': code.strip()}
            parent = code.parent
            if parent:
                siblings = parent.find_next_siblings()
                for sibling in siblings[:3]:
                    text = sibling.get_text(strip=True)
                    if text and not text.isdigit():
                        direction_info['name'] = text
                        break
            
            directions.append(direction_info)
        
        return directions
    
    def _extract_career_info(self, soup):
        """Извлечение информации о карьере"""
        career_section = soup.find(text=lambda text: text and 'карьера' in text.lower())
        if career_section:
            parent = career_section.parent
            while parent:
                next_content = parent.find_next_sibling()
                if next_content:
                    career_text = next_content.get_text(strip=True)
                    if len(career_text) > 50:
                        return career_text
                parent = parent.parent
        return ""
    
    def _extract_partners(self, soup):
        """Извлечение информации о партнерах"""
        partners = []
        partner_images = soup.find_all('img', src=lambda src: src and 'partners' in src)
        
        for img in partner_images:
            src = img.get('src', '')
            if src:
                partner_name = src.split('/')[-1].split('.')[0]
                partners.append(partner_name)
        
        return partners
    
    def _extract_faq(self, soup):
        """Извлечение часто задаваемых вопросов"""
        faq_section = soup.find(text=lambda text: text and 'часто задаваемые вопросы' in text.lower())
        faq_list = []
        
        if faq_section:
            current_element = faq_section.parent
            while current_element:
                next_element = current_element.find_next_sibling()
                if next_element:
                    text = next_element.get_text(strip=True)
                    if text.endswith('?'):
                        question = text
                        answer_element = next_element.find_next_sibling()
                        answer = answer_element.get_text(strip=True) if answer_element else ""
                        faq_list.append({'question': question, 'answer': answer})
                current_element = next_element
                if len(faq_list) > 10:
                    break
        
        return faq_list
    
    def _extract_admission_requirements(self, soup):
        """Извлечение требований для поступления"""
        requirements = []
        admission_methods = [
            'вступительный экзамен',
            'портфолио',
            'олимпиада',
            'мегашкола',
            'я-профессионал'
        ]
        
        for method in admission_methods:
            method_info = soup.find(text=lambda text: text and method in text.lower())
            if method_info:
                parent = method_info.parent
                while parent:
                    content = parent.find_next_sibling()
                    if content:
                        method_text = content.get_text(strip=True)
                        if len(method_text) > 30:
                            requirements.append({
                                'method': method,
                                'description': method_text
                            })
                            break
                    parent = parent.parent
        
        return requirements
    
    def _extract_curriculum_info(self, soup):
        """Извлечение информации об учебном плане"""
        curriculum_link = soup.find('a', text=lambda text: text and 'учебный план' in text.lower())
        if curriculum_link:
            return {
                'link': curriculum_link.get('href', ''),
                'text': curriculum_link.get_text(strip=True)
            }
        return {}