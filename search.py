"""Interface for searching through course data."""

import pandas as pd
import re
import itertools

from CourseList import CourseListPrimitive, CompoundCourseList

def code_in(course, courselist):
    """Check if course is in nested list, and return list of other courses in that list.

    :param course: Course code, string.
    :param courselist: List with courses and lists of courses as elements.
                       The sublists represent interchangeable courses.

    :return: List with all other elements than the one containing the course.
             False if course is not in list.
    """
    for level1 in courselist:
        if isinstance(level1, list):
            for level2 in level1:
                if course == level2:
                    codereturn = courselist.copy()
                    codereturn.remove(level1)
                    return codereturn
    
        elif course == level1:
            codereturn = courselist.copy()
            codereturn.remove(course)
            return codereturn
    return False

def text_from_courselist(prefix, courselist, suffix, errortext=''):
    """Makes a string out of a list of courses.

    :param prefix: Prefix string.
    :param courselist: List with courses and lists of courses as elements.
                       The sublists represent interchangeable courses.
    :param suffix: Suffix string.
    :param errortext: String to return if courselist is empty.
                      Defaults to ''

    :return: String that explains the rrelationship between the courses in the list.
    """
    text = ''
    for level1 in courselist:
        if type(level1) is list:
            text += 'enten '
            for level2 in level1:
                text += level2 + ' eller '
            text = text[:-7] + ' og '
        else:
            text += level1 + ' og '
    text = text[:-4]
    return prefix + text + suffix if text != '' else errortext

def listify(element):
    """Turns something into a list if it isn't already a list"""
    return element if isinstance(element, list) else [element]

def new_root(course, obligatory_list, recommended_list, checked_courses, course_df):
    """

    :param course: Course code, string.
    :param obligatory_list:
    :param recommended_list:
    :param checked_courses:
    
    :return: 3-tuple with lists of obligatory, recommended and checked courses
    """
    print(type(obligatory_list))
    new_obligatory, new_recommended, new_checked_courses = grow_roots(course, checked_courses, course_df)
    obligatory_list.extend(listify(new_obligatory))
    recommended_list.extend(listify(new_recommended))
    checked_courses.extend(listify(new_checked_courses))

    return obligatory_list, recommended_list, checked_courses

def grow_roots(course, checked_courses, course_df):
    """Makes lists of courses that are obligatory and recommended precursors to a course.

    Works recursively with new_root() to walk down the tree. To prevent it from infinite 
    loops it also returns courses checked.

    :param course: Course code, string.
    :param checked_courses: List of course codes to ignore.
    :param course_df: pandas.DataFrame instance with data.

    :return: 3-tuple of lists of obligatory, recommended, and checked courses.
    """
    if course in course_df.index and course not in checked_courses:
        checked_courses.append(course)
        obligatory_list = course_df.at[course, 'obligatory']
        recommended_list = course_df.at[course, 'recommended']
        if obligatory_list != []:
            for obligatory_element in obligatory_list:
                if isinstance(obligatory_element, list):
                    for obligatory_course in obligatory_element:
                        obligatory_list, recommended_list, checked_courses = \
                            new_root(
                                obligatory_course,
                                obligatory_list,
                                recommended_list,
                                checked_courses,
                                course_df
                            )
                else:
                    obligatory_list, recommended_list, checked_courses = \
                        new_root(
                            obligatory_element,
                            obligatory_list,
                            recommended_list,
                            checked_courses,
                            course_df
                        )

        return obligatory_list, recommended_list, checked_courses
    return [], [], []

def duplicate_or_super(this_list, other_list):
    """Checks if two lists are identical or one is a superset of the other.

    :param this_list: Nested list of courses.
    :param other_list: Nested list of courses.

    :return: Bool. True if duplicate or first is super, False if not.
    """
    this_copy = this_list.copy()
    other_copy = other_list.copy()
    for this_item in this_list:
        for other_item in other_list:
            if this_item == other_item:
                this_copy.remove(this_item)
                other_copy.remove(other_item)
    if this_copy == []:
        return True
    else:
        return False

def untangle_roots(messy_roots):
    """Cleans up list of courses, removing duplicate information.

    Other than removing complete duplicates, it also removes redundant information.
    Say that to take course A, you have to take course B and D. To take B, you must take C or D.
    This function would return that you only have to take B and D to take course A.

    :param messy_roots: Nested list of courses.

    :return: Nested list of courses.
    """
    messy_roots_copy = list(messy_roots)[0].copy()
    untangled_roots = []
    if messy_roots_copy != []:
        for messy_root in messy_roots[0]:
            if isinstance(messy_root, str):
                untangled_roots.append(messy_root)
                messy_roots_copy.remove(messy_root)
        
        for this_messy_root in messy_roots_copy:
            for this_messy_subroot in this_messy_root:
                if this_messy_subroot in untangled_roots:
                    messy_roots_copy.remove(this_messy_root)
                    break

        messy_roots_copy2 = messy_roots_copy.copy()
        for i, j in itertools.combinations(range(len(messy_roots_copy)), 2):
            if i < j and duplicate_or_super(messy_roots_copy2[i], messy_roots_copy2[j]):
                messy_roots_copy.remove(messy_roots_copy2[j])
    
    untangled_roots.extend(messy_roots_copy)
    return untangled_roots

