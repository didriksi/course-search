import pytest

from CourseList import CourseListPrimitive, CompoundCourseList

@pytest.mark.parametrize(
    "test_case, str_course_parameters, quantity, course_parameters",
    [
        ("basic, list of courses", [], None, {"coursecode": ["MAT1100", "MAT1120"]}),
        ("list of courses, faculties and insitutes", [], None, {"faculty": ["hf"], "institute": ["mat"], "coursecode": ["MAT1100", "MAT1120"]}),
        ("list of courses and a faculty", [], None, {"faculty": ["hf"], "coursecode": ["MAT1100", "MAT1120"]}),
        ("search", [], None, {"faculty": ["-hf"], "search": ["MAT3..."]}),
        ("quantity", [], 2, {"faculty": ["-hf"], "search": ["MAT3..."]})
    ],
)
def test_valid_CourseListPrimitive_init(test_case, str_course_parameters, quantity, course_parameters):
    """Shadow test that some valid init calls don't produce errors."""
    CourseListPrimitive(*str_course_parameters, quantity=quantity, **course_parameters)

@pytest.mark.parametrize(
    "test_case, str_course_parameters, quantity, course_parameters, expected",
    [
        ("basic, list of courses", [], None, {"coursecode": ["MAT1100", "MAT1120"]}, ["MAT1100", "MAT1120"]),
        ("list of courses, faculties and insitutes", [], None, {"faculty": ["hf"], "institute": ["mat"], "coursecode": ["MAT1100", "MAT1120"]}, None),
        ("list of courses and a faculty", [], None, {"faculty": ["hf"], "coursecode": ["MAT1100", "MAT1120"]}, None),
        ("search", [], None, {"faculty": ["-hf"], "search": ["MAT3..."]}, None),
        ("quantity", [], 2, {"faculty": ["-hf"], "search": ["MAT3..."]}, None)
    ],
)
def test_valid_CourseListPrimitive_course(test_case, str_course_parameters, quantity, course_parameters, expected):
    """Test course property"""
    courseList = CourseListPrimitive(
                    *str_course_parameters,
                    quantity=quantity,
                    **course_parameters
                 )
    
    assert isinstance(courseList.courses, list), "Didn't return courses as list"

    if expected is not None:
        assert courseList.courses == expected

def test_CourseListPrimitive_contains():
    """Test __contains__ special method"""

    courseList = CourseListPrimitive(coursecode=["MAT1100"])
    
    assert "MAT1100" in courseList, "__contains__ method failed"
    # This can possibly fail if MAT1100 stops being a course found on UiO,
    # so that the course isn't in the dataframe

def test_CourseListPrimitive_str():
    """Test that str(), from_str() work.

    Implicitly and poorly also tests __eq__ and __hash__"""

    course_parameters = {"faculty": ["hf", "sv"], "coursecode": ["FIL1000"], "quantity": 2}
    courseList = CourseListPrimitive(**course_parameters)
    str_course_parameters = str(courseList)
    strCourseList = CourseListPrimitive.from_str(str_course_parameters)
    assert set(strCourseList.courses) == set(courseList.courses), "Courses don't match"
    assert strCourseList == courseList, "Equality failed"

def test_CourseListPrimitive_to_Compound():
    """Tests __mul__, __and__ and __or__"""

    courseList_1 = CourseListPrimitive(search=["MAT3..."])
    courseList_2 = CourseListPrimitive(coursecode=["MAT3440", "IN3200"])
    
    double_courseList_1 = courseList_1*2
    assert isinstance(double_courseList_1, CourseListPrimitive), "__mul__ changed type"
    assert double_courseList_1.quantity == 2, "__mul__ didn't change quantity"
    
    compound = courseList_1 & courseList_2
    print(compound)
    print(type(compound))
    assert isinstance(compound, CompoundCourseList), "__and__ didn't turn primitives into compound"
    
    compound_2 = courseList_1*3 | courseList_2
    assert compound_2.relationship == "or", "__or__ didn't give compound with 'or'-relationship"

def test_is_simple():
    """Tests is the is_simple method of both classes work."""

    simple_1 = CourseListPrimitive(faculty=["hf"])
    simple_2 = CourseListPrimitive(search=["STK1...", "STK2..."])
    not_simple = simple_1*2

    assert simple_1.is_simple and simple_2.is_simple
    assert not not_simple.is_simple, "Misclassified unsimple list"

    assert (simple_1 & simple_2).is_simple, "Simple compound misclassified"
    assert not (simple_1 | simple_2).is_simple, "Unsimple compound misclassified"
    assert not (not_simple & simple_2).is_simple, "Unsimple compound misclassified"

def test_implies():
    """Test that the implies method works."""

    implied_1 = CourseListPrimitive(coursecode=["MAT1100"])
    implies_1 = CourseListPrimitive(coursecode=["MAT1100", "MAT1110", "MAT1120"])
    assert implies_1.implies(implied_1), "Missed simple implication"

    implied_2 = CourseListPrimitive(search=["MATdddd"], quantity=2)
    implies_2 = CourseListPrimitive(coursecode=["MAT1100", "MAT1110"])
    assert implies_2.implies(implied_2), "Missed quantity based implication"

    implies_1_compound = implies_1*1 & implied_1
    assert implies_1_compound.implies(implied_1), "Missed simple compound implication"

    implied_3 = implies_1*1
    implies_3_compound = implied_1 & CourseListPrimitive(coursecode=["MAT1110", "MAT1120"])
    assert implies_3_compound.implies(implied_3), "Missed 'and'-implication"

# TODO: Make tests for: requirements_not_fulfilled_by and assume_taken 

def test_course_combinations():
    """Test course_combinations method, for both classes."""

    courseList_1 = CourseListPrimitive(coursecode=["MAT1100", "MAT1110", "MAT1120"])
    assert list(courseList_1.course_combinations) == [("MAT1100", "MAT1110", "MAT1120")]

    expected = [("MAT1100", "MAT1110"), ("MAT1100", "MAT1120"), ("MAT1110", "MAT1120")]
    assert list((courseList_1*2).course_combinations) == expected, "Couldn't find simple combinations"

    courseList_2 = CourseListPrimitive(coursecode=["STK1100", "STK1110"], quantity=1)
    compound_1 = courseList_1*2 | courseList_2

    expected = [
                    ("MAT1100", "MAT1110"),
                    ("MAT1100", "MAT1120"),
                    ("MAT1110", "MAT1120"),
                    ("STK1100",),
                    ("STK1110",)
    ]
    assert list(compound_1.course_combinations) == expected, "Couldn't find compound 'or'-combinations"

    compound_2 = courseList_1 & courseList_2
    expected = [
                    ("MAT1100", "MAT1110", "MAT1120", "STK1100"),
                    ("MAT1100", "MAT1110", "MAT1120", "STK1110")
    ]
    assert list(compound_2.course_combinations) == expected, "Couldn't find compound 'and'-combinations"















