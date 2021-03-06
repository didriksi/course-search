"""Functions for scraping courses."""

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

from scrapeForCourses import make_soup
from CourseList import CourseListPrimitive, CompoundCourseList

def is_clean(string):
    """Checks if string has no very special characters.

    :param string: String to check.

    :retur: Boolean indicating whether there are special characters or not.
    """
    search = re.compile(r'[<>\\\n]').search
    return not search(string)
    
def make_courselist(coursecodes, course_relations):
    """Merge coursecodes and course_relations into one nested list.

    :param coursecodes: List of course code strings.
    :param course_relations: List of strings where element i specifies the 
                             relation between element i-1 and i in the coursecodes list.
                             Each element can be either 'interchangeable' or 'none'.

    :return: List of coursecodes in a nested list. List looks like
             [['either this course', 'or this'], ['also either this', 'or this'], 'and this']
    """
    courselist = []
    current_group = []
    for code, relation in zip(coursecodes, course_relations):
        if relation == 'interchangeable':
            current_group.append(code)
        elif current_group != []:
            current_group.append(code)
            courselist.append(current_group)
            current_group = []
        else:
            courselist.append(code)

    return courselist

def get_courses(string):
    """Find all mentions of course codes in a string, and their relations.

    Courses can either be interchangeable (eg 'To take this course, you have to
    take either course A or course B'), or not.
    
    :param string: String with possible course codes used.

    :return: 2-tuple of course codes list and course relations list.
             In the course relations list element i specifies the 
             relation between element i-1 and i in the course codes list.
             Each element can be either 'interchangeable' or 'none'.
    """

    # Find all courses mentioned in the string
    coursecodes, coursecodes_indexes = [], []
    for match in re.finditer(r"[A-ZÆØÅ\-]+\d+[A-ZÆØÅ\-]{0,6}\d{0,2}", string):
        coursecodes.append(match.group(0))
        coursecodes_indexes.append([match.start(), match.end()])

    # Find special cases where interchangeability is implied by something other than '/'
    special_group_indexes = []
    for beginning in re.finditer(r"Ett av emnene|One of the courses", string):
        special_group_indexes.append([beginning.end()])
        end = re.search(r".", string[special_group_indexes[-1][0]:])
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
        if re.search(r"\/|[ (]eller |[ (]or ", string[start:end]) and not re.search(r"og ", string[start:end]):
            course_relations.append('interchangeable')
        else:
            course_relations.append('none')
    course_relations.append('none')

    return coursecodes, course_relations

def get_prerequisites(content_tag):
    """Makes lists of prerequisites for a course, given the content tag of the course.

    :param content_tag: bs4.BeautifulSoup instance of content tag in course page.

    :return: 2-tuple of obligatory and recommended lists, with format as described in make_courselist().
    """
    descendants = []
    if content_tag is None:
        # Occasional error that isn't impossible to handle,
        # but that occurs so rarely and with courses UiO has
        # themselves made an error, so this should do
        return [], []
    
    for child in content_tag.descendants:
        if child.name == 'a':
            continue
        else:
            descendants.append(str(child))

    pure_text = ' '.join([string for string in descendants if is_clean(string)])
    #print(f"Pure text: {pure_text}")

    # Find where the sections start and end
    obligatory_start = -2; obligatory_end = -1
    recommended_start = -2; recommended_end = -1

    oblig_match = re.search(r'Formal prerequisites|Obligatoriske forkunnskaper', pure_text)
    if oblig_match:
        obligatory_start = oblig_match.end()

    recommended_match = re.search(r'Recommended previous knowledge|Anbefalte forkunnskaper', pure_text)
    if recommended_match:
        obligatory_end = recommended_match.start()
        recommended_start = recommended_match.end()

    end_search_beginning = obligatory_start if obligatory_start > recommended_start else recommended_start
    end_of_prerequisites_match = re.search(r'Overlapping courses|Overlappende emner|Undervisning|Teaching', pure_text[end_search_beginning:])
    if end_of_prerequisites_match:
        recommended_end = end_of_prerequisites_match.start() + end_search_beginning
        if recommended_start == -2:
            obligatory_end = recommended_end

    # Use get_courses to make a list of all courses in each section, if the section exists
    if ((obligatory_start, obligatory_end) != (-2, -1)):
        coursecodes, course_relations = get_courses(pure_text[obligatory_start:obligatory_end])
        obligatory_list = make_courselist(coursecodes, course_relations)
    else:
        obligatory_list = []

    if ((recommended_start, recommended_end) != (-2, -1)):
        coursecodes, course_relations = get_courses(pure_text[recommended_start:recommended_end])
        recommended_list = make_courselist(coursecodes, course_relations)
    else:
        recommended_list = []

    return obligatory_list, recommended_list

if __name__ == '__main__':
    courseData = pd.read_pickle('courses.pkl')
    num_courses = len(courseData.index)

    obligatories, recommendeds = [], []

    for i, (code, course) in enumerate(courseData.iterrows()):
        print(f"\r|{'='*(i*50//num_courses)}{' '*(50-i*50//num_courses)}| {i/num_courses:.2%} Scraping {course['coursecode']}\033[K", flush=True, end='')

        course_url = 'https://www.uio.no/studier/emner/'\
                   + course['faculty'] + '/'\
                   + course['institute'] + '/'\
                   + course['coursecode'] + '/'
        course_soup = make_soup(course_url)

        content = course_soup.find(id='vrtx-course-content')
        obligatory, recommended = get_prerequisites(content)
        obligatories.append(obligatory if obligatory else "")
        recommendeds.append(recommended if recommended else "")

    courseData['obligatory'] = obligatories
    courseData['recommended'] = recommendeds

    courseData.to_pickle('courses.pkl')

    print("\rScraped all courses, and updated dataframe in 'courses.pkl'\033[K")
