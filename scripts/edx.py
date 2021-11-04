#!/usr/bin/env python3

import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException
from markdownify import markdownify as md
import requests


class EdxCrawler():
    url = 'https://courses.edx.org/login'
    course = 'LinuxFoundationX+LFS158x+3T2020'
    course_name = 'k8s'
    email = 'xxx'
    password = 'xxx'
    headers = {'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36')}

    def __init__(self):
        self.driver = webdriver.Chrome(service=Service('bin/chromedriver'))
        self.driver.set_window_size(1920, 980)
        self.current_section = ''
        Path(f'out/{self.course_name}/images').mkdir(parents=True, exist_ok=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()

    def start(self):
        self.driver.get(self.url)
        self._login(self.email, self.password)
        self._navigate_to_course(self.course)
        self._crawl_content()

    def _login(self, email, password):
        submit_button = self._wait_and_get("//form//button[@type='submit']")
        self.driver.find_element(By.ID, 'emailOrUsername').send_keys(email)
        self.driver.find_element(By.ID, 'password').send_keys(password)
        submit_button.click()

    def _navigate_to_course(self, course_name):
        course = self._wait_and_get(
            f"//h3//a[@data-course-key='course-v1:{course_name}']")
        self._append_content('# ' + course.get_attribute('innerHTML'))
        course.click()
        self._wait_and_get("//button[text()='Expand all']").click()
        self._wait_and_get('//ol/li[1]//ol/li[1]//a').click()

    def _crawl_content(self):
        has_next = True
        while has_next:
            self._get_content()
            has_next = self._next()

    def _get_content(self):
        iframe = self._wait_and_get('//div/iframe')
        breadcrumb_elements = self.driver.find_elements(
            By.XPATH, "//nav[@aria-label='breadcrumb']/ol/li")
        breadcrumbs = list(map(lambda e: e.text, breadcrumb_elements))
        section = ' '.join(breadcrumbs[2:])
        if self.current_section != section:
            self.current_section = section
            self._append_content('## ' + section)
        heading = self._wait_and_get('.unit h1', By.CSS_SELECTOR)
        self._append_content('### ' + heading.get_attribute('innerHTML'))
        self.driver.switch_to.frame(iframe)
        content_elements = self.driver.find_elements(
            By.CSS_SELECTOR, '.edx-notes-wrapper-content')
        for content_element in content_elements:
            self._extract_and_append_content(content_element)
        self.driver.switch_to.default_content()

    def _wait_and_get(self, locator, strategy=By.XPATH):
        return WebDriverWait(self.driver, 15).until(
            expected_conditions.presence_of_element_located((strategy, locator)))

    def _next(self):
        try:
            self._wait_and_get("//button[text()='Next']").click()
            return True
        except TimeoutException:
            return False

    def _append_content(self, content):
        with open(f'out/{self.course_name}/edx.md', 'a', encoding='utf8') as file:
            file.write(content + '\n\n')

    def _extract_and_append_content(self, content_element):
        images = content_element.find_elements(By.CSS_SELECTOR, 'img')
        for image in images:
            url = image.get_attribute('src')
            filename = os.path.basename(url)
            self._download_image(url, filename)
            self.driver.execute_script(
                'arguments[0].src = arguments[1]', image, 'images/' + filename)
        content = content_element.get_attribute('innerHTML')
        self._append_content(md(content))

    def _download_image(self, url, filename):
        session = requests.session()
        session.headers.update(self.headers)
        session.cookies.update({c['name']: c['value']
                               for c in self.driver.get_cookies()})
        response = session.get(url, allow_redirects=True)
        with open(f'out/{self.course_name}/images/{filename}', 'wb') as image:
            image.write(response.content)


if __name__ == '__main__':
    with EdxCrawler() as crawler:
        crawler.start()
