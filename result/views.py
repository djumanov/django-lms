from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from accounts.models import User, Student
from app.models import Session, Semester
from course.models import Course
from accounts.decorators import lecturer_required, student_required
from .models import TakenCourse, Result

User = settings.AUTH_USER_MODEL

#pdf
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse


cm = 2.54

from SMS.settings import MEDIA_ROOT, BASE_DIR, STATIC_URL
import os

from .models import *
# ########################################################
# Score Add & Add for
# ########################################################
@login_required
@lecturer_required
def add_score(request):
    """ 
    Shows a page where a lecturer will select a course allocated to him for score entry.
    in a specific semester and session 

    """
    current_session = Session.objects.get(is_current_session=True)
    current_semester = get_object_or_404(Semester, is_current_semester=True, session=current_session)
    # semester = Course.objects.filter(allocated_course__lecturer__pk=request.user.id, semester=current_semester)
    courses = Course.objects.filter(allocated_course__lecturer__pk=request.user.id).filter(semester=current_semester)
    context = {
        "current_session": current_session,
        "current_semester": current_semester,
        "courses": courses,
    }
    return render(request, 'result/add_score.html', context)


@login_required
@lecturer_required
def add_score_for(request, id):
    """
    Shows a page where a lecturer will add score for students that are taking courses allocated to him
    in a specific semester and session 
    """
    current_session = Session.objects.get(is_current_session=True)
    current_semester = get_object_or_404(Semester, is_current_semester=True, session=current_session)
    if request.method == 'GET':
        courses = Course.objects.filter(allocated_course__lecturer__pk=request.user.id).filter(
            semester=current_semester)
        course = Course.objects.get(pk=id)
        # myclass = Class.objects.get(lecturer__pk=request.user.id)
        # myclass = get_object_or_404(Class, lecturer__pk=request.user.id)

        # students = TakenCourse.objects.filter(course__allocated_course__lecturer__pk=request.user.id).filter(
        #     course__id=id).filter(student__allocated_student__lecturer__pk=request.user.id).filter(
        #         course__semester=current_semester)
        students = TakenCourse.objects.filter(course__allocated_course__lecturer__pk=request.user.id).filter(
            course__id=id).filter(course__semester=current_semester)
        context = {
            "title": "Submit Score | DjangoSMS",
            "courses": courses,
            "course": course,
            # "myclass": myclass,
            "students": students,
            "current_session": current_session,
            "current_semester": current_semester,
        }
        return render(request, 'result/add_score_for.html', context)

    if request.method == 'POST':
        ids = ()
        data = request.POST.copy()
        data.pop('csrfmiddlewaretoken', None)  # remove csrf_token
        for key in data.keys():
            ids = ids + (str(key),)  # gather all the all students id (i.e the keys) in a tuple
        for s in range(0, len(ids)):  # iterate over the list of student ids gathered above
            student = TakenCourse.objects.get(id=ids[s])
            # print(student)
            # print(student.student)
            # print(student.student.department.id)
            courses = Course.objects.filter(level=student.student.level).filter(program__pk=student.student.department.id).filter(
                semester=current_semester)  # all courses of a specific level in current semester
            total_credit_in_semester = 0
            for i in courses:
                if i == courses.count():
                    break
                else:
                    total_credit_in_semester += int(i.credit)
            score = data.getlist(ids[s])  # get list of score for current student in the loop
            assignment = score[0]  # subscript the list to get the fisrt value > ca score
            mid_exam = score[1]  # do the same for exam score
            quiz = score[2]
            attendance = score[3]
            final_exam = score[4]
            obj = TakenCourse.objects.get(pk=ids[s])  # get the current student data
            obj.assignment = assignment  # set current student assignment score
            obj.mid_exam = mid_exam  # set current student mid_exam score
            obj.quiz = quiz  # set current student quiz score
            obj.attendance = attendance  # set current student attendance score
            obj.final_exam = final_exam  # set current student final_exam score

            obj.total = obj.get_total(assignment=assignment, mid_exam=mid_exam, quiz=quiz, attendance=attendance, final_exam=final_exam)
            obj.grade = obj.get_grade(total=obj.total)

            # obj.total = obj.get_total(assignment, mid_exam, quiz, attendance, final_exam)
            # obj.grade = obj.get_grade(assignment, mid_exam, quiz, attendance, final_exam)

            obj.point = obj.get_point(grade=obj.grade)

            obj.comment = obj.get_comment(grade=obj.grade)
            # obj.carry_over(obj.grade)
            # obj.is_repeating()
            obj.save()
            gpa = obj.calculate_gpa(total_credit_in_semester)
            cgpa = obj.calculate_cgpa()

            try:
                a = Result.objects.get(student=student.student, semester=current_semester, session=current_session, level=student.student.level)
                a.gpa = gpa
                a.cgpa = cgpa
                a.save()
            except:
                Result.objects.get_or_create(student=student.student, gpa=gpa, semester=current_semester,
                                             session=current_session, level=student.student.level)

            # try:
            #     a = Result.objects.get(student=student.student, semester=current_semester, level=student.student.level)
            #     a.gpa = gpa
            #     a.cgpa = cgpa
            #     a.save()
            # except:
            #     Result.objects.get_or_create(student=student.student, gpa=gpa, semester=current_semester, level=student.student.level)

        messages.success(request, 'Successfully Recorded! ')
        return HttpResponseRedirect(reverse_lazy('add_score_for', kwargs={'id': id}))
    return HttpResponseRedirect(reverse_lazy('add_score_for', kwargs={'id': id}))
# ########################################################


@login_required
@student_required
def grade_result(request):
    student = Student.objects.get(student__pk=request.user.id)
    courses = TakenCourse.objects.filter(student__student__pk=request.user.id).filter(course__level=student.level)
    # total_credit_in_semester = 0
    results = Result.objects.filter(student__student__pk=request.user.id)

    result_set = set()

    for result in results:
        result_set.add(result.session)

    sorted_result = sorted(result_set)

    total_first_semester_credit = 0
    total_sec_semester_credit = 0
    for i in courses:
        if i.course.semester == "First":
            total_first_semester_credit += int(i.course.credit)
        if i.course.semester == "Second":
            total_sec_semester_credit += int(i.course.credit)

    previousCGPA = 0
    # previousLEVEL = 0
    # calculate_cgpa
    for i in results:
        previousLEVEL = i.level
        try:
            a = Result.objects.get(student__student__pk=request.user.id, level=previousLEVEL, semester="Second")
            previousCGPA = a.cgpa
            break
        except:
            previousCGPA = 0

    context = {
        "courses": courses,
        "results": results,
        "sorted_result": sorted_result,
        "student": student,
        'total_first_semester_credit': total_first_semester_credit,
        'total_sec_semester_credit': total_sec_semester_credit,
        'total_first_and_second_semester_credit': total_first_semester_credit + total_sec_semester_credit,
        "previousCGPA": previousCGPA,
    }

    return render(request, 'result/grade_results.html', context)


@login_required
@student_required
def assessment_result(request):
    student = Student.objects.get(student__pk=request.user.id)
    courses = TakenCourse.objects.filter(student__student__pk=request.user.id, course__level=student.level)
    result = Result.objects.filter(student__student__pk=request.user.id)

    context = {
        "courses": courses,
        "result": result,
        "student": student,
    }
    
    return render(request, 'result/assessment_results.html', context)
