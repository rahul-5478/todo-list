from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('delete/<int:id>/', views.deleteTask, name='delete_task'),
    path('toggle/<int:id>/', views.toggleTask, name='toggle_task'),
    path('edit/<int:id>/', views.editTask, name='edit_task'),
    path('clear-completed/', views.clearCompleted, name='clear_completed'),
    path('reorder/', views.reorderTasks, name='reorder_tasks'),
    path('category/add/', views.addCategory, name='add_category'),
    path('category/delete/<int:id>/', views.deleteCategory, name='delete_category'),
    path('export/csv/', views.exportCSV, name='export_csv'),
]