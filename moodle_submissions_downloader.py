'''
Download all your assignment submissions from moodle.
@author: Asif Imtial, CSE16, BUET
@date: 4 June, 2022
'''
import argparse
from getpass import getpass
from pathlib import Path
import mechanicalsoup as ms
import zipfile
import re
import os


default_download_dir = os.environ.get("HOME") + "/Downloads"

parser = argparse.ArgumentParser(description="Download own assignment submissions from BUET CSE Moodle.")

parser.add_argument("--username", "-u", help="Username for your moodle account")
parser.add_argument("--output_dir", "-o", help=f"Absolute path for the download directory. Default: {default_download_dir}", default=default_download_dir)
parser.add_argument("--extract", "-e", action="store_true", help="Extract zip & delete the compressed file.")
parser.add_argument("--interactive", "-i", action="store_true", help="Turn interactive mode on.")

args = parser.parse_args()

if args.interactive:
    username = input("Username: ").strip()
    password = getpass("Password: ")
    output_dir = input(f"Download directory (Default: {default_download_dir}): ").strip()
    parent_dir = output_dir if output_dir else default_download_dir
else:
    username = args.username
    password = getpass("Password: ")
    parent_dir = args.output_dir

def is_compressed(filename: str):
    return filename.endswith(".zip")

def uncompress_and_delete(filename: str, target_dir: str):
    if filename.endswith(".zip"):
        with zipfile.ZipFile(filename,"r") as zip_ref:
            zip_ref.extractall(target_dir)
            os.remove(filename)

browser = ms.StatefulBrowser(
    soup_config={'features': 'lxml'},
    raise_on_404=True,
    user_agent='MyBot/0.1: mysite.example.com/bot_info',
)

browser.open("https://moodle.cse.buet.ac.bd/")
browser.follow_link("login")
form = browser.select_form()
browser["username"] = username
browser["password"] = password

resp = browser.submit_selected()

browser.follow_link("my")
link_all_courses = browser.links(link_text="Show all courses")[0]
browser.follow_link(link_all_courses)
sessional_link_list = browser.links(title=re.compile("(.*)Sessional(.*)"))
for sessional_link in sessional_link_list:
    sessional_dir = sessional_link['title']
    browser.follow_link(sessional_link)

    assignment_link_list = browser.links(url_regex="(.*)assign(.*)")
    for assignment_link in assignment_link_list:
        browser.follow_link(assignment_link)
        assignment_dir = browser.page.h2.string

        submission_link = browser.links("(.*)submission_files(.*)")
        if submission_link:
            file_dir = f"{parent_dir}/{sessional_dir}/{assignment_dir}"
            Path(file_dir).mkdir(parents=True, exist_ok=True)
            file_name = submission_link[0].string
            print(f"Downloading... {file_dir}/{file_name}")
            browser.download_link(link=submission_link[0], file=f"{file_dir}/{file_name}")
            if is_compressed(file_name) and args.extract:
                print(f"Extracting {file_name} in {file_dir}")
                uncompress_and_delete(f"{file_dir}/{file_name}", file_dir)