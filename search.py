import pandas as pd
import re
import itertools

def code_in(code, codelist):
    for level1 in codelist:
        if type(level1) is list:
            for level2 in level1:
                if code == level2:
                    codereturn = codelist.copy()
                    codereturn.remove(level1)
                    return codereturn
        elif code == level1:
            codereturn = codelist.copy()
            codereturn.remove(code)
            return codereturn
    return False

def text_from_codelist(pretext, codelist, posttext, errortext=''):
    text = ''
    for level1 in codelist:
        if type(level1) is list:
            text += 'enten '
            for level2 in level1:
                text += level2 + ' eller '
            text = text[:-7] + ' og '
        else:
            text += level1 + ' og '
    text = text[:-4]
    return pretext + text + posttext if text != '' else errortext

def new_root(coursecode, obligatory_list, recommended_list, checked_courses):
    new_obligatory, new_recommended, new_checked_courses = grow_roots(coursecode, checked_courses)
    obligatory_list.extend(new_obligatory if isinstance(new_obligatory, list) else [new_obligatory])
    recommended_list.extend(new_recommended if isinstance(new_recommended, list) else [new_recommended])
    checked_courses.extend(new_checked_courses if isinstance(new_checked_courses, list) else [new_checked_courses])

    return obligatory_list, recommended_list, checked_courses

def grow_roots(input_code, checked_courses):
    if input_code in courseData.index and input_code not in checked_courses:
        checked_courses.append(input_code)
        obligatory_list = courseData.at[input_code, 'obligatory']
        recommended_list = courseData.at[input_code, 'recommended']
        if obligatory_list != []:
            for obligatory_element in obligatory_list:
                if isinstance(obligatory_element, list):
                    for obligatory_course in obligatory_element:
                        obligatory_list, recommended_list, checked_courses = new_root(obligatory_course, obligatory_list, recommended_list, checked_courses)
                else:
                    obligatory_course = obligatory_element
                    obligatory_list, recommended_list, checked_courses = new_root(obligatory_course, obligatory_list, recommended_list, checked_courses)

        return obligatory_list, recommended_list, checked_courses
    return [], [], []

def duplicate_or_super(this_list, other_list):
    this_copy = this_list.copy()
    other_copy = other_list.copy()
    for this_item in this_list:
        for other_item in other_list:
            if this_item == other_item:
                #print(f"Denne tingen: {this_item} og denne listen {this_list}")
                this_copy.remove(this_item)
                other_copy.remove(other_item)
    if this_copy == []:
        print(this_list, other_list)
        return True
    else:
        return False

def untangle_roots(messy_roots):
    messy_roots_copy = list(messy_roots)[0].copy()
    untangled_roots = []
    if messy_roots_copy != []:
        #print(messy_roots_copy)
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

def search_single_course(input_code, courseData, flags):

    text_index = 0
    for flag in flags:
        if flag == 'compact' or flag == 'c':
            text_index = 1
        elif flag == 'roots' or flag == 'r':
            messy_roots = grow_roots(input_code, [])[0:2]
            untangled_roots = untangle_roots(messy_roots)
            print(text_from_codelist(f"For å ta {input_code} må du først ta ", untangled_roots, '.', errortext='Fant ingen obligatoriske forkunnskapskrav.'))

    results = False
    print(f'\n---\nSøker etter emner {input_code} peker mot...')
    for index, course in courseData.iterrows():
        total_text = ['\nEmnet ', '']
        obligatory_list = code_in(input_code, course['obligatory'])
        recommended_list = code_in(input_code, course['recommended'])
        if obligatory_list:
            total_text[0] += f"leder til {course['coursecode']} - {course['coursename']}{text_from_codelist(', hvis du også tar ', obligatory_list, '')}."
            total_text[1] += f"{course['coursecode']} - {course['coursename']} (obligatorisk)"
            if recommended_list:
                total_text[0] += text_from_codelist('', recommended_list, ' er anbefalte forkunnskaper.')
        elif recommended_list:
            total_text[0] += f"er en anbefalt forkunnskap til {course['coursecode']} - {course['coursename']}{text_from_codelist(', sammen med ', recommended_list, '')}.{text_from_codelist(' Den obligatoriske forkunnskapen får du gjennom ', course['obligatory'], '.')}"
            total_text[1] += f"{course['coursecode']} - {course['coursename']} (anbefalt)"

        chosen_text = total_text[text_index]
        
        if total_text[0] != '\nEmnet ':
            results = True
            print(chosen_text)
    

    if results:
        print('\n---\n')
    else:
        print(f'Fant dessverre ingen emner {input_code} leder til.')

    return results

if __name__ == '__main__':
    courseData = pd.read_pickle('courses.pkl')
    courseData.set_index('coursecode', drop = False, inplace = True)

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
        input_code = re.search(r"^ *([A-ZÆØÅ\-]+\d*[A-ZÆØÅ\-]{0,6}\d{0,2})", command.upper()).group(1)

        flags = []
        for flag in re.finditer(r"-(\w+)", command):
            flag_str = flag.group(1)
            flags.append(flag_str)

            if flag_str == 'h' or flag_str == 'help':
                print(help_text)

        if input_code[0] != '-':
            results = search_single_course(input_code, courseData, flags)
