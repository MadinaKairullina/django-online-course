from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import Course, Lesson, Enrollment, Question, Choice, Submission

class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        return Course.objects.order_by('-total_enrollment')[:10]

class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_details_bootstrap.html'

def enroll(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, pk=course_id)
        user = request.user
        if user.is_authenticated:
            Enrollment.objects.get_or_create(user=user, course=course)
            course.total_enrollment += 1
            course.save()
            return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))

def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    enrollment, _ = Enrollment.objects.get_or_create(user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)
    
    choice_ids = []
    for key, value in request.POST.items():
        if key.startswith('choice_'):
            choice_ids.append(int(value))
            
    for choice_id in choice_ids:
        choice = get_object_or_404(Choice, id=choice_id)
        submission.choices.add(choice)
        
    return redirect('onlinecourse:show_exam_result', course_id=course.id, submission_id=submission.id)

def show_exam_result(request, course_id, submission_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    selected_ids = submission.choices.values_list('id', flat=True)
    
    total_score = 0
    grade = 0
    for question in course.question_set.all():
        total_score += question.grade
        if question.is_get_score(selected_ids):
            grade += question.grade
            
    context['course'] = course
    context['grade'] = grade
    context['total_score'] = total_score
    context['submission'] = submission
    return render(request, 'onlinecourse/exam_result.html', context)