def search_single_course(course, course_df, flags):
    """Prints out text describing what courses must be taken before taking a given course.

    :param course: Course code, string.
    :param course_df: pandas.DataFrame instance with data.
    :param flags: Flags that change what's printed out. Supported flags are:
                        'compact' or 'c': Removes whitespace and other courses required
                                          to take a course the input is a precursor to.
                        'roots' or 'r': Also prints out info about courses that themselves
                                        are precursors to the input course.
    
    :return: Bool. Whether or not any results could be found.
    """
    text_index = 0
    for flag in flags:
        if flag == 'compact' or flag == 'c':
            text_index = 1
        elif flag == 'roots' or flag == 'r':
            messy_roots = grow_roots(course, [], course_df)[:2]
            compound_obligatory = CompoundCourseList.from_nested_list(messy_roots[0])
            compound_recommended = CompoundCourseList.from_nested_list(messy_roots[1])

            compound_obligatory.simplify()
            compound_recommended.simplify()

            if compound_obligatory and compound_recommended:
                print(f"For å ta {course} må du først ta {compound_obligatory},"
                      f"og det anbefales også at du tar {compound_recommended}")
            elif compound_obligatoy:
                print(f"For å ta {course} må du først ta {compound_obligatory}.")
            elif compound_recommended:
                print(f"For å ta {course} anbefales de å ta {compound_obligatory}.")
            else:
                print(f"Finner ingen forkunnskapskrav til {course}")

    results = False
    print(f'\n---\nSøker etter emner {course} peker mot...')

    course_primitive = CourseListPrimitive(coursecode=[course])
    if not course_primitive:
        print("Couldn't find a course with that course code, please try another.")
        return results

    total_text = ['\nEmnet ', '']

    for index, other_course_row in course_df.iterrows():

        obligatory = False
        if course in other_course_row['obligatory']:
            obligatory = True
        else:
            for element in other_course_row['obligatory']:
                if isinstance(element, list) and course in element:
                    obligatory = True

        recommended = False
        if course in other_course_row['recommended']:
            recommended = True
        else:
            for element in other_course_row['recommended']:
                if isinstance(element, list) and course in element:
                    recommended = True
        

        if obligatory:
            obligatory_compound = CompoundCourseList.from_nested_list(other_course_row['obligatory'])
            not_done = obligatory_compound.requirements_not_implied_by(course_primitive)
            not_done.simplify()

            total_text[0] += f"Leder til {other_course_row['coursecode']} - {other_course_row['coursename']}"\
                           + f"{f', hvis du også tar {not_done}' if not_done else ''}."
            total_text[1] += f"{other_course_row['coursecode']} - {other_course_row['coursename']} (obligatorisk)"

            recommended_compound = CompoundCourseList.from_nested_list(other_course_row['recommended'])
            total_text[0] += f"\n{recommended_compound} er anbefalt forkunnskaper." if recommended_compound else ""
            total_text[0] += "\n\n"
            total_text[1] += "\n"

        elif recommended:
            recommended_compound = CompoundCourseList.from_nested_list(other_course_row['obligatory'])
            not_done = recommended_compound.requirements_not_implied_by(course_primitive)
            not_done.simplify()
            total_text[0] += f"Er en anbefalt forkunnskap til {other_course_row['coursecode']} - {other_course_row['coursename']}"\
                           + f"{f', sammen med {not_done}' if not_done else ''}."

            total_text[1] += f"{other_course_row['coursecode']} - {other_course_row['coursename']} (anbefalt)"

            obligatory_compound = CompoundCourseList.from_nested_list(other_course_row['obligatory'])
            total_text[0] += f"\n{obligatory_compound} er den nødvendige forkunnskapen." if obligatory_compound else ""
            total_text[0] += "\n\n"
            total_text[1] += "\n"

    chosen_text = total_text[text_index]
    
    if total_text[0] != '\nEmnet ':
        results = True
        print(chosen_text, "\n\n---\n")
    else:
        print(f'Fant dessverre ingen emner {course} leder til.')

    return results

if __name__ == '__main__':
    course_df = pd.read_pickle('courses.pkl')
    print(course_df)
    course_df.set_index('coursecode', drop=False, inplace=True)

    print('Skriv inn en emnekode du vil se hva slags muligheter gir senere. Skriv \"-help\" for å se kommandoer og få hjelp.')

    help_text = """---\nSkriv inn emnekode for å se hva slags andre emner du kan ta senere, hvis du tar det emnet først. Du kan også bruke følgende kommandoer:\n
    -help eller -h tar deg med hit\n
    -compact eller -c viser deg en mer kompakt oversikt over emnene, hvor du ikke ser andre krav, men ser om emnet du drøfter er anbefalt eller obligatorisk forkunnskap
    -leaves eller -l viser et tre med emner lengre frem enn ett hakk (ikke lagt til ennå)
    -roots eller -r viser et tre med alle emnene du må ta for å kunne ta det emnet
    -old eller -o tar med emner som ikke lengre holdes (ikke lagt til ennå)
    -multiple eller -m lar deg oppgi en liste med emner istedenfor bare ett (ikke lagt til ennå)
    -forest eller -f lager en skog med alle koblinger enten i røtter eller i grener, til emnet du oppgir (ikke lagt til ennå)
    \n---"""

    run = True
    while(run):
        command = input('Emnekode: ')
        course = re.search(r"^ *([A-ZÆØÅ\-]+\d*[A-ZÆØÅ\-]{0,6}\d{0,2})", command.upper()).group(1)

        flags = []
        for flag in re.finditer(r"-(\w+)", command):
            flag_str = flag.group(1)
            flags.append(flag_str)

            if flag_str == 'h' or flag_str == 'help':
                print(help_text)

        if course[0] != '-':
            results = search_single_course(course, course_df, flags)
