import pandas as pd
import re
import itertools

# TODO: Make iterator special method (for course in CourseListPrimitive())

class CourseListPrimitive:
    def __init__(self, **course_parameters):
        """A list of courses, along with a quantity of courses.

        The quantity is a number up to the number of courses, and is usually interpreted
        as the amount of courses among them that has to be taken for the requirement
        to be fulfilled.

        More complicated set of requirements can be made like this:
            'course_list_primitive1*2 & course_list_primitive2', or
            'course_list_primitive1*2 | course_list_primitive2'
        where the requirements are a CompoundCourseList instance that represents a
        requirement of two courses from the first list, and all in the second.
        
        :param **course_parameters: Keyword arguments dictating what to search for.
               faculty: List of faculties to search for courses in.
               institute: List of institutes to search for courses in. 
               coursecode: List of courses codes to search for.
               search: List of queries to be interpreted as regexp. For ease of readability,
                       when this is displayed as a string, and because of character escaping,
                       please use as light regexp as possible. Special characters might fail
                       in unexpected ways. Luckily, I believe almost all cases can be solved 
                       with these two patterns:
                        - Letters or numbers are interpreted literally
                        - '.' represent any character
                       All lower case letters are also escaped, meaning they get a backslash
                       before them. This makes it so that 'd' represents all numbers

               All parameters are additive by default, but leading '-' in element of list
               makes them excluding. TODO: Make better and easier to understand union, 
               snitt, and exclusion operators.

               quantity: This one is a bit different. If not given it defauls to the amount
                         of courses. If an int is given, it specifies how many courses among
                         the results that have to be taken for the list to be fulfilled.

        :raise ValueError: If invalid course_parameter keys are given.
        :raise TypeError: If course_parameter values aren't lists of strings.
        """
        self._course_parameters = course_parameters

        for param_name, param in self._course_parameters.items():
            if param_name not in ["faculty", "institute", "coursecode", "search", "quantity"]:
                raise ValueError("Only valid course parameter names are faculty, institute,"
                                 f"coursecode, and search, not {param_name}")
            if param_name in ["faculty", "institute", "coursecode", "search"]:
                if not isinstance(param, list):
                    raise TypeError(f"Parameters must be of type list, not {type(param)}")
                for element in param:
                    if not isinstance(element, str):
                        raise TypeError(f"Parameter elements must be of type str, not {type(element)}")
            elif param_name == "quantity":
                if not (param is None or isinstance(param, int)):
                    raise TypeError(f"Quantity must be of type str or None, not {type(param)}")
        
        if "quantity" in self._course_parameters:
            self._quantity = self._course_parameters["quantity"]

    @classmethod
    def from_str(cls, str_course_parameters):
        """Factory method for creating instance based on string representation or params.

        :param str_course_parameters: Can be constructed by str(self), and is useful
                                      because it allows instance to be saved as a string,
                                      without needing unsafe eval() to reinstantiate.
        
        :return: CourseListPrimitive instance.
        """
        course_parameters = {}
        regex = r"(\w+)\: ([\w, ]+)"
        for match in re.finditer(regex, str_course_parameters):
            parameter_value = []
            for secondary_match in re.finditer(r"(\w+)", match.group(2)):
                parameter_value.append(secondary_match.group(1))
            course_parameters[match.group(1).lower()] = parameter_value

        return cls(**course_parameters)

    @property
    def courses(self):
        """List of courses. Makes it by searching, if it hasn't already been done."""
        
        if "_courses" not in self.__dict__:
            self._courses = []
            courses_to_exclude = []

            course_df = pd.read_pickle("courses.pkl")

            for parameter in ["faculty", "institute"]:
                if parameter in self._course_parameters:
                    for element in self._course_parameters[parameter]:
                        if element[0] == "-":
                            course_list = courses_to_exclude
                            parameter_value = element[1:]
                        else:
                            course_list = self._courses
                            parameter_value = element
                        
                        indexes = course_df[parameter] == parameter_value
                        course_list.extend(
                            list(course_df.loc[indexes, "coursecode"].values)
                        )

            if "coursecode" in self._course_parameters:
                for course in self._course_parameters["coursecode"]:
                    if course[0] == "-":
                        courses_to_exclude.append(course[1:])
                    else:
                        self._courses.append(course)

            # Remove duplicates
            self._courses = list(dict.fromkeys(self._courses))

            for course_to_exclude in courses_to_exclude:
                if course_to_exclude in self._courses:
                    self._courses.remove(course_to_exclude)

            if "search" in self._course_parameters:
                for search_query in self._course_parameters["search"]:
                    if search_query[0] == "-":
                        course_list = courses_to_exclude
                        regex = self.regexpify(search_query[1:])
                    else:
                        course_list = self._courses
                        regex = self.regexpify(search_query)

                    indexes = course_df["coursecode"].str.contains(regex)
                    course_list.extend(list(course_df["coursecode"].loc[indexes]))

        return self._courses

    @property
    def quantity(self):
        """How many of the courses selected by parameters have to be included"""
        
        if "_quantity" not in self.__dict__:
            self._quantity = len(self.courses)
        
        return self._quantity

    @property
    def course_combinations(self):
        """An iterable with all combinations of courses, that satisfy parameters."""

        return itertools.combinations(self.courses, self.quantity)

    @staticmethod
    def regexpify(search_query):
        """Turns a string into a Regex object.

        :param search_query: String.

        :return: Regex object.
        """
        for i, match in enumerate(re.finditer(r"[a-z]", search_query)):
            search_query = f"{search_query[:match.start()+i]}\\{search_query[match.start()+i:]}"
        return rf"{search_query}"

    def __len__(self):
        """Returns number of courses to be taken from instance.

        Also deals with bool, because bool(Object) == False if len(Object) == 0.
        """
        return self.quantity

    def __mul__(self, other):
        """Sets the quantity."""
        if isinstance(other, int):
            if other == 0:
                return CourseListPrimitive()
            else:
                return CourseListPrimitive(**self._course_parameters, quantity=other)
        else:
            raise TypeError("CourseListPrimitive instance can only be multiplied with "
                            f"int, not {type(other)}")

    def __and__(self, other):
        """Makes a CompoundCourseList object with relationship 'and'."""
        if isinstance(other, CourseListPrimitive):
            print("Make compound")
            return CompoundCourseList(self, other, relationship="and")
        elif isinstance(other, CompoundCourseList):
            return other and self
        else:
            raise TypeError("CourseListPrimitive instance can only be added "
                            "with another CourseListPrimitive instance, or a "
                            f"CompoundCourseList, not {type(other)}")

    def __or__(self, other):
        """Makes a CompoundCourseList object with relationship 'or'."""
        if isinstance(other, CourseListPrimitive):
            return CompoundCourseList(self, other, relationship="or")
        elif isinstance(other, CompoundCourseList):
            return other or self
        else:
            raise TypeError("CourseListPrimitive instance can only be added "
                            "with another CourseListPrimitive instance, or a "
                            f"CompoundCourseList, not {type(other)}")

    def __contains__(self, other):
        """Check if course or course list is selected by these parameters.

        If other is a course list, it checks if all courses in other can also be
        found in self.
        """
        if isinstance(other, str):
            return other in self.courses
        elif isinstance(other, (CourseListPrimitive, CompoundCourseList)):
            for course in other.courses:
                if course not in self:
                    return False
            return True
        
        return False

    def __hash__(self):
        """Hashes, makes a unique int, that represents the courses and quantity"""
        return hash((", ".join(self.courses), self.quantity))

    def __eq__(self, other):
        """Checks equality, by checking the hashes are the same"""

        if isinstance(other, CourseListPrimitive):
            if hash(self) == hash(other):
                return True
                
        return False

    @property
    def is_simple(self):
        """If all courses in list has to be taken, this is true.

        This means, if the quantity is just the default, the same as the amount of courses,
        this evaluates as True.
        """
        return len(self.courses) == self.quantity

    def implies(self, other):
        """Like __contains__, just harder. Other HAS to be done for self to fulfill.

                         Truth table, self.implies(other)
                                     self
                           fulfilled   |  not fulfilled
        other          ----------------|-----------------
         fulfilled     |      True     |      False     |
         not fulfilled |      True     |      True      |
                       ----------------------------------

        Called recursively by CompoundCourseList.

        :param other: String, CourseListPrimitive or CompoundCourseList.

        :return: Bool.
        """
        if isinstance(other, str):
            return other in self and self.is_simple

        elif isinstance(other, (CourseListPrimitive, CompoundCourseList)):
            for other_combo in other.course_combinations:
                for self_combo in self.course_combinations:
                    for course in other_combo:
                        if course not in self_combo:
                            return False

            return True

        else:
            raise TypeError("Only accepts other in the form of "
                            "CourseListPrimitive or CompoundCourseList instances, "
                            f"not {type(other)}")

    def requirements_not_fulfilled_by(self, other):
        """Makes a list of courses that would need to be taken to fulfill requirements.

        This primitives requirements is fulfilled if the courses in the other primitive
        and this primitives courses have self.quantity matches.

        The CourseListPrimitive returned is therefore either a copy of this with the same
        or a lower quantity value, or empty.

        :param other: CourseListPrimitive or CompoundCourseList specifying what courses are
                      to be checked if fulfill requirements set up by this primitive.

        :return: CourseListPrimitive of unfulfilled requirements.
        """
        if isinstance(other, (CourseListPrimitive, CompoundCourseList)):
            not_fulfilled = []
            for other_combo in other.course_combinations:
                for self_combo in self.course_combinations:
                    for course in self_combo:
                        if course not in other_combo:
                            not_fulfilled.append(course)
        else:
            raise TypeError("Only accepts requirements in the form of "
                            "CourseListPrimitive or CompoundCourseList instances, "
                            f"not {type(other)}")

        return list(dict.fromkeys(not_fulfilled))

    def assume_taken(self, course):
        """Assume a course has been taken, removing it, and reducing quantity by one.

        :param course: String course code.
        """
        if course in self:
            self.remove(course)
            self._quantity -= 1

    def __str__(self):
        """Prints out courses"""
        properties = []
        if "faculty" in self._course_parameters:
            properties.append(f"Faculty: {', '.join(self._course_parameters['faculty'])}")
        if "institute" in self._course_parameters:
            properties.append(f"Institute: {', '.join(self._course_parameters['institute'])}")
        if "coursecode" in self._course_parameters:
            properties.append(f"Coursecode: {', '.join(self._course_parameters['coursecode'])}")
        if "course_regexp" in self._course_parameters:
            properties.append(f"Regexp requirement: {self._course_parameters['course_regexp']}")

        return f"[{'. '.join(properties)}]"



