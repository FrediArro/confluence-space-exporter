import os
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
import json

# Settings for Chrome and Selenium
options = Options()
options.headless = False
prefs = {"download.default_directory": os.path.dirname(os.path.realpath(__file__)) + "/downloads"}
options.add_experimental_option("prefs", prefs)
s = Service("./chromedriver")
driver = webdriver.Chrome(options=options, service=s)

# Global variables for the script
confluence_url = ""
spaces = []


# login(usr, pwd) - function that logs into the users Confluence
# usr - Confluence username (email address)
# pwd - Confluence user's password
def login():
    confluence_url = "https://" + input("Enter your Confluence domain (ex. DOMAAIN.atlassian.com): ") + ".atlassian.net"
    print(confluence_url)
    username = input("Enter your email account used for Confluence: ")
    password = input("Enter your account password: ")
    print("Logging into Confluence:... ", end="", flush=True)
    driver.get(confluence_url + "/wiki/home")
    input_and_click(username, "username", "login-submit")
    driver.implicitly_wait(4)
    input_and_click(password, "password", "login-submit")
    try:
        WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.ID, "confluence-ui")))
    except:
        print("FAILED!")
        login()
    finally:
        print("DONE!")


# input_and_click(input_text, input_id, button_id) - finds the input field and click the submit button
# input_text - text to input tot the specified field
# input_id - input fields id
# button_id - button id
def input_and_click(input_text, input_id, button_id):
    driver.find_element(By.ID, input_id).send_keys(input_text)
    driver.find_element(By.ID, button_id).click()


# get_spaces_urls() - gets all the info about the spaces
# Currently receives only the first 500 spaces
# and currently there is no way to filter between personal and global spaces
def get_spaces_info():
    print("Getting spaces URLs:... ", end="", flush=True)
    spaces_url = confluence_url + "/wiki/rest/api/space?start=0&limit=500"
    driver.get(spaces_url)
    result = json.loads(driver.find_elements(By.TAG_NAME, "pre")[0].text)
    for element in result["results"]:
        spaces.append(element)
    print("DONE!\n")


# export_space(space) - exports the space in HTML format with all the attachments
# space - space info in a list
def export_space(space):
    # Navigates to the space's url
    export_url = confluence_url + "/wiki/spaces/exportspacehtml.action?key=" + space["key"]
    driver.get(export_url)
    driver.find_element(By.ID, "contentOptionVisible").click()
    # Waits until the confirm button is clickable
    try:
        export_button = WebDriverWait(driver, 30).until(
            expected_conditions.element_to_be_clickable((By.NAME, "confirm"))
        )
    finally:
        export_button.click()
    progress_percent = driver.find_element(By.ID, "percentComplete").text
    # While the export is not done, the "time elapsed" is updated
    while progress_percent != "100":
        progress_percent = driver.find_element(By.ID, "percentComplete").text
        time_elapsed = driver.find_element(By.ID, "taskElapsedTime").text
        print("", end=f"\rExporting {space['name']} space. Time elapsed: {time_elapsed}")
    print("")
    print("Export DONE!\n")
    # When export process is done, then the download button is clicked
    driver.find_element(By.CLASS_NAME, "space-export-download-path").click()
    return


# Logs into cloud Confluence
login()
# Waits for the body to load (to get all the authorization
try:
    elem = WebDriverWait(driver, 30).until(
        expected_conditions.presence_of_element_located((By.ID, "content-body"))  # This is a dummy element
    )
finally:
    # Gets all the info about the spaces
    get_spaces_info()

# Exports the spaces
for space in spaces:
    print(str(spaces.index(space) + 1) + "/" + str(len(spaces)))
    export_space(space)
    # When the last export is done, then the program waits for 1 hour to let the download finish
    if (spaces.index(space) + 1) == len(spaces):
        sleep(3600)
driver.quit()
