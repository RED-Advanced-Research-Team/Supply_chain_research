from selenium import webdriver
from time import sleep
# Using Chrome to access web
driver = webdriver.Chrome()
# Open the website
driver.get('https://github.com/signup?ref_cta=Sign+up&ref_loc=header+logged+out&ref_page=%2F&source=header-home')
sleep(3)
driver.find_element('id', 'email').send_keys('test@mail.com')
sleep(1)
driver.find_element('xpath', '//button[@data-optimizely-event="click.signup_continue.email"]').click()
sleep(1)
driver.find_element('id', 'password').send_keys('test_password')
sleep(1)
driver.find_element('xpath', '//button[@data-optimizely-event="click.signup_continue.password"]').click()
sleep(1)
with open("result_github_user.txt", "r") as git_users:
    for user in git_users:
        driver.find_element('id', 'login').send_keys(user.strip())
        sleep(1)
        result = driver.find_element('id', 'login-err').text
        driver.find_element('id', 'login').clear()
        print(result)
