import pandas as pd

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

def text_from_codelist(pretext, codelist, posttext):
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
    return pretext + text + posttext if text != '' else ''

if __name__ == '__main__':
    courseData = pd.read_pickle('courses.pkl')

    print('Skriv inn en emnekode du vil se hva slags muligheter gir senere. Hvis det blir litt mye tekst kan du skrive \"-\" rett etter emnekoden. Da får du liste med litt mindre info.')

    run = True
    while(run):
        input_code = input('Emnekode: ')
        code = input_code[:-1] if input_code[-1] == '-' else input_code
        results = False
        print(f'\n---\nSøker etter emner {code} peker mot...')

        for index, course in courseData.iterrows():
            total_text = ['\nEmnet ', '']
            obligatory_list = code_in(code, course['obligatory'])
            recommended_list = code_in(code, course['recommended'])
            if obligatory_list:
                total_text[0] += f"leder til {course['coursecode']} - {course['coursename']}{text_from_codelist(', hvis du også tar ', obligatory_list, '')}."
                total_text[1] += f"{course['coursecode']} - {course['coursename']} (obligatorisk)"
                if recommended_list:
                    total_text[0] += text_from_codelist('', recommended_list, ' er anbefalte forkunnskaper.')
            elif recommended_list:
                total_text[0] += f"er en anbefalt forkunnskap til {course['coursecode']} - {course['coursename']}{text_from_codelist(', sammen med ', recommended_list, '')}.{text_from_codelist(' Den obligatoriske forkunnskapen får du gjennom ', course['obligatory'], '.')}"
                total_text[1] += f"{course['coursecode']} - {course['coursename']} (anbefalt)"

            if total_text[0] != '\nEmnet ':
                results = True

                if input_code[-1] == '-':
                    print(total_text[1]) 
                else:
                    print(total_text[0])

        if results:
            print('---\n')
        else:
            print(f'Fant dessverre ingen emner {code} leder til.')
