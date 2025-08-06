import requests
from bs4 import BeautifulSoup
import json
import os
import re
import PyPDF2
import io
from collections import defaultdict

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
                print(f"Парсинг программы: {program_key}")
                data = await self._parse_program_page(url, program_key)
                programs_data[program_key] = data
                print(f"Программа {program_key} успешно спарсена")
                pdf_url = programs_data[program_key]['curriculum_info']['link']
                cur_data =  await self.parse_curriculum_2(pdf_url, program_key)
            except Exception as e:
                print(f"Ошибка парсинга {program_key}: {e}")

        os.makedirs('data', exist_ok=True)
        with open('data/programs_data.json', 'w', encoding='utf-8') as f:
            json.dump(programs_data, f, ensure_ascii=False, indent=2)
 
        
        return programs_data, cur_data
    
    async def _parse_program_page(self, url, program_key):
        """Парсинг одной страницы программы"""

        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        next_data = self._extract_next_data(soup)
        
        if next_data:
            print(f"  → Найден __NEXT_DATA__, используем структурированные данные")
            return self._parse_from_next_data(next_data, url)
        else:
            print(f"  → __NEXT_DATA__ не найден, используем fallback парсинг")
            return self._parse_from_html_fallback(soup, url)
    
    def _extract_next_data(self, soup):
        """Извлечение данных из __NEXT_DATA__ скрипта"""
        try:
            script = soup.find('script', {'id': '__NEXT_DATA__', 'type': 'application/json'})
            if script and script.string:
                return json.loads(script.string)
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Ошибка парсинга JSON: {e}")
        return None
    
    def _parse_from_next_data(self, next_data, url):
        """Парсинг данных из структурированного JSON"""
        try:

            page_props = next_data.get('props', {}).get('pageProps', {})
            json_program = page_props.get('jsonProgram', {})
            api_program = page_props.get('apiProgram', {})
            
            program_data = {
                'url': url,
                'title': api_program.get('title', ''),
                'description': self._extract_description_from_json(json_program),
                'admission_info': self._extract_admission_from_json(api_program),
                'career_prospects': self._extract_career_from_json(json_program),
                'partners': self._extract_partners_from_json(json_program),
                'faq': json_program.get('faq', []),
                'admission_requirements': self._extract_requirements_from_json(api_program),
                'curriculum_info': self._extract_curriculum_from_json(api_program),
                'study_info': self._extract_study_info_from_json(api_program),
                'cost_info': self._extract_cost_info_from_json(api_program),
                'social_links': json_program.get('social', {}),
                'achievements': json_program.get('achievements', [])
            }
            
            return program_data
            
        except Exception as e:
            print(f"Ошибка обработки JSON данных: {e}")
            return None
    
    def _extract_description_from_json(self, json_program):
        """Извлечение описания из JSON"""
        about = json_program.get('about', {})
        lead = about.get('lead', '')
        desc = about.get('desc', '')

        if desc:
            desc = re.sub(r'<[^>]+>', '', desc)
            desc = desc.replace('\\u003cbr\\u003e', ' ').replace('&nbsp;', ' ')
        
        return {
            'lead': lead,
            'full_description': desc
        }
    
    def _extract_admission_from_json(self, api_program):
        """Извлечение информации о поступлении из JSON"""
        directions = api_program.get('directions', [])
        admission_info = {
            'directions': []
        }
        
        for direction in directions:
            direction_data = {
                'code': direction.get('code', ''),
                'title': direction.get('title', ''),
                'quotas': direction.get('admission_quotas', {}),
                'disciplines': []
            }

            for discipline in direction.get('disciplines', []):
                disc_info = discipline.get('discipline', {})
                direction_data['disciplines'].append({
                    'title': disc_info.get('title', ''),
                    'description': disc_info.get('description', ''),
                    'link': disc_info.get('link', '')
                })
            
            admission_info['directions'].append(direction_data)

        education_cost = api_program.get('educationCost', {})
        if education_cost:
            admission_info['cost'] = {
                'russian': education_cost.get('russian', 0),
                'foreigner': education_cost.get('foreigner', 0),
                'year': education_cost.get('year', 2025)
            }
        
        return admission_info
    
    def _extract_career_from_json(self, json_program):
        """Извлечение информации о карьере из JSON"""
        career = json_program.get('career', {})
        lead = career.get('lead', '')
        
        if lead:
            lead = re.sub(r'<[^>]+>', '', lead)
            lead = lead.replace('\\u003cbr\\u003e', ' ').replace('&nbsp;', ' ')
        
        return lead
    
    def _extract_partners_from_json(self, json_program):
        """Извлечение партнеров из JSON"""
        partners_images = json_program.get('partnersImages', [])
        return [img.split('/')[-1].split('.')[0] for img in partners_images]
    
    def _extract_requirements_from_json(self, api_program):
        """Извлечение требований поступления из JSON"""
        requirements = []
        directions = api_program.get('directions', [])
        
        for direction in directions:
            for discipline in direction.get('disciplines', []):
                disc_info = discipline.get('discipline', {})
                if disc_info.get('title') and disc_info.get('description'):
                    requirements.append({
                        'method': disc_info.get('title', ''),
                        'description': disc_info.get('description', ''),
                        'link': disc_info.get('link', '')
                    })
        
        return requirements
    
    def _extract_curriculum_from_json(self, api_program):
        """Извлечение информации об учебном плане из JSON"""
        academic_plan = api_program.get('academic_plan', '')
        if academic_plan:
            return {
                'link': academic_plan,
                'text': 'Учебный план программы'
            }
        return {}
    
    def _extract_study_info_from_json(self, api_program):
        """Извлечение информации об обучении"""
        study = api_program.get('study', {})
        return {
            'period': study.get('period', ''),
            'label': study.get('label', ''),
            'mode': study.get('mode', ''),
            'language': api_program.get('language', ''),
            'military': api_program.get('isMilitary', False)
        }
    
    def _extract_cost_info_from_json(self, api_program):
        """Извлечение информации о стоимости"""
        education_cost = api_program.get('educationCost', {})
        return {
            'russian': education_cost.get('russian', 0),
            'foreigner': education_cost.get('foreigner', 0),
            'year': education_cost.get('year', 2025)
        }
        
    async def parse_curriculum_2(self, pdf_url, program_key):
        try:
            print(f"Загружаем учебный план: {program_key}")
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()
            pdf_content = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_content)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

            with open(f'curric_{program_key}.txt', 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(text[:100])
            print(f"PDF загружен, {len(pdf_reader.pages)} страниц")
        
        
            categories = {
                "obligatory_courses": ["Обязательные дисциплины"],
                "elective_courses": ["Пул выборных дисциплин"],
                "soft_skills": [
                    "Микромодули Soft Skills", "Элективные микромодули Soft Skills",
                    "Мировоззренческий модуль", "Предпринимательская культура", "Мышление",
                    "Этика", "Критическое мышление", "Навыки критического мышления"
                ],
                "universal_preparation": ["Универсальная (надпрофессиональная) подготовка"],
                "practices": ["Блок 2. Практика", "Производственная практика", "практика", "Преддипломная практика"],
                "gia": ["Государственная итоговая аттестация", "ГИА"],
            }
            curriculum = defaultdict(list)
            current_category = None
            course_line_pattern = re.compile(r"^(\d)([А-Яа-яA-Za-z /().-]+)\s+\d{4,}$")
            for line in text.split('\n'):
                stripped = line.strip()

                if not stripped:
                    continue
                for key, keywords in categories.items():
                    if any(kw.lower() in stripped.lower() for kw in keywords):
                        current_category = key
                        break
                match = course_line_pattern.match(stripped)
                if current_category and match:
                    semester = int(match.group(1))
                    title = match.group(2).strip()
                    curriculum[current_category].append({"semester": semester, "title": title})
            curriculum = dict(curriculum)
            await self._save_curriculum_data(curriculum, program_key)

        except Exception as e:
                print(f"Ошибка парсинга: {e}")
        
        return curriculum
    
    async def _save_curriculum_data(self, curriculum, program_key):
        """Сохранение данных учебного плана"""
        os.makedirs('data', exist_ok=True)
        
        filename = f'data/curriculum_{program_key}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(curriculum, f, ensure_ascii=False, indent=2)
        
        print(f"Учебный план сохранен: {filename}")
    
    def _parse_from_html_fallback(self, soup, url):
        """Fallback парсинг из HTML (если JSON недоступен)"""
        return {
            'url': url,
            'title': self._extract_title_html(soup),
            'description': self._extract_description_html(soup),
            'admission_info': self._extract_admission_html(soup),
            'career_prospects': self._extract_career_html(soup),
            'partners': self._extract_partners_html(soup),
            'faq': self._extract_faq_html(soup),
            'admission_requirements': self._extract_requirements_html(soup),
            'curriculum_info': self._extract_curriculum_html(soup)
        }
    
    def _extract_title_html(self, soup):
        """Извлечение названия программы из HTML"""
        title_element = soup.find('h1') or soup.find('title')
        return title_element.get_text(strip=True) if title_element else ""
    
    def _extract_description_html(self, soup):
        """Извлечение описания программы из HTML"""
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
    
    def _extract_admission_html(self, soup):
        """Извлечение информации о поступлении из HTML"""
        admission_info = {}
        directions_text = soup.find_all(text=lambda text: text and 'направления подготовки' in text.lower())
        if directions_text:
            admission_info['directions'] = self._extract_directions_info_html(soup)
        
        cost_elements = soup.find_all(text=lambda text: text and 'стоимость' in text.lower())
        for elem in cost_elements:
            if elem.parent:
                cost_text = elem.parent.get_text(strip=True)
                admission_info['cost'] = cost_text
                break
        
        return admission_info
    
    def _extract_directions_info_html(self, soup):
        """Извлечение информации о направлениях подготовки из HTML"""
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
    
    def _extract_career_html(self, soup):
        """Извлечение информации о карьере из HTML"""
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
    
    def _extract_partners_html(self, soup):
        """Извлечение информации о партнерах из HTML"""
        partners = []
        partner_images = soup.find_all('img', src=lambda src: src and 'partners' in src)
        
        for img in partner_images:
            src = img.get('src', '')
            if src:
                partner_name = src.split('/')[-1].split('.')[0]
                partners.append(partner_name)
        
        return partners
    
    def _extract_faq_html(self, soup):
        """Извлечение FAQ из HTML"""
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
    
    def _extract_requirements_html(self, soup):
        """Извлечение требований для поступления из HTML"""
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
    
    def _extract_curriculum_html(self, soup):
        """Извлечение информации об учебном плане из HTML"""
        curriculum_link = soup.find('a', text=lambda text: text and 'учебный план' in text.lower())
        if curriculum_link:
            return {
                'link': curriculum_link.get('href', ''),
                'text': curriculum_link.get_text(strip=True)
            }
        return {}