class CompoundCourseList:
    def __init__(self, *course_lists, relationship="and"):
        """A set of CourseListPrimitives, or other CompoundCourseLists, with a logic relationship.

        The relationship can be either 'and' or 'or', and 

        :param *course_lists: CourseListPrimitives and/or CompoundCourseLists.
        :param relationship: 'and' or 'or'. 'and' by default. Is used in the is_fulfilled_by method.
                             In the is_fulfilled_by method, the truth value is dictated by the truth
                             value of this instances children, with the given relationship.

        :raise ValueError: If relationship isn't 'and' or 'or'.
        :raise TypeError: If type of course list isn't CompoundCourseList or CourseListPrimitive.
        """

        if not (relationship == "and" or relationship == "or"):
            raise ValueError(f"Relationship must be either 'and' or 'or', not {relationship}")

        for course_list in course_lists:
            if not isinstance(course_list, (CompoundCourseList, CourseListPrimitive)):
                raise TypeError("Can only create CompoundCourseList from other CompoundCourseLists"
                                f" or CourseListPrimitives, not {type(course_list)}")

        self.children = course_lists
        self.relationship = relationship

    # TODO: Make from_str factory method

    @property
    def courses(self):
        if "_courses" not in self.__dict__:
            self._courses = []

            for child in self.children:
                self._courses.extend(child.courses)

        return self._courses

    # TODO: Update self._courses and self._quantity when course is removed

    @staticmethod
    def _join_product(*iterables):
        """Helper function for course_combinations
        
        Flattens the results of itertools.product.
        """
        end_product = []
        for iterable in iterables:
            if len(iterable) > 1:
                end_product.extend(iterable)
            else:
                end_product.append(iterable[0])
        return tuple(end_product)

    @property
    def course_combinations(self):
        """An iterable with all combinations of courses that satisfy childrens parameters."""
        
        course_combinations_list = [child.course_combinations for child in self.children]
        
        if self.relationship == "and":
            course_combinations_prod = itertools.product(*course_combinations_list)
            course_combinations_iter = itertools.starmap(self._join_product, course_combinations_prod)
        else:
            course_combinations_iter = itertools.chain(*course_combinations_list)

        return course_combinations_iter

    def __and__(self, other):
        """Make new CompoundCourseList with 'and' relationship."""

        return CompoundCourseList(self, other, relationship="and")

    def __or__(self, other):
        """Make new CompoundCourseList with 'or' relationship."""

        return CompoundCourseList(self, other, relationship="or")

    def __contains__(self, other):
        """Check if course or course list is in self"""
        if isinstance(other, str):
            for child in self.children:
                if other in child:
                    return True
        else:
            for course in other.courses:
                if course not in self:
                    return False
            return True
        
        return False

    def __str__(self):
        """Prints out relationships between all children, and their contents"""
        return "{" + f" {f' {self.relationship} '.join([str(child) for child in self.children])}" + "}"

    def __len__(self):
        """Returns number of primitives and compounds in this compound.

        Also deals with bool, because bool(Object) == False if len(Object) == 0.
        """
        return len(self.children)

    def __hash__(self):
        """Hashes, makes a unique int, that represents the courses and quantity"""
        return hash(tuple([child.hash for child in self.children] + [self.relationship]))

    @property
    def is_simple(self):
        """If all courses in list has to be taken, this is true.

        This means, if the quantity is just the default, the same as the amount of courses,
        for all children, and the relationship is 'and', this evaluates as True.
        """
        if self.relationship == 'and':
            for child in self.children:
                if not child.is_simple:
                    return False
            return True
        else:
            return False

    def requirements_not_fulfilled_by(self, course_list):
        """Makes a list of courses that would need to be taken to fulfill requirements.

        This objects stipulated requirements is fulfilled if the courses in the primitive
        together make the statement
            'child1 relationship child2 relationship … childn',
        true. Finding the courses that need to be taken to fulfill requirements therefore
        means finding the subset of this object, that isn't at all fulfilled by the courses
        in the course_list parameter.

        Works recursively.

        :param course_list: CourseListPrimitive. Assumes quantity == len(course_list._courses).

        :return: CompoundCourseList of unfulfilled requirements.
        """
        new_compound = CompoundCourseList(
            *[child.requirements_not_fulfilled_by(course_list) for child in self.children],
            relationship=self.relationship
        )
        return new_compound

    def implies(self, other):
        """Like __contains__, just harder. Other HAS to be done for self to fulfill.

                         Truth table, self.implies(other)
                                     self
                           fulfilled   |  not fulfilled
        other          ----------------|-----------------
         fulfilled     |      True     |      False     |
         not fulfilled |      True     |      True      |
                       ----------------------------------

        :param other: String, CourseListPrimitive or CompoundCourseList.

        :return: Bool.
    
        :raise ValueError: if other is a string representing an unknown course code.
        :raise TypeError: if other isn't either a string, CourseListPrimitive or 
                          CompoundCourseList.
        """
        if isinstance(other, str):
            other = CourseListPrimitive(coursecode = other)
            if not other:
                raise ValueError(f"Not valid course.")
        elif isinstance(other, CourseListPrimitive):
            if self.relationship == "and":
                for child in self.children:
                    if child.implies(other):
                        return True

                # This is a bit hacky, and could probably be done smoother
                guaranteed_courses = []
                for child in self.children:
                    if len(child.courses) == child.quantity:
                        guaranteed_courses.extend(child.courses)
                self_guaranteed = CourseListPrimitive(coursecode=guaranteed_courses)
                if self_guaranteed.implies(other):
                    return True

                # TODO: Make combinatorically complicated test for other options 
                return False
            else:
                for child in self.children:
                    if not child.implies(other):
                        return False
                return True
            return False
        elif isinstance(other, CompoundCourseList):
            if other.relationship == "and":
                for child in other.children:
                    if not self.implies(child):
                        return False
                return True
            else:
                for child in other.children:
                    if self.implies(child):
                        return True
                return False
        else:
            raise TypeError("Only accepts str, CourseListPrimitive and CompoundCourseList, "
                            f"not {type(other)}")

    def simplify(self):
        """Simplifies the tree structure, removing redundancy.

        This is not able to remove tier-differing redundancy, where an overlapping
        set of requirements is given in two different levels of the tree.
        """
        for i, child in enumerate(self.children):
            if isinstance(child, CompoundCourseList):
                child.simplify()

                if len(child) == 1:
                    # Make it a primitive if it has only one child
                    child = child.children[0]
                    self.children[i] = child

                # Remove children that imply other children
                # TODO: Figure out if this is the same as the similar thing
                #       in implies
                if self.relationship == "or" and child.relationship == "or":
                    for e, grandchild in enumerate(child.children):
                        for j, other_child in enumerate(self.children):
                            if i != j:
                                if other_child.implies(grandchild):
                                    self.remove(grandchild)

            if child:
                # Compare it with its siblings
                for other_child in self.children[:i]:
                    if other_child.implies(child):
                        self.remove(child)
                    elif child.implies(other_child):
                        self.remove(other_child)

                    if self.relationship == "and":
                        if other_child.is_simple:
                            for course in other_child.courses:
                                if course in child:
                                    child.assume_taken(course)
                        if child.is_simple:
                            for course in child.courses:
                                if course in other_child:
                                    other_child.assume_taken(course)
            
            if not child:
                # Remove empty children
                self.remove(child)

    def remove(self, child):
        """Removes a child.

        :param child: CourseListPrimitive or CompoundCourseList, in self.children.
        """

        self.children.remove(child)

    def assume_taken(self, course):
        """Assume a course has been taken, removing it from children.

        :param course: String course code.
        """
        for child in self.children:
            child.assume_taken(course)
            if not child:
                self.remove(child)

    def __eq__(self, other):
        """Checks equality, by checking that all children are the same"""

        if isinstance(other, CompoundCourseList):
            if hash(self) == hash(other):
                return True

        return False
