import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

def make_soup(url):
    coursepage = requests.get(url)
    coursecontent = coursepage.content
    return BeautifulSoup(coursecontent, 'html.parser')

def get_course_url_list(url_to_begin):
    url_list = []
    i = 0
    run = True
    print(f"Checking if there are courses on page: ")
    while(run):
        print(f"{i}")
        current_url = url_to_begin + str(i)
        course_list = make_soup(current_url)
        if course_list.find(id='vrtx-listing-filter-no-results'):
            print("Invalid page.")
            run = False
        else:
            url_list.append(current_url)
            i += 1
            
    
    print(f"Completed. Found {len(url_list)} courselists.")
    return url_list

def coursecode_from_URL(courseurl):
    regex = r"/studier\/emner\/(\w*)\/(\w*)\/(.*)\/index.html"
    for match in re.finditer(regex, courseurl):
        return match.group(1), match.group(2), match.group(3)
    return ['not_course', 'not_course', 'not_course']

def scrape_coursecodes(coursepage_soup):

    faculties, institutes, coursecodes, coursenames = [], [], [], []
    for link in coursepage_soup.tbody.find_all('a'):
        courseurl = link.get('href')
        
        faculty, institute, coursecode = coursecode_from_URL(courseurl)
        coursename_search = re.search(r"^[A-ZÆØÅ\-]+\d*[A-ZÆØÅ\-]{0,6}\d{0,2} *.? *(.*)", link.string)
        coursename = coursename_search.group(1)
        
        faculties.append(faculty)
        institutes.append(institute)
        coursecodes.append(coursecode)
        coursenames.append(coursename)

    return faculties, institutes, coursecodes, coursenames


if __name__ == '__main__':

    course_url_list = get_course_url_list('https://www.uio.no/studier/emner/alle/?page=')
    faculties, institutes, coursecodes, coursenames = [], [], [], []

    for url in course_url_list:
        print(f"Going through {url}. Have so far found {len(coursecodes)} courses.")
        coursepage_soup = make_soup(url)
        new_faculties, new_institutes, new_coursecodes, new_coursenames = scrape_coursecodes(coursepage_soup)
        
        faculties.extend(new_faculties)
        institutes.extend(new_institutes)
        coursecodes.extend(new_coursecodes)
        coursenames.extend(new_coursenames)

    courseData = pd.DataFrame()

    courseData['coursecode'] = coursecodes
    courseData['coursename'] = coursenames
    courseData['faculty'] = faculties
    courseData['institute'] = institutes
    
    courseData.to_pickle('data/courses.pkl')
    #courseData.to_csv('data/courses.csv')










