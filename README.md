# course-search
Scrape the websites of the University of Oslo to get data on course dependencies, and make it searchable.

## Quick breakdown of the modules:
 * `scrapeForCourses` uses the search results at https://www.uio.no/studier/emner/alle/ to make a list of all courses offered, with their respective faculties and institutes.
 * `scrapeEachCourse` goes through the courses gathered, visits each of their course pages, and stores information about the recommended and obligatory precursors.
 * `search` is both an interface, and houses some functions for searching through the course relations. The key feature here is that it can print a list of courses that have a given course as its precursor, along with other precursors of it.
 * `CourseList` has two classes that deal with lists of courses, and their relationships.
 
## Data storage
 The data is stored in a Pandas dataframe, which works reasonably well. I expect performance and readability could be increased by moving to SQL, but since performance isn't a concern due to small data sizes, and SQL set up would require people cloning this repo to set up a server, pandas does well enough.
 
## Data structure
A repeating data pattern is nested lists for course precursors. Here, each element is required, but while some elements are strings representing a single course, others are lists. In the latter case, the courses in the list are interchangeable requirements. This covers most cases, but it is impossible to represent the occassionally occuring "two among this list of courses", so it isn't perfect.

To do the latter, the `CourseList` module has two classes that together allow much more complicated and nested relationships, having some list of parameters select a list of courses, specifying how many of these courses need to be taken to fulfill the requirements, and then organising these requirements in a directed acyclic graph.

## Inaccuracies
Scraping the websites have shown that they are quite inconsistent. The precursor course property interchangeability is especially hard to find, because it is sometimes marked with 'or' and commas, sometimes with a header like 'One of these courses' and then a list, and sometimes implied even more indirectly. There are also at least one example of it not being indicated at all, even though it is obvious through what courses were listed that they were in fact interchangeable. This means that there are some inaccuracies in the data gathered.

## Further work
I am now working on features for handling not only single courses, but sets of courses. In particular, scraping for requirements for different Master's programs, and checking if a set of courses satisfy those requirements.
