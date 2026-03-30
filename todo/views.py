from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
import csv

from .models import Task, Category


def index(request):
    filter_by = request.GET.get('filter', 'all')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '').strip()

    tasks = Task.objects.select_related('category').all()

    if filter_by == 'active':
        tasks = tasks.filter(completed=False)
    elif filter_by == 'completed':
        tasks = tasks.filter(completed=True)

    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    if category_filter:
        tasks = tasks.filter(category__id=category_filter)

    if search_query:
        tasks = tasks.filter(title__icontains=search_query)

    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        priority = request.POST.get('priority', 'medium')
        due_date = request.POST.get('due_date', '') or None
        category_id = request.POST.get('category', '') or None

        if not title:
            messages.error(request, "Task title cannot be empty.")
            return redirect('/')
        if len(title) > 200:
            messages.error(request, "Task title is too long (max 200 characters).")
            return redirect('/')

        category = None
        if category_id:
            category = Category.objects.filter(id=category_id).first()

        Task.objects.create(
            title=title,
            priority=priority,
            due_date=due_date,
            category=category
        )
        messages.success(request, f'Task "{title}" added!')
        return redirect('/')

    today = timezone.now().date()

    context = {
        'tasks': tasks,
        'filter': filter_by,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'total_count': Task.objects.count(),
        'done_count': Task.objects.filter(completed=True).count(),
        'categories': Category.objects.all(),
        'today': today,
    }
    return render(request, 'todo/index.html', context)


def deleteTask(request, id):
    task = get_object_or_404(Task, id=id)
    title = task.title
    task.delete()
    messages.success(request, f'Task "{title}" deleted.')
    return redirect('/')


def toggleTask(request, id):
    task = get_object_or_404(Task, id=id)
    task.completed = not task.completed
    task.save()
    return redirect('/')


def editTask(request, id):
    task = get_object_or_404(Task, id=id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        priority = request.POST.get('priority', task.priority)
        due_date = request.POST.get('due_date', '') or None
        category_id = request.POST.get('category', '') or None

        if not title:
            messages.error(request, "Task title cannot be empty.")
            return redirect('/')

        task.title = title
        task.priority = priority
        task.due_date = due_date
        task.category = Category.objects.filter(id=category_id).first() if category_id else None
        task.save()
        messages.success(request, f'Task updated!')
    return redirect('/')


def clearCompleted(request):
    if request.method == "POST":
        deleted_count, _ = Task.objects.filter(completed=True).delete()
        messages.success(request, f'{deleted_count} completed task(s) cleared.')
    return redirect('/')


@require_POST
def reorderTasks(request):
    """Handle drag & drop reorder — expects JSON body: {order: [id1, id2, ...]}"""
    try:
        data = json.loads(request.body)
        order_list = data.get('order', [])
        for index, task_id in enumerate(order_list):
            Task.objects.filter(id=task_id).update(order=index)
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def addCategory(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '#6366f1')
        if name:
            Category.objects.get_or_create(name=name, defaults={'color': color})
            messages.success(request, f'Category "{name}" added!')
    return redirect('/')


def deleteCategory(request, id):
    category = get_object_or_404(Category, id=id)
    category.delete()
    messages.success(request, 'Category deleted.')
    return redirect('/')


def exportCSV(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tasks.csv"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Priority', 'Category', 'Due Date', 'Completed', 'Created At'])

    for task in Task.objects.select_related('category').all():
        writer.writerow([
            task.title,
            task.priority,
            task.category.name if task.category else '',
            task.due_date or '',
            'Yes' if task.completed else 'No',
            task.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    return response