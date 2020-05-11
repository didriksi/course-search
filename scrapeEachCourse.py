import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from scrapeForCourses import make_soup

def is_clean(strg, search=re.compile(r'[<>\\\n]').search):
        return not bool(search(strg))
    
def make_courselist(coursecodes, course_relations):
    # Merge coursecodes and course_relations into one nested list
    # Final list looks like [['either this', 'or this'], ['also either this', 'or this'], 'and this']
    print(coursecodes, course_relations)
    courselist = []
    current_group = []
    for code, relation in zip(coursecodes, course_relations):
        if relation == 'interchangeable':
            current_group.append(code)
        elif current_group != []:
            current_group.append(code)
            courselist.append(current_group)
            # print(f"Current group: {current_group}")
            current_group = []
        else:
            courselist.append(code)

    return courselist

def get_courses(text):
    # Find all courses mentioned in the text
    coursecodes, coursecodes_indexes = [], []
    for match in re.finditer(r"[A-ZÆØÅ\-]+\d{4}", text):
        coursecodes.append(match.group(0))
        coursecodes_indexes.append([match.start(), match.end()])

    # Find special cases where interchangeability is implied by something other than '/'
    special_group_indexes = []
    for beginning in re.finditer(r"Ett av emnene|One of the courses", text):
        special_group_indexes.append([beginning.end()])
        end = re.search(r".", text[special_group_indexes[-1][0]:])
        if end:
            special_group_indexes[-1].append(end.start())

    # Find out whether two or more courses are interchangeable
    course_relations = []
    e, in_special_group = 0, 0
    for i in range(0, len(coursecodes_indexes) - 1):
        start = coursecodes_indexes[i][1]
        end = coursecodes_indexes[i+1][0]

        # Check if this code is in a special interchangeability group with the previous one
        if special_group_indexes != [] and course_relations != []:
            if in_special_group == 1 and end > special_group_indexes[e][0]:
                e += 1
            if special_group_indexes[e][0] < start < end < special_group_indexes[e][0]:
                course_relations[-1] = 'interchangeable'
                in_special_group = 1
            else:
                in_special_group = 0
        
        # Check if there's a '/' or an 'or' between the codes, implying interchangeability
        if re.search(r"\/|[ (]eller |[ (]or ", text[start:end]) and not re.search(r"og ", text[start:end]):
            course_relations.append('interchangeable')
        else:
            course_relations.append('none')
    course_relations.append('none')

    return make_courselist(coursecodes, course_relations)

def get_prerequisites(content_tag):
    descendants = []
    for child in content_tag.descendants:
        if child.name == 'a':
            continue
            #descendants.append(child.string)
        else:
            descendants.append(str(child))

    pure_text = ' '.join([ strg for strg in descendants if is_clean(strg) ])
    #print(f"Pure text: {pure_text}")

    # Find where the sections start and end
    obligatory_start = -2; obligatory_end = -1
    recommended_start = -2; recommended_end = -1

    oblig_match = re.search(r'Formal prerequisites|Obligatoriske forkunnskaper', pure_text)
    if oblig_match:
        obligatory_start = oblig_match.end()
        print(f"Fant oblig, og den starter på {obligatory_start}")

    recommended_match = re.search(r'Recommended previous knowledge|Anbefalte forkunnskaper', pure_text)
    if recommended_match:
        obligatory_end = recommended_match.start()
        recommended_start = recommended_match.end()
        print(f"Fant anbefalt, og den starter på {recommended_start}")

    end_search_beginning = obligatory_start if obligatory_start > recommended_start else recommended_start
    end_of_prerequisites_match = re.search(r'Overlapping courses|Overlappende emner|Undervisning|Teaching', pure_text[end_search_beginning:])
    if end_of_prerequisites_match:
        recommended_end = end_of_prerequisites_match.start() + end_search_beginning
        if recommended_start == -2:
            obligatory_end = recommended_end
        print(f"Fant slutten, den er {recommended_end}. Startet søket ved {end_search_beginning}")

    # Use get_courses to make a list of all courses in each section, if the section exists
    if ((obligatory_start, obligatory_end) != (-2, -1)):
        # print(f"Søker gjennom obligatorisk tekst: {pure_text[obligatory_start:obligatory_end]}")
        obligatory_list = get_courses(pure_text[obligatory_start:obligatory_end])
        # print(f"Resultat: {obligatory_list}")
    else:
        obligatory_list = '0'

    if ((recommended_start, recommended_end) != (-2, -1)):
        # print(f"Søker gjennom anbefalt tekst: {pure_text[recommended_start:recommended_end]}")
        recommended_list = get_courses(pure_text[recommended_start:recommended_end])
        # print(f"Resultat: {recommended_list}")
    else:
        recommended_list = '0'

    return obligatory_list, recommended_list

def scrape_course(faculty, institute, coursecode):
    print(f'Scraping {coursecode}')

    course_url = 'https://www.uio.no/studier/emner/' + faculty + '/' + institute + '/' + coursecode + '/'
    course_soup = make_soup(course_url)

    content = course_soup.find(id='vrtx-course-content')
    obligatory, recommended = get_prerequisites(content)

    return obligatory, recommended

if __name__ == '__main__':
    courseData = pd.read_pickle('courses.pkl')

    obligatories, recommendeds = [], []

    for code, course in courseData.iterrows():
        obligatory, recommended = scrape_course(course['faculty'], course['institute'], course['coursecode'])
        obligatories.append(obligatory)
        recommendeds.append(recommended)

    courseData['obligatory'] = obligatories
    courseData['recommended'] = recommendeds

    courseData.to_pickle('courses.pkl')
