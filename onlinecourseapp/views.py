from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Course, Choice, Submission


def course_details(request, course_id):
    course = get_object_or_404(
        Course.objects.prefetch_related(
            "lessons",
            "questions__choices"
        ),
        id=course_id
    )

    return render(
        request,
        "onlinecourseapp/course_details_bootstrap.html",
        {"course": course}
    )


@login_required
@require_POST
def submit(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    selected_choices = []
    score = 0

    for question in course.questions.all():
        choice_id = request.POST.get(f"choice_{question.id}")

        if choice_id:
            choice = get_object_or_404(
                Choice,
                id=choice_id,
                question=question
            )

            selected_choices.append(choice)

            if choice.is_correct:
                score += 1

    submission = Submission.objects.create(
        user=request.user,
        course=course,
        score=score
    )

    submission.selected_choices.set(selected_choices)

    return redirect(
        "show_exam_result",
        submission_id=submission.id
    )


@login_required
def show_exam_result(request, submission_id):
    submission = get_object_or_404(
        Submission,
        id=submission_id,
        user=request.user
    )

    questions = submission.course.questions.prefetch_related("choices")

    results = []

    for question in questions:
        selected = submission.selected_choices.filter(
            question=question
        ).first()

        correct = question.choices.filter(
            is_correct=True
        ).first()

        results.append({
            "question": question,
            "selected": selected,
            "correct": correct,
            "is_correct": (
                selected is not None
                and correct is not None
                and selected.id == correct.id
            ),
        })

    total_questions = questions.count()

    return render(
        request,
        "onlinecourseapp/exam_result.html",
        {
            "submission": submission,
            "results": results,
            "total_questions": total_questions,
        }
    )