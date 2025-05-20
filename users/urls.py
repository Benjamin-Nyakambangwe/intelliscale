from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # If you need to customize logout more

app_name = 'users'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='users:login'), name='logout'), 

    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),
    path('dashboard/operator/', views.operator_dashboard, name='operator_dashboard'),
    path('dashboard/default/', views.default_dashboard, name='default_dashboard'), # Fallback

    # User Management URLs
    path('manage/', views.user_list, name='user_list'),
    path('manage/create/', views.user_create, name='user_create'),
    path('manage/<int:pk>/', views.user_detail, name='user_detail'),
    path('manage/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('manage/<int:pk>/delete/', views.user_delete, name='user_delete'),
]