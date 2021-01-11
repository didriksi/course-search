"""Interface for searching through course data."""

import pandas as pd
import re
import itertools

from CourseList import CourseListPrimitive, CompoundCourseList

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

    total_text = ['', '']

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

            total_text[0] += f"\nEmnet leder til {other_course_row['coursecode']} - {other_course_row['coursename']}"\
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
            total_text[0] += f"Emnet er en anbefalt forkunnskap til {other_course_row['coursecode']} - {other_course_row['coursename']}"\
                           + f"{f', sammen med {not_done}' if not_done else ''}."

            total_text[1] += f"{other_course_row['coursecode']} - {other_course_row['coursename']} (anbefalt)"

            obligatory_compound = CompoundCourseList.from_nested_list(other_course_row['obligatory'])
            total_text[0] += f"\n{obligatory_compound} er den nødvendige forkunnskapen." if obligatory_compound else ""
            total_text[0] += "\n\n"
            total_text[1] += "\n"

    chosen_text = total_text[text_index]
    
    if total_text[0] != '':
        results = True
        print(chosen_text, "---\n")
    else:
        print(f'Fant dessverre ingen emner {course} leder til.')

    return results

if __name__ == '__main__':
    course_df = pd.read_pickle('courses.pkl')
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
